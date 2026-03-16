from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Business, Vehicle, Payment, Violation, AuditLog
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta

bp = Blueprint('enforcement', __name__, url_prefix='/enforcement')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

# ==================== ENFORCER DASHBOARD ====================
@bp.route('/dashboard')
@login_required
def dashboard():
    """Enforcer dashboard with statistics"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    # Get today's date range
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    # Statistics
    verifications_today = Payment.query.filter(
        Payment.verified_by == current_user.id,
        Payment.verification_date >= today,
        Payment.verification_date < tomorrow
    ).count()
    
    violations_today = Violation.query.filter_by(
        enforcer_id=current_user.id
    ).filter(
        Violation.created_at >= today,
        Violation.created_at < tomorrow
    ).count()
    
    total_violations = Violation.query.filter_by(
        enforcer_id=current_user.id
    ).count()
    
    pending_payments = Payment.query.filter_by(
        verification_status='unverified',
        payment_status='success'
    ).count()
    
    # Recent activities
    recent_verifications = Payment.query.filter_by(
        verified_by=current_user.id
    ).order_by(Payment.verification_date.desc()).limit(10).all()
    
    recent_violations = Violation.query.filter_by(
        enforcer_id=current_user.id
    ).order_by(Violation.created_at.desc()).limit(10).all()
    
    return render_template('enforcement/dashboard.html',
                         verifications_today=verifications_today,
                         violations_today=violations_today,
                         total_violations=total_violations,
                         pending_payments=pending_payments,
                         recent_verifications=recent_verifications,
                         recent_violations=recent_violations)

# ==================== PAYMENT VERIFICATION ====================
@bp.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    """Verify payments by receipt, plate, NIN, or business name"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        search_type = request.form.get('search_type')
        search_value = request.form.get('search_value')
        
        # Search by receipt number
        if search_type == 'receipt':
            payment = Payment.query.filter_by(receipt_number=search_value).first()
            if payment:
                return redirect(url_for('enforcement.verify_payment', payment_id=payment.id))
            else:
                flash('Receipt not found', 'danger')
        
        # Search by plate number
        elif search_type == 'plate':
            vehicle = Vehicle.query.filter_by(plate_number=search_value.upper()).first()
            if vehicle:
                payments = Payment.query.filter_by(
                    vehicle_id=vehicle.id,
                    payment_status='success'
                ).order_by(Payment.payment_date.desc()).all()
                return render_template('enforcement/vehicle_payments.html',
                                     vehicle=vehicle,
                                     payments=payments)
            else:
                flash('Vehicle not found', 'danger')
        
        # Search by NIN
        elif search_type == 'nin':
            user = User.query.filter_by(nin=search_value).first()
            if user:
                payments = Payment.query.filter_by(
                    user_id=user.id,
                    payment_status='success'
                ).order_by(Payment.payment_date.desc()).all()
                return render_template('enforcement/user_payments.html',
                                     user=user,
                                     payments=payments)
            else:
                flash('User not found', 'danger')
        
        # Search by business name
        elif search_type == 'business':
            businesses = Business.query.filter(
                Business.business_name.contains(search_value)
            ).all()
            if businesses:
                return render_template('enforcement/business_list.html',
                                     businesses=businesses,
                                     search_term=search_value)
            else:
                flash('No businesses found', 'danger')
    
    return render_template('enforcement/verify.html')

@bp.route('/verify-payment/<int:payment_id>')
@login_required
def verify_payment(payment_id):
    """View and verify a specific payment"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    payment = Payment.query.get_or_404(payment_id)
    
    # Mark as verified if not already
    if not payment.verified_by and payment.payment_status == 'success':
        payment.verified_by = current_user.id
        payment.verification_status = 'verified'
        payment.verification_date = datetime.utcnow()
        
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='PAYMENT_VERIFIED',
            resource_type='payment',
            resource_id=payment.payment_reference,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Payment verified successfully!', 'success')
    
    return render_template('enforcement/payment_detail.html', payment=payment)

# ==================== VIOLATION MANAGEMENT ====================
@bp.route('/violations')
@login_required
def violations():
    """List all violations"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if current_user.role == 'super_admin':
        violations = Violation.query.order_by(Violation.created_at.desc()).all()
    else:
        violations = Violation.query.filter_by(
            enforcer_id=current_user.id
        ).order_by(Violation.created_at.desc()).all()
    
    return render_template('enforcement/violations.html', violations=violations)

