from flask.views import MethodView
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_smorest import Blueprint

from api.errors import NotFoundError
from api.models.models import User, Organization, CertificationBody
from api.schemas.schemas import UserSchema

user_bp = Blueprint('User', 'user', url_prefix='/user')
@user_bp.route('/profile')
class ProfileDetails(MethodView):
    @jwt_required()
    @user_bp.response(status_code=200, schema=UserSchema)
    def get(self):
        user_id = get_jwt_identity()
        user = User.query.filter_by(id=user_id).first()
        if not user:
            raise NotFoundError("User not found.")

        response_data = {

            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

        if user.organization_id:
            organization = Organization.query.filter_by(id=user.organization_id).first()
            response_data["organization_id"] = user.organization_id
            response_data["organization_name"] = organization.name
        elif user.certification_body_id:
            certification_body = CertificationBody.query.filter_by(id=user.certification_body_id).first()
            response_data["certification_body_id"] = user.certification_body_id
            response_data["certification_body_name"] = certification_body.name

        return response_data

