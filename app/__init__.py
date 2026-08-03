from flask import Flask
from flask_cors import CORS
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    from app.routes.registration import registration_bp
    from app.routes.contact import contact_bp
    from app.routes.courses import courses_bp
    from app.routes.health import health_bp

    app.register_blueprint(registration_bp, url_prefix='/api')
    app.register_blueprint(contact_bp, url_prefix='/api')
    app.register_blueprint(courses_bp, url_prefix='/api')
    app.register_blueprint(health_bp, url_prefix='/api')

    return app
