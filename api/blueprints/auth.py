import uuid
from datetime import datetime
from typing import Dict, Any

from flask import url_for, request, current_app
from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt
)
from flask_mail import Message
from flask_smorest import Blueprint
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError

from api.errors import (
    BadRequestError,
    ConflictError,
    ForbiddenError,
    InternalServerError,
    NotFoundError, UnauthorizedError
)
from api.models.models import (
    User,
    RoleEnum,
    Invitation,
    RevokedToken,
    InvitationStatusEnum,
    Organization
)
from api.schemas.schemas import (
    UserRegistrationSchema,
    UserLoginSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    MessageSchema
)
from api.utils.utils import (
    generate_confirmation_token,
    confirm_token,
    generate_reset_token,
    confirm_reset_token,
    verify_invitation_token
)
from ..extensions import db, mail
from ..utils.email_utils import send_account_confirmation_email, send_password_reset_email

auth_bp = Blueprint("Auth", "auth", url_prefix="/auth", description="Authentication services")


@auth_bp.route("/register")
class UserRegister(MethodView):
    """Endpoint for new user registration with dual registration workflows.

    Supports two registration scenarios:
    1. Invitation-based registration using valid invitation tokens for organization members
    2. Self-registration for Guest users requiring email confirmation

    Methods:
        POST: Create new user account with provided credentials and optional invitation token
    """

    @auth_bp.arguments(UserRegistrationSchema)
    @auth_bp.response(201, MessageSchema)
    def post(self, user_data: Dict[str, Any]):
        """Register new user account.

            Args:
                user_data: User registration data containing:
                    - email: Unique email address for the account
                    - password: Account password
                    - full_name: User's full name
                    - invitation_token: Optional token for organization invitations

            Returns:
                Dictionary with operation status message and tokens (if invitation-based)

            Raises:
                ConflictError: If email already exists in system
                BadRequestError: For invalid/expired invitation tokens or role mismatches
                InternalServerError: For database or email service failures
            """

        email = user_data.get("email")
        password = user_data["password"]
        full_name = user_data["full_name"]
        invitation_token = user_data.get("token")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            raise ConflictError(f"User with email '{email}' already exists.")
        if invitation_token:
            try:
                invitation_id = verify_invitation_token(invitation_token, max_age=604800)
            except SignatureExpired:
                raise BadRequestError("Invitation token has expired.")
            except BadSignature:
                raise BadRequestError("Invalid invitation token.")


            invitation = Invitation.query.filter_by(
                id=invitation_id,
                token=invitation_token,
                status=InvitationStatusEnum.PENDING
            ).first()

            if not invitation:
                raise BadRequestError("Invalid or already responded invitation token.")
            if invitation.expires_at < datetime.utcnow():
                raise BadRequestError("Invitation token has expired.")

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

            invitation.status = InvitationStatusEnum.ACCEPTED
            invitation.is_used = True
            invitation.responded_at = datetime.utcnow()

            try:
                db.session.add(new_user)
                db.session.commit()
            except SQLAlchemyError as exc:
                db.session.rollback()
                raise InternalServerError(f"Database error during registration: {str(exc)}")

            access_token = create_access_token(
                identity=new_user.id,
                additional_claims={"email": new_user.email, "role": new_user.role.value}
            )

            organization = Organization.query.get(invitation.organization_id) if invitation.organization_id else None
            org_name = organization.name if organization else "Your Organization"

            msg = Message(
                subject=f"Welcome to {org_name}",
                recipients=[new_user.email],
                body=(
                    f"Hello {new_user.full_name},\n\n"
                    f"Welcome to {org_name}!\n"
                    f"You have been successfully registered as {new_user.role.value}.\n\n"
                    f"Email: {new_user.email}\n"
                    "Password: [Your chosen password]\n\n"
                    f"Best regards,\n"
                    f"{org_name}"
                )
            )
            try:
                mail.send(msg)
            except Exception as exc:
                return {
                    "message": (
                        "Registration successful, but sending the welcome email failed."
                    ),
                    "access_token": access_token
                }

            return {
                "message": "Registration successful.",
                "access_token": access_token
            }

        user = User(
            email=email,
            full_name=full_name,
            role=RoleEnum.GUEST,
            is_confirmed=False
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as exc:
            db.session.rollback()
            raise InternalServerError(f"Database error during registration: {str(exc)}")

        token = generate_confirmation_token(user.email)
        frontend_url = f"https://127.0.0.1:5000/auth/verify-email/"
        confirmation_url = f"{frontend_url}?token={token}"
        try:
            send_account_confirmation_email(user, confirmation_url)
        except Exception as exc:
            return {
                "message": (
                    "Guest registered successfully, but the confirmation email could "
                    f"not be sent: {str(exc)}"
                )
            },400

        return {"message": "Guest registered successfully. Please confirm your email."}


@auth_bp.route("/verify-email/")
class ConfirmEmail(MethodView):
    """Endpoint for email address confirmation through validation tokens.

    Methods:
        GET: Validate confirmation token from query parameters and activate user account
    """

    def get(self) -> Dict[str, Any]:
        """Confirm user email address using validation token from query parameters.

        Query Parameters:
            token: Email confirmation JWT token sent to user's email

        Returns:
            Success message or notification if already confirmed

        Raises:
            BadRequestError: For missing, expired, or invalid confirmation tokens
            NotFoundError: If no user exists for the email in the token
        """
        token = request.args.get('token')
        print(token)
        if not token:
            raise BadRequestError("Missing token parameter in request.")

        try:
            email = confirm_token(token)
        except SignatureExpired:
            raise BadRequestError("The confirmation link has expired.")
        except BadSignature:
            raise BadRequestError("Invalid confirmation token.")

        user = User.query.filter_by(email=email).first()
        if not user:
            raise NotFoundError("User not found.")

        if user.is_confirmed:
            return {"message": "Account already confirmed."}

        user.is_confirmed = True
        access_token = create_access_token(
            identity=user.id,
            additional_claims={"email": user.email, "role": user.role.value}
        )
        db.session.commit()
        return {"message": "Email confirmed successfully.", "access_token": access_token}


@auth_bp.route("/login")
class UserLogin(MethodView):
    """Endpoint for user authentication and JWT token generation.

      Methods:
          POST: Authenticate user credentials and return access/refresh tokens
      """
    @auth_bp.arguments(UserLoginSchema)
    def post(self, login_data: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate user and generate JWT tokens.

        Args:
            login_data: Authentication credentials containing:
                - email: Registered user email
                - password: Account password

        Returns:
            Dictionary containing access and refresh JWT tokens

        Raises:
            UnauthorizedError: For invalid credentials
            ForbiddenError: If email confirmation is pending
        """
        email = login_data["email"]
        password = login_data["password"]
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            raise UnauthorizedError("Invalid credentials.")
        if not user.is_confirmed:
            raise ForbiddenError("Email not confirmed.")

        access_token = create_access_token(
            identity=user.id,
            additional_claims={"email": user.email, "role": user.role.value}
        )
        return {
            "access_token": access_token
        }


@auth_bp.route("/password-reset-request")
class PasswordResetRequest(MethodView):
    """Endpoint for initiating password reset workflow.

    Methods:
        POST: Generate and send password reset token to registered email
    """
    @auth_bp.arguments(PasswordResetRequestSchema)
    def post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate password reset process by email.

        Args:
            data: Contains email address for password reset

        Returns:
            Status message regardless of email existence (security measure)

        Note:
            Always returns success message to prevent email enumeration
        """
        email = data["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "If the email exists, a reset link has been sent."}

        token = generate_reset_token(user.email)
        reset_url = url_for("Auth.PasswordReset", token=token, _external=True)
        try:
            send_password_reset_email(user, reset_url)
        except Exception as exc:
            return {
                "message": (
                    f"Password reset email could not be sent {str(exc)}"
                )
            }

        return {"message": "If the email exists, a reset link has been sent."}


@auth_bp.route("/password-reset")
class PasswordReset(MethodView):
    """Endpoint for completing password reset process.

    Methods:
        POST: Validate reset token and update user password
    """
    @auth_bp.arguments(PasswordResetSchema)
    def post(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize password reset with token and new password.

        Args:
            data: Contains reset token and new password

        Returns:
            Success message upon password update

        Raises:
            BadRequestError: For invalid/expired reset tokens
            NotFoundError: If no user exists for the email in valid token
        """
        try:
            email = confirm_reset_token(data["token"])
        except SignatureExpired:
            raise BadRequestError("The reset link has expired.")
        except BadSignature:
            raise BadRequestError("Invalid reset token.")

        user = User.query.filter_by(email=email).first()
        if not user:
            raise NotFoundError("User not found.")

        user.set_password(data["new_password"])
        db.session.commit()
        return {"message": "Password has been reset successfully."}


@auth_bp.route("/logout")
class UserLogout(MethodView):
    """Endpoint for JWT token revocation and user logout.

    Methods:
        POST: Invalidate current JWT token
    """
    @jwt_required()
    def post(self) -> Dict[str, Any]:
        """Revoke current authentication token.

        Returns:
            Success message upon token revocation

        Raises:
            InternalServerError: For token revocation storage failures

        Security:
            Requires valid JWT in Authorization header
        """
        try:
            jti = get_jwt()["jti"]
            revoked_token = RevokedToken(jti=jti)
            db.session.add(revoked_token)
            db.session.commit()
            return {"message": "Successfully logged out."}
        except Exception as exc:
            raise InternalServerError(f"An error occurred during logout: {str(exc)}")
