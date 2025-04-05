import os
import secrets
from datetime import timedelta

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Güvenli rastgele anahtarlar oluştur
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)
    
    # Veritabanı yapılandırması
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "instance", "kuyumcu.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Güvenlik ayarları
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # SSL/HTTPS ayarları
    PREFERRED_URL_SCHEME = 'https'
    
    # Production modu
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = False 