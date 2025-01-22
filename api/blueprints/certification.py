from datetime import datetime

from flask.views import MethodView
from flask_smorest import Blueprint
from flask import send_file
from ..extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models.models import User, Audit, Certification, AuditStatusEnum, CertificationStatusEnum
from api.schemas.certification_schemas import CertificationSchema, CertificationCreateSchema
from api.utils.utils import roles_required
from api.utils.certification_utils import generate_certificate_pdf
from api.utils.email_utils import send_certification_email
from api.errors import BadRequestError, ForbiddenError, NotFoundError  # Added imports

certification_bp = Blueprint('Certification', 'certification', url_prefix='/certification')


@certification_bp.route('/certificates')
class CertificationList(MethodView):
    @certification_bp.response(200, CertificationSchema(many=True))
    @jwt_required()
    @roles_required(['employee', 'manager'])
    def get(self):
        """Retrieve a list of issued certifications.

        Raises:
            NotFoundError: If no certifications exist for the user's organization or certification body.
        """
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if user.organization_id:
            certifications = Certification.query.filter_by(organization_id=user.organization_id).all()
        elif user.certification_body_id:
            certifications = Certification.query.filter_by(certification_body_id=user.certification_body_id).all()
        else:
            raise NotFoundError(message="No certifications found")
        return certifications

    @certification_bp.arguments(CertificationCreateSchema)
    @certification_bp.response(201, CertificationSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def post(self, certification_data):
        """Issue a new certification based on an audit.

        Raises:
            ForbiddenError: If the user is not part of a certification body.
            NotFoundError: If the specified audit does not exist.
            BadRequestError: If the audit is not in a completed state.
        """
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user.certification_body_id:
            raise ForbiddenError(message="Only certification body managers can issue certifications")

        audit = Audit.query.get(certification_data['audit_id'])
        if not audit:
            raise NotFoundError(message="Audit not found")
        if audit.status != AuditStatusEnum.COMPLETED:
            raise BadRequestError(message="Audit must be completed before issuing certification.")

        certification = Certification(
            audit_id=audit.id,
            organization_id=audit.organization_id,
            certification_body_id=audit.certification_body_id,
            issued_date=certification_data['issued_date'],
            status=CertificationStatusEnum.ISSUED,
            issuer_id=user_id,
            certificate_pdf=generate_certificate_pdf(
                {"organization_id": audit.organization_id, "recipient_name": audit.organization.name,
                 "checklist": audit.checklist}),
        )
        db.session.add(certification)
        db.session.commit()

        send_certification_email(certification)

        return certification


@certification_bp.route('/download/<string:certificate_id>')
class DownloadCertification(MethodView):
    @jwt_required()
    @roles_required(['employee', 'manager'])
    def get(self, certificate_id):
        """Download the certification PDF.

        Raises:
            NotFoundError: If the certification does not exist.
            ForbiddenError: If the user lacks access to the certification.
        """
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        certification = Certification.query.get(certificate_id)
        if not certification:
            raise NotFoundError(message="Certification not found")

        if user.certification_body_id != certification.certification_body_id and certification.organization_id != user.organization_id:
            raise ForbiddenError(message="Unauthorized access")

        return send_file(
            certification.certificate_pdf,
            as_attachment=True,
            download_name=f"Certificate_{certification.organization.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        )