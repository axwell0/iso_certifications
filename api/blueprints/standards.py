# blueprints/standards.py

from flask.views import MethodView
from flask_smorest import Blueprint
from flask import request
from api.schemas.mongodb_schemas import ISOStandardSchema
from api.models.mongodb_models import MongoDBClient
from api.utils.utils import roles_required
from flask_jwt_extended import jwt_required

standards_bp = Blueprint('Standards', 'standards', url_prefix='/standards')


@standards_bp.route('/')
class StandardsList(MethodView):
    @standards_bp.response(200, ISOStandardSchema(many=True))
    def get(self):
        """
        Retrieve a list of ISO standards with search and filter options.
        Query Parameters:
            - keyword: Search term across multiple fields.
            - category: Filter by Category.
            - subcategory: Filter by SubCategory.
            - publication_date: Filter by Publication Date.
            - stage: Filter by Stage.
            - technical_committee: Filter by Technical Committee.
            - ics: Filter by ICS codes (can be multiple).
        """
        mongo = MongoDBClient()
        query = {}
        keyword = request.args.get('keyword')
        if keyword:
            query['$or'] = [
                {'Iso': {'$regex': keyword, '$options': 'i'}},
                {'Category': {'$regex': keyword, '$options': 'i'}},
                {'SubCategory': {'$regex': keyword, '$options': 'i'}},
                {'description': {'$regex': keyword, '$options': 'i'}},
            ]
        # Additional filters
        category = request.args.get('category')
        if category:
            query['Category'] = category
        subcategory = request.args.get('subcategory')
        if subcategory:
            query['SubCategory'] = subcategory
        publication_date = request.args.get('publication_date')
        if publication_date:
            query['publication_date'] = publication_date
        stage = request.args.get('stage')
        if stage:
            query['stage'] = stage
        technical_committee = request.args.get('technical_committee')
        if technical_committee:
            query['technical_committee'] = technical_committee
        ics = request.args.getlist('ics')
        if ics:
            query['ics'] = {'$in': [int(ic) for ic in ics]}

        standards = mongo.fetch_standards(query)
        return standards

    @standards_bp.arguments(ISOStandardSchema)
    @standards_bp.response(201, ISOStandardSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def post(self, standard_data):
        """
        Add a new ISO standard to the catalog.
        """
        mongo = MongoDBClient()
        # Check for duplicates
        existing = mongo.standards.find_one({'Iso': standard_data['Iso']})
        if existing:
            return {"message": "ISO standard with this Iso already exists."}, 400
        inserted_id = mongo.insert_standard(standard_data)
        standard_data['_id'] = str(inserted_id)
        return standard_data


@standards_bp.route('/<string:standard_id>')
class StandardDetail(MethodView):
    @standards_bp.response(200, ISOStandardSchema)
    def get(self, standard_id):
        """
        Retrieve details of a specific ISO standard by its ID.
        """
        mongo = MongoDBClient()
        standard = mongo.find_standard_by_id(standard_id)
        if not standard:
            return {"message": "ISO standard not found."}, 404
        standard['_id'] = str(standard['_id'])
        return standard

    @standards_bp.arguments(ISOStandardSchema)
    @standards_bp.response(200, ISOStandardSchema)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def put(self, standard_data, standard_id):
        """
        Update details of a specific ISO standard.
        """
        mongo = MongoDBClient()
        standard = mongo.find_standard_by_id(standard_id)
        if not standard:
            return {"message": "ISO standard not found."}, 404
        mongo.update_standard(standard_id, standard_data)
        updated_standard = mongo.find_standard_by_id(standard_id)
        updated_standard['_id'] = str(updated_standard['_id'])
        return updated_standard

    @standards_bp.response(204)
    @jwt_required()
    @roles_required(['admin', 'manager'])
    def delete(self, standard_id):
        """
        Delete a specific ISO standard.
        """
        mongo = MongoDBClient()
        standard = mongo.find_standard_by_id(standard_id)
        if not standard:
            return {"message": "ISO standard not found."}, 404
        mongo.delete_standard(standard_id)
        return '', 204
