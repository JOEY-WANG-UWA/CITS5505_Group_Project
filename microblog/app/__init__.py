from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap5
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
import logging
from flask_dropzone import Dropzone

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
bootstrap = Bootstrap5()
moment = Moment()
babel = Babel()
dropzone = Dropzone()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    login.login_view = 'main.login'
    login.login_message = _l('Please log in to access this page.')

    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])  # Temporary line for debugging
    print("Debug mode is", app.debug)  # Print debug mode status

    from app.search_routes import search_bp
    from app.main_routes import main_bp
    from app.user_routes import user_bp

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(search_bp, url_prefix='/search')

    from app import models  # Import models after initializing app and blueprints

    return app
