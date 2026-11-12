import os
import shutil
from app import create_app
from models import db
from models.user import User
from models.complaint import Complaint, StatusHistory

app = create_app()

with app.app_context():
    # Clear existing tables completely
    db.session.query(StatusHistory).delete()
    db.session.query(Complaint).delete()
    db.session.query(User).delete()
    db.session.commit()

    # Clear uploads folder
    upload_dir = app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_dir):
        for f in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, f)
            if os.path.isfile(file_path):
                os.remove(file_path)

    # Seed 1 Municipal Officer
    officer = User(
        name='Rajesh Sharma',
        email='rajesh.sharma@civic.gov.in',
        role='Municipal Officer'
    )
    officer.set_password('officer123')

    # Seed 1 Administrator
    admin = User(
        name='Ananya Verma',
        email='ananya.verma@civic.gov.in',
        role='Administrator'
    )
    admin.set_password('admin123')

    db.session.add(officer)
    db.session.add(admin)
    db.session.commit()

    print("=" * 60)
    print("DATABASE CLEANED & DEMO USERS SEEDED SUCCESSFULLY")
    print("=" * 60)
    print("1. Municipal Officer:")
    print("   - Name: Rajesh Sharma")
    print("   - Email: rajesh.sharma@civic.gov.in")
    print("   - Password: officer123")
    print("   - Direct Demo URL: http://127.0.0.1:5000/officer")
    print("-" * 60)
    print("2. Administrator:")
    print("   - Name: Ananya Verma")
    print("   - Email: ananya.verma@civic.gov.in")
    print("   - Password: admin123")
    print("   - Direct Demo URL: http://127.0.0.1:5000/admin")
    print("-" * 60)
    print("Complaints & Status History: 0 records (Clean)")
    print("Citizens: 0 records (Ready for you to register live)")
    print("=" * 60)
