import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/cadpoint_db')
    DB_NAME = os.getenv('DB_NAME', 'cadpoint_db')
    
    RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'notifications@caddpoint.co.in')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'support@caddpoint.co.in')
    
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN', '')
    WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID', '')
