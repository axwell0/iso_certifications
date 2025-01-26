# audit_request_schemas.py
from marshmallow import Schema, fields, validate
from api.models.models import RequestStatusEnum

class AuditRequestCreateSchema(Schema):
    """
    Used by Organization Managers to create an audit request.
    """
    name = fields.String(required=True)
    certification_body_id = fields.String(required=True)
    scheduled_date = fields.String(required=True)
    standard_ids = fields.List(fields.String(), required=True)


class AuditRequestSchema(Schema):
    """
    For serializing/deserializing AuditRequest model data.
    """
    id = fields.String(dump_only=True)
    name = fields.String()
    organization_id = fields.String()
    certification_body_id = fields.String()
    requested_by_id = fields.String()
    standard_ids = fields.String()
    scheduled_date = fields.String()
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True, format="%d-%m-%Y")
    updated_at = fields.DateTime(dump_only=True, format="%d-%m-%Y")
