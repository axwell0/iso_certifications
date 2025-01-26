import uuid

from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import User, Audit, AuditStatusEnum, AuditRequest, RequestStatusEnum, RoleEnum, db
from api.utils.email_utils import send_audit_request_notification_to_cb_managers, \
    send_audit_request_response_to_org_managers, send_audit_created_notification
from api.utils.utils import roles_required
from ..schemas.audit_request_schemas import AuditRequestCreateSchema, AuditRequestSchema
from ..schemas.audit_schemas import AuditSchema, AuditCreateSchema, AuditUpdateSchema

audit_bp = Blueprint('Audit', 'audit', url_prefix='/audits')


@audit_bp.route('/')
class AuditList(MethodView):
    @audit_bp.response(200, AuditSchema(many=True))
    @jwt_required()
    @roles_required(['auditor', 'manager','employee'])
    def get(self):
        """
        Retrieve a list of audits for the user making the request,
        filtered by their organization_id or certification_body_id.
        """
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        if user.organization_id and not user.certification_body_id:
            audits = Audit.query.filter_by(organization_id=user.organization_id).all()

        elif user.certification_body_id and not user.organization_id:
            audits = Audit.query.filter_by(certification_body_id=user.certification_body_id).all()

        else:
            audits = []

        return audits


@audit_bp.route('/<string:audit_id>')
class AuditDetail(MethodView):
    @audit_bp.response(200, AuditSchema)
    @jwt_required()
    @roles_required(['manager'])
    def get(self, audit_id):
        """
        Retrieve details of a specific audit by its ID.
        """
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        audit = Audit.query.get_or_404(audit_id)
        if user.certification_body_id != audit.certification_body_id and user.organization_id != audit.organization_id:
            return {"message": "Unauthorized access"}, 404
        return audit

    @audit_bp.arguments(AuditUpdateSchema)
    @audit_bp.response(200, AuditSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def put(self, audit_data, audit_id):
        """
        Update details or status of a specific audit.
        """
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)
        if not user.certification_body_id:
            return {"Message": "Only certification body managers can change status"}, 400
        audit = Audit.query.get_or_404(audit_id)
        if 'status' in audit_data:
            status_str = audit_data['status']
            try:
                audit.status = AuditStatusEnum(status_str)
            except ValueError:
                valid_statuses = [status.value for status in AuditStatusEnum]
                return {"message": f"Invalid status value. Valid statuses are: {', '.join(valid_statuses)}"}, 400

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"message": "An error occurred while updating the audit.", "error": str(e)}, 500

        return audit


@audit_bp.route('/requests')
class AuditRequestList(MethodView):
    @audit_bp.arguments(AuditRequestCreateSchema)
    @audit_bp.response(201, AuditRequestSchema)
    @jwt_required()
    @roles_required(['manager'])
    def post(self, req_data):
        """
        (Organization Manager) Create a new audit request to a certification body.
        - Saves an AuditRequest with status=PENDING
        - Sends email to all CB managers with a link to confirm/reject
        """
        current_user_id = get_jwt_identity()
        org_manager = User.query.get_or_404(current_user_id)
        print(org_manager)

        if not org_manager.organization_id:
            return {"message": "You must be an Organization Manager to request an audit."}, 400
        print(req_data)
        audit_request = AuditRequest(
            id=str(uuid.uuid4()),
            name=req_data['name'],
            organization_id=org_manager.organization_id,
            certification_body_id=req_data['certification_body_id'],
            requested_by_id=current_user_id,
            scheduled_date=req_data['scheduled_date'],
            standard_ids=", ".join(req_data['standard_ids']),
            status=RequestStatusEnum.PENDING
        )
        db.session.add(audit_request)
        db.session.commit()


        cb_managers = User.query.filter_by(
            certification_body_id=req_data['certification_body_id'],
            role=RoleEnum.MANAGER
        ).all()
        print(cb_managers)

        if not cb_managers:
            return {"message": "No managers found for the specified certification body."}, 404
        print('WE HERE')
        send_audit_request_notification_to_cb_managers(audit_request, cb_managers)

        return audit_request


