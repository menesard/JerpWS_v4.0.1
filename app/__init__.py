import os
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.utils.helpers import convert_utc_to_local
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import sys
from flask_jwt_extended import JWTManager

# Veritabanı nesnesi oluştur
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login'
jwt = JWTManager()


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    # Yapılandırma ayarlarını yükle
    app.config.from_object(config_class)
    app.config.from_pyfile('config.py', silent=True)  # Instance klasöründeki gizli config

    # JWT yapılandırmaları
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_SECRET_KEY"] = app.config['SECRET_KEY']

    # Eklentileri uygulama ile ilişkilendir
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    jwt.init_app(app)

    # Loglama yapılandırması
    if not app.debug and not app.testing:
        # Log dizini oluştur
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Dosya handler'ı
        file_handler = RotatingFileHandler(
            'logs/jerpws.log',
            maxBytes=10240,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        # Konsol handler'ı
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.INFO)
        app.logger.addHandler(console_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('JerpWS başlatılıyor...')

    # Blueprint'leri kaydet
    from app.routes.views import main_bp
    app.register_blueprint(main_bp)

    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Veritabanı modellerini içe aktar (migrate için gerekli)
    from app.models import database
    from app.models.database import Setting

    # Shell context oluştur
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': database.User,
            'Setting': database.Setting,
            'Region': database.Region,
            'Transaction': database.Transaction,
            'Customer': database.Customer,
            'GlobalSetting': database.GlobalSetting
        }

    # Template context processor ekle
    @app.context_processor
    def inject_settings():
        settings = Setting.query.all()
        return dict(settings=settings)

    @app.template_filter('localtime')
    def localtime_filter(value):
        """UTC zamanını yerel zamana çeviren şablon filtresi"""
        if hasattr(g, 'user_timezone'):
            return convert_utc_to_local(value, g.user_timezone)
        return value

    # Veritabanı oluşturulduğunda varsayılan ayarları ekle
    with app.app_context():
        db.create_all()
        Setting.init_default_settings()

    return app