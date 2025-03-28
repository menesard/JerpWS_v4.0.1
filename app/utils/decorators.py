from functools import wraps
from flask import flash, redirect, url_for, request, g
from flask_login import current_user
from app.utils.helpers import get_timezone_from_ip

def role_required(role):
    """
    Belirli bir role sahip olma gerektiren rotalar için decorator
    role: 'admin', 'manager', 'staff'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_role(role):
                flash('Bu sayfaya erişim yetkiniz yok!', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def with_user_timezone(f):
    """
    İsteğin IP adresine göre kullanıcı zaman dilimini belirler
    ve g.user_timezone içinde saklar
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # İstemci IP adresini al
        ip_address = request.remote_addr
        # Proxy arkasındaysa X-Forwarded-For header'ını kontrol et
        if request.headers.get('X-Forwarded-For'):
            ip_address = request.headers.get('X-Forwarded-For').split(',')[0].strip()
            
        # Zaman dilimini belirle
        g.user_timezone = get_timezone_from_ip(ip_address)
        
        return f(*args, **kwargs)
    return decorated_function