@audit_bp.route('/requests/<string:request_id>/action')
class AuditRequestAction(MethodView):
    @audit_bp.response(200, AuditRequestSchema)
    @jwt_required()
    @roles_required(['manager'])
    def post(self, request_id):
        """
        Approve or Reject an audit request (Certification Body manager side) via query parameter.
        - action query param: 'approve' or 'reject'
        - If approved, create an actual Audit, status = SCHEDULED.
        - If rejected, set status = REJECTED.
        - Then notify the organization managers of the result.
        """
        from flask import request

        current_user_id = get_jwt_identity()
        cb_manager = User.query.get_or_404(current_user_id)
        if not cb_manager.certification_body_id:
            return {"message": "Only certification body managers can approve or reject requests."}, 400
        audit_request = AuditRequest.query.get_or_404(request_id)

        if audit_request.certification_body_id != cb_manager.certification_body_id:
            return {"message": "This request is not associated with your certification body."}, 403

        if audit_request.status != RequestStatusEnum.PENDING:
            return {"message": f"This request is already {audit_request.status.value}."}, 400

        action = request.args.get('decision')
        if not action:
            return {"message": "Missing 'action' query parameter"}, 400
        if action not in ['approve', 'reject']:
            return {"message": "Invalid action. Must be 'approve' or 'reject'"}, 400

        if action == 'approve':
            audit_request.status = RequestStatusEnum.APPROVED

            print('APPROVED')
            new_audit = Audit(
                id=str(uuid.uuid4()),
                name=audit_request.name,
                organization_id=audit_request.organization_id,
                certification_body_id=audit_request.certification_body_id,
                scheduled_date=audit_request.scheduled_date,
                status=AuditStatusEnum.SCHEDULED,
                checklist=audit_request.standard_ids,
                manager_id=current_user_id,
            )
            db.session.add(new_audit)

        else:  # reject
            audit_request.status = RequestStatusEnum.REJECTED

        db.session.commit()

        # Notify organization managers
        org_managers = User.query.filter_by(
            organization_id=audit_request.organization_id,
            role=RoleEnum.MANAGER
        ).all()
        approved = (action == 'approve')
        send_audit_request_response_to_org_managers(audit_request, org_managers, approved=approved)

        return new_audit


@audit_bp.route('/requests/<string:request_id>')
class AuditRequestDetail(MethodView):
    @audit_bp.response(200, AuditRequestSchema)
    @jwt_required()
    @roles_required(["manager", "auditor",'employee'])  # manager or employee in a CB or org
    def get(self, request_id):
        """
        Retrieve details of an AuditRequest.
        Only relevant for employees/managers in the same org or same CB.
        """
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        audit_request = AuditRequest.query.get_or_404(request_id)

        if (user.organization_id != audit_request.organization_id and
                user.certification_body_id != audit_request.certification_body_id):
            return {"message": "You do not have permission to view this request."}, 403

        return audit_request

@audit_bp.route('/create-for-organization')
class CreateAuditForOrganization(MethodView):
    """
    Alternative endpoint to create an Audit for an Organization
    from the CB side without waiting for an org's request.
    This is somewhat redundant with the POST /audits/ route,
    but is more explicit about the manager's intention.
    """

    @audit_bp.arguments(AuditCreateSchema)
    @audit_bp.response(201, AuditSchema)
    @jwt_required()
    @roles_required(['manager'])
    def post(self, audit_data):
        """
        Example of a dedicated route for a CB Manager to create an audit
        (and notify the entire organization).
        """
        current_user_id = get_jwt_identity()
        cb_manager = User.query.get_or_404(current_user_id)
        if not cb_manager.certification_body_id:
            return {"message": "Only Certification Body managers can create an audit."}, 400

        new_audit = Audit(
            id=str(uuid.uuid4()),
            name=audit_data['name'],
            organization_id=audit_data['organization_id'],
            certification_body_id=cb_manager.certification_body_id,
            scheduled_date=audit_data['scheduled_date'],
            status=AuditStatusEnum.SCHEDULED,
            checklist=", ".join(audit_data['standard_ids']),
            manager_id=current_user_id
        )
        db.session.add(new_audit)
        db.session.commit()

        # Notify all members (managers + employees) of that organization
        org_users = User.query.filter_by(organization_id=audit_data['organization_id']).all()
        send_audit_created_notification(new_audit, org_users)

        return new_audit
