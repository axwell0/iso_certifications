from marshmallow import Schema, fields, validate


class ISOStandardSchema(Schema):
    Iso = fields.String(required=True, validate=validate.Length(min=1))
    Category = fields.String(required=True, validate=validate.Length(min=1))
    SubCategory = fields.String(required=True, validate=validate.Length(min=1))
    description = fields.String(required=True, validate=validate.Length(min=1))
    publication_date = fields.String(required=True)
    stage = fields.String(required=True, validate=validate.Length(min=1))
    edition = fields.String(required=True, validate=validate.Length(min=1))
    number_of_pages = fields.String(required=True, validate=validate.Range(min=1))
    technical_committee = fields.String(required=True, validate=validate.Length(min=1))
    ics = fields.String(required=True, validate=validate.Length(min=1))
    url = fields.String(required=True)
