# utils/audit_utils.py
from bson import ObjectId
from api.models.mongodb_models import MongoDBClient

def generate_audit_checklist(organization_id, standard_ids):
    """
    Generate an audit checklist based on selected ISO standards.
    """
    mongo = MongoDBClient()
    standards = mongo.fetch_standards({'_id': {'$in': [ObjectId(sid) for sid in standard_ids]}})
    checklist = []
    for standard in standards:
        checklist.append({
            'standard': standard.get('Iso'),
            'requirements': standard.get('description'),
            'compliance_status': False
        })
    return checklist
