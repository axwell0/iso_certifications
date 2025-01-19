import uuid
from datetime import datetime, timedelta

from flask import url_for, abort
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from flask_smorest import Blueprint
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import User, db, Invitation, RoleEnum, InvitationStatusEnum, RequestStatusEnum, \
    OrganizationCreationRequest, Organization
from .. import mail
from ..schemas.schemas import InvitationSchema, MessageSchema, AdminReviewRequestSchema, \
    OrganizationCreationRequestSchema, AcceptInvitationSchema
from ..utils import roles_required, generate_confirmation_token

users_bp = Blueprint('Users', 'users', url_prefix='/users')

@users_bp.route('/invite')
class UserInvite(MethodView):
    @jwt_required()
    @roles_required([RoleEnum.MANAGER, RoleEnum.ADMIN])  # Pass RoleEnum instances
    @users_bp.arguments(InvitationSchema)
    def post(self, invitation_data):
        """Invite a new user (employee) by a manager or admin"""
        inviter_id = get_jwt_identity()
        inviter = User.query.get_or_404(inviter_id, description="Inviter not found.")

        invited_email = invitation_data['email']
        invited_role = RoleEnum(invitation_data['role'])

        # Check if the guest exists
        guest = User.query.filter_by(email=invited_email).first()

        if not guest:
            # Email does not exist: invite to register via Auth.RegisterInvitation
            # Create an invitation for registration
            invitation = Invitation(
                email=invited_email,
                role=invited_role,
                organization_id=inviter.organization_id if inviter.organization_id else None,
                certification_body_id=inviter.certification_body_id if inviter.certification_body_id else None,
                token=str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(days=7),
                status=InvitationStatusEnum.PENDING,
                is_used=False
            )
            # Add to DB
            try:
                db.session.add(invitation)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                abort(500, description="An error occurred while sending the invitation.")

            # Generate registration invitation link
            registration_link = url_for('Auth.RegisterInvitation', token=invitation.token, _external=True)

            # Send registration invitation email
            msg = Message('You are Invited to Join', recipients=[invitation.email])
            msg.body = f'''
            Hello,

            You have been invited to join our platform as an {invitation.role.value}. Please click the link below to register:

            {registration_link}

            This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC.

            If you did not expect this invitation, please ignore this email.

            Best regards,
            Your Company
            '''
            mail.send(msg)

            return {"message": "Invitation sent successfully to register."}, 201

        else:
            # Email exists: check if it's a guest
            if guest.role != RoleEnum.GUEST:
                abort(400, description="Only guests can be invited to join an organization as employees.")
            if guest.organization_id:
                abort(400, description="Guest is already part of an organization.")

            # Check if an invitation already exists and is pending
            existing_invitation = Invitation.query.filter_by(
                email=invitation_data['email'],
                organization_id=inviter.organization_id if inviter.organization_id else None,
                certification_body_id=inviter.certification_body_id if inviter.certification_body_id else None,
                status=InvitationStatusEnum.PENDING
            ).first()
            if existing_invitation:
                abort(400, description="A pending invitation already exists for this guest and organization.")

            # Create an invitation for existing guest
            invitation = Invitation(
                email=invited_email,
                role=invited_role,
                organization_id=inviter.organization_id if inviter.organization_id else None,
                certification_body_id=inviter.certification_body_id if inviter.certification_body_id else None,
                token=str(uuid.uuid4()),
                expires_at=datetime.utcnow() + timedelta(days=7),
                status=InvitationStatusEnum.PENDING,
                is_used=False
            )
            # Add to DB
            try:
                db.session.add(invitation)
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
                abort(500, description="An error occurred while sending the invitation.")

            # Generate invitation acceptance link
            # Since the guest is existing and authenticated, the acceptance link can be a route that requires JWT
            acceptance_link = url_for('Users.AcceptInvitation', _external=True)  # User will send token in body

            # Send invitation acceptance email
            msg = Message('You are Invited to Join', recipients=[invitation.email])
            msg.body = f'''
            Hello,

            You have been invited to join our organization as an {invitation.role.value}. Please log in and accept the invitation by clicking the link below:

            {acceptance_link}

            Alternatively, you can accept the invitation by sending a POST request to the accept endpoint with your invitation token.

            This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC.

            If you did not expect this invitation, please ignore this email.

            Best regards,
            Your Company
            '''
            mail.send(msg)

            return {"message": "Invitation sent successfully to existing guest."}, 201
@users_bp.route('/invitations')
class UserInvitations(MethodView):
    @jwt_required()
    @roles_required('manager')
    @users_bp.response(200, InvitationSchema(many=True))
    def get(self):
        """Retrieve all invitations sent by the manager's organization or certification body"""
        inviter_identity = get_jwt_identity()
        inviter = User.query.get_or_404(inviter_identity['id'])

        if inviter.organization_id:
            invitations = Invitation.query.filter_by(organization_id=inviter.organization_id).all()
        elif inviter.certification_body_id:
            invitations = Invitation.query.filter_by(certification_body_id=inviter.certification_body_id).all()
        else:
            invitations = []

        return invitations


