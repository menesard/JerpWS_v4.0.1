import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Genel ayarlar
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gelistirme-ortami-gizli-anahtar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT ayarları
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-gizli-anahtar'
    JWT_TOKEN_LOCATION = ["headers", "cookies"]  # Token'ı headers veya cookies'den alabilir
    JWT_COOKIE_SECURE = False  # HTTPS için True yapın
    JWT_COOKIE_CSRF_PROTECT = False  # CSRF koruması için True yapın
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, '../instance/jewelry_dev.db')


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, '../instance/jewelry_test.db')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, '../instance/jewelry.db')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}