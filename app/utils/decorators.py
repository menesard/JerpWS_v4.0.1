from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

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