@users_bp.route('/invitations/<string:invitation_id>/resend')
class ResendInvitation(MethodView):
    @jwt_required()
    @roles_required('manager')
    def post(self, invitation_id):
        """Resend an invitation email"""
        inviter_identity = get_jwt_identity()
        inviter = User.query.get_or_404(inviter_identity['id'])

        invitation = Invitation.query.get_or_404(invitation_id, description="Invitation not found.")

        # Ensure the invitation belongs to the inviter's organization or certification body
        if inviter.organization_id and invitation.organization_id != inviter.organization_id:
            return {"message": "Access forbidden: Invitation does not belong to your organization."}, 403
        if inviter.certification_body_id and invitation.certification_body_id != inviter.certification_body_id:
            return {"message": "Access forbidden: Invitation does not belong to your certification body."}, 403

        if invitation.is_used:
            return {"message": "Cannot resend a used invitation."}, 400
        if invitation.expires_at < datetime.utcnow():
            return {"message": "Cannot resend an expired invitation."}, 400

        # Resend invitation email
        invitation_link = url_for('Auth.RegisterInvitation', token=invitation.token, _external=True)
        msg = Message('You are Invited to Join', recipients=[invitation.email])
        msg.body = f'''
        Hello,

        You have been invited to join our platform as a {invitation.role.value}. Please click the link below to register:

        {invitation_link}

        This invitation will expire on {invitation.expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC.

        If you did not expect this invitation, please ignore this email.

        Best regards,
        Your Company
        '''
        mail.send(msg)

        return {"message": "Invitation resent successfully."}, 200
@users_bp.route('/organizations/requests/<string:request_id>/approve')
class ApproveOrganizationRequest(MethodView):
    @users_bp.arguments(AdminReviewRequestSchema, location="json")
    @users_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')  # Only admins can approve requests
    def post(self, review_data, request_id):
        """Approve an organization creation request and elevate the guest to manager."""
        org_request = OrganizationCreationRequest.query.get_or_404(request_id,
                                                                   description="Organization creation request not found.")
        if org_request.status != RequestStatusEnum.PENDING:
            abort(400, description="This request has already been processed.")

        guest = User.query.get_or_404(org_request.guest_id, description="Guest user not found.")

        # Create the new organization
        organization = Organization(
            name=org_request.organization_name,
            address="",  # Assuming address is provided elsewhere or can be updated later
            contact_email=guest.email,  # Using guest's email as contact email
            contact_phone=""  # Assuming phone is provided elsewhere or can be updated later
        )

        try:
            db.session.add(organization)
            db.session.flush()  # Flush to get organization.id

            # Elevate guest to manager and associate with the new organization
            guest.role = RoleEnum.MANAGER
            guest.organization_id = organization.id
            guest.is_confirmed = True  # Optionally confirm email upon elevation

            # Update the request status
            org_request.status = RequestStatusEnum.APPROVED
            org_request.admin_comment = review_data.get('admin_comment')

            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="An error occurred while approving the request.")

        # Send email notification to the guest
        confirmation_url = url_for('Auth.ConfirmEmail',
                                   token=generate_confirmation_token(guest.email),
                                   _external=True)
        msg = Message(
            subject='Your Organization Creation Request Has Been Approved',
            recipients=[guest.email]
        )
        msg.body = f'''
        Hello {guest.full_name},

        Your request to create the organization '{organization.name}' has been approved. You have been elevated to a manager role.

        Please confirm your email address by clicking the link below:

        {confirmation_url}

        Best regards,
        Admin Team
        '''
        mail.send(msg)

        return {"message": "Organization creation request approved and guest elevated to manager."}, 200
@users_bp.route('/organizations/requests/<string:request_id>/reject')
class RejectOrganizationRequest(MethodView):
    @users_bp.arguments(AdminReviewRequestSchema, location="json")
    @users_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required('admin')  # Only admins can reject requests
    def post(self, review_data, request_id):
        """Reject an organization creation request."""
        org_request = OrganizationCreationRequest.query.get_or_404(request_id,
                                                                   description="Organization creation request not found.")
        if org_request.status != RequestStatusEnum.PENDING:
            abort(400, description="This request has already been processed.")

        # Update the request status
        org_request.status = RequestStatusEnum.REJECTED
        org_request.admin_comment = review_data.get('admin_comment')

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="An error occurred while rejecting the request.")

        # Send email notification to the guest
        guest = User.query.get_or_404(org_request.guest_id, description="Guest user not found.")
        msg = Message(
            subject='Your Organization Creation Request Has Been Rejected',
            recipients=[guest.email]
        )
        msg.body = f'''
        Hello {guest.full_name},

        We regret to inform you that your request to create the organization '{org_request.organization_name}' has been rejected.

        Comments: {org_request.admin_comment}

        If you have any questions, please contact the admin team.

        Best regards,
        Admin Team
        '''
        mail.send(msg)

        return {"message": "Organization creation request rejected."}, 200

