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

certification_bp = Blueprint('Certification', 'certification', url_prefix='/certification')

@certification_bp.route('/certificates')
class CertificationList(MethodView):
    @certification_bp.response(200, CertificationSchema(many=True))
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def get(self):
        """
        Retrieve a list of issued certifications.
        """
        certifications = Certification.query.all()
        return certifications

    @certification_bp.arguments(CertificationCreateSchema)
    @certification_bp.response(201, CertificationSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def post(self, certification_data):
        """
        Issue a new certification based on an audit.
        """
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        print(user)
        if not user.certification_body_id:
            return {"message": "Only certification body managers can issue certifications"}, 400
        audit = Audit.query.get_or_404(certification_data['audit_id'])
        if audit.status != AuditStatusEnum.COMPLETED:
            return {"message": "Audit must be completed before issuing certification."}, 400

        certification = Certification(
            audit_id=audit.id,
            organization_id=audit.organization_id,
            certification_body_id=audit.certification_body_id,
            issued_date=certification_data['issued_date'],
            status=CertificationStatusEnum.ISSUED,
            issuer_id = user_id,
            certificate_pdf=generate_certificate_pdf({"organization_id":audit.organization_id,"recipient_name":"cock","checklist":audit.checklist}),
        )
        print(certification)
        db.session.add(certification)
        db.session.commit()

        # Send certification email
        send_certification_email(certification)

        return certification

@certification_bp.route('/certificates/<string:certificate_id>/download')
class DownloadCertification(MethodView):
    @jwt_required()
    @roles_required(['admin', 'manager', 'user'])
    def get(self, certificate_id):
        """
        Download the certification PDF.
        """
        certification = Certification.query.get_or_404(certificate_id)
        return send_file(certification.certificate_pdf, as_attachment=True)
