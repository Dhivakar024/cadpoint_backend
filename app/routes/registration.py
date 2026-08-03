from flask import Blueprint, request, jsonify
from app.services.db_service import db_service
from app.services.email_service import send_registration_email
from app.services.whatsapp_service import send_whatsapp_notification

registration_bp = Blueprint('registration', __name__)

@registration_bp.route('/registration', methods=['POST'])
def handle_registration():
    try:
        data = request.form.to_dict() if request.form else (request.json or {})
        
        if not data.get('fullName') or not data.get('email') or not data.get('phone'):
            return jsonify({'error': 'Missing required fields: fullName, email, phone'}), 400

        reg_id = db_service.save_registration(data)

        send_registration_email(
            to_email=data.get('email'),
            full_name=data.get('fullName'),
            reg_id=reg_id,
            course_name=data.get('courseName', 'CADPOINT Program'),
            extra_data=data
        )

        send_whatsapp_notification(
            phone_number=data.get('whatsapp') or data.get('phone'),
            full_name=data.get('fullName'),
            reg_id=reg_id
        )

        return jsonify({
            'success': True,
            'message': 'Registration submitted successfully',
            'registrationId': reg_id
        }), 201

    except Exception as e:
        print(f"Registration Route Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
