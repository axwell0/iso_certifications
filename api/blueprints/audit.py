import uuid

from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_smorest import Blueprint
from sqlalchemy.exc import SQLAlchemyError

from api.models.models import User, Audit, AuditStatusEnum
from api.schemas.audit_schemas import AuditSchema, AuditCreateSchema, AuditUpdateSchema
from api.utils.email_utils import send_audit_notification
from api.utils.utils import roles_required
from ..extensions import db

audit_bp = Blueprint('Audit', 'audit', url_prefix='/audits')


@audit_bp.route('/')
class AuditList(MethodView):
    @audit_bp.response(200, AuditSchema(many=True))
    @jwt_required()
    @roles_required(['employee', 'manager'])
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

    @audit_bp.arguments(AuditCreateSchema)
    @audit_bp.response(201, AuditSchema)
    @jwt_required()
    @roles_required(['manager'])
    def post(self, audit_data):
        """
        Create a new audit.
        """
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)

        audit = Audit(
            id=str(uuid.uuid4()),
            name=audit_data['name'],
            organization_id=audit_data['organization_id'],
            certification_body_id=user.certification_body_id,
            scheduled_date=audit_data['scheduled_date'],
            status=AuditStatusEnum.SCHEDULED,
            checklist=", ".join(audit_data['standard_ids']), manager_id=current_user_id
        )
        print(audit.organization)
        db.session.add(audit)
        db.session.commit()
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
