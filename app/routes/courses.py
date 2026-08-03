from flask import Blueprint, request, jsonify
from app.services.db_service import db_service

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/courses', methods=['GET'])
def get_courses():
    category = request.args.get('category', 'All')
    courses = db_service.get_courses(category)
    return jsonify({
        'success': True,
        'count': len(courses),
        'courses': courses
    }), 200
