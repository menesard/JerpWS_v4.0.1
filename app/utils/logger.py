import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from flask import current_app

class Logger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Log dizini oluştur
        if not os.path.exists('logs'):
            os.mkdir('logs')
            
        # Dosya handler'ı
        self.file_handler = RotatingFileHandler(
            f'logs/{name}.log',
            maxBytes=10240,  # 10MB
            backupCount=10
        )
        self.file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        self.logger.addHandler(self.file_handler)
        
    def info(self, message):
        self.logger.info(message)
        
    def error(self, message):
        self.logger.error(message)
        
    def warning(self, message):
        self.logger.warning(message)
        
    def debug(self, message):
        self.logger.debug(message)
        
    def critical(self, message):
        self.logger.critical(message)

# Özel log fonksiyonları
def log_user_activity(user_id, action, details=None):
    """Kullanıcı aktivitelerini logla"""
    logger = Logger('user_activity')
    log_message = f"Kullanıcı ID: {user_id}, İşlem: {action}"
    if details:
        log_message += f", Detaylar: {details}"
    logger.info(log_message)

def log_system_event(event_type, message, severity='info'):
    """Sistem olaylarını logla"""
    logger = Logger('system')
    log_message = f"Olay Tipi: {event_type}, Mesaj: {message}"
    if severity == 'error':
        logger.error(log_message)
    elif severity == 'warning':
        logger.warning(log_message)
    else:
        logger.info(log_message)

def log_backup_event(action, status, details=None):
    """Yedekleme olaylarını logla"""
    logger = Logger('backup')
    log_message = f"İşlem: {action}, Durum: {status}"
    if details:
        log_message += f", Detaylar: {details}"
    logger.info(log_message)

def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """Güvenlik olaylarını logla"""
    logger = Logger('security')
    log_message = f"Olay Tipi: {event_type}"
    if user_id:
        log_message += f", Kullanıcı ID: {user_id}"
    if ip_address:
        log_message += f", IP Adresi: {ip_address}"
    if details:
        log_message += f", Detaylar: {details}"
    logger.warning(log_message) 