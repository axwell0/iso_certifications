from .extensions import db
from api.models.models import User, RoleEnum


def create_admin_user(email, full_name, password):
    existing_admin = User.query.filter_by(email=email).first()
    if not existing_admin:
        admin_user = User(email=email, full_name=full_name, role=RoleEnum.ADMIN)
        admin_user.set_password(password)
        admin_user.is_confirmed = True
        db.session.add(admin_user)
        db.session.commit()
