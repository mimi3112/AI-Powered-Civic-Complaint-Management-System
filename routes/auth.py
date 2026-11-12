import re
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

@auth_bp.route('/')
def index():
    """Landing page displaying project title, overview, and quick links."""
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration handling for Citizen, Municipal Officer, and Administrator."""
    if 'user_id' in session:
        # Redirect already authenticated users to their corresponding dashboard
        return redirect_by_role(session.get('user_role'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role = request.form.get('role', '').strip()

        # Validation: Required fields
        if not name or not email or not password or not role:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

        # Validation: Email format
        if not re.match(EMAIL_REGEX, email):
            flash('Please enter a valid email address.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

        # Validation: Role validity
        if role not in User.VALID_ROLES:
            flash('Please select a valid user role.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

        # Validation: Duplicate email
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists. Please log in.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

        # Create new user and hash password with Werkzeug
        new_user = User(
            name=name,
            email=email,
            role=role
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You may now log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('auth/register.html', name=name, email=email, role=role)

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login handling with session creation and role-based redirection."""
    if 'user_id' in session:
        return redirect_by_role(session.get('user_role'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()

        # Validate credentials without disclosing which piece was incorrect
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        # Create session
        session.clear()
        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_role'] = user.role

        flash(f'Welcome back, {user.name}!', 'success')
        return redirect_by_role(user.role)

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    """Clears user session and redirects to login page."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

def redirect_by_role(role: str):
    """Helper to route authenticated users to their authorized dashboard."""
    if role == User.ROLE_CITIZEN:
        return redirect(url_for('citizen.dashboard'))
    elif role == User.ROLE_OFFICER:
        return redirect(url_for('officer.dashboard'))
    elif role == User.ROLE_ADMIN:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))
