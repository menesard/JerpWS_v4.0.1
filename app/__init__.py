from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Veritabanı nesnesi oluştur
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name='default'):
    app = Flask(__name__, instance_relative_config=True)

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    # Yapılandırma ayarlarını yükle
    from app.config import config
    app.config.from_object(config[config_name])
    app.config.from_pyfile('config.py', silent=True)  # Instance klasöründeki gizli config

    # JWT yapılandırmaları
    app.config["JWT_TOKEN_LOCATION"] = ["headers"]
    app.config["JWT_SECRET_KEY"] = app.config['SECRET_KEY']

    # Eklentileri uygulama ile ilişkilendir
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # auth.login değil, main.login

    # JWT başlat
    from app.routes.api import jwt
    jwt.init_app(app)

    # Blueprint'leri kaydet
    from app.routes.views import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Veritabanı modellerini içe aktar (migrate için gerekli)
    from app.models import database

    # Shell context oluştur
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': database.User,
            'Setting': database.Setting,
            'Region': database.Region,
            'Operation': database.Operation
        }

    with app.app_context():
        db.create_all()

    return app