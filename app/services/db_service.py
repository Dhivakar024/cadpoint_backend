from pymongo import MongoClient
import os
import random
from datetime import datetime

class DBService:
    def __init__(self):
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/cadpoint_db')
        db_name = os.getenv('DB_NAME', 'cadpoint_db')
        self.is_connected = False
        
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            self.is_connected = True
            print("Successfully connected to MongoDB Atlas / Local DB!")
        except Exception as e:
            print(f"MongoDB connection timeout/warning: {e}. Operating in graceful memory mode.")
            self.memory_registrations = []
            self.memory_enquiries = []

    def save_registration(self, reg_data):
        ref_id = f"CAD-{datetime.now().year}-{random.randint(100000, 999999)}"
        reg_data['registrationId'] = ref_id
        reg_data['status'] = 'pending'
        reg_data['createdAt'] = datetime.utcnow().isoformat()

        if self.is_connected:
            self.db.registrations.insert_one(reg_data)
        else:
            self.memory_registrations.append(reg_data)
            
        return ref_id

    def save_enquiry(self, enquiry_data):
        enquiry_data['status'] = 'new'
        enquiry_data['createdAt'] = datetime.utcnow().isoformat()

        if self.is_connected:
            self.db.enquiries.insert_one(enquiry_data)
        else:
            self.memory_enquiries.append(enquiry_data)
            
        return True

    def get_courses(self, category=None):
        if self.is_connected:
            query = {}
            if category and category != 'All':
                query['category'] = category
            courses = list(self.db.courses.find(query, {'_id': 0}))
            return courses
        return []

db_service = DBService()
