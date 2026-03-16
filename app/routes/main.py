from flask import Blueprint, render_template 
from flask_login import login_required, current_user 
from app.models import User, Business, Vehicle, Payment

bp = Blueprint('main', __name__) 
 
@bp.route('/') 
def index(): 
    return render_template('index.html') 
 
@bp.route('/dashboard') 
@login_required 
def dashboard(): 
    # Common data for all users
    context = {}
    
    # Role-specific data
    if current_user.role == 'payee':
        if current_user.category == 'MSME':
            # MSME users see their businesses
            businesses = Business.query.filter_by(owner_id=current_user.id).all()
            context['businesses'] = businesses
            context['businesses_count'] = len(businesses)
            context['recent_payments'] = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(5).all()
            
        elif current_user.category == 'Transporter':
            # Transporter users see their vehicles
            vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all()
            context['vehicles'] = vehicles
            context['vehicles_count'] = len(vehicles)
            context['recent_payments'] = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(5).all()
        else:
            # Payee with no category
            context['recent_payments'] = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc()).limit(5).all()
    
    elif current_user.role == 'enforcer':
        # Enforcer dashboard data
        context['recent_verifications'] = Payment.query.filter_by(verified_by=current_user.id).order_by(Payment.verification_date.desc()).limit(10).all()
        context['pending_verifications'] = Payment.query.filter_by(verification_status='unverified', payment_status='success').count()
        context['total_verifications'] = Payment.query.filter_by(verified_by=current_user.id).count()
    
    elif current_user.role == 'super_admin':
        # Admin dashboard stats
        context['total_users'] = User.query.count()
        context['total_businesses'] = Business.query.count()
        context['total_vehicles'] = Vehicle.query.count()
        context['total_payments'] = Payment.query.count()
        context['recent_users'] = User.query.order_by(User.created_at.desc()).limit(5).all()
        context['recent_businesses'] = Business.query.order_by(Business.created_at.desc()).limit(5).all()
        context['recent_vehicles'] = Vehicle.query.order_by(Vehicle.created_at.desc()).limit(5).all()
        context['recent_payments'] = Payment.query.order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', **context)