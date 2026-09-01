from flask import Blueprint, request, jsonify
from app.services.db_service import db_service

privacy_bp = Blueprint('privacy', __name__)

@privacy_bp.route('/privacy/view-data', methods=['POST'])
def view_user_data():
    try:
        data = request.json or request.form.to_dict() or {}
        email = data.get('email')
        phone = data.get('phone')

        if not email or not phone:
            return jsonify({'error': 'Both Email and Phone Number are required for verification'}), 400

        user_data = db_service.get_user_data(email, phone)

        return jsonify({
            'success': True,
            'email': email,
            'phone': phone,
            'data': user_data
        }), 200

    except Exception as e:
        print(f"Privacy View Data Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@privacy_bp.route('/privacy/request-deletion', methods=['POST'])
def request_data_deletion():
    try:
        data = request.json or request.form.to_dict() or {}
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')

        if not name or not email or not phone:
            return jsonify({'error': 'Name, Email, and Phone Number are required'}), 400

        req_id = db_service.save_privacy_request(data)

        return jsonify({
            'success': True,
            'message': 'Your data deletion request has been submitted successfully. Our team will review the request and process it accordingly.',
            'requestId': req_id
        }), 201

    except Exception as e:
        print(f"Privacy Request Deletion Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
