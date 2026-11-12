from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    """
    User model representing actors in the Civic Complaint System:
    - Citizen
    - Municipal Officer
    - Administrator
    """
    __tablename__ = 'users'

    ROLE_CITIZEN = 'Citizen'
    ROLE_OFFICER = 'Municipal Officer'
    ROLE_ADMIN = 'Administrator'
    VALID_ROLES = [ROLE_CITIZEN, ROLE_OFFICER, ROLE_ADMIN]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship to complaints submitted by the user (primarily Citizens)
    complaints = db.relationship('Complaint', foreign_keys='Complaint.user_id', backref='author', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password: str):
        """Hashes the user password using Werkzeug."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies the plain password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' role='{self.role}'>"
