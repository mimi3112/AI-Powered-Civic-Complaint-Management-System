import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base application configuration for civic complaint management prototype."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'civic-complaint-prototype-secret-key-2026')
    
    # SQLite is used for this prototype. SQLAlchemy ORM allows future swap to MySQL without changing business logic.
    instance_dir = os.path.join(basedir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(instance_dir, 'civic_complaints.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration for supporting images
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 Megabytes maximum file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
