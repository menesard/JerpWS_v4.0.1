import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

# Uygulama bilgileri
APP_NAME = "JerpWS"
APP_FULL_NAME = "Jewelry ERP - Workshop"
APP_VERSION = "1.0.0"
APP_COMPANY = "ARD INC."
APP_YEAR = "2025"
APP_COPYRIGHT = f"© {APP_YEAR} {APP_COMPANY}. Tüm hakları saklıdır."


class Config:
    # Genel ayarlar
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gelistirme-ortami-gizli-anahtar'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uygulama bilgileri
    APP_NAME = APP_NAME
    APP_FULL_NAME = APP_FULL_NAME
    APP_VERSION = APP_VERSION
    APP_COMPANY = APP_COMPANY
    APP_COPYRIGHT = APP_COPYRIGHT

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
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, '../instance/jewelry.db')

    # Prodüksiyon ortamında daha güvenli ayarlar
    JWT_COOKIE_SECURE = True  # HTTPS gerektir
    JWT_COOKIE_CSRF_PROTECT = True  # CSRF koruması aktif


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
}