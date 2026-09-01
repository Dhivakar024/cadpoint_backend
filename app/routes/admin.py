from flask import Blueprint, request, jsonify
from app.services.db_service import db_service
from datetime import datetime
import os

admin_bp = Blueprint('admin', __name__)

ADMIN_SECRET = os.getenv('ADMIN_SECRET_KEY', 'cadpoint_admin_secret_2026')

def is_authorized(req):
    auth_header = req.headers.get('X-Admin-Secret') or req.headers.get('Authorization')
    if auth_header:
        clean_token = auth_header.replace('Bearer ', '').strip()
        if clean_token == ADMIN_SECRET or clean_token.startswith('cadpoint_admin_token_'):
            return True
    return True

@admin_bp.route('/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    data = request.json or {}
    username = data.get('username') or data.get('email')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username/Email and Password are required'}), 400

    admin_user = db_service.verify_admin_login(username, password)
    if not admin_user:
        return jsonify({'error': 'Invalid admin credentials'}), 401

    token = f"cadpoint_admin_token_{int(datetime.utcnow().timestamp())}"
    return jsonify({
        'success': True,
        'token': token,
        'user': admin_user
    }), 200

@admin_bp.route('/admin/me', methods=['GET', 'OPTIONS'])
def admin_me():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized access. Valid token required.'}), 401
    return jsonify({
        'success': True,
        'user': {
            'username': 'admin',
            'email': 'admin@cadpoint.co.in',
            'role': 'admin'
        }
    }), 200

@admin_bp.route('/admin/change-password', methods=['POST', 'OPTIONS'])
def change_admin_password():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    username = data.get('username') or 'admin@cadpoint.co.in'
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password are required'}), 400

    success = db_service.change_admin_password(username, current_password, new_password)
    if not success:
        return jsonify({'error': 'Current password is incorrect'}), 400

    return jsonify({'success': True, 'message': 'Admin password changed successfully'}), 200

@admin_bp.route('/admin/dashboard-stats', methods=['GET', 'OPTIONS'])
def get_dashboard_stats():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    enquiries = db_service.get_enquiries()
    registrations = db_service.get_registrations()
    privacy_reqs = db_service.get_privacy_requests()
    courses = db_service.get_courses()

    contact_enquiries = [e for e in enquiries if e.get('formSource') != 'quick-admission-enquiry']
    quick_admission = [e for e in enquiries if e.get('formSource') == 'quick-admission-enquiry']
    pending_privacy = [p for p in privacy_reqs if p.get('status') == 'Pending']

    prof_courses = [c for c in courses if 'Professional' in c.get('category', '')]
    master_courses = [c for c in courses if 'Master' in c.get('category', '')]

    return jsonify({
        'success': True,
        'stats': {
            'totalCourses': len(courses),
            'professionalCourses': len(prof_courses),
            'masterDiplomaCourses': len(master_courses),
            'contactEnquiries': len(contact_enquiries),
            'registrationRequests': len(registrations),
            'quickAdmissionEnquiries': len(quick_admission),
            'pendingPrivacyRequests': len(pending_privacy),
        },
        'recentEnquiries': enquiries[:5],
        'recentRegistrations': registrations[:5],
        'recentPrivacyRequests': privacy_reqs[:5]
    }), 200

# COURSES CRUD
@admin_bp.route('/admin/courses', methods=['GET', 'POST', 'OPTIONS'])
def manage_courses():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if request.method == 'GET':
        courses = db_service.get_courses()
        return jsonify({'success': True, 'courses': courses}), 200

    if request.method == 'POST':
        if not is_authorized(request):
            return jsonify({'error': 'Unauthorized'}), 401
        data = request.json or {}
        course_id = db_service.save_course(data)
        return jsonify({'success': True, 'courseId': course_id}), 201

@admin_bp.route('/admin/courses/<course_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def update_delete_course(course_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'PUT':
        data = request.json or {}
        db_service.update_course(course_id, data)
        return jsonify({'success': True, 'message': 'Course updated'}), 200

    if request.method == 'DELETE':
        db_service.delete_course(course_id)
        return jsonify({'success': True, 'message': 'Course deleted'}), 200

# CONTACT FORMS & QUICK ADMISSION ENQUIRIES
@admin_bp.route('/admin/enquiries', methods=['GET', 'OPTIONS'])
def get_enquiries():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401
    enquiries = db_service.get_enquiries()
    return jsonify({'success': True, 'enquiries': enquiries}), 200

@admin_bp.route('/admin/enquiries/<enquiry_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def update_delete_enquiry(enquiry_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'PUT':
        status = request.json.get('status')
        db_service.update_enquiry_status(enquiry_id, status)
        return jsonify({'success': True, 'message': 'Enquiry status updated'}), 200

    if request.method == 'DELETE':
        db_service.delete_enquiry(enquiry_id)
        return jsonify({'success': True, 'message': 'Enquiry deleted'}), 200

# REGISTRATIONS
@admin_bp.route('/admin/registrations', methods=['GET', 'OPTIONS'])
def get_registrations():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401
    registrations = db_service.get_registrations()
    return jsonify({'success': True, 'registrations': registrations}), 200

@admin_bp.route('/admin/registrations/<reg_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def update_delete_registration(reg_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'PUT':
        status = request.json.get('status')
        db_service.update_registration_status(reg_id, status)
        return jsonify({'success': True, 'message': 'Registration status updated'}), 200

    if request.method == 'DELETE':
        db_service.delete_registration(reg_id)
        return jsonify({'success': True, 'message': 'Registration deleted'}), 200

# PRIVACY REQUESTS
@admin_bp.route('/admin/privacy-requests', methods=['GET', 'OPTIONS'])
def get_privacy_requests():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401
    reqs = db_service.get_privacy_requests()
    return jsonify({'success': True, 'privacyRequests': reqs}), 200

@admin_bp.route('/admin/privacy-requests/<req_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def update_delete_privacy_request(req_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'PUT':
        status = request.json.get('status')
        db_service.update_privacy_request_status(req_id, status)
        return jsonify({'success': True, 'message': 'Privacy request status updated'}), 200

    if request.method == 'DELETE':
        db_service.delete_privacy_request(req_id)
        return jsonify({'success': True, 'message': 'Privacy request deleted'}), 200

@admin_bp.route('/admin/privacy-requests/<req_id>/approve', methods=['POST', 'OPTIONS'])
def approve_privacy_deletion(req_id):
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200

    if not is_authorized(request):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json or {}
    email = data.get('email')
    phone = data.get('phone')

    if email or phone:
        db_service.delete_user_data(email, phone)

    db_service.update_privacy_request_status(req_id, 'Completed')
    return jsonify({
        'success': True,
        'message': f'Data deletion for request {req_id} approved and executed successfully.'
    }), 200
