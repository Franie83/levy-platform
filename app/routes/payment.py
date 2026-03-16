# app/routes/payment.py (updated with simulation)

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Payment, Business, Vehicle, User, Receipt, AuditLog, LevyType
from app.services.payment_service import PaymentService
import qrcode
import uuid
import os
from datetime import datetime

bp = Blueprint('payment', __name__, url_prefix='/payment')
payment_service = PaymentService(simulation_mode=True)  # Use simulation mode

@bp.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():
    """Initialize a payment"""
    is_admin = current_user.role == 'super_admin'
    
    if not is_admin and current_user.role not in ['payee']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        entity_type = request.form.get('entity_type')
        entity_id = request.form.get('entity_id')
        levy_type_name = request.form.get('levy_type')
        custom_amount = request.form.get('custom_amount', type=float)
        
        # Determine the user who will own this payment
        if is_admin and request.form.get('user_id'):
            paying_user = User.query.get(request.form.get('user_id'))
            if not paying_user:
                flash('Selected user not found', 'danger')
                return redirect(url_for('payment.pay'))
        else:
            paying_user = current_user
        
        # Determine the amount
        amount = 0
        
        if levy_type_name and levy_type_name.strip():
            # Use levy type amount if selected
            levy = LevyType.query.filter_by(name=levy_type_name, is_active=True).first()
            if not levy:
                flash('Invalid levy type selected', 'danger')
                return redirect(url_for('payment.pay'))
            amount = levy.amount
            levy_display = levy_type_name
        elif custom_amount and custom_amount > 0:
            # Use custom amount if provided
            amount = custom_amount
            levy_display = 'Custom Amount'
        else:
            # Use entity type amount
            if entity_type == 'business':
                business = Business.query.get(entity_id)
                if business and business.business_type_ref:
                    amount = business.business_type_ref.amount
                    levy_display = f"{business.business_type_ref.name} (Default)"
                else:
                    flash('Could not determine amount for this business', 'danger')
                    return redirect(url_for('payment.pay'))
            elif entity_type == 'vehicle':
                vehicle = Vehicle.query.get(entity_id)
                if vehicle and vehicle.vehicle_type_ref:
                    amount = vehicle.vehicle_type_ref.amount
                    levy_display = f"{vehicle.vehicle_type_ref.name} (Default)"
                else:
                    flash('Could not determine amount for this vehicle', 'danger')
                    return redirect(url_for('payment.pay'))
            else:
                flash('Invalid entity type', 'danger')
                return redirect(url_for('payment.pay'))
        
        if amount <= 0:
            flash('Invalid amount', 'danger')
            return redirect(url_for('payment.pay'))
        
        # Generate unique references
        payment_reference = f"PAY{uuid.uuid4().hex[:12].upper()}"
        receipt_number = f"RCP{uuid.uuid4().hex[:12].upper()}"
        
        # Create payment record
        payment = Payment(
            payment_reference=payment_reference,
            receipt_number=receipt_number,
            user_id=paying_user.id,
            levy_type=levy_display,
            amount=amount,
            payment_status='pending',
            verification_status='unverified',
            initiated_by=current_user.id if is_admin and paying_user.id != current_user.id else None
        )
        
        # Link to business or vehicle
        entity_name = 'Unknown'
        if entity_type == 'business':
            payment.business_id = entity_id
            entity = Business.query.get(entity_id)
            entity_name = entity.business_name if entity else 'Unknown'
        elif entity_type == 'vehicle':
            payment.vehicle_id = entity_id
            entity = Vehicle.query.get(entity_id)
            entity_name = entity.plate_number if entity else 'Unknown'
        
        db.session.add(payment)
        db.session.commit()
        
        # Log the action
        action = 'PAYMENT_INITIATED'
        if is_admin and paying_user.id != current_user.id:
            action = 'ADMIN_PAYMENT_FOR_USER'
            
        log = AuditLog(
            user_id=current_user.id,
            action=action,
            resource_type='payment',
            resource_id=payment_reference,
            ip_address=request.remote_addr,
            device=f"User: {paying_user.name}" if is_admin and paying_user.id != current_user.id else None
        )
        db.session.add(log)
        db.session.commit()
        
        # Initialize payment with service
        metadata = {
            'payment_id': payment.id,
            'user_id': paying_user.id,
            'user_name': paying_user.name,
            'entity_type': entity_type,
            'entity_name': entity_name,
            'initiated_by': current_user.name if is_admin and paying_user.id != current_user.id else None
        }
        
        response = payment_service.initialize_payment(
            email=paying_user.email,
            amount=amount,
            reference=payment_reference,
            metadata=metadata
        )
        
        if response and response['status']:
            if payment_service.simulation_mode:
                # Redirect to simulation page
                return redirect(url_for('payment.simulate', reference=payment_reference))
            else:
                # Redirect to Paystack
                return redirect(response['data']['authorization_url'])
        else:
            flash('Payment initialization failed. Please try again.', 'danger')
            return redirect(url_for('payment.pay'))
    
    # GET request - show payment form
    if is_admin:
        # Admin sees all businesses and vehicles, plus user selection
        businesses = Business.query.filter_by(status='active').all()
        vehicles = Vehicle.query.filter_by(status='active').all()
        users = User.query.filter_by(role='payee').all()
    else:
        # Regular users see only their own
        businesses = Business.query.filter_by(owner_id=current_user.id, status='active').all()
        vehicles = Vehicle.query.filter_by(owner_id=current_user.id, status='active').all()
        users = []
    
    levy_types = LevyType.query.filter_by(is_active=True).all()
    
    return render_template('payment/pay.html', 
                         businesses=businesses, 
                         vehicles=vehicles,
                         users=users,
                         levy_types=levy_types,
                         is_admin=is_admin)

