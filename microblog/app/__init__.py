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

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
mail = Mail()
bootstrap = Bootstrap5()
moment = Moment()
babel = Babel()


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

    # print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])  # Temporary line for debugging
    # print("Debug mode is", app.debug)  # Print debug mode status

    # Define the to_int filter function
    def to_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    # Register the to_int filter with Jinja2
    app.jinja_env.filters['to_int'] = to_int

    from app.main_routes import main_bp
    from app.user_routes import user_bp

    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(user_bp, url_prefix='/user')

    from app import models  # Import models after initializing app and blueprints

    return app
