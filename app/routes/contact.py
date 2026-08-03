from flask import Blueprint, request, jsonify
from app.services.db_service import db_service
from app.services.email_service import send_enquiry_email
from app.services.whatsapp_service import send_contact_whatsapp_notification

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['POST'])
def handle_contact():
    try:
        data = request.json or request.form.to_dict() or {}
        
        if not data.get('name') or not data.get('email') or not data.get('message'):
            return jsonify({'error': 'Name, email, and message are required'}), 400

        # 1. Save Enquiry Lead to MongoDB Atlas
        db_service.save_enquiry(data)

        # 2. Trigger Transactional Email via Resend API to Admin Email (dhivakarm205@gmail.com)
        email_sent = send_enquiry_email(data)

        # 3. Trigger WhatsApp Lead Alert to 917811822644
        send_contact_whatsapp_notification(
            name=data.get('name'),
            phone=data.get('phone'),
            subject=data.get('subject', 'General Enquiry')
        )

        return jsonify({
            'success': True,
            'message': 'Enquiry received successfully',
            'email_sent': email_sent
        }), 201

    except Exception as e:
        print(f"Contact Route Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
