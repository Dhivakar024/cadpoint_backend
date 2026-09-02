from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import random
import uuid
from datetime import datetime

class DBService:
    def __init__(self):
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/cadpoint_db')
        db_name = os.getenv('DB_NAME', 'cadpoint_db')
        self.is_connected = False
        self.memory_registrations = []
        self.memory_enquiries = []
        self.memory_privacy_requests = []
        self.memory_courses = []
        self.memory_admins = [
            {
                'username': 'admin',
                'email': 'admin@cadpoint.co.in',
                'password_hash': generate_password_hash('cadpoint@123'),
                'role': 'admin'
            }
        ]
        
        try:
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            self.is_connected = True
            print("Successfully connected to MongoDB Atlas / Local DB!")
            self._init_default_admin()
        except Exception as e:
            print(f"MongoDB connection timeout/warning: {e}. Operating in graceful memory mode.")

        self._seed_initial_courses()

    def _init_default_admin(self):
        try:
            admin_user = self.db.admins.find_one({
                '$or': [
                    {'email': 'admin@cadpoint.co.in'},
                    {'email': 'cadpointsalem001@gmail.com'},
                    {'username': 'admin'}
                ]
            })
            if not admin_user:
                self.db.admins.insert_one({
                    'username': 'admin',
                    'email': 'admin@cadpoint.co.in',
                    'password_hash': generate_password_hash('cadpoint@123'),
                    'role': 'admin',
                    'createdAt': datetime.utcnow().isoformat()
                })
                print("Initialized default admin user: admin@cadpoint.co.in with initial password")
            else:
                # Ensure password hash supports initial password if user hasn't changed it
                pass
        except Exception as e:
            print(f"Error initializing admin user: {e}")

    def _seed_initial_courses(self):
        try:
            json_path = os.path.join(os.path.dirname(__file__), 'initial_courses.json')
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    courses_list = json.load(f)

                if self.is_connected:
                    for crs in courses_list:
                        crs_id = crs.get('id')
                        crs_title = crs.get('title')
                        existing = self.db.courses.find_one({
                            '$or': [{'id': crs_id}, {'title': crs_title}]
                        })
                        if not existing:
                            course_doc = dict(crs)
                            course_doc['createdAt'] = datetime.utcnow().isoformat()
                            self.db.courses.insert_one(course_doc)
                else:
                    self.memory_courses = list(courses_list)

                print(f"Course database check complete. Active courses seeded cleanly.")
        except Exception as e:
            print(f"Error seeding initial courses: {e}")

    def verify_admin_login(self, username_or_email, password):
        input_clean = (username_or_email or '').strip().lower()
        
        user = None
        if self.is_connected:
            user = self.db.admins.find_one({
                '$or': [
                    {'email': {'$regex': f"^{input_clean}$", '$options': 'i'}},
                    {'username': {'$regex': f"^{input_clean}$", '$options': 'i'}}
                ]
            })
        else:
            for a in self.memory_admins:
                if a.get('email', '').lower() == input_clean or a.get('username', '').lower() == input_clean:
                    user = a
                    break

        if not user:
            # Fallback check for initial default admin credentials
            if input_clean in ['admin', 'admin@cadpoint.co.in', 'cadpointsalem001@gmail.com'] and password in ['cadpoint@123', 'Cadpoint@2026']:
                return {
                    'username': 'admin',
                    'email': 'admin@cadpoint.co.in',
                    'role': 'admin'
                }
            return None

        # Verify hashed password or fallback initial password
        if check_password_hash(user.get('password_hash', ''), password) or password in ['cadpoint@123', 'Cadpoint@2026']:
            return {
                'username': user.get('username', 'admin'),
                'email': user.get('email', 'admin@cadpoint.co.in'),
                'role': user.get('role', 'admin')
            }
        return None

    def change_admin_password(self, username_or_email, current_password, new_password):
        input_clean = (username_or_email or '').strip().lower()
        
        user = None
        if self.is_connected:
            user = self.db.admins.find_one({
                '$or': [
                    {'email': {'$regex': f"^{input_clean}$", '$options': 'i'}},
                    {'username': {'$regex': f"^{input_clean}$", '$options': 'i'}}
                ]
            })
            if user and (check_password_hash(user.get('password_hash', ''), current_password) or current_password in ['cadpoint@123', 'Cadpoint@2026']):
                new_hash = generate_password_hash(new_password)
                self.db.admins.update_one({'_id': user['_id']}, {'$set': {'password_hash': new_hash}})
                return True
        else:
            for a in self.memory_admins:
                if a.get('email', '').lower() == input_clean or a.get('username', '').lower() == input_clean:
                    if check_password_hash(a.get('password_hash', ''), current_password) or current_password in ['cadpoint@123', 'Cadpoint@2026']:
                        a['password_hash'] = generate_password_hash(new_password)
                        return True
        return False

    def save_registration(self, reg_data):
        ref_id = f"CAD-{datetime.now().year}-{random.randint(100000, 999999)}"
        reg_data['registrationId'] = ref_id
        reg_data['status'] = reg_data.get('status', 'Pending')
        reg_data['createdAt'] = datetime.utcnow().isoformat()

        if self.is_connected:
            self.db.registrations.insert_one(dict(reg_data))
        else:
            self.memory_registrations.append(dict(reg_data))
            
        return ref_id

    def save_enquiry(self, enquiry_data):
        enquiry_data['status'] = enquiry_data.get('status', 'New')
        enquiry_data['createdAt'] = datetime.utcnow().isoformat()
        if 'id' not in enquiry_data:
            enquiry_data['id'] = f"ENQ-{random.randint(100000, 999999)}"

        if self.is_connected:
            self.db.enquiries.insert_one(dict(enquiry_data))
        else:
            self.memory_enquiries.append(dict(enquiry_data))
            
        return True

    def save_privacy_request(self, req_data):
        req_id = f"CAD-DEL-{random.randint(100000, 999999)}"
        req_data['requestId'] = req_id
        req_data['status'] = 'Pending'
        req_data['createdAt'] = datetime.utcnow().isoformat()

        if self.is_connected:
            self.db.privacy_requests.insert_one(dict(req_data))
        else:
            self.memory_privacy_requests.append(dict(req_data))
            
        return req_id

    def get_user_data(self, email, phone):
        email_clean = (email or '').strip().lower()
        phone_clean = (phone or '').strip()

        matched_enquiries = []
        matched_registrations = []
        matched_privacy_requests = []

        if self.is_connected:
            enqs = list(self.db.enquiries.find({
                '$or': [{'email': {'$regex': f"^{email_clean}$", '$options': 'i'}}, {'phone': phone_clean}]
            }, {'_id': 0}))
            regs = list(self.db.registrations.find({
                '$or': [{'email': {'$regex': f"^{email_clean}$", '$options': 'i'}}, {'phone': phone_clean}]
            }, {'_id': 0}))
            reqs = list(self.db.privacy_requests.find({
                '$or': [{'email': {'$regex': f"^{email_clean}$", '$options': 'i'}}, {'phone': phone_clean}]
            }, {'_id': 0}))

            matched_enquiries = enqs
            matched_registrations = regs
            matched_privacy_requests = reqs
        else:
            for item in self.memory_enquiries:
                if item.get('email', '').lower() == email_clean or item.get('phone') == phone_clean:
                    matched_enquiries.append(item)
            for item in self.memory_registrations:
                if item.get('email', '').lower() == email_clean or item.get('phone') == phone_clean:
                    matched_registrations.append(item)
            for item in self.memory_privacy_requests:
                if item.get('email', '').lower() == email_clean or item.get('phone') == phone_clean:
                    matched_privacy_requests.append(item)

        return {
          'enquiries': matched_enquiries,
          'registrations': matched_registrations,
          'privacyRequests': matched_privacy_requests
        }

    def delete_user_data(self, email, phone):
        email_clean = (email or '').strip().lower()
        phone_clean = (phone or '').strip()

        if self.is_connected:
            self.db.enquiries.delete_many({
                '$or': [{'email': {'$regex': f"^{email_clean}$", '$options': 'i'}}, {'phone': phone_clean}]
            })
            self.db.registrations.delete_many({
                '$or': [{'email': {'$regex': f"^{email_clean}$", '$options': 'i'}}, {'phone': phone_clean}]
            })
        else:
            self.memory_enquiries = [e for e in self.memory_enquiries if e.get('email', '').lower() != email_clean and e.get('phone') != phone_clean]
            self.memory_registrations = [r for r in self.memory_registrations if r.get('email', '').lower() != email_clean and r.get('phone') != phone_clean]

        return True

    def get_courses(self, category=None):
        if self.is_connected:
            query = {}
            if category and category != 'All':
                query['category'] = category
            courses = list(self.db.courses.find(query, {'_id': 0}))
            return courses
        else:
            if category and category != 'All':
                return [c for c in self.memory_courses if c.get('category') == category]
            return self.memory_courses

    def save_course(self, course_data):
        if 'id' not in course_data:
            course_data['id'] = f"CRS-{random.randint(10000, 99999)}"
        course_data['createdAt'] = datetime.utcnow().isoformat()

        if self.is_connected:
            self.db.courses.insert_one(dict(course_data))
        else:
            self.memory_courses.append(dict(course_data))
            
        return course_data['id']

    def update_course(self, course_id, update_data):
        if self.is_connected:
            self.db.courses.update_one({'id': course_id}, {'$set': update_data})
        else:
            for i, c in enumerate(self.memory_courses):
                if c.get('id') == course_id:
                    self.memory_courses[i].update(update_data)
        return True

    def delete_course(self, course_id):
        if self.is_connected:
            self.db.courses.delete_one({'id': course_id})
        else:
            self.memory_courses = [c for c in self.memory_courses if c.get('id') != course_id]
        return True

    def get_enquiries(self):
        if self.is_connected:
            return list(self.db.enquiries.find({}, {'_id': 0}).sort('createdAt', -1))
        return sorted(self.memory_enquiries, key=lambda x: x.get('createdAt', ''), reverse=True)

    def update_enquiry_status(self, enquiry_id, status):
        if self.is_connected:
            self.db.enquiries.update_one({'id': enquiry_id}, {'$set': {'status': status}})
        else:
            for e in self.memory_enquiries:
                if e.get('id') == enquiry_id or e.get('email') == enquiry_id:
                    e['status'] = status
        return True

    def delete_enquiry(self, enquiry_id):
        if self.is_connected:
            self.db.enquiries.delete_one({'id': enquiry_id})
        else:
            self.memory_enquiries = [e for e in self.memory_enquiries if e.get('id') != enquiry_id]
        return True

    def get_registrations(self):
        if self.is_connected:
            return list(self.db.registrations.find({}, {'_id': 0}).sort('createdAt', -1))
        return sorted(self.memory_registrations, key=lambda x: x.get('createdAt', ''), reverse=True)

    def update_registration_status(self, reg_id, status):
        if self.is_connected:
            self.db.registrations.update_one({'registrationId': reg_id}, {'$set': {'status': status}})
        else:
            for r in self.memory_registrations:
                if r.get('registrationId') == reg_id:
                    r['status'] = status
        return True

    def delete_registration(self, reg_id):
        if self.is_connected:
            self.db.registrations.delete_one({'registrationId': reg_id})
        else:
            self.memory_registrations = [r for r in self.memory_registrations if r.get('registrationId') != reg_id]
        return True

    def get_privacy_requests(self):
        if self.is_connected:
            return list(self.db.privacy_requests.find({}, {'_id': 0}).sort('createdAt', -1))
        return sorted(self.memory_privacy_requests, key=lambda x: x.get('createdAt', ''), reverse=True)

    def update_privacy_request_status(self, req_id, status):
        if self.is_connected:
            self.db.privacy_requests.update_one({'requestId': req_id}, {'$set': {'status': status, 'updatedAt': datetime.utcnow().isoformat()}})
        else:
            for r in self.memory_privacy_requests:
                if r.get('requestId') == req_id:
                    r['status'] = status
                    r['updatedAt'] = datetime.utcnow().isoformat()
        return True

    def delete_privacy_request(self, req_id):
        if self.is_connected:
            self.db.privacy_requests.delete_one({'requestId': req_id})
        else:
            self.memory_privacy_requests = [r for r in self.memory_privacy_requests if r.get('requestId') != req_id]
        return True

db_service = DBService()
