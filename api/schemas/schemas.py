from datetime import datetime

from marshmallow import Schema, fields, validates, ValidationError, validate

from api.models.models import RoleEnum, CertificationBody, Organization, Invitation

class MessageSchema(Schema):
    message = fields.Str(required=True)

class OrganizationCreationRequestSchema(Schema):
    id = fields.Str(dump_only=True)
    guest_id = fields.Str(dump_only=True)
    organization_name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(required=False, allow_none=True)
    status = fields.Str(dump_only=True)
    admin_comment = fields.Str(required=False, allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AdminReviewRequestSchema(Schema):
    admin_comment = fields.Str(required=False, allow_none=True)

class AcceptInvitationSchema(Schema):
    token = fields.Str(required=True)
class InvitationSchema(Schema):
    email = fields.Email(required=True)
    role = fields.Str(required=True, validate=validate.OneOf([role.value for role in RoleEnum if role != RoleEnum.ADMIN]))  # Exclude ADMIN from being assigned via invitation



class UserSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Email(required=True)
    full_name = fields.Str(required=True)
    role = fields.Str(required=True)
    organization_id = fields.Str(allow_none=True)
    certification_body_id = fields.Str(allow_none=True)
    is_confirmed = fields.Bool(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserRegistrationSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    full_name = fields.Str(required=True)
    invitation_token = fields.Str(required=False)  # Optional for guests

    @validates('invitation_token')
    def validate_invitation_token(self, value):
        if value:
            invitation = Invitation.query.filter_by(token=value, is_used=False).first()
            if not invitation:
                raise ValidationError("Invalid or expired invitation token.")
            if invitation.expires_at < datetime.utcnow():
                raise ValidationError("Invitation token has expired.")


class GuestRegistrationSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    full_name = fields.Str(required=True)
    role = fields.Str(required=True, validate=lambda x: x == 'guest')


class UserLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True)


class PasswordResetSchema(Schema):
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, load_only=True)


class UserEmailSchema(Schema):
    role = fields.Str(required=True,
                      validate=lambda x: x in [role.value for role in RoleEnum if role != RoleEnum.GUEST])
