from flask import Flask, jsonify
from flask_cors import CORS
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/*": {
        "origins": [
            "https://cadpoint-frontend.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
            "*"
        ],
        "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"]
    }})

    @app.route('/')
    @app.route('/api')
    def index():
        return jsonify({
            "status": "online",
            "service": "CADPOINT Production API Server",
            "version": "1.0.0",
            "frontend": "https://cadpoint-frontend.vercel.app",
            "endpoints": {
                "health": "/api/health",
                "courses": "/api/courses",
                "contact": "/api/contact",
                "registration": "/api/registration"
            }
        }), 200

    from app.routes.registration import registration_bp
    from app.routes.contact import contact_bp
    from app.routes.courses import courses_bp
    from app.routes.health import health_bp

    app.register_blueprint(registration_bp, url_prefix='/api')
    app.register_blueprint(contact_bp, url_prefix='/api')
    app.register_blueprint(courses_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')

    return app
