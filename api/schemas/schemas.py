from datetime import datetime

from marshmallow import Schema, fields, validates, ValidationError, validate, pre_load

from api.models.models import RoleEnum, CertificationBody, Organization, Invitation

class MessageSchema(Schema):
    message = fields.Str(required=True)

class CertificationBodyCreationRequestSchema(Schema):
    id = fields.String(dump_only=True)
    guest_id = fields.String(dump_only=True)
    certification_body_name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    address = fields.String(required=True, validate=validate.Length(min=1, max=255))
    contact_phone = fields.String(required=True, validate=validate.Length(min=10, max=20))
    contact_email = fields.Email(required=True, validate=validate.Length(max=120))
    status = fields.String(dump_only=True)
    admin_comment = fields.String(required=False, allow_none=True, validate=validate.Length(max=1000))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates('certification_body_name')
    def validate_certification_body_name(self, value):
        """Ensure that the certification body name is unique."""
        if CertificationBody.query.filter_by(name=value).first():
            raise ValidationError('A certification body with this name already exists.')
class OrganizationCreationRequestSchema(Schema):
    id = fields.Str(dump_only=True)
    guest_id = fields.Str(dump_only=True)
    organization_name = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(required=True, allow_none=True)
    address = fields.Str(required=True, nullable=False)
    contact_email = fields.Str(required=True, nullable=False)
    contact_phone = fields.Str(required=True, nullable=False)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class AdminReviewRequestSchema(Schema):
    admin_comment = fields.Str(required=False, allow_none=True)
    id = fields.Str(required=True)

class AcceptInvitationSchema(Schema):
    token = fields.Str(required=True)

class InvitationRevokeID(Schema):
    id = fields.Str(required=True)


class InvitationSchema(Schema):
    id = fields.Str(dump_only=True)
    email = fields.Email(required=True)
    role = fields.Str(required=True, validate=validate.OneOf([role.value for role in RoleEnum if role != RoleEnum.ADMIN]))  # Exclude ADMIN from being assigned via invitation
    status = fields.Str(dump_only=True)


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
    email = fields.Email(required=False)
    password = fields.Str(required=True, load_only=True)
    full_name = fields.Str(required=True)
    token = fields.Str(required=False)

    @pre_load
    def validate_email_or_token(self, data, **kwargs):
        """
        Ensure that either `email` is provided (for self-registration) or
        `invitation_token` is provided (for invitation-based registration).
        """
        if not data.get("email") and not data.get("token"):
            raise ValidationError("Either 'email' or 'token' must be provided.")
        return data



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
