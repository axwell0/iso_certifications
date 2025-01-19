import uuid
from datetime import datetime

from flask import url_for
from flask.views import MethodView
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt
from flask_mail import Message
from flask_smorest import Blueprint
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import User, RoleEnum, Invitation, RevokedToken, InvitationStatusEnum, Organization
from api.schemas.schemas import UserRegistrationSchema, UserLoginSchema, PasswordResetRequestSchema, \
    PasswordResetSchema, MessageSchema, RegisterInvitationSchema
from ..extensions import db, mail
from api.utils.utils import generate_confirmation_token, confirm_token, generate_reset_token, confirm_reset_token, \
    verify_invitation_token

auth_bp = Blueprint('Auth', 'auth', url_prefix='/auth', description='Authentication services')


@auth_bp.route('/register')
class UserRegister(MethodView):
    @auth_bp.arguments(UserRegistrationSchema)
    @auth_bp.response(201, MessageSchema)
    def post(self, user_data):
        """
        Register a new user.
        - Guests can self-register without an invitation.
        - Employees and Managers must register via an invitation token.
        """
        email = user_data['email']
        password = user_data['password']
        full_name = user_data['full_name']
        invitation_token = user_data.get('invitation_token')

        if invitation_token:
            return RegisterInvitation().post(user_data)
        else:
            role = RoleEnum.GUEST
            if User.query.filter_by(email=email).first():
                return {"message": "User already exists."}, 400

            user = User(
                email=email,
                full_name=full_name,
                role=role,
                is_confirmed=False
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            token = generate_confirmation_token(user.email)
            confirm_url = url_for('Auth.ConfirmEmail', token=token, _external=True)
            msg = Message('Confirm Your Email', recipients=[email])
            msg.body = f'Please click the link to confirm your email: <a href="{confirm_url}"> cock </a>'
            mail.send(msg)

            return {"message": "Guest registered successfully. Please confirm your email.", "obj":user}, 201



@auth_bp.route('/register_invitation')
class RegisterInvitation(MethodView):
    @auth_bp.arguments(RegisterInvitationSchema)
    @auth_bp.response(201, MessageSchema)
    def post(self, registration_data):
        """
        Register a new user via invitation token.
        """
        token = registration_data['token']
        password = registration_data['password']
        full_name = registration_data['full_name']

        try:
            # Decode and verify the token (max_age matches invitation expiry)
            token_payload = verify_invitation_token(token, max_age=7*24*3600)
            invitation_id = token_payload.get('invitation_id')
            token_role_str = token_payload.get('role')
        except SignatureExpired:
            return {"message": "Invitation token has expired."}, 400
        except BadSignature:
            return {"message": "Invalid invitation token."}, 400

        invitation = Invitation.query.filter_by(id=invitation_id, token=token, status=InvitationStatusEnum.PENDING).first()
        if not invitation:
            return {"message": "Invalid or already responded invitation token."}, 400

        if invitation.expires_at < datetime.utcnow():
            return {"message": "Invitation token has expired."}, 400

        # Check if the email already exists
        existing_user = User.query.filter_by(email=invitation.email).first()
        if existing_user:
            return {"message": "A user with this email already exists."}, 400

        # Ensure the role in the token matches the invitation's role
        if token_role_str != invitation.role.value:
            return {"message": "Invitation role mismatch."}, 400

        # Create a new user
        new_user = User(
            id=str(uuid.uuid4()),
            email=invitation.email,
            full_name=full_name,
            role=invitation.role,
            organization_id=invitation.organization_id,
            certification_body_id=invitation.certification_body_id,
            is_confirmed=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        new_user.set_password(password)

        # Update invitation status
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.add(new_user)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {"message": "An error occurred during registration."}, 500

        # Generate JWT tokens
        access_token = create_access_token(identity=new_user.id, additional_claims={
            "email": new_user.email,
            "role": new_user.role.value
        })
        refresh_token = create_refresh_token(identity=new_user.id)

        # Send welcome email
        organization = Organization.query.get(invitation.organization_id) if invitation.organization_id else None
        org_name = organization.name if organization else "Your Company"

        confirmation_subject = f'Welcome to {org_name}'
        confirmation_body = f'''
        Hello {new_user.full_name},

        Welcome to {org_name}!
        You have been successfully registered as an {new_user.role.value}.

        You can now log in to your account using the following credentials:
        Email: {new_user.email}
        Password: [Your Password]  # It's recommended to have users set their password securely.

        Best regards,
        {org_name}
        '''

        msg = Message(
            subject=confirmation_subject,
            recipients=[new_user.email],
            body=confirmation_body
        )
        try:
            mail.send(msg)
        except Exception:
            return {"message": "Failed to send welcome email."}, 500

        return {
            "message": "Registration successful.",
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 201


@auth_bp.route('/confirm/<token>')
class ConfirmEmail(MethodView):
    def get(self, token):
        """Confirm user's email address"""
        try:
            email = confirm_token(token)
        except SignatureExpired:
            return {"message": "The confirmation link has expired."}, 400
        except BadSignature:
            return {"message": "Invalid confirmation token."}, 400

        user = User.query.filter_by(email=email).first_or_404(description="User not found.")
        if user.is_confirmed:
            return {"message": "Account already confirmed."}, 200
        user.is_confirmed = True
        db.session.commit()
        return {"message": "Email confirmed successfully."}, 200


@auth_bp.route('/login')
class UserLogin(MethodView):
    @auth_bp.arguments(UserLoginSchema)
    def post(self, login_data):
        """User login"""
        email = login_data['email']
        password = login_data['password']
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"message": "Invalid credentials."}, 401
        if not user.is_confirmed:
            return {"message": "Email not confirmed."}, 403

        access_token = create_access_token(identity=user.id, additional_claims={
            "email": user.email,
            "role": user.role.value
        })
        refresh_token = create_refresh_token(identity=user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200


@auth_bp.route('/password-reset-request')
class PasswordResetRequest(MethodView):
    @auth_bp.arguments(PasswordResetRequestSchema)
    def post(self, data):
        """Request a password reset"""
        email = data['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "If the email exists, a reset link has been sent."}, 200

        # Generate reset token
        token = generate_reset_token(user.email)
        reset_url = url_for('Auth.PasswordReset', token=token, _external=True)
        msg = Message('Password Reset Request', recipients=[email])
        msg.body = f'Please click the link to reset your password: {reset_url}'
        mail.send(msg)

        return {"message": "If the email exists, a reset link has been sent."}, 200


@auth_bp.route('/password-reset')
class PasswordReset(MethodView):
    @auth_bp.arguments(PasswordResetSchema)
    def post(self, data):
        """Reset the user's password"""
        try:
            email = confirm_reset_token(data['token'])
        except SignatureExpired:
            return {"message": "The reset link has expired."}, 400
        except BadSignature:
            return {"message": "Invalid reset token."}, 400

        user = User.query.filter_by(email=email).first_or_404(description="User not found.")
        new_password = data['new_password']
        user.set_password(new_password)
        db.session.commit()
        return {"message": "Password has been reset successfully."}, 200


@auth_bp.route('/logout')
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        """Logout a user by revoking their current access token"""
        try:
            jti = get_jwt()['jti']
            revoked_token = RevokedToken(jti=jti)
            db.session.add(revoked_token)
            db.session.commit()
            return {"message": "Successfully logged out."}, 200
        except Exception as e:
            return {"message": "An error occurred during logout."}, 500