@users_bp.route('/invitations/<string:invitation_id>/revoke')
class RevokeInvitation(MethodView):
    @jwt_required()
    @roles_required('manager')
    def post(self, invitation_id):
        """Revoke an invitation"""
        inviter_identity = get_jwt_identity()
        inviter = User.query.get_or_404(inviter_identity['id'])

        invitation = Invitation.query.get_or_404(invitation_id, description="Invitation not found.")

        # Ensure the invitation belongs to the inviter's organization or certification body
        if inviter.organization_id and invitation.organization_id != inviter.organization_id:
            return {"message": "Access forbidden: Invitation does not belong to your organization."}, 403
        if inviter.certification_body_id and invitation.certification_body_id != inviter.certification_body_id:
            return {"message": "Access forbidden: Invitation does not belong to your certification body."}, 403

        if invitation.is_used:
            return {"message": "Cannot revoke a used invitation."}, 400

        # Revoke the invitation by deleting it
        db.session.delete(invitation)
        db.session.commit()

        return {"message": "Invitation revoked successfully."}, 200

@users_bp.route('/organizations/requests')
class OrganizationRequestList(MethodView):
    @users_bp.arguments(OrganizationCreationRequestSchema)
    @users_bp.response(201, MessageSchema)
    @jwt_required()
    @roles_required('guest')  # Only guests can submit requests
    def post(self, request_data):
        """Submit a request to create a new organization."""
        identity = get_jwt_identity()
        guest = User.query.get_or_404(identity)

        # Check if the guest already has a pending request
        existing_request = OrganizationCreationRequest.query.filter_by(
            guest_id=guest.id,
            status=RequestStatusEnum.PENDING
        ).first()
        if existing_request:

            abort(400, description="You already have a pending organization creation request.")

        # Create a new organization creation request
        org_request = OrganizationCreationRequest(
            guest_id=guest.id,
            organization_name=request_data['organization_name'],
            description=request_data.get('description')
        )

        try:
            db.session.add(org_request)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="An error occurred while submitting the request.")

        return {"message": "Organization creation request submitted successfully."}, 201

    @users_bp.response(200, OrganizationCreationRequestSchema(many=True))
    @jwt_required()
    @roles_required('admin')  # Only admins can view all requests
    def get(self):
        """List all organization creation requests."""
        requests = OrganizationCreationRequest.query.all()
        return requests, 200
# users.py (continued)

@users_bp.route('/invitations/accept')
class AcceptInvitation(MethodView):
    @users_bp.arguments(AcceptInvitationSchema)
    @users_bp.response(200, MessageSchema)
    @jwt_required()
    @roles_required([RoleEnum.GUEST])  # Only guests can accept invitations
    def post(self, accept_data):
        """Accept an invitation to join an organization as an employee."""
        token = accept_data['token']
        invitation = Invitation.query.filter_by(token=token, status=InvitationStatusEnum.PENDING).first()
        if not invitation:
            abort(400, description="Invalid or already responded invitation token.")

        # Check if the invitation has expired
        if invitation.expires_at < datetime.utcnow():
            abort(400, description="Invitation token has expired.")

        guest_id = get_jwt_identity()
        guest = User.query.get_or_404(guest_id, description="Guest user not found.")

        # Ensure the invitation is for the authenticated guest
        if guest.email != invitation.email:
            abort(403, description="You do not have permission to accept this invitation.")

        if guest.role != RoleEnum.GUEST:
            abort(400, description="Only guests can accept invitations.")
        if guest.organization_id:
            abort(400, description="Guest is already part of an organization.")

        # Elevate guest to employee and associate with the organization
        guest.role = RoleEnum.EMPLOYEE
        guest.organization_id = invitation.organization_id

        # Update invitation status
        invitation.status = InvitationStatusEnum.ACCEPTED
        invitation.is_used = True
        invitation.responded_at = datetime.utcnow()

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="An error occurred while accepting the invitation.")

        # Send confirmation email
        organization = Organization.query.get(invitation.organization_id)
        msg = Message(
            subject='Invitation Accepted',
            recipients=[guest.email]
        )
        msg.body = f'''
        Hello {guest.full_name},

        You have successfully joined the organization '{organization.name}' as an employee.

        Best regards,
        Admin Team
        '''
        mail.send(msg)

        return {"message": "Invitation accepted and role updated to employee."}, 200
