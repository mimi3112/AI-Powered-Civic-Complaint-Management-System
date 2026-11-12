"""
AI-Powered Civic Complaint Management System
Database Inspection Utility for Evaluation & Demonstration
"""
import os
from app import create_app
from config import Config
from models import db
from models.user import User
from models.complaint import Complaint, StatusHistory

def inspect_database():
    app = create_app()
    with app.app_context():
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'instance', 'civic_complaints.db'))
        print("=" * 80)
        print("       CIVIC COMPLAINT MANAGEMENT SYSTEM - DATABASE INSPECTION")
        print(f"Database File: {db_path}")
        print("=" * 80)

        # 1. USERS TABLE
        users = User.query.all()
        print(f"\n[TABLE: users] -> Total Records: {len(users)}")
        print("-" * 80)
        print(f"{'ID':<4} | {'Name':<22} | {'Email':<30} | {'Role':<18}")
        print("-" * 80)
        if not users:
            print("  (No user records found)")
        for u in users:
            print(f"{u.id:<4} | {u.name:<22} | {u.email:<30} | {u.role:<18}")

        # 2. COMPLAINTS TABLE
        complaints = Complaint.query.all()
        print(f"\n[TABLE: complaints] -> Total Records: {len(complaints)}")
        print("-" * 80)
        print(f"{'ID':<4} | {'Title':<25} | {'Category':<22} | {'Priority':<8} | {'Status':<18}")
        print("-" * 80)
        if not complaints:
            print("  (No complaint records found)")
        for c in complaints:
            print(f"#{c.id:<3} | {c.title[:24]:<25} | {c.category[:21]:<22} | {c.priority:<8} | {c.status:<18}")

        # 3. STATUS HISTORY TABLE
        histories = StatusHistory.query.order_by(StatusHistory.created_at.asc()).all()
        print(f"\n[TABLE: status_history] -> Total Records: {len(histories)}")
        print("-" * 80)
        print(f"{'CID':<4} | {'Status':<22} | {'Updated By':<22} | {'Remarks':<28}")
        print("-" * 80)
        if not histories:
            print("  (No status history records found)")
        for h in histories:
            print(f"#{h.complaint_id:<3} | {h.status:<22} | {h.updated_by:<22} | {h.remarks[:27]:<28}")
        print("=" * 80)

if __name__ == '__main__':
    inspect_database()
