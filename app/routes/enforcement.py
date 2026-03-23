from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Business, Vehicle, Payment, Violation, AuditLog
from app.decorators import check_suspended, role_required
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta
import json
import qrcode
from io import BytesIO
import base64

bp = Blueprint('enforcement', __name__, url_prefix='/enforcement')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def log_audit(action, resource_type, resource_id, details=None):
    """Helper function to log audit actions"""
    try:
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            ip_address=request.remote_addr,
            details=json.dumps(details) if details else None
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit: {e}")

def generate_qr_code(data):
    """Generate QR code image as base64 string"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

# ==================== QR CODE SCANNER API ====================
@bp.route('/api/scan-qr', methods=['POST'])
@login_required
def api_scan_qr():
    """API endpoint to scan QR code from uploaded image"""
    if current_user.role not in ['enforcer', 'super_admin']:
        return jsonify({'error': 'Access denied'}), 403
    
    if 'qr_image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['qr_image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read the image data
        image_data = file.read()
        
        # Try to decode QR code using pyzbar
        try:
            from pyzbar import pyzbar
            from PIL import Image
            import io
            import numpy as np
            
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
            decoded_objects = pyzbar.decode(img_array)
            
            if decoded_objects:
                qr_data = decoded_objects[0].data.decode('utf-8')
                return jsonify({'success': True, 'data': qr_data})
        except ImportError:
            pass
        except Exception as e:
            print(f"Pyzbar error: {e}")
        
        # Fallback: Look for receipt number patterns
        import re
        image_str = base64.b64encode(image_data).decode('utf-8')
        receipt_pattern = r'(RCP[A-Z0-9]{12}|REC[A-Z0-9]{12}|RCP[A-Z0-9]{11}|REC[A-Z0-9]{11})'
        matches = re.findall(receipt_pattern, image_str)
        
        if matches:
            receipt_number = matches[0]
            return jsonify({'success': True, 'data': receipt_number})
        
        return jsonify({'error': 'No QR code or receipt number found in the image'}), 400
        
    except Exception as e:
        print(f"QR scan error: {e}")
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

# ==================== ENFORCER DASHBOARD ====================
@bp.route('/dashboard')
@login_required
@role_required('enforcer', 'super_admin')
def dashboard():
    """Enforcer dashboard with statistics"""
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
    
    # Get active suspensions count
    active_suspensions = User.query.filter_by(status='suspended').count()
    
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
                         recent_violations=recent_violations,
                         active_suspensions=active_suspensions)

# ==================== QR CODE SCANNER PAGE ====================
@bp.route('/scanner')
@login_required
@role_required('enforcer', 'super_admin')
def scanner():
    """QR Code scanner page"""
    return render_template('enforcement/scanner.html')

# ==================== VERIFY PAYMENT PAGE ====================
@bp.route('/verify')
@login_required
@role_required('enforcer', 'super_admin')
def verify():
    """Verify payment page"""
    return render_template('enforcement/verify_payment_page.html')

# ==================== RECEIPT VERIFICATION ====================
@bp.route('/verify-receipt')
@login_required
@role_required('enforcer', 'super_admin')
def verify_receipt():
    """Verify receipt by number, user QR code, or entity QR code"""
    receipt_number = request.args.get('receipt', '').strip()
    if not receipt_number:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Receipt number is required'}), 400
        flash('Receipt number is required', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if this is an entity QR code
    if '/verify-entity/' in receipt_number:
        import re
        match = re.search(r'/verify-entity/(business|vehicle)/(\d+)', receipt_number)
        if match:
            entity_type = match.group(1)
            entity_id = match.group(2)
            return redirect(url_for('enforcement.verify_entity', entity_type=entity_type, entity_id=entity_id))
    
    # Check if this is a user QR code
    if '/verify-user/' in receipt_number:
        import re
        match = re.search(r'/verify-user/(\d+)', receipt_number)
        if match:
            user_id = match.group(1)
            return redirect(url_for('enforcement.verify_user', user_id=user_id))
    
    # Check if it's just a user ID
    if receipt_number.isdigit():
        user = User.query.get(int(receipt_number))
        if user:
            return redirect(url_for('enforcement.verify_user', user_id=user.id))
    
    # Otherwise, treat as receipt number
    payment = Payment.query.filter_by(receipt_number=receipt_number).first()
    
    if not payment:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'Receipt not found in system'}), 404
        flash('Receipt not found in system', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if payment is successful
    if payment.payment_status != 'success':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'This receipt is for a failed or pending payment'}), 400
        flash('This receipt is for a failed or pending payment', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if payment is for today
    today = datetime.now().date()
    payment_date = payment.payment_date.date() if payment.payment_date else None
    
    # Log the scan
    log_audit(
        action='RECEIPT_SCANNED',
        resource_type='payment',
        resource_id=payment.id,
        details={
            'receipt_number': receipt_number,
            'valid': payment_date == today
        }
    )
    
    if payment_date == today:
        # Valid payment for today
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'valid': True,
                'payment': {
                    'id': payment.id,
                    'receipt_number': payment.receipt_number,
                    'amount': float(payment.amount),
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'user': {
                        'id': payment.payer.id,
                        'name': payment.payer.name,
                        'nin': payment.payer.nin
                    } if payment.payer else None,
                    'business': {
                        'id': payment.business.id,
                        'name': payment.business.business_name
                    } if payment.business else None,
                    'vehicle': {
                        'id': payment.vehicle.id,
                        'plate_number': payment.vehicle.plate_number
                    } if payment.vehicle else None
                },
                'current_date': today.isoformat()
            })
        
        return render_template('enforcement/receipt_verified.html', 
                             valid=True, 
                             payment=payment,
                             current_date=today)
    else:
        # No valid payment for today - prepare to record violation
        user = payment.payer
        business = payment.business
        vehicle = payment.vehicle
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'valid': False,
                'receipt': receipt_number,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'nin': user.nin
                } if user else None,
                'business': {
                    'id': business.id,
                    'name': business.business_name
                } if business else None,
                'vehicle': {
                    'id': vehicle.id,
                    'plate_number': vehicle.plate_number
                } if vehicle else None,
                'current_date': today.isoformat()
            })
        
        return render_template('enforcement/receipt_verified.html',
                             valid=False,
                             receipt=receipt_number,
                             user=user,
                             business=business,
                             vehicle=vehicle,
                             current_date=today)

# ==================== VERIFY USER ====================
@bp.route('/verify-user/<int:user_id>')
@login_required
@role_required('enforcer', 'super_admin')
def verify_user(user_id):
    """Verify a user by scanning their personal QR code"""
    user = User.query.get_or_404(user_id)
    
    # Check if user is suspended
    if user.status == 'suspended':
        flash(f'User {user.name} is suspended. Cannot verify payments.', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Get today's date
    today = datetime.now().date()
    
    # Find today's payment
    today_payment = Payment.query.filter(
        Payment.user_id == user.id,
        Payment.payment_status == 'success',
        db.func.date(Payment.payment_date) == today
    ).first()
    
    if today_payment:
        # User has paid today - show receipt
        return render_template('enforcement/user_receipt.html',
                             valid=True,
                             payment=today_payment,
                             user=user,
                             current_date=today)
    else:
        # No payment today - prepare to record violation
        return render_template('enforcement/user_receipt.html',
                             valid=False,
                             user=user,
                             current_date=today)

# ==================== RECORD VIOLATION FROM USER ====================
@bp.route('/record-violation-from-user', methods=['POST'])
@login_required
@role_required('enforcer', 'super_admin')
def record_violation_from_user():
    """Record a violation from user QR scan and suspend the user"""
    user_id = request.form.get('user_id')
    violation_type = request.form.get('violation_type')
    description = request.form.get('description')
    gps_coordinates = request.form.get('gps_coordinates')
    
    if not user_id:
        flash('User ID is required', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if user is already suspended
    if user.status == 'suspended':
        flash('User is already suspended', 'warning')
        return redirect(url_for('enforcement.user_detail', user_id=user.id))
    
    # Create violation record
    violation = Violation(
        enforcer_id=current_user.id,
        user_id=user.id,
        violation_type=violation_type,
        description=description,
        gps_coordinates=gps_coordinates,
        status='pending'
    )
    
    db.session.add(violation)
    db.session.flush()
    
    # Automatically suspend the user
    user.status = 'suspended'
    if hasattr(user, 'suspended_at'):
        user.suspended_at = datetime.utcnow()
    if hasattr(user, 'suspended_by'):
        user.suspended_by = current_user.id
    
    # Log the action
    log_audit(
        action='VIOLATION_RECORDED_FROM_USER_QR',
        resource_type='user',
        resource_id=user.id,
        details={
            'violation_id': violation.id,
            'violation_type': violation_type,
            'description': description,
            'gps_coordinates': gps_coordinates
        }
    )
    
    db.session.commit()
    
    flash(f'Violation recorded and user {user.name} has been suspended!', 'success')
    return redirect(url_for('enforcement.violation_detail', violation_id=violation.id))

# ==================== VERIFY ENTITY ====================
@bp.route('/verify-entity/<entity_type>/<int:entity_id>')
@login_required
@role_required('enforcer', 'super_admin')
def verify_entity(entity_type, entity_id):
    """Verify a business or vehicle by scanning its QR code"""
    entity = None
    entity_name = ""
    
    if entity_type == 'business':
        entity = Business.query.get_or_404(entity_id)
        entity_name = entity.business_name
    elif entity_type == 'vehicle':
        entity = Vehicle.query.get_or_404(entity_id)
        entity_name = entity.plate_number
    else:
        flash('Invalid entity type', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if entity is active
    if entity.status != 'active':
        flash(f'{entity_type.title()} {entity_name} is not active.', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Get today's date
    today = datetime.now().date()
    
    # Find today's payment for this entity
    today_payment = None
    if entity_type == 'business':
        today_payment = Payment.query.filter(
            Payment.business_id == entity.id,
            Payment.payment_status == 'success',
            db.func.date(Payment.payment_date) == today
        ).first()
    else:
        today_payment = Payment.query.filter(
            Payment.vehicle_id == entity.id,
            Payment.payment_status == 'success',
            db.func.date(Payment.payment_date) == today
        ).first()
    
    if today_payment:
        # Entity has paid today - show receipt
        return render_template('enforcement/entity_receipt.html',
                             valid=True,
                             payment=today_payment,
                             entity=entity,
                             entity_type=entity_type,
                             current_date=today)
    else:
        # No payment today - prepare to record violation
        return render_template('enforcement/entity_receipt.html',
                             valid=False,
                             entity=entity,
                             entity_type=entity_type,
                             current_date=today)

# ==================== RECORD VIOLATION FROM ENTITY ====================
@bp.route('/record-violation-from-entity', methods=['POST'])
@login_required
@role_required('enforcer', 'super_admin')
def record_violation_from_entity():
    """Record a violation from entity QR scan and suspend the entity owner"""
    entity_type = request.form.get('entity_type')
    entity_id = request.form.get('entity_id')
    violation_type = request.form.get('violation_type')
    description = request.form.get('description')
    gps_coordinates = request.form.get('gps_coordinates')
    
    if not entity_id or not entity_type:
        flash('Entity information is required', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Get entity and its owner
    entity = None
    owner = None
    entity_name = ""
    
    if entity_type == 'business':
        entity = Business.query.get(entity_id)
        if entity:
            owner = entity.owner
            entity_name = entity.business_name
    elif entity_type == 'vehicle':
        entity = Vehicle.query.get(entity_id)
        if entity:
            owner = entity.owner
            entity_name = entity.plate_number
    
    if not entity:
        flash('Entity not found', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    if not owner:
        flash('Entity owner not found', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if owner is already suspended
    if owner.status == 'suspended':
        flash(f'User {owner.name} is already suspended', 'warning')
        return redirect(url_for('enforcement.user_detail', user_id=owner.id))
    
    # Create violation record
    violation = Violation(
        enforcer_id=current_user.id,
        user_id=owner.id,
        violation_type=violation_type,
        description=description,
        gps_coordinates=gps_coordinates,
        status='pending'
    )
    
    # Link to entity
    if entity_type == 'business':
        violation.business_id = entity.id
    else:
        violation.vehicle_id = entity.id
    
    db.session.add(violation)
    db.session.flush()
    
    # Automatically suspend the user
    owner.status = 'suspended'
    if hasattr(owner, 'suspended_at'):
        owner.suspended_at = datetime.utcnow()
    if hasattr(owner, 'suspended_by'):
        owner.suspended_by = current_user.id
    
    # Log the action
    log_audit(
        action='VIOLATION_RECORDED_FROM_ENTITY_QR',
        resource_type='user',
        resource_id=owner.id,
        details={
            'violation_id': violation.id,
            'violation_type': violation_type,
            'entity_type': entity_type,
            'entity_id': entity.id,
            'entity_name': entity_name,
            'gps_coordinates': gps_coordinates
        }
    )
    
    db.session.commit()
    
    flash(f'Violation recorded and user {owner.name} has been suspended!', 'success')
    return redirect(url_for('enforcement.violation_detail', violation_id=violation.id))

# ==================== RECORD VIOLATION (General) ====================
@bp.route('/record-violation', methods=['GET', 'POST'])
@login_required
@role_required('enforcer', 'super_admin')
def record_violation():
    """Record a new violation"""
    if request.method == 'POST':
        # Get form data
        violation_type = request.form.get('violation_type')
        description = request.form.get('description')
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        
        # Validate required fields
        if not violation_type or not description:
            flash('Violation type and description are required', 'danger')
            return redirect(url_for('enforcement.record_violation'))
        
        if not entity_id:
            flash('Please select a user, business, or vehicle', 'danger')
            return redirect(url_for('enforcement.record_violation'))
        
        # Handle evidence photo
        evidence_photo = None
        if 'evidence_photo' in request.files:
            file = request.files['evidence_photo']
            if file and file.filename and allowed_file(file.filename):
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'violations')
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(f"violation_{uuid.uuid4().hex}_{file.filename}")
                file.save(os.path.join(upload_folder, filename))
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
        entity_name = 'Unknown'
        if entity_type == 'user':
            violation.user_id = entity_id
            entity = User.query.get(entity_id)
            if entity:
                entity_name = entity.name
        elif entity_type == 'business':
            violation.business_id = entity_id
            entity = Business.query.get(entity_id)
            entity_name = entity.business_name if entity else 'Unknown'
        elif entity_type == 'vehicle':
            violation.vehicle_id = entity_id
            entity = Vehicle.query.get(entity_id)
            entity_name = entity.plate_number if entity else 'Unknown'
        
        db.session.add(violation)
        db.session.commit()
        
        # Log the action
        log_audit(
            action='VIOLATION_RECORDED',
            resource_type='violation',
            resource_id=str(violation.id),
            details={'entity': entity_name, 'violation_type': violation_type}
        )
        
        flash('Violation recorded successfully!', 'success')
        return redirect(url_for('enforcement.violation_detail', violation_id=violation.id))
    
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

# ==================== VIOLATIONS LIST ====================
@bp.route('/violations')
@login_required
@role_required('enforcer', 'super_admin')
def violations():
    """List all violations"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    if current_user.role == 'super_admin':
        violations_pagination = Violation.query.order_by(
            Violation.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        violations_list = violations_pagination.items
        total_pages = violations_pagination.pages
    else:
        violations_pagination = Violation.query.filter_by(
            enforcer_id=current_user.id
        ).order_by(Violation.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        violations_list = violations_pagination.items
        total_pages = violations_pagination.pages
    
    return render_template('enforcement/violations.html', 
                         violations=violations_list,
                         page=page,
                         total_pages=total_pages)

# ==================== VIOLATION DETAIL ====================
@bp.route('/violation/<int:violation_id>')
@login_required
@role_required('enforcer', 'super_admin')
def violation_detail(violation_id):
    """View violation details"""
    violation = Violation.query.get_or_404(violation_id)
    
    # Check permission
    if current_user.role != 'super_admin' and violation.enforcer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('enforcement.violations'))
    
    return render_template('enforcement/violation_detail.html', violation=violation)

# ==================== UPDATE VIOLATION STATUS ====================
@bp.route('/violation/<int:violation_id>/update-status', methods=['POST'])
@login_required
@role_required('enforcer', 'super_admin')
def update_violation_status(violation_id):
    """Update violation status"""
    violation = Violation.query.get_or_404(violation_id)
    
    # Check permission
    if current_user.role != 'super_admin' and violation.enforcer_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('enforcement.violations'))
    
    new_status = request.form.get('status')
    resolution_notes = request.form.get('resolution_notes')
    
    if new_status in ['pending', 'resolved', 'rejected']:
        old_status = violation.status
        violation.status = new_status
        
        if resolution_notes:
            violation.resolution_notes = resolution_notes
        
        if new_status == 'resolved':
            violation.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log the action
        log_audit(
            action='VIOLATION_STATUS_UPDATED',
            resource_type='violation',
            resource_id=violation.id,
            details={
                'old_status': old_status,
                'new_status': new_status,
                'notes': resolution_notes
            }
        )
        
        flash(f'Violation #{violation.id} status updated to {new_status}', 'success')
    
    return redirect(url_for('enforcement.violation_detail', violation_id=violation.id))

# ==================== SUSPENDED USERS ====================
@bp.route('/suspended-users')
@login_required
@role_required('enforcer', 'super_admin')
def suspended_users():
    """View all suspended users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Check if suspended_at exists in User model
    if hasattr(User, 'suspended_at'):
        suspended_pagination = User.query.filter_by(status='suspended').order_by(
            User.suspended_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    else:
        suspended_pagination = User.query.filter_by(status='suspended').order_by(
            User.id.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('enforcement/suspended_users.html',
                         users=suspended_pagination.items,
                         page=page,
                         total_pages=suspended_pagination.pages)

# ==================== USER DETAIL ====================
@bp.route('/user/<int:user_id>')
@login_required
@role_required('enforcer', 'super_admin')
def user_detail(user_id):
    """View user details including violation history"""
    user = User.query.get_or_404(user_id)
    violations_list = Violation.query.filter_by(user_id=user.id).order_by(Violation.created_at.desc()).all()
    payments = Payment.query.filter_by(user_id=user.id, payment_status='success').order_by(Payment.payment_date.desc()).limit(10).all()
    
    return render_template('enforcement/user_detail.html', 
                         user=user, 
                         violations=violations_list,
                         payments=payments)

# ==================== UNSUSPEND USER ====================
@bp.route('/unsuspend-user/<int:user_id>', methods=['POST'])
@login_required
@role_required('enforcer', 'super_admin')
def unsuspend_user(user_id):
    """Unsuspend a user"""
    user = User.query.get_or_404(user_id)
    
    if user.status != 'suspended':
        flash('User is not suspended', 'warning')
        return redirect(url_for('enforcement.suspended_users'))
    
    # Unsuspend the user
    user.status = 'active'
    
    # Only set these attributes if they exist
    if hasattr(user, 'unsuspended_at'):
        user.unsuspended_at = datetime.utcnow()
    if hasattr(user, 'unsuspended_by'):
        user.unsuspended_by = current_user.id
    
    # Log the action
    log_audit(
        action='USER_UNSUSPENDED',
        resource_type='user',
        resource_id=user.id,
        details={'reason': request.form.get('reason', 'No reason provided')}
    )
    
    db.session.commit()
    
    flash(f'User {user.name} has been unsuspended successfully!', 'success')
    return redirect(url_for('enforcement.suspended_users'))

# ==================== RECORD VIOLATION FROM SCAN ====================
@bp.route('/record-violation-from-scan', methods=['POST'])
@login_required
@role_required('enforcer', 'super_admin')
def record_violation_from_scan():
    """Record a violation from QR scan and suspend the user"""
    user_id = request.form.get('user_id')
    violation_type = request.form.get('violation_type')
    description = request.form.get('description')
    gps_coordinates = request.form.get('gps_coordinates')
    receipt_number = request.form.get('receipt_number')
    
    # Validation
    if not user_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'User ID is required'}), 400
        flash('User ID is required', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    user = User.query.get(user_id)
    if not user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'User not found'}), 404
        flash('User not found', 'danger')
        return redirect(url_for('enforcement.scanner'))
    
    # Check if user is already suspended
    if user.status == 'suspended':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'User is already suspended'}), 400
        flash('User is already suspended', 'warning')
        return redirect(url_for('enforcement.user_detail', user_id=user.id))
    
    # Create violation record
    violation = Violation(
        enforcer_id=current_user.id,
        user_id=user.id,
        violation_type=violation_type,
        description=description,
        gps_coordinates=gps_coordinates,
        status='pending'
    )
    
    # Link to business or vehicle if applicable
    payment = Payment.query.filter_by(receipt_number=receipt_number).first()
    if payment:
        if payment.business:
            violation.business_id = payment.business.id
        if payment.vehicle:
            violation.vehicle_id = payment.vehicle.id
        violation.payment_id = payment.id
    
    db.session.add(violation)
    db.session.flush()
    
    # Automatically suspend the user
    user.status = 'suspended'
    if hasattr(user, 'suspended_at'):
        user.suspended_at = datetime.utcnow()
    if hasattr(user, 'suspended_by'):
        user.suspended_by = current_user.id
    
    # Log the action
    log_audit(
        action='VIOLATION_RECORDED_WITH_SUSPENSION',
        resource_type='user',
        resource_id=user.id,
        details={
            'violation_id': violation.id,
            'violation_type': violation_type,
            'receipt_number': receipt_number,
            'gps_coordinates': gps_coordinates
        }
    )
    
    db.session.commit()
    
    success_message = f'Violation recorded and user {user.name} has been suspended!'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'message': success_message,
            'violation_id': violation.id,
            'user_id': user.id,
            'user_name': user.name
        })
    
    flash(success_message, 'success')
    return redirect(url_for('enforcement.violation_detail', violation_id=violation.id))