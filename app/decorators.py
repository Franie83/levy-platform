from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def check_suspended(f):
    """Decorator to check if user is suspended"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and hasattr(current_user, 'status') and current_user.status == 'suspended':
            flash('Your account has been suspended. Please contact support.', 'danger')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please login to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            
            if current_user.role not in roles:
                flash('Access denied. You do not have permission to access this page.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
