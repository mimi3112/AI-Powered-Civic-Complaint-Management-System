"""
Utility script to delete a specific complaint and its status history.
Usage:
    python delete_complaint.py <complaint_id_or_title>
Example:
    python delete_complaint.py 3
    python delete_complaint.py manhole
"""
import sys
from app import create_app
from models import db
from models.complaint import Complaint, StatusHistory

def delete_complaint(target):
    app = create_app()
    with app.app_context():
        complaint = None
        if target.isdigit():
            complaint = db.session.get(Complaint, int(target))
        else:
            complaint = Complaint.query.filter(Complaint.title.ilike(f"%{target}%")).first()

        if not complaint:
            print(f"[ERROR] No complaint found matching: '{target}'")
            return False

        c_id = complaint.id
        c_title = complaint.title
        
        # Complaint model has cascade='all, delete-orphan' on status_history
        db.session.delete(complaint)
        db.session.commit()
        print(f"[SUCCESS] Deleted Complaint #{c_id} ('{c_title}') and all its associated audit history.")
        return True

if __name__ == '__main__':
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = "manhole"
    delete_complaint(target)
