from flask import Blueprint, render_template, session, redirect, url_for
from models.user import User
from models.complaint import Complaint
from routes import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('')
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@role_required(User.ROLE_ADMIN)
def dashboard():
    """
    Administrator dashboard.
    Strictly restricted to users with role == 'Administrator'.
    """
    total_users = User.query.count()
    total_complaints = Complaint.query.count()

    return render_template(
        'admin/dashboard.html',
        name=session.get('user_name', 'Administrator'),
        role=session.get('user_role', User.ROLE_ADMIN),
        total_users=total_users,
        total_complaints=total_complaints
    )
