from flask import Blueprint, jsonify
from app.services.db_service import db_service

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'CADPOINT Backend API',
        'mongodb_connected': db_service.is_connected
    }), 200
