from functools import wraps

from flask import current_app, abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from .extensions import mail

def send_email(to, subject, template):
    msg = Message(
        subject,
        recipients=[to],
        html=template,
        sender=current_app.config['MAIL_USERNAME']
    )
    mail.send(msg)

def roles_required(required_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            jwt = get_jwt()
            user_role = jwt.get('role')
            print(user_role)
            if user_role not in [role.value for role in required_roles]:
                abort(403, description="You do not have permission to access this resource.")
            return fn(*args, **kwargs)
        return wrapper
    return decorator


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
