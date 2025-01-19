# schemas/mongodb_schemas.py

from marshmallow import Schema, fields, validate, ValidationError
from datetime import datetime

class ISOStandardSchema(Schema):
    Iso = fields.String(required=True, validate=validate.Length(min=1))
    Category = fields.String(required=True, validate=validate.Length(min=1))
    SubCategory = fields.String(required=True, validate=validate.Length(min=1))
    description = fields.String(required=True, validate=validate.Length(min=1))
    publication_date = fields.Date(required=True)
    stage = fields.String(required=True, validate=validate.Length(min=1))
    edition = fields.String(required=True, validate=validate.Length(min=1))
    number_of_pages = fields.Integer(required=True, validate=validate.Range(min=1))
    technical_committee = fields.String(required=True, validate=validate.Length(min=1))
    ics = fields.List(fields.Integer(), required=True)
    url = fields.URL(required=True)