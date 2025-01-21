from datetime import datetime, timedelta

from flask import request
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from itsdangerous import SignatureExpired, BadSignature
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import User, db, Invitation, RoleEnum, InvitationStatusEnum, RequestStatusEnum, \
    OrganizationCreationRequest, Organization
from ..errors import BadRequestError, NotFoundError, ConflictError, ForbiddenError, InternalServerError
from api.utils.email_utils import send_invitation_email, send_revocation_email, \
    send_organization_approval_email, send_organization_rejection_email, send_invitation_accepted_email
from ..schemas.schemas import InvitationSchema, MessageSchema, AdminReviewRequestSchema, \
    OrganizationCreationRequestSchema, AcceptInvitationSchema, InvitationRevokeID
from api.utils.utils import roles_required, generate_invitation_token, verify_invitation_token

organization_bp = Blueprint('Organization', 'organization', url_prefix='/organization')


@organization_bp.route('/invite')
class UserInvite(MethodView):
    @jwt_required()
    @roles_required('manager')
    @organization_bp.arguments(InvitationSchema)
    def post(self, invitation_data):
        """Invite a new user (employee) by a manager or admin"""
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
                raise BadRequestError("Only guests can be invited to join an organization as employees.")
            if guest.organization_id:
                raise BadRequestError("Guest is already part of an organization.")

            existing_invitation = Invitation.query.filter_by(
                email=invited_email,
                organization_id=inviter.organization_id,
                certification_body_id=inviter.certification_body_id,
                status=InvitationStatusEnum.PENDING
            ).first()

            if existing_invitation:
                raise ConflictError("A pending invitation already exists for this guest and organization.")

        invitation = Invitation(
            email=invited_email,
            role=invited_role,
            organization_id=inviter.organization_id,
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

        if guest:
            send_invitation_email(invitation, invitation.organization.name, 'Organization', is_new_user=False)
            return {"message": "Invitation sent successfully to existing guest."}, 201
        else:
            send_invitation_email(invitation, invitation.organization.name, 'Organization')
            return {"message": "Invitation sent successfully to register."}, 201


@organization_bp.route('/requests/create')
class OrganizationRequest(MethodView):
    @organization_bp.arguments(OrganizationCreationRequestSchema)
    @organization_bp.response(201, MessageSchema)
    @jwt_required()
    @roles_required('guest')
    def post(self, request_data):
        """Submit a request to create a new organization."""
        identity = get_jwt_identity()
        guest = User.query.get(identity)
        if not guest:
            raise NotFoundError("User not found.")

        existing_request = OrganizationCreationRequest.query.filter_by(
            guest_id=guest.id,
            status=RequestStatusEnum.PENDING
        ).first()

        if existing_request:
            raise ConflictError("You already have a pending organization creation request.")

        org_request = OrganizationCreationRequest(
            guest_id=guest.id,
            organization_name=request_data.get('organization_name'),
            description=request_data.get('description'),
            address=request_data.get('address'),
            contact_phone=request_data.get('contact_phone'),
            contact_email=request_data.get('contact_email'),
        )

        try:
            db.session.add(org_request)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while submitting the request.")

        return {"message": "Organization creation request submitted successfully."}, 201


@organization_bp.route('/requests/view')
class OrganizationRequestsView(MethodView):
    @organization_bp.response(200, OrganizationCreationRequestSchema(many=True))
    @jwt_required()
    @roles_required('admin')
    def get(self):
        """List all organization creation requests."""
        requests = OrganizationCreationRequest.query.all()
        return requests, 200


@organization_bp.route('/requests/approve')
class ApproveOrganizationRequest(MethodView):
    @organization_bp.arguments(AdminReviewRequestSchema, location="json")
    @organization_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')
    def post(self, review_data):
        """Approve an organization creation request and elevate the guest to manager."""
        org_request = OrganizationCreationRequest.query.get(review_data['id'])
        if not org_request:
            raise NotFoundError("Organization creation request not found.")

        if org_request.status != RequestStatusEnum.PENDING:
            raise BadRequestError("This request has already been processed.")

        guest = User.query.get(org_request.guest_id)
        if not guest:
            raise NotFoundError("Guest user not found.")

        organization = Organization(
            name=org_request.organization_name,
            address=org_request.address,
            contact_email=org_request.contact_email,
            contact_phone=org_request.contact_phone,
        )

        try:
            db.session.add(organization)
            db.session.flush()

            guest.role = RoleEnum.MANAGER
            guest.organization_id = organization.id
            guest.is_confirmed = True
            org_request.status = RequestStatusEnum.APPROVED
            org_request.admin_comment = review_data.get('admin_comment')

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while approving the request.")

        send_organization_approval_email(guest, organization)
        return {"message": "Organization creation request approved and guest elevated to manager."}, 200


@organization_bp.route('/requests/reject')
class RejectOrganizationRequest(MethodView):
    @organization_bp.arguments(AdminReviewRequestSchema, location="json")
    @organization_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')
    def post(self, review_data):
        """Reject an organization creation request."""
        org_request = OrganizationCreationRequest.query.get(review_data['id'])
        if not org_request:
            raise NotFoundError("Organization creation request not found.")

        if org_request.status != RequestStatusEnum.PENDING:
            raise BadRequestError("This request has already been processed.")

        org_request.status = RequestStatusEnum.REJECTED
        org_request.admin_comment = review_data.get('admin_comment')

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while rejecting the request.")

        guest = User.query.get(org_request.guest_id)
        if not guest:
            raise NotFoundError("Guest user not found.")

        send_organization_rejection_email(guest, org_request)
        return {"message": "Organization creation request rejected."}, 200


@organization_bp.route('/invitations')
class UserInvitations(MethodView):
    @jwt_required()
    @roles_required('manager')
    @organization_bp.response(200, InvitationSchema(many=True))
    def get(self):
        """Retrieve all invitations sent by the manager's organization or certification body"""
        inviter_identity = get_jwt_identity()
        inviter = User.query.get(inviter_identity)
        if not inviter:
            raise NotFoundError("User not found.")

        if inviter.organization_id:
            return Invitation.query.filter_by(organization_id=inviter.organization_id).all()
        if inviter.certification_body_id:
            return Invitation.query.filter_by(certification_body_id=inviter.certification_body_id).all()
        return []


@organization_bp.route('/invitations/accept')
class AcceptInvitation(MethodView):
    @organization_bp.arguments(AcceptInvitationSchema)
    @organization_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required([RoleEnum.GUEST])
    def post(self, accept_data):
        """Accept an invitation to join an organization as an employee."""
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
        if guest.organization_id:
            raise BadRequestError("Guest is already part of an organization.")

        if token_role_str != invitation.role.value:
            raise BadRequestError("Invitation role mismatch.")

        try:
            new_role = RoleEnum(token_role_str)
        except ValueError:
            raise BadRequestError("Invalid role specified in the invitation token.")

        guest.role = new_role
        guest.organization_id = invitation.organization_id

        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("An error occurred while accepting the invitation.")

        organization = Organization.query.get(invitation.organization_id)
        send_invitation_accepted_email(guest, organization)
        return {"message": f"Invitation accepted and role updated to {guest.role.value}."}, 200

    @organization_bp.response(200, MessageSchema)
    def get(self):
        """Accept an invitation via GET request."""
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

        if guest.role != RoleEnum.GUEST or guest.organization_id:
            raise BadRequestError("Invalid guest status for invitation acceptance.")

        if token_role_str != invitation.role.value:
            raise BadRequestError("Invitation role mismatch.")

        try:
            new_role = RoleEnum(token_role_str)
        except ValueError:
            raise BadRequestError("Invalid role specified in invitation token.")

        guest.role = new_role
        guest.organization_id = invitation.organization_id
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError("Error accepting invitation.")

        organization = Organization.query.get(invitation.organization_id)
        send_invitation_accepted_email(guest, organization)
        return {"message": f"Invitation accepted. Role updated to {guest.role.value}."}, 200


@organization_bp.route('/invitations/revoke')
class RevokeInvitation(MethodView):
    @organization_bp.arguments(InvitationRevokeID)
    @jwt_required()
    @roles_required('manager')
    def delete(self, invitation_req):
        """Revoke an invitation"""
        inviter = User.query.get(get_jwt_identity())
        if not inviter:
            raise NotFoundError("User not found.")

        invitation = Invitation.query.get(invitation_req['id'])
        if not invitation:
            raise NotFoundError("Invitation not found.")

        if (inviter.organization_id and invitation.organization_id != inviter.organization_id) or \
                (inviter.certification_body_id and invitation.certification_body_id != inviter.certification_body_id):
            raise ForbiddenError("Unauthorized to revoke this invitation.")

        if invitation.is_used:
            raise BadRequestError("Cannot revoke used invitation.")

        send_revocation_email(invitation, invitation.organization.name)
        db.session.delete(invitation)
        db.session.commit()
        return {"message": "Invitation revoked successfully."}, 200
