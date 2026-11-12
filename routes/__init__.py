from functools import wraps
from flask import session, flash, redirect, url_for, abort

def login_required(f):
    """Decorator to enforce that the user must be authenticated."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """
    Decorator to enforce Role-Based Access Control (RBAC).
    Restricts access to users having one of the specified allowed roles.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                # Abort with HTTP 403 Forbidden if the user lacks authorization
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
