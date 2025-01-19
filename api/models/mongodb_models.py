from pymongo import MongoClient
from flask import current_app

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(current_app.config['MONGO_URI'])
        self.db = self.client['iso']
        self.standards = self.db['ISO']


    def fetch_standards(self, query={}, projection=None):
        return list(self.standards.find(query, projection))

    def insert_standard(self, standard_data):
        return self.standards.insert_one(standard_data).inserted_id

    def update_standard(self, standard_id, update_data):
        return self.standards.update_one({'_id': standard_id}, {'$set': update_data})

    def delete_standard(self, standard_id):
        return self.standards.delete_one({'_id': standard_id})

    def find_standard_by_id(self, standard_id):
        return self.standards.find_one({'_id': standard_id})

    def find_standards_with_missing_data(self):
        query = {
            "$or": [
                {"Iso": {"$exists": False}},
                {"Category": {"$exists": False}},
                {"SubCategory": {"$exists": False}},
                {"description": {"$exists": False}},
                {"publication_date": {"$exists": False}},
                {"stage": {"$exists": False}},
                {"edition": {"$exists": False}},
                {"number_of_pages": {"$exists": False}},
                {"technical_committee": {"$exists": False}},
                {"ics": {"$exists": False}},
                {"url": {"$exists": False}},
            ]
        }
        return list(self.standards.find(query))