# blueprints/audit.py

from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models.models import User, Audit, AuditStatusEnum
from api.schemas.audit_schemas import AuditSchema, AuditCreateSchema, AuditUpdateSchema
from api.utils.utils import roles_required
from api.utils.audit_utils import generate_audit_checklist
from api.utils.email_utils import send_audit_notification

audit_bp = Blueprint('Audit', 'audit', url_prefix='/audits')


@audit_bp.route('/')
class AuditList(MethodView):
    @audit_bp.response(200, AuditSchema(many=True))
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def get(self):
        """
        Retrieve a list of audits with optional filtering.
        Query Parameters:
            - status
            - organization_id
            - certification_body_id
            - start_date
            - end_date
        """
        query_params = request.args
        query = {}
        status = query_params.get('status')
        if status:
            query['status'] = status
        organization_id = query_params.get('organization_id')
        if organization_id:
            query['organization_id'] = organization_id
        certification_body_id = query_params.get('certification_body_id')
        if certification_body_id:
            query['certification_body_id'] = certification_body_id
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')
        if start_date and end_date:
            query['scheduled_date'] = {'$gte': start_date, '$lte': end_date}

        audits = Audit.query.filter_by(**query).all()
        return audits

    @audit_bp.arguments(AuditCreateSchema)
    @audit_bp.response(201, AuditSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def post(self, audit_data):
        """
        Create a new audit.
        """
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        audit = Audit(
            name=audit_data['name'],
            organization_id=audit_data['organization_id'],
            certification_body_id=user.certification_body_id,
            scheduled_date=audit_data['scheduled_date'],
            status=AuditStatusEnum.SCHEDULED,
            checklist=generate_audit_checklist(audit_data['organization_id'], audit_data['standard_ids'])
        )
        Audit.add(audit)

        # Send notification to organization members
        send_audit_notification(audit)

        return audit


@audit_bp.route('/<string:audit_id>')
class AuditDetail(MethodView):
    @audit_bp.response(200, AuditSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def get(self, audit_id):
        """
        Retrieve details of a specific audit by its ID.
        """
        audit = Audit.query.get_or_404(audit_id)
        return audit

    @audit_bp.arguments(AuditUpdateSchema)
    @audit_bp.response(200, AuditSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def put(self, audit_data, audit_id):
        """
        Update details or status of a specific audit.
        """
        audit = Audit.query.get_or_404(audit_id)
        for key, value in audit_data.items():
            setattr(audit, key, value)
        Audit.save(audit)
        return audit