@bp.route('/simulate/<reference>')
@login_required
def simulate(reference):
    """Show simulation page for a payment"""
    payment = Payment.query.filter_by(payment_reference=reference).first_or_404()
    
    # Check ownership
    if payment.user_id != current_user.id and current_user.role != 'super_admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('payment/simulate.html', payment=payment)

@bp.route('/simulate/success/<reference>')
@login_required
def simulate_success(reference):
    """Simulate a successful payment"""
    payment = Payment.query.filter_by(payment_reference=reference).first_or_404()
    
    # Update payment record
    payment.payment_status = 'success'
    payment.verification_status = 'verified'
    payment.payment_date = datetime.now()
    payment.transaction_id = f"SIM_{uuid.uuid4().hex[:12].upper()}"
    
    # Generate receipt
    generate_receipt(payment)
    
    db.session.commit()
    
    # Log the action
    log = AuditLog(
        user_id=current_user.id,
        action='PAYMENT_SIMULATED_SUCCESS',
        resource_type='payment',
        resource_id=payment.payment_reference,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Payment successful! (SIMULATED)', 'success')
    return redirect(url_for('payment.receipt', payment_reference=payment.payment_reference))

@bp.route('/simulate/failure/<reference>')
@login_required
def simulate_failure(reference):
    """Simulate a failed payment"""
    payment = Payment.query.filter_by(payment_reference=reference).first_or_404()
    
    # Update payment record
    payment.payment_status = 'failed'
    payment.verification_status = 'unverified'
    
    db.session.commit()
    
    # Log the action
    log = AuditLog(
        user_id=current_user.id,
        action='PAYMENT_SIMULATED_FAILURE',
        resource_type='payment',
        resource_id=payment.payment_reference,
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Payment failed! (SIMULATED)', 'danger')
    return redirect(url_for('payment.history'))

@bp.route('/cancel')
@login_required
def cancel():
    """Cancel payment and return to dashboard"""
    flash('Payment cancelled.', 'info')
    return redirect(url_for('main.dashboard'))

@bp.route('/history')
@login_required
def history():
    """View payment history"""
    if current_user.role == 'super_admin':
        payments = Payment.query.order_by(Payment.created_at.desc()).all()
    elif current_user.role == 'payee':
        payments = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).all()
    else:
        payments = Payment.query.filter_by(verification_status='verified').order_by(Payment.created_at.desc()).all()
    
    return render_template('payment/history.html', payments=payments)

@bp.route('/verify/<receipt_number>')
@login_required
def verify(receipt_number):
    """Verify a payment by receipt number (for enforcers)"""
    payment = Payment.query.filter_by(receipt_number=receipt_number).first()
    
    if not payment:
        flash('Invalid receipt number', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('payment/verify.html', payment=payment)

@bp.route('/receipt/<payment_reference>')
@login_required
def receipt(payment_reference):
    """View payment receipt"""
    payment = Payment.query.filter_by(payment_reference=payment_reference).first_or_404()
    
    # Check permissions
    if current_user.role not in ['super_admin', 'enforcer'] and payment.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('payment.history'))
    
    return render_template('payment/receipt.html', payment=payment)

def generate_receipt(payment):
    """Generate a receipt for a successful payment"""
    from flask import url_for, current_app
    import qrcode
    import os
    
    # Create receipt record if not exists
    receipt = Receipt.query.filter_by(payment_id=payment.id).first()
    if not receipt:
        receipt = Receipt(
            payment_id=payment.id,
            receipt_number=payment.receipt_number
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"{url_for('payment.verify', receipt_number=payment.receipt_number, _external=True)}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code - use current_app instead of app
        qr_filename = f"qr_{payment.receipt_number}.png"
        qr_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'qrcodes', qr_filename)
        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        img.save(qr_path)
        
        receipt.qr_code = qr_filename
        
        db.session.add(receipt)
        db.session.commit()
    
    return receipt