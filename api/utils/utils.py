from functools import wraps

from flask import current_app, abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from api.extensions import mail
from api.models.models import User


def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_USERNAME']
    )
    mail.send(msg)

    
def roles_required(required_roles):
    if isinstance(required_roles, str):
        required_roles = [required_roles]
        
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get_or_404(user_id)
            if not any(user.role.value == role for role in required_roles):
                abort(403, description="Insufficient permissions")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def generate_invitation_token(invitation_id):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    print("invitation_id", invitation_id)
    return serializer.dumps(invitation_id,salt='invitation-token')



def verify_invitation_token(token, max_age=604800):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        invitation_id = serializer.loads(
            token,
            salt='invitation-token',
            max_age=max_age
        )
    except Exception:
        return False
    return invitation_id


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirmation-salt')


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='email-confirmation-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')


def confirm_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
    except Exception:
        return False
    return email
