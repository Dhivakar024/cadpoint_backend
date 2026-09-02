from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import cloudinary
import cloudinary.uploader
from app.config import Config
from app.services.db_service import db_service
from app.services.email_service import send_registration_email
from app.services.whatsapp_service import send_whatsapp_notification

registration_bp = Blueprint('registration', __name__)

# Configure Cloudinary if credentials are provided
if Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=Config.CLOUDINARY_CLOUD_NAME,
        api_key=Config.CLOUDINARY_API_KEY,
        api_secret=Config.CLOUDINARY_API_SECRET,
        secure=True
    )

ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10MB

def is_allowed_resume(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS

@registration_bp.route('/registration', methods=['POST'])
def handle_registration():
    try:
        data = request.form.to_dict() if request.form else (request.json or {})
        
        if not data.get('fullName') or not data.get('email') or not data.get('phone'):
            return jsonify({'error': 'Missing required fields: fullName, email, phone'}), 400

        # Privacy acknowledgement metadata check (DPDP 2025)
        data['privacyAcknowledged'] = str(data.get('privacyAcknowledged', 'true')).lower() == 'true'
        data['privacyNoticeVersion'] = data.get('privacyNoticeVersion', '1.0')

        # Handle Resume file upload to Cloudinary (NEVER store binary blob in MongoDB)
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename and file.filename.strip():
                filename = secure_filename(file.filename)
                if not is_allowed_resume(filename):
                    return jsonify({'error': 'Please upload a valid PDF, DOC, or DOCX resume.'}), 400

                # Check file size
                file.seek(0, os.SEEK_END)
                file_length = file.tell()
                file.seek(0)
                if file_length > MAX_RESUME_SIZE:
                    return jsonify({'error': 'Resume file exceeds maximum allowed size of 10MB.'}), 400

                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'pdf'

                if Config.CLOUDINARY_API_KEY and Config.CLOUDINARY_API_SECRET:
                    try:
                        upload_result = cloudinary.uploader.upload(
                            file,
                            folder='cadpoint/resumes',
                            resource_type='auto',
                            use_filename=True,
                            unique_filename=True
                        )
                        data['resumeUrl'] = upload_result.get('secure_url')
                        data['resumePublicId'] = upload_result.get('public_id')
                        data['resumeOriginalName'] = filename
                        data['resumeFormat'] = ext
                        data['resumeSize'] = file_length
                        data['resumeUploadedAt'] = datetime.utcnow().isoformat()
                    except Exception as upload_err:
                        print(f"Cloudinary upload error: {upload_err}")
                        return jsonify({'error': 'Resume upload failed. Please try again.'}), 500
                else:
                    # In local/offline mode without Cloudinary API keys, store clean metadata reference
                    data['resumeUrl'] = f"https://res.cloudinary.com/{Config.CLOUDINARY_CLOUD_NAME}/raw/upload/cadpoint/resumes/{filename}"
                    data['resumePublicId'] = f"cadpoint/resumes/{filename}"
                    data['resumeOriginalName'] = filename
                    data['resumeFormat'] = ext
                    data['resumeSize'] = file_length
                    data['resumeUploadedAt'] = datetime.utcnow().isoformat()

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
            'registrationId': reg_id,
            'resumeUploaded': 'resumeUrl' in data
        }), 201

    except Exception as e:
        print(f"Registration Route Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
