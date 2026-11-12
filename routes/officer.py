from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db
from models.user import User
from models.complaint import Complaint, StatusHistory
from routes import role_required

officer_bp = Blueprint('officer', __name__, url_prefix='/officer')

@officer_bp.route('')
@officer_bp.route('/')
@officer_bp.route('/dashboard')
@role_required(User.ROLE_OFFICER)
def dashboard():
    """
    Municipal Officer dashboard.
    Strictly restricted to users with role == 'Municipal Officer'.
    """
    complaints = Complaint.query.order_by(Complaint.created_at.desc()).all()

    return render_template(
        'officer/dashboard.html',
        name=session.get('user_name', 'Municipal Officer'),
        role=session.get('user_role', User.ROLE_OFFICER),
        complaints=complaints
    )

@officer_bp.route('/update-status/<int:complaint_id>', methods=['POST'])
@role_required(User.ROLE_OFFICER)
def update_status(complaint_id: int):
    """
    Allows Municipal Officer to review and update complaint status
    (e.g., In Progress, Complaint Resolved, Needs More Info).
    Logs the transition into the StatusHistory audit table.
    """
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        flash('Complaint not found.', 'danger')
        return redirect(url_for('officer.dashboard'))

    new_status = request.form.get('new_status', '').strip()
    remarks = request.form.get('remarks', '').strip()

    valid_statuses = [
        Complaint.STATE_IN_PROGRESS,
        Complaint.STATE_RESOLVED,
        'Needs More Info',
        'Complaint Rejected'
    ]

    if new_status in valid_statuses:
        complaint.status = new_status
        history = StatusHistory(
            complaint_id=complaint.id,
            status=new_status,
            remarks=remarks if remarks else f'Status updated to {new_status} by officer.',
            updated_by=session.get('user_name', 'Municipal Officer')
        )
        db.session.add(history)
        db.session.commit()
        flash(f'Complaint #{complaint.id} status successfully updated to "{new_status}".', 'success')
    else:
        flash('Please select a valid status transition.', 'danger')

    return redirect(url_for('officer.dashboard'))
