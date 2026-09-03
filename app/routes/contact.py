from flask import Blueprint, request, jsonify
from app.services.db_service import db_service
from app.services.email_service import send_enquiry_email
from app.services.whatsapp_service import send_contact_whatsapp_notification

contact_bp = Blueprint('contact', __name__)

@contact_bp.route('/contact', methods=['POST'])
def handle_contact():
    try:
        data = request.json or request.form.to_dict() or {}
        
        # Name is required; Contact must have at least phone or email
        if not data.get('name') or (not data.get('email') and not data.get('phone')):
            return jsonify({'error': 'Name and contact info (phone or email) are required'}), 400

        # Support optional message (default for quick admission enquiries)
        if not data.get('message') or not str(data.get('message')).strip():
            subject = data.get('subject', 'Course Counselling')
            data['message'] = f"Quick Admission Enquiry for {subject}"

        # Privacy acknowledgement metadata check (DPDP 2025)
        data['privacyAcknowledged'] = str(data.get('privacyAcknowledged', 'true')).lower() == 'true'
        data['privacyNoticeVersion'] = data.get('privacyNoticeVersion', '1.0')
        data['formSource'] = data.get('formSource', 'contact-us')
        data['status'] = data.get('status', 'New')

        # 1. Save Enquiry Lead to MongoDB Atlas
        db_service.save_enquiry(data)

        # 2. Trigger Transactional Email via Resend API to Admin Email
        email_sent = False
        try:
            email_sent = send_enquiry_email(data)
        except Exception as mail_err:
            print(f"Email service error: {mail_err}")

        # 3. Trigger WhatsApp Lead Alert
        try:
            send_contact_whatsapp_notification(
                name=data.get('name'),
                phone=data.get('phone'),
                subject=data.get('subject', 'General Enquiry')
            )
        except Exception as wa_err:
            print(f"WhatsApp notification error: {wa_err}")

        return jsonify({
            'success': True,
            'message': 'Enquiry received successfully',
            'email_sent': email_sent
        }), 201

    except Exception as e:
        print(f"Contact Route Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
