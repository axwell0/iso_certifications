from bson import ObjectId
from flask import current_app
from pymongo import MongoClient, TEXT
from pymongo.errors import PyMongoError, ConnectionFailure, OperationFailure


class MongoDBClient:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        """Initialize MongoDB connection with proper encoding and pooling"""

        self.client = MongoClient(current_app.config['MONGO_URI'])
        self.db = self.client['iso']
        self.standards = self.db['ISO']

        index_name = "text_search_index"
        index_fields = [
            ('Iso', TEXT),
            ('Category', TEXT),
            ('SubCategory', TEXT),
            ('description', TEXT)
        ]

        try:
            existing_indexes = self.standards.index_information()
            if index_name not in existing_indexes:
                self.standards.create_index(
                    index_fields,
                    name=index_name,
                    background=True
                )
                print(f"Created new index: {index_name}")
            else:
                print(f"Index {index_name} already exists")

        except OperationFailure as e:
            if "already exists with a different name" in str(e):
                print("Warning: Duplicate index with different name exists")
            else:
                raise RuntimeError(f"Index creation failed: {str(e)}")

    @staticmethod
    def _handle_errors(func):
        """Static decorator for error handling"""

        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)

            except ConnectionFailure:
                raise RuntimeError("Database connection failed")
            except OperationFailure as e:
                raise RuntimeError(f"Database operation failed: {str(e)}")
            except PyMongoError as e:
                raise RuntimeError(f"Database error: {str(e)}")

        return wrapper
    @_handle_errors
    def fetch_standards(self, query=None, projection=None, skip=0, limit=10):
        """Safe query execution with pagination"""
        query = query or {}

        return list(self.standards.find(
            filter=query,
            projection=projection,
            skip=skip,
            limit=limit
        ))

    @_handle_errors
    def count_standards(self, query=None):
        """Count documents matching the query"""
        query = query or {}
        return self.standards.count_documents(query)
    @_handle_errors
    def insert_standard(self, standard_data):
        """Insert with server-side validation"""
        result = self.standards.insert_one(standard_data)
        return self.standards.find_one({'_id': result.inserted_id})

    @_handle_errors
    def retire_standard(self, standard_iso):
        """Safe delete with proper ID conversion"""
        result = self.standards.update_one(
            {'Iso': standard_iso},
            {'$set': {'is_active': False}}
        )
        return result.matched_count > 0

    @_handle_errors
    def find_standard_by_id(self, standard_id):
        """Safe ID-based lookup"""
        return self.standards.find_one({'_id': ObjectId(standard_id)})

    @_handle_errors
    def find_standards_with_missing_data(self):
        """Optimized missing data query"""
        return list(self.standards.find({
            "$or": [
                {"Iso": {"$exists": False}},
                {"Category": {"$exists": False}},
                {"SubCategory": {"$exists": False}},
                {"description": {"$exists": False}},
            ]
        }))

    def health_check(self):
        """Connection health check"""
        try:
            self.client.admin.command('ping')
            return True
        except PyMongoError:
            return False