from datetime import datetime, timedelta
from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import (
    User, db, Invitation, RoleEnum, InvitationStatusEnum,
    RequestStatusEnum, CertificationBodyCreationRequest, CertificationBody
)
from ..errors import (
    BadRequestError, NotFoundError, ConflictError,
    ForbiddenError, InternalServerError
)
from api.utils.email_utils import (
    send_invitation_email, send_revocation_email,
    send_cert_body_approval_email, send_cert_body_rejection_email,
    send_cert_invitation_accepted_email
)
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
        """
        Invite a new user (employee) by a manager or admin within a certification body.

        Possible errors:
        - 404: Inviter not found.
        - 400: Invalid role, guest is not eligible.
        - 409: Existing pending invitation.
        - 500: Database operation failed.
        """
        inviter_id = get_jwt_identity()
        inviter = User.query.get(inviter_id)

        if not inviter:
            raise NotFoundError("Inviter not found.")

        invited_email = invitation_data['email']
        role_str = invitation_data['role']

        try:
            invited_role = RoleEnum(role_str)
        except ValueError:
            raise BadRequestError("Invalid role specified.")

        guest = User.query.filter_by(email=invited_email).first()
        invitation_email = Invitation.query.filter_by(email=invited_email).first()
        if invitation_email and not invitation_email.is_used:
            raise ConflictError("This email already has an outstanding invitation")

        if guest:
            if guest.role != RoleEnum.GUEST:
                raise BadRequestError("Only guests can be invited to join a certification body as employees.")
            if guest.certification_body_id:
                raise BadRequestError("Guest is already part of a certification body.")

            existing_invitation = Invitation.query.filter_by(
                email=invited_email,
                organization_id=None,
                certification_body_id=inviter.certification_body_id,
                status=InvitationStatusEnum.PENDING
            ).first()

            if existing_invitation:
                raise ConflictError("A pending invitation already exists for this guest and certification body.")

        invitation = Invitation(
            email=invited_email,
            role=invited_role,
            organization_id=None,
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
            raise InternalServerError("An error occurred while creating the invitation.")

        token = generate_invitation_token(invitation.id)
        invitation.token = token

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while finalizing the invitation.")

        send_invitation_email(invitation, invitation.certification_body.name, 'CertificationBody',
                              is_new_user=not guest)
        return {"message": "Invitation sent successfully."}, 201


@certification_body_bp.route('/invitations')
class CertificationBodyInvitations(MethodView):
    @jwt_required()
    @roles_required('manager')
    @certification_body_bp.response(200, InvitationSchema(many=True))
    def get(self):
        """
        Retrieve all invitations sent by the manager's certification body.

        Possible errors:
        - 404: User not found.
        - 500: Database operation failed.
        """
        inviter_identity = get_jwt_identity()
        inviter = User.query.get(inviter_identity)

        if not inviter:
            raise NotFoundError("User not found.")

        try:
            if inviter.certification_body_id:
                return Invitation.query.filter_by(certification_body_id=inviter.certification_body_id).all()
            return []
        except SQLAlchemyError:
            raise InternalServerError("Failed to retrieve invitations.")


@certification_body_bp.route('/requests/view')
class CertificationBodyRequestsView(MethodView):
    @certification_body_bp.response(200, CertificationBodyCreationRequestSchema(many=True))
    @jwt_required()
    @roles_required('admin')
    def get(self):
        """
        List all certification body creation requests.

        Possible errors:
        - 500: Database operation failed.
        """
        try:
            requests = CertificationBodyCreationRequest.query.all()
            return requests, 200
        except SQLAlchemyError:
            raise InternalServerError("Failed to fetch requests.")


@certification_body_bp.route('/requests/create')
class CertificationBodyRequest(MethodView):
    @certification_body_bp.arguments(CertificationBodyCreationRequestSchema)
    @certification_body_bp.response(201, MessageSchema)
    @jwt_required()
    @roles_required("guest")
    def post(self, request_data):
        """
        Submit a request to create a new certification body.

        Possible errors:
        - 404: User not found.
        - 409: Pending request exists.
        - 500: Database operation failed.
        """
        identity = get_jwt_identity()
        guest = User.query.get(identity)
        if not guest:
            raise NotFoundError("User not found.")

        existing_request = CertificationBodyCreationRequest.query.filter_by(
            guest_id=guest.id,
            status=RequestStatusEnum.PENDING
        ).first()

        if existing_request:
            raise ConflictError("You already have a pending certification body creation request.")

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
            raise InternalServerError("An error occurred while submitting the request.")

        return {"message": "Certification body creation request submitted successfully."}, 201


@certification_body_bp.route('/requests/approve')
class ApproveCertificationBodyRequest(MethodView):
    @certification_body_bp.arguments(AdminReviewRequestSchema, location="json")
    @certification_body_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')
    def post(self, review_data):
        """
        Approve a certification body creation request and elevate the guest to manager.

        Possible errors:
        - 404: Request or guest not found.
        - 400: Request already processed.
        - 500: Database operation failed.
        """
        cert_body_request = CertificationBodyCreationRequest.query.get(review_data['id'])
        if not cert_body_request:
            raise NotFoundError("Certification body creation request not found.")

        if cert_body_request.status != RequestStatusEnum.PENDING:
            raise BadRequestError("This request has already been processed.")

        guest = User.query.get(cert_body_request.guest_id)
        if not guest:
            raise NotFoundError("Guest user not found.")

        certification_body = CertificationBody(
            name=cert_body_request.certification_body_name,
            address=cert_body_request.address,
            contact_email=cert_body_request.contact_email,
            contact_phone=cert_body_request.contact_phone
        )

        try:
            db.session.add(certification_body)
            db.session.flush()

            guest.role = RoleEnum.MANAGER
            guest.certification_body_id = certification_body.id
            guest.is_confirmed = True
            cert_body_request.status = RequestStatusEnum.APPROVED
            cert_body_request.admin_comment = review_data.get('admin_comment')

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while approving the request.")

        send_cert_body_approval_email(guest, certification_body)
        return {"message": "Certification body creation request approved and guest elevated to manager."}, 200


@certification_body_bp.route('/requests/reject')
class RejectCertificationBodyRequest(MethodView):
    @certification_body_bp.arguments(AdminReviewRequestSchema, location="json")
    @certification_body_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')
    def post(self, review_data):
        """
        Reject a certification body creation request.

        Possible errors:
        - 404: Request not found.
        - 400: Request already processed.
        - 500: Database operation failed.
        """
        cert_body_request = CertificationBodyCreationRequest.query.get(review_data['id'])
        if not cert_body_request:
            raise NotFoundError("Certification body creation request not found.")

        if cert_body_request.status != RequestStatusEnum.PENDING:
            raise BadRequestError("This request has already been processed.")

        cert_body_request.status = RequestStatusEnum.REJECTED
        cert_body_request.admin_comment = review_data.get('admin_comment')

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while rejecting the request.")

        guest = User.query.get(cert_body_request.guest_id)
        if not guest:
            raise NotFoundError("Guest user not found.")

        send_cert_body_rejection_email(guest, cert_body_request)
        return {"message": "Certification body creation request rejected."}, 200


@certification_body_bp.route('/invitations/accept')
class AcceptInvitation(MethodView):
    @certification_body_bp.arguments(AcceptInvitationSchema)
    @certification_body_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required([RoleEnum.GUEST])
    def post(self, accept_data):
        """
        Accept an invitation to join a certification body as an employee.

        Possible errors:
        - 400: Invalid/expired token, role mismatch, invalid guest status.
        - 403: Email mismatch.
        - 404: Invitation or guest not found.
        - 500: Database operation failed.
        """
        token = accept_data['token']

        try:
            token_payload = verify_invitation_token(token, max_age=7 * 24 * 3600)
            invitation_id = token_payload.get('invitation_id')
            token_role_str = token_payload.get('role')
        except SignatureExpired:
            raise BadRequestError("Invitation token has expired.")
        except BadSignature:
            raise BadRequestError("Invalid invitation token.")

        invitation = Invitation.query.filter_by(
            id=invitation_id,
            token=token,
            status=InvitationStatusEnum.PENDING
        ).first()

        if not invitation:
            raise BadRequestError("Invalid or already responded invitation token.")

        if invitation.expires_at < datetime.utcnow():
            raise BadRequestError("Invitation token has expired.")

        guest_id = get_jwt_identity()
        guest = User.query.get(guest_id)
        if not guest:
            raise NotFoundError("Guest user not found.")

        if guest.email != invitation.email:
            raise ForbiddenError("You do not have permission to accept this invitation.")

        if guest.role != RoleEnum.GUEST:
            raise BadRequestError("Only guests can accept invitations.")
        if guest.certification_body_id:
            raise BadRequestError("Guest is already part of a certification body.")

        if token_role_str != invitation.role.value:
            raise BadRequestError("Invitation role mismatch.")

        try:
            new_role = RoleEnum(token_role_str)
        except ValueError:
            raise BadRequestError("Invalid role specified in the invitation token.")

        guest.role = new_role
        guest.certification_body_id = invitation.certification_body_id

        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while accepting the invitation.")

        certification_body = CertificationBody.query.get(invitation.certification_body_id)
        send_cert_invitation_accepted_email(guest, certification_body)
        return {"message": f"Invitation accepted and role updated to {guest.role.value}."}, 200

    @certification_body_bp.response(200, MessageSchema)
    def get(self):
        """
        Accept an invitation via GET request.

        Possible errors:
        - 400: Missing/invalid token, role mismatch, invalid guest status.
        - 403: Email mismatch.
        - 404: Invitation or guest not found.
        - 500: Database operation failed.
        """
        token = request.args.get('token')
        if not token:
            raise BadRequestError("Invitation token is missing from the URL.")

        schema = AcceptInvitationSchema()
        if schema.validate({'token': token}):
            raise BadRequestError("Invalid invitation token.")

        try:
            token_payload = verify_invitation_token(token, max_age=7 * 24 * 3600)
            invitation_id = token_payload.get('invitation_id')
            token_role_str = token_payload.get('role')
        except SignatureExpired:
            raise BadRequestError("Invitation token has expired.")
        except BadSignature:
            raise BadRequestError("Invalid invitation token.")

        invitation = Invitation.query.filter_by(
            id=invitation_id,
            token=token,
            status=InvitationStatusEnum.PENDING
        ).first()

        if not invitation or invitation.expires_at < datetime.utcnow():
            raise BadRequestError("Invalid or expired invitation token.")

        guest = User.query.filter_by(email=invitation.email).first()
        if not guest:
            raise NotFoundError("Guest user not found.")

        if guest.role != RoleEnum.GUEST or guest.certification_body_id:
            raise BadRequestError("Invalid guest status for invitation acceptance.")

        if token_role_str != invitation.role.value:
            raise BadRequestError("Invitation role mismatch.")

        try:
            new_role = RoleEnum(token_role_str)
        except ValueError:
            raise BadRequestError("Invalid role specified in invitation token.")

        guest.role = new_role
        guest.certification_body_id = invitation.certification_body_id
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("Error accepting invitation.")

        certification_body = CertificationBody.query.get(invitation.certification_body_id)
        send_cert_invitation_accepted_email(guest, certification_body)
        return {"message": f"Invitation accepted. Role updated to {guest.role.value}."}, 200


@certification_body_bp.route('/invitations/revoke')
class RevokeCertificationBodyInvitation(MethodView):
    @certification_body_bp.arguments(InvitationRevokeID)
    @jwt_required()
    @roles_required('manager')
    def delete(self, invitation_req):
        """
        Revoke an invitation within a certification body.

        Possible errors:
        - 404: User or invitation not found.
        - 403: Unauthorized revocation.
        - 400: Invitation already used.
        - 500: Database operation failed.
        """
        inviter = User.query.get(get_jwt_identity())
        if not inviter:
            raise NotFoundError("User not found.")

        invitation = Invitation.query.get(invitation_req['id'])
        if not invitation:
            raise NotFoundError("Invitation not found.")

        if inviter.certification_body_id and invitation.certification_body_id != inviter.certification_body_id:
            raise ForbiddenError("Unauthorized to revoke this invitation.")

        if invitation.is_used:
            raise BadRequestError("Cannot revoke a used invitation.")

        send_revocation_email(invitation, invitation.certification_body.name)
        try:
            db.session.delete(invitation)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while revoking the invitation.")

        return {"message": "Invitation revoked successfully."}, 200