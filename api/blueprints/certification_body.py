from datetime import datetime, timedelta
from flask import abort, request
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from flask_smorest import Blueprint
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import (
    User, db, Invitation, RoleEnum, InvitationStatusEnum,
    RequestStatusEnum, CertificationBodyCreationRequest, CertificationBody
)
from api.utils.email_utils import send_invitation_email
from ..extensions import mail
from ..schemas.schemas import (
    InvitationSchema, MessageSchema, AdminReviewRequestSchema,
    CertificationBodyCreationRequestSchema, AcceptInvitationSchema, InvitationRevokeID
)
from api.utils.utils import roles_required, generate_invitation_token, verify_invitation_token

certification_body_bp = Blueprint('CertificationBody', 'certificationbody', url_prefix='/certification_body')

@certification_body_bp.route('/invite')
class CertificationBodyInvite(MethodView):
    @jwt_required()
    @roles_required('manager')
    @certification_body_bp.arguments(InvitationSchema)
    def post(self, invitation_data):
        """Invite a new user (employee) by a manager or admin within a certification body"""
        inviter_id = get_jwt_identity()
        inviter = User.query.get(inviter_id)

        if not inviter:
            return {"message": "Inviter not found."}, 404

        invited_email = invitation_data['email']
        role_str = invitation_data['role']

        try:
            invited_role = RoleEnum(role_str)
        except ValueError:
            return {"message": "Invalid role specified."}, 400

        guest = User.query.filter_by(email=invited_email).first()

        if guest:
            if guest.role != RoleEnum.GUEST:
                return {"message": "Only guests can be invited to join a certification body as employees."}, 400
            if guest.certification_body_id:
                return {"message": "Guest is already part of a certification body."}, 400
            existing_invitation = Invitation.query.filter_by(
                email=invited_email,
                organization_id=None,  # Ensure it's not linked to an organization
                certification_body_id=inviter.certification_body_id,
                status=InvitationStatusEnum.PENDING
            ).first()
            if existing_invitation:
                return {"message": "A pending invitation already exists for this guest and certification body."}, 400

            invitation = Invitation(
                email=invited_email,
                role=invited_role,
                organization_id=None,  # Not linked to any organization
                certification_body_id=inviter.certification_body_id,
                expires_at=datetime.utcnow() + timedelta(days=7),
                status=InvitationStatusEnum.PENDING,
                is_used=False
            )
            try:
                db.session.add(invitation)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                return {"message": "An error occurred while creating the invitation."}, 500

            # Generate signed token with invitation_id and role
            token = generate_invitation_token(invitation.id, invited_role)

            # Update the Invitation record with the token
            invitation.token = token
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                return {"message": "An error occurred while finalizing the invitation."}, 500

            send_invitation_email(invitation, invitation.certification_body.name,'Certification', is_new_user=False)

            return {"message": "Invitation sent successfully to existing guest."}, 201

        else:
            # Create invitation for a new user to register
            invitation = Invitation(
                email=invited_email,
                role=invited_role,
                organization_id=None,  # Not linked to any organization
                certification_body_id=inviter.certification_body_id,
                expires_at=datetime.utcnow() + timedelta(days=7),
                status=InvitationStatusEnum.PENDING,
                is_used=False
            )
            try:
                db.session.add(invitation)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                print(e)
                return {"message": "An error occurred while creating the invitation."}, 500

            # Generate signed token with invitation_id and role
            token = generate_invitation_token(invitation.id, invited_role)

            # Update the Invitation record with the token
            invitation.token = token
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                return {"message": "An error occurred while finalizing the invitation."}, 500

            # Send registration invitation email
            send_invitation_email(invitation,invitation.certification_body.name,'Certification')

            return {"message": "Invitation sent successfully to register."}, 201

@certification_body_bp.route('/invitations')
class CertificationBodyInvitations(MethodView):
    @jwt_required()
    @roles_required('manager')
    @certification_body_bp.response(200, InvitationSchema(many=True))
    def get(self):
        """Retrieve all invitations sent by the manager's certification body"""
        inviter_identity = get_jwt_identity()
        inviter = User.query.get_or_404(inviter_identity)


        if inviter.certification_body_id:
            invitations = Invitation.query.filter_by(certification_body_id=inviter.certification_body_id).all()
        else:
            invitations = []

        return invitations

@certification_body_bp.route('/requests/view')
class CertificationBodyRequestsView(MethodView):
    @certification_body_bp.response(200, CertificationBodyCreationRequestSchema(many=True))
    @jwt_required()
    @roles_required('admin')
    def get(self):
        """List all certification body creation requests."""
        requests = CertificationBodyCreationRequest.query.all()
        return requests, 200

@certification_body_bp.route('/requests/create')
class CertificationBodyRequest(MethodView):
    @certification_body_bp.arguments(CertificationBodyCreationRequestSchema)
    @certification_body_bp.response(201, MessageSchema)
    @jwt_required()
    @roles_required("guest")
    def post(self, request_data):
        """Submit a request to create a new certification body."""
        identity = get_jwt_identity()
        guest = User.query.get_or_404(identity)
        existing_request = CertificationBodyCreationRequest.query.filter_by(
            guest_id=guest.id,
            status=RequestStatusEnum.PENDING
        ).first()
        if existing_request:
            return {"message": "You already have a pending certification body creation request."}, 400

        cert_body_request = CertificationBodyCreationRequest(
            guest_id=guest.id,
            certification_body_name=request_data.get('certification_body_name'),
            address=request_data.get('address'),
            contact_phone=request_data.get('contact_phone'),
            contact_email=request_data.get('contact_email'),
        )

        try:
            db.session.add(cert_body_request)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {"message": "An error occurred while submitting the request."}, 500

        return {"message": "Certification body creation request submitted successfully."}, 201

@certification_body_bp.route('/requests/approve')
class ApproveCertificationBodyRequest(MethodView):
    @certification_body_bp.arguments(AdminReviewRequestSchema, location="json")
    @certification_body_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')
    def post(self, review_data):
        """Approve a certification body creation request and elevate the guest to manager."""
        cert_body_request = CertificationBodyCreationRequest.query.get_or_404(
            review_data['id'],
            description="Certification body creation request not found."
        )
        if cert_body_request.status != RequestStatusEnum.PENDING:
            abort(400, description="This request has already been processed.")

        guest = User.query.get_or_404(cert_body_request.guest_id, description="Guest user not found.")

        certification_body = CertificationBody(
            name=cert_body_request.certification_body_name,
            address=cert_body_request.address,
            contact_email=cert_body_request.contact_email,
            contact_phone=cert_body_request.contact_phone
        )

        try:
            db.session.add(certification_body)
            db.session.flush()  # Flush to get the certification_body.id

            guest.role = RoleEnum.MANAGER
            guest.certification_body_id = certification_body.id
            guest.is_confirmed = True
            cert_body_request.status = RequestStatusEnum.APPROVED
            cert_body_request.admin_comment = review_data.get('admin_comment')

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="An error occurred while approving the request.")

        msg = Message(
            subject='Your Certification Body Creation Request Has Been Approved',
            recipients=[guest.email]
        )
        msg.body = f'''
        Hello {guest.full_name},

        Your request to create the certification body '{certification_body.name}' has been approved. You have been elevated to a manager role.

        Best regards,
        Admin Team
        '''
        mail.send(msg)

        return {"message": "Certification body creation request approved and guest elevated to manager.", "obj": certification_body}, 200

@certification_body_bp.route('/requests/reject')
class RejectCertificationBodyRequest(MethodView):
    @certification_body_bp.arguments(AdminReviewRequestSchema, location="json")
    @certification_body_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')
    def post(self, review_data):
        """Reject a certification body creation request."""
        cert_body_request = CertificationBodyCreationRequest.query.get_or_404(
            review_data['id'],
            description="Certification body creation request not found."
        )
        if cert_body_request.status != RequestStatusEnum.PENDING:
            abort(400, description="This request has already been processed.")
        cert_body_request.status = RequestStatusEnum.REJECTED
        cert_body_request.admin_comment = review_data.get('admin_comment')

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="An error occurred while rejecting the request.")

        guest = User.query.get_or_404(cert_body_request.guest_id, description="Guest user not found.")
        msg = Message(
            subject='Your Certification Body Creation Request Has Been Rejected',
            recipients=[guest.email]
        )
        msg.body = f'''
        Hello {guest.full_name},

        We regret to inform you that your request to create the certification body '{cert_body_request.certification_body_name}' has been rejected.

        Comments: {cert_body_request.admin_comment}

        If you have any questions, please contact the admin team.

        Best regards,
        Admin Team
        '''
        mail.send(msg)

        return {"message": "Certification body creation request rejected."}, 200

