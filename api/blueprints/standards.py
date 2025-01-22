from functools import lru_cache

from bson.errors import InvalidId
from flask import request, current_app
from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from pymongo.errors import PyMongoError

from api.models.mongodb_model import MongoDBClient
from api.schemas.mongodb_schemas import ISOStandardSchema
from api.utils.utils import roles_required

standards_bp = Blueprint('Standards', 'standards', url_prefix='/standards')


@lru_cache(maxsize=None)
def get_mongo_client():
    return MongoDBClient()


QUERY_PARAMS = {
    'category': 'Category',
    'subcategory': 'SubCategory',
    'publication_date': 'publication_date',
    'stage': 'stage',
    'technical_committee': 'technical_committee',
    'edition': 'edition',
    'ics': 'ics'
}


def build_query():
    """Handle both URL params and JSON body"""
    if request.method == 'GET':
        args = request.args
    else:
        args = request.get_json(silent=True) or {}

    query = {}

    if keyword := args.get('keyword'):
        print(keyword)
        query['$text'] = {'$search': keyword}

    for param, field in QUERY_PARAMS.items():
        if value := args.get(param):
            query[field] = value

    return query


@standards_bp.route('/')
class StandardsList(MethodView):
    @standards_bp.response(200, ISOStandardSchema(many=True))
    def get(self):
        """Optimized search with pagination and indexing"""
        mongo = get_mongo_client()
        try:
            query = build_query()
            offset = int(request.args.get('offset', 0))
            limit = int(request.args.get('limit', 50))

            return mongo.fetch_standards(
                query=query,
                skip=offset,
                limit=limit
            )
        except PyMongoError as e:
            current_app.logger.error(f"MongoDB error: {str(e)}")
            abort(500, message="Database operation failed")
        except ValueError as e:
            abort(400, message=str(e))


@standards_bp.route('/<string:standard_iso>')
class StandardDetail(MethodView):
    @standards_bp.response(204)
    @jwt_required()
    @roles_required('admin')
    def delete(self, standard_iso):
        """Retires standard"""
        mongo = get_mongo_client()
        try:
            if not mongo.retire_standard(standard_iso):
                abort(404, message="ISO standard not found")
            return {"message": f"{standard_iso} has been retired!"}, 204
        except InvalidId:
            abort(400, message="Invalid standard ID format")
        except PyMongoError as e:
            current_app.logger.error(f"MongoDB error: {str(e)}")
            abort(500, message="Database operation failed")
