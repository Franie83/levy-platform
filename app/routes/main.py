from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import User, Business, Vehicle, Payment
from app.decorators import check_suspended
from app.utils.qr_utils import generate_user_qr_code

bp = Blueprint('main', __name__) 

@bp.route('/') 
def index(): 
    return render_template('index.html') 

@bp.route('/dashboard') 
@login_required 
@check_suspended
def dashboard(): 
    # Common data for all users
    context = {}
    
    # Role-specific data
    if current_user.role == 'payee':
        # Generate QR code for user if not exists
        if not current_user.qr_code:
            generate_user_qr_code(current_user)
            flash('Your personal QR code has been generated! You can find it in your profile.', 'success')
        
        # Add user QR code to context
        if hasattr(current_user, 'qr_code') and current_user.qr_code:
            context['user_qr_code'] = url_for('static', filename=f'uploads/qrcodes/users/{current_user.qr_code}')
        
        if current_user.category == 'MSME':
            # MSME users see their businesses
            businesses = Business.query.filter_by(owner_id=current_user.id).all()
            context['businesses'] = businesses
            context['businesses_count'] = len(businesses)
            context['recent_payments'] = Payment.query.filter_by(
                user_id=current_user.id
            ).order_by(Payment.created_at.desc()).limit(5).all()
            
        elif current_user.category == 'Transporter':
            # Transporter users see their vehicles
            vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all()
            context['vehicles'] = vehicles
            context['vehicles_count'] = len(vehicles)
            context['recent_payments'] = Payment.query.filter_by(
                user_id=current_user.id
            ).order_by(Payment.created_at.desc()).limit(5).all()
        else:
            # Payee with no category
            context['recent_payments'] = Payment.query.filter_by(
                user_id=current_user.id
            ).order_by(Payment.created_at.desc()).limit(5).all()
    
    elif current_user.role == 'enforcer':
        # Enforcer dashboard data
        context['recent_verifications'] = Payment.query.filter_by(
            verified_by=current_user.id
        ).order_by(Payment.verification_date.desc()).limit(10).all()
        context['pending_verifications'] = Payment.query.filter_by(
            verification_status='unverified', 
            payment_status='success'
        ).count()
        context['total_verifications'] = Payment.query.filter_by(
            verified_by=current_user.id
        ).count()
    
    elif current_user.role == 'super_admin':
        # Admin dashboard stats
        context['total_users'] = User.query.count()
        context['total_businesses'] = Business.query.count()
        context['total_vehicles'] = Vehicle.query.count()
        context['total_payments'] = Payment.query.count()
        context['suspended_users'] = User.query.filter_by(status='suspended').count()
        context['recent_users'] = User.query.order_by(User.created_at.desc()).limit(5).all()
        context['recent_businesses'] = Business.query.order_by(Business.created_at.desc()).limit(5).all()
        context['recent_vehicles'] = Vehicle.query.order_by(Vehicle.created_at.desc()).limit(5).all()
        context['recent_payments'] = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', **context)

@bp.route('/profile')
@login_required
@check_suspended
def profile():
    """User profile page with QR code"""
    # Generate QR code for user if not exists
    if current_user.role == 'payee' and not current_user.qr_code:
        generate_user_qr_code(current_user)
        flash('Your personal QR code has been generated!', 'success')
    
    # Get user's businesses or vehicles
    businesses = []
    vehicles = []
    if current_user.category == 'MSME':
        businesses = Business.query.filter_by(owner_id=current_user.id).all()
    elif current_user.category == 'Transporter':
        vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all()
    
    return render_template('main/profile.html', 
                         user=current_user,
                         businesses=businesses,
                         vehicles=vehicles)

@bp.route('/my-qr-code')
@login_required
@check_suspended
def my_qr_code():
    """Display user's QR code"""
    if current_user.role != 'payee':
        flash('Only payee users have QR codes.', 'info')
        return redirect(url_for('main.dashboard'))
    
    # Generate QR code if not exists
    if not current_user.qr_code:
        generate_user_qr_code(current_user)
        flash('Your QR code has been generated!', 'success')
    
    return render_template('main/my_qr_code.html', user=current_user)

# Helper function to get QR code URL
def get_qr_code_url(user):
    """Get the QR code URL for a user"""
    if user.qr_code:
        return url_for('static', filename=f'uploads/qrcodes/users/{user.qr_code}')
    return None