@bp.route('/violation/<int:violation_id>')
@login_required
def view_violation(violation_id):
    """View violation details"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    violation = Violation.query.get_or_404(violation_id)
    
    # Check permission
    if current_user.role != 'super_admin' and violation.enforcer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('enforcement.violations'))
    
    return render_template('enforcement/violation_detail.html', violation=violation)

@bp.route('/record-violation', methods=['GET', 'POST'])
@login_required
def record_violation():
    """Record a new violation"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Get form data
        violation_type = request.form.get('violation_type')
        description = request.form.get('description')
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        
        # Handle evidence photo
        evidence_photo = None
        if 'evidence_photo' in request.files:
            file = request.files['evidence_photo']
            if file and file.filename and allowed_file(file.filename):
                # Create violations directory if it doesn't exist
                os.makedirs(os.path.join(current_app.config['UPLOAD_FOLDER'], 'violations'), exist_ok=True)
                
                filename = secure_filename(f"violation_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], 'violations', filename))
                evidence_photo = filename
        
        # Get GPS coordinates if provided
        gps_coordinates = request.form.get('gps_coordinates')
        
        # Create violation record
        violation = Violation(
            enforcer_id=current_user.id,
            violation_type=violation_type,
            description=description,
            evidence_photo=evidence_photo,
            gps_coordinates=gps_coordinates,
            status='pending'
        )
        
        # Link to entity
        if entity_type == 'user':
            violation.user_id = entity_id
            entity = User.query.get(entity_id)
            entity_name = entity.name if entity else 'Unknown'
        elif entity_type == 'business':
            violation.business_id = entity_id
            entity = Business.query.get(entity_id)
            entity_name = entity.business_name if entity else 'Unknown'
        elif entity_type == 'vehicle':
            violation.vehicle_id = entity_id
            entity = Vehicle.query.get(entity_id)
            entity_name = entity.plate_number if entity else 'Unknown'
        else:
            entity_name = 'Unknown'
        
        db.session.add(violation)
        db.session.commit()
        
        # Log the action
        log = AuditLog(
            user_id=current_user.id,
            action='VIOLATION_RECORDED',
            resource_type='violation',
            resource_id=str(violation.id),
            ip_address=request.remote_addr,
            device=f"Entity: {entity_name}"
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Violation recorded successfully!', 'success')
        return redirect(url_for('enforcement.view_violation', violation_id=violation.id))
    
    # GET request - get parameters for pre-filling
    user_id = request.args.get('user_id')
    business_id = request.args.get('business_id')
    vehicle_id = request.args.get('vehicle_id')
    
    user = User.query.get(user_id) if user_id else None
    business = Business.query.get(business_id) if business_id else None
    vehicle = Vehicle.query.get(vehicle_id) if vehicle_id else None
    
    return render_template('enforcement/record_violation.html',
                         user=user,
                         business=business,
                         vehicle=vehicle)

@bp.route('/violation/<int:violation_id>/update-status', methods=['POST'])
@login_required
def update_violation_status(violation_id):
    """Update violation status (resolve/reject)"""
    if current_user.role not in ['enforcer', 'super_admin']:
        flash('Access denied. Enforcer only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    violation = Violation.query.get_or_404(violation_id)
    
    # Check permission
    if current_user.role != 'super_admin' and violation.enforcer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('enforcement.violations'))
    
    new_status = request.form.get('status')
    if new_status in ['pending', 'resolved', 'rejected']:
        violation.status = new_status
        db.session.commit()
        
        flash(f'Violation status updated to {new_status}', 'success')
    
    return redirect(url_for('enforcement.view_violation', violation_id=violation.id))

# ==================== API ENDPOINTS FOR QUICK SEARCH ====================
@bp.route('/api/search')
@login_required
def api_search():
    """API endpoint for quick search (AJAX)"""
    if current_user.role not in ['enforcer', 'super_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'all')
    
    results = {'users': [], 'businesses': [], 'vehicles': [], 'payments': []}
    
    if len(query) < 2:
        return jsonify(results)
    
    # Search users
    if search_type in ['all', 'users']:
        users = User.query.filter(
            (User.nin.contains(query)) |
            (User.name.contains(query)) |
            (User.phone.contains(query))
        ).limit(5).all()
        
        results['users'] = [{
            'id': u.id,
            'name': u.name,
            'nin': u.nin,
            'category': u.category
        } for u in users]
    
    # Search businesses
    if search_type in ['all', 'businesses']:
        businesses = Business.query.filter(
            (Business.business_name.contains(query)) |
            (Business.registration_number.contains(query))
        ).limit(5).all()
        
        results['businesses'] = [{
            'id': b.id,
            'business_id': b.business_id,
            'business_name': b.business_name,
            'owner_name': b.owner.name
        } for b in businesses]
    
    # Search vehicles
    if search_type in ['all', 'vehicles']:
        vehicles = Vehicle.query.filter(
            (Vehicle.plate_number.contains(query.upper())) |
            (Vehicle.vin.contains(query))
        ).limit(5).all()
        
        results['vehicles'] = [{
            'id': v.id,
            'vehicle_id': v.vehicle_id,
            'plate_number': v.plate_number,
            'owner_name': v.owner.name
        } for v in vehicles]
    
    # Search payments
    if search_type in ['all', 'payments']:
        payments = Payment.query.filter(
            (Payment.receipt_number.contains(query)) |
            (Payment.payment_reference.contains(query))
        ).limit(5).all()
        
        results['payments'] = [{
            'id': p.id,
            'receipt_number': p.receipt_number,
            'amount': p.amount,
            'status': p.payment_status,
            'verification': p.verification_status
        } for p in payments]
    
    return jsonify(results)