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
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):

            inviter_identity = get_jwt_identity()
            inviter = User.query.get_or_404(inviter_identity)
            if inviter.role.value not in required_roles:
                return {'message': 'You are not authorized to access this resource'}, 401
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def generate_invitation_token(invitation_id, role):
    """
    Generates a signed token containing the invitation_id and role.

    :param invitation_id: The unique identifier of the invitation.
    :param role: The role to assign upon accepting the invitation.
    :return: A signed token as a string.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    token_payload = {'invitation_id': invitation_id, 'role': role.value}
    return serializer.dumps(token_payload)


def verify_invitation_token(token, max_age=7 * 24 * 3600):
    """
    Verifies and decodes the invitation token.

    :param token: The signed token to verify.
    :param max_age: Maximum age of the token in seconds (default: 7 days).
    :return: A dictionary containing 'invitation_id' and 'role'.
    :raises: SignatureExpired, BadSignature
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.loads(token, max_age=max_age)


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
