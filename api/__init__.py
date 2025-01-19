import atexit

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager

from .config import Config
from .extensions import db, migrate, mail, blp
from .models.models import RevokedToken
from .resources.auth import auth_bp
from .resources.users import users_bp
from .seed import create_admin_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    jwt = JWTManager()
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    blp.init_app(app)
    with app.app_context():
        db.create_all()
        create_admin_user(app.config['ADMIN_EMAIL'], app.config['ADMIN_FULL_NAME'], app.config['ADMIN_PASSWORD'])

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)


    def cleanup_database():
        with app.app_context():
            db.drop_all()
            print("All database tables have been dropped.")

    #atexit.register(cleanup_database)

    return app
