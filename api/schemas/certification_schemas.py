from marshmallow import Schema, fields


class CertificationSchema(Schema):
    id = fields.String(dump_only=True)
    audit_id = fields.String(required=True)
    organization_id = fields.String(required=True)
    certification_body_id = fields.String(required=True)
    issued_date = fields.Date(required=True)
    status = fields.String(required=True)
    certificate_pdf = fields.String(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    issuer_id = fields.String(required=True)

class CertificationCreateSchema(Schema):
    audit_id = fields.String(required=True)
    issued_date = fields.Date(required=True)
