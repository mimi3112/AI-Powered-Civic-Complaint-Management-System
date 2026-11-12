from datetime import datetime, timezone
from models import db

class Complaint(db.Model):
    """
    Complaint model representing civic issues submitted by Citizens.
    Supports complete submission details including title, description, location,
    category, priority, supporting image, assigned officer, and audit history.
    """
    __tablename__ = 'complaints'

    STATE_SUBMITTED = 'Complaint Submitted'
    STATE_CATEGORIZED = 'Complaint Categorized'
    STATE_ASSIGNED = 'Department Assigned'
    STATE_UNDER_REVIEW = 'Complaint Under Review'
    STATE_IN_PROGRESS = 'In Progress'
    STATE_RESOLVED = 'Complaint Resolved'
    STATE_CLOSED = 'Complaint Closed'

    CATEGORIES = [
        'Roads & Potholes',
        'Water Supply & Drainage',
        'Electricity & Streetlights',
        'Garbage & Sanitation',
        'Public Infrastructure',
        'Other'
    ]

    PRIORITIES = ['Low', 'Medium', 'High', 'Highest']

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False, default='Not specified')
    category = db.Column(db.String(50), nullable=False, default='Other')
    priority = db.Column(db.String(20), nullable=False, default='Medium')
    image_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False, default=STATE_SUBMITTED)
    
    # Association with Citizen (User)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Association with Assigned Municipal Officer
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id])
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Status History relationship for chronological tracking audit trail
    status_history = db.relationship(
        'StatusHistory',
        backref='complaint',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='StatusHistory.created_at.asc()'
    )

    def __init__(self, **kwargs):
        super(Complaint, self).__init__(**kwargs)
        if not self.status:
            self.status = self.STATE_SUBMITTED
        if not self.category:
            self.category = 'Other'
        if not self.priority:
            self.priority = 'Medium'

    def __repr__(self):
        return f"<Complaint id={self.id} title='{self.title[:20]}' status='{self.status}'>"


class StatusHistory(db.Model):
    """
    StatusHistory model maintaining the chronological audit trail of state changes
    for each complaint, as specified in the Class, Sequence, and State diagrams.
    """
    __tablename__ = 'status_history'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.String(255), nullable=True)
    updated_by = db.Column(db.String(100), nullable=False, default='System')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<StatusHistory id={self.id} complaint_id={self.complaint_id} status='{self.status}'>"
