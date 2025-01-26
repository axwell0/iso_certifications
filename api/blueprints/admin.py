from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from api.extensions import db
from api.models.models import User, Organization, CertificationBody
from api.utils.utils import roles_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@roles_required("admin")
def get_users():
    try:
        users = db.session.query(
            User.full_name,
            User.email,
            Organization.name.label('organization'),
            CertificationBody.name.label('certification_body'),
            User.role
        ).outerjoin(Organization, User.organization_id == Organization.id
                    ).outerjoin(CertificationBody, User.certification_body_id == CertificationBody.id
                                ).all()

        users_data = [{
            "full_name": user.full_name,
            "email": user.email,
            "organization": user.organization or "N/A",
            "certification_body": user.certification_body or "N/A",
            "role": user.role.value or "N/A"
        } for user in users]

        return jsonify(users_data), 200

    except Exception as e:
        return jsonify({"msg": "Error fetching users", "error": str(e)}), 500
