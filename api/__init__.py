import atexit

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager

from .blueprints import certification_body, certification
from .blueprints.audit import audit_bp
from .blueprints.certification import certification_bp
from .blueprints.standards import standards_bp
from .config import Config
from .errors import register_error_handlers
from .extensions import db, migrate, mail, blp
from .jwt_utils import setup_jwt_callbacks
from .models.models import RevokedToken
from .blueprints.auth import auth_bp
from .blueprints.certification_body import certification_body_bp
from .blueprints.organization import organization_bp
from .seed import create_admin_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    jwt = JWTManager(app)
    db.init_app(app)
    migrate.init_app(app, db)
    register_error_handlers(app)
    mail.init_app(app)
    blp.init_app(app)
    setup_jwt_callbacks(jwt)
    with app.app_context():
        db.create_all()
        create_admin_user(app.config['ADMIN_EMAIL'], app.config['ADMIN_FULL_NAME'], app.config['ADMIN_PASSWORD'])

    app.register_blueprint(auth_bp)
    app.register_blueprint(organization_bp)
    app.register_blueprint(certification_bp)
    app.register_blueprint(standards_bp)
    app.register_blueprint(certification_body_bp)
    app.register_blueprint(audit_bp)



    def cleanup_database():
        with app.app_context():
            db.drop_all()
            print("All database tables have been dropped.")

    #atexit.register(cleanup_database)

    return app
