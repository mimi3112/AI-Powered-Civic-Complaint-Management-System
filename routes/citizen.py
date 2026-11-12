import os
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.complaint import Complaint, StatusHistory
from routes import role_required

citizen_bp = Blueprint('citizen', __name__, url_prefix='/citizen')

def allowed_file(filename: str) -> bool:
    """Checks if the uploaded file has an allowed image extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})

@citizen_bp.route('/dashboard')
@role_required(User.ROLE_CITIZEN)
def dashboard():
    """Citizen dashboard displaying user details and links to actions."""
    return render_template(
        'citizen/dashboard.html',
        name=session.get('user_name'),
        role=session.get('user_role')
    )

@citizen_bp.route('/submit-complaint', methods=['GET', 'POST'])
@role_required(User.ROLE_CITIZEN)
def submit_complaint():
    """
    Citizen complaint submission with complete details:
    Title, Category, Priority, Location (3-200 chars), Description, and optional Image.
    Automatically assigns to available Municipal Officer as per SRS Feature 3 & State Diagram.
    """
    categories = Complaint.CATEGORIES
    priorities = Complaint.PRIORITIES

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        location = request.form.get('location', '').strip()
        category = request.form.get('category', '').strip()
        priority = request.form.get('priority', '').strip()

        # Validation: Required fields
        if not title or not description or not location or not category or not priority:
            flash('All fields (Title, Category, Priority, Location, Description) are required.', 'danger')
            return render_template(
                'citizen/submit_complaint.html',
                title=title,
                description=description,
                location=location,
                category=category,
                priority=priority,
                categories=categories,
                priorities=priorities
            )

        # Validation: Location length (3 to 200 characters)
        if len(location) < 3 or len(location) > 200:
            flash('Location must be between 3 and 200 characters in length.', 'danger')
            return render_template(
                'citizen/submit_complaint.html',
                title=title,
                description=description,
                location=location,
                category=category,
                priority=priority,
                categories=categories,
                priorities=priorities
            )

        # Validation: Category & Priority in allowed lists
        if category not in categories:
            flash('Please select a valid complaint category.', 'danger')
            return render_template(
                'citizen/submit_complaint.html',
                title=title,
                description=description,
                location=location,
                category=category,
                priority=priority,
                categories=categories,
                priorities=priorities
            )

        if priority not in priorities:
            flash('Please select a valid complaint priority.', 'danger')
            return render_template(
                'citizen/submit_complaint.html',
                title=title,
                description=description,
                location=location,
                category=category,
                priority=priority,
                categories=categories,
                priorities=priorities
            )

        saved_image_rel_path = None

        # Process optional supporting image
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash('Invalid file format. Allowed image formats: PNG, JPG, JPEG, GIF, WEBP.', 'danger')
                    return render_template(
                        'citizen/submit_complaint.html',
                        title=title,
                        description=description,
                        location=location,
                        category=category,
                        priority=priority,
                        categories=categories,
                        priorities=priorities
                    )

                original_safe_name = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex[:10]}_{original_safe_name}"
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                file_path = os.path.join(upload_dir, unique_filename)
                
                try:
                    file.save(file_path)
                    saved_image_rel_path = f"uploads/{unique_filename}"
                except Exception as e:
                    flash('Error saving image. Please try again.', 'danger')
                    return render_template(
                        'citizen/submit_complaint.html',
                        title=title,
                        description=description,
                        location=location,
                        category=category,
                        priority=priority,
                        categories=categories,
                        priorities=priorities
                    )

        # Auto-assignment logic (SRS Feature 3 & Sequence Diagram)
        officer = User.query.filter_by(role=User.ROLE_OFFICER).first()
        initial_status = Complaint.STATE_ASSIGNED if officer else Complaint.STATE_SUBMITTED
        officer_id = officer.id if officer else None

        # Create new complaint record
        new_complaint = Complaint(
            title=title,
            description=description,
            location=location,
            category=category,
            priority=priority,
            image_path=saved_image_rel_path,
            status=initial_status,
            user_id=session['user_id'],
            assigned_officer_id=officer_id
        )

        try:
            db.session.add(new_complaint)
            db.session.flush()

            # Entry 1: Complaint Submitted
            initial_history = StatusHistory(
                complaint_id=new_complaint.id,
                status=Complaint.STATE_SUBMITTED,
                remarks='Complaint registered with supporting details.',
                updated_by=session.get('user_name', 'Citizen')
            )
            db.session.add(initial_history)

            # Entry 2: Department Assigned (if officer present)
            if officer:
                assign_history = StatusHistory(
                    complaint_id=new_complaint.id,
                    status=Complaint.STATE_ASSIGNED,
                    remarks=f'Automatically assigned to Municipal Officer {officer.name} for departmental inspection.',
                    updated_by='AI Assignment Service'
                )
                db.session.add(assign_history)

            db.session.commit()

            flash(f'Complaint successfully submitted! Generated Complaint ID: #{new_complaint.id}', 'success')
            return redirect(url_for('citizen.track_complaints'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to submit complaint. Please try again.', 'danger')
            return render_template(
                'citizen/submit_complaint.html',
                title=title,
                description=description,
                location=location,
                category=category,
                priority=priority,
                categories=categories,
                priorities=priorities
            )

    return render_template(
        'citizen/submit_complaint.html',
        categories=categories,
        priorities=priorities
    )

@citizen_bp.route('/track-complaints')
@role_required(User.ROLE_CITIZEN)
def track_complaints():
    """
    Display and filter complaints submitted by the currently logged-in Citizen.
    Supports searching by Complaint ID, title/location keyword, and filtering by status.
    """
    user_id = session.get('user_id')
    query_str = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = Complaint.query.filter_by(user_id=user_id)

    if query_str:
        if query_str.isdigit():
            query = query.filter(Complaint.id == int(query_str))
        else:
            query = query.filter(
                db.or_(
                    Complaint.title.ilike(f'%{query_str}%'),
                    Complaint.location.ilike(f'%{query_str}%'),
                    Complaint.category.ilike(f'%{query_str}%')
                )
            )

    if status_filter:
        query = query.filter_by(status=status_filter)

    complaints = query.order_by(Complaint.created_at.desc()).all()

    statuses = [
        Complaint.STATE_SUBMITTED,
        Complaint.STATE_CATEGORIZED,
        Complaint.STATE_ASSIGNED,
        Complaint.STATE_UNDER_REVIEW,
        Complaint.STATE_IN_PROGRESS,
        Complaint.STATE_RESOLVED,
        Complaint.STATE_CLOSED
    ]

    return render_template(
        'citizen/track_complaints.html',
        complaints=complaints,
        query_str=query_str,
        status_filter=status_filter,
        statuses=statuses
    )

@citizen_bp.route('/complaint/<int:complaint_id>')
@role_required(User.ROLE_CITIZEN)
def view_complaint(complaint_id: int):
    """
    Detailed view of a specific complaint.
    Enforces server-side ownership checking and shows the chronological status history timeline.
    """
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        flash('Complaint not found.', 'danger')
        return redirect(url_for('citizen.track_complaints'))

    if complaint.user_id != session.get('user_id'):
        abort(403)

    history = StatusHistory.query.filter_by(complaint_id=complaint.id).order_by(StatusHistory.created_at.asc()).all()

    return render_template(
        'citizen/complaint_detail.html',
        complaint=complaint,
        history=history
    )