@certification_body_bp.route('/invitations/accept')
class AcceptInvitation(MethodView):
    @certification_body_bp.arguments(AcceptInvitationSchema)
    @certification_body_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required([RoleEnum.GUEST])
    def post(self, accept_data):
        """Accept an invitation to join a certification body as an employee."""
        token = accept_data['token']

        try:
            token_payload = verify_invitation_token(token, max_age=7 * 24 * 3600)  # 7 days
            invitation_id = token_payload.get('invitation_id')
            token_role_str = token_payload.get('role')
        except SignatureExpired:
            return {"message": "Invitation token has expired."}, 400
        except BadSignature:
            return {"message": "Invalid invitation token."}, 400

        invitation = Invitation.query.filter_by(
            id=invitation_id,
            token=token,
            status=InvitationStatusEnum.PENDING
        ).first()
        if not invitation:
            return {"message": "Invalid or already responded invitation token."}, 400

        if invitation.expires_at < datetime.utcnow():
            return {"message": "Invitation token has expired."}, 400

        guest_id = get_jwt_identity()
        guest = User.query.get(guest_id)
        if not guest:
            return {"message": "Guest user not found."}, 404

        # Ensure the invitation is for the authenticated guest
        if guest.email != invitation.email:
            return {"message": "You do not have permission to accept this invitation."}, 403

        if guest.role != RoleEnum.GUEST:
            return {"message": "Only guests can accept invitations."}, 400
        if guest.certification_body_id:
            return {"message": "Guest is already part of a certification body."}, 400

        # Ensure the role in the token matches the invitation's role
        if token_role_str != invitation.role.value:
            return {"message": "Invitation role mismatch."}, 400

        # Elevate guest to the role specified in the token
        try:
            new_role = RoleEnum(token_role_str)
        except ValueError:
            return {"message": "Invalid role specified in the invitation token."}, 400

        guest.role = new_role
        guest.certification_body_id = invitation.certification_body_id

        # Update invitation status
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {"message": "An error occurred while accepting the invitation."}, 500

        # Fetch the certification body details
        certification_body = CertificationBody.query.get(invitation.certification_body_id)
        cert_body_name = certification_body.name if certification_body else "the certification body"

        # Send confirmation email
        confirmation_subject = 'Invitation Accepted'
        confirmation_body = f'''
        Hello {guest.full_name},

        You have successfully joined {cert_body_name} as an {guest.role.value}.

        Best regards,
        Admin Team
        '''
        try:
            msg = Message(
                subject=confirmation_subject,
                recipients=[guest.email],
                body=confirmation_body
            )
            mail.send(msg)
        except Exception:
            return {"message": "Failed to send confirmation email."}, 500

        return {"message": f"Invitation accepted and role updated to {guest.role.value}."}, 200


    @certification_body_bp.response(200, MessageSchema)
    def get(self):
        """Accept an invitation to join a certification body via a GET request."""
        token = request.args.get('token', None)
        if not token:
            return {"message": "Invitation token is missing from the URL."}, 400

        # Validate the token using the schema
        schema = AcceptInvitationSchema()
        errors = schema.validate({'token': token})
        if errors:
            return {"message": "Invalid invitation token.", "errors": errors}, 400

        try:
            token_payload = verify_invitation_token(token, max_age=7 * 24 * 3600)  # 7 days
            invitation_id = token_payload.get('invitation_id')
            token_role_str = token_payload.get('role')
        except SignatureExpired:
            return {"message": "Invitation token has expired."}, 400
        except BadSignature:
            return {"message": "Invalid invitation token."}, 400

        invitation = Invitation.query.filter_by(
            id=invitation_id,
            token=token,
            status=InvitationStatusEnum.PENDING
        ).first()
        if not invitation:
            return {"message": "Invalid or already responded invitation token."}, 400

        if invitation.expires_at < datetime.utcnow():
            return {"message": "Invitation token has expired."}, 400

        # Find the guest user by email
        guest = User.query.filter_by(email=invitation.email).first()
        if not guest:
            return {"message": "Guest user not found."}, 404

        # Ensure the guest is still a guest and not part of any organization
        if guest.role != RoleEnum.GUEST:
            return {"message": "Only guests can accept invitations."}, 400
        if guest.certification_body_id or guest.organization_id:
            return {"message": "Guest is already part of a certification body or an organization."}, 400

        # Ensure the role in the token matches the invitation's role
        if token_role_str != invitation.role.value:
            return {"message": "Invitation role mismatch."}, 400

        # Elevate guest to the role specified in the token
        try:
            new_role = RoleEnum(token_role_str)
        except ValueError:
            return {"message": "Invalid role specified in the invitation token."}, 400

        guest.role = new_role
        guest.certification_body_id = invitation.certification_body_id

        # Update invitation status
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {"message": "An error occurred while accepting the invitation."}, 500

        # Fetch the certification body details
        certification_body = CertificationBody.query.get(invitation.certification_body_id)
        cert_body_name = certification_body.name if certification_body else "the certification body"

        # Send confirmation email
        confirmation_subject = 'Invitation Accepted'
        confirmation_body = f'''
        Hello {guest.full_name},

        You have successfully joined {cert_body_name} as an {guest.role.value}.

        Best regards,
        Admin Team
        '''
        try:
            msg = Message(
                subject=confirmation_subject,
                recipients=[guest.email],
                body=confirmation_body
            )
            mail.send(msg)
        except Exception:
            return {"message": "Failed to send confirmation email."}, 500

        # Optionally, render a confirmation page
        return {"message": f"Invitation accepted and role updated to {guest.role.value}."}, 200

@certification_body_bp.route('/invitations/revoke')
class RevokeCertificationBodyInvitation(MethodView):
    @certification_body_bp.arguments(InvitationRevokeID)
    @jwt_required()
    @roles_required('manager')
    def post(self, invitation_req):
        """Revoke an invitation within a certification body"""
        inviter_identity = get_jwt_identity()
        inviter = User.query.get_or_404(inviter_identity)
        invitation_id = invitation_req['id']

        invitation = Invitation.query.get_or_404(invitation_id, description="Invitation not found.")

        # Ensure the invitation belongs to the inviter's certification body
        if inviter.certification_body_id and invitation.certification_body_id != inviter.certification_body_id:
            return {"message": "Access forbidden: Invitation does not belong to your certification body."}, 403

        if invitation.is_used:
            return {"message": "Cannot revoke a used invitation."}, 400

        db.session.delete(invitation)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return {"message": "An error occurred while revoking the invitation."}, 500

        return {"message": "Invitation revoked successfully."}, 200
