from marshmallow import fields, validate, Schema

from api.models.models import AuditStatusEnum


class AuditSchema(Schema):
    id = fields.String(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1))
    organization_id = fields.String(required=True)
    certification_body_id = fields.String(required=True)
    scheduled_date = fields.Date(required=True)
    status = fields.String(required=True)
    checklist = fields.String(required=True)
    created_at = fields.DateTime(dump_only=True, format="%d-%m-%Y")
    updated_at = fields.DateTime(dump_only=True, format="%d-%m-%Y")
    manager_id = fields.String(required=True)


class AuditCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1))
    organization_id = fields.String(required=True)
    standard_ids = fields.List(fields.String(), required=True)
    scheduled_date = fields.Date(required=True)


class AuditUpdateSchema(Schema):
    status = fields.String(validate=validate.OneOf([status.value for status in AuditStatusEnum]))
    scheduled_date = fields.String()
