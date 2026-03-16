from flask import Blueprint, render_template, redirect, url_for, flash, request 
from flask_login import login_required, current_user 
from app import db 
from app.models import User, Business, Vehicle, Payment 
 
bp = Blueprint('admin_correct', __name__, url_prefix='/admin-correct') 
 
@bp.route('/dashboard') 
@login_required 
def dashboard(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    return render_template('admin/dashboard.html') 
 
@bp.route('/users') 
@login_required 
def users(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    users = User.query.all() 
    return render_template('admin/users.html', users=users) 
 
@login_required 
def view_user(user_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    user = User.query.get_or_404(user_id) 
    return render_template('admin/view_user.html', user=user) 
 
@bp.route('/businesses') 
@login_required 
def businesses(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    businesses = Business.query.all() 
    return render_template('admin/businesses.html', businesses=businesses) 
 
@login_required 
def view_business(business_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    business = Business.query.get_or_404(business_id) 
    return render_template('admin/view_business.html', business=business) 
 
@bp.route('/vehicles') 
@login_required 
def vehicles(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    vehicles = Vehicle.query.all() 
    return render_template('admin/vehicles.html', vehicles=vehicles) 
 
@login_required 
def view_vehicle(vehicle_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    vehicle = Vehicle.query.get_or_404(vehicle_id) 
    return render_template('admin/view_vehicle.html', vehicle=vehicle) 
 
@bp.route('/payments') 
def payments(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    payments = Payment.query.all() 
    return render_template('admin/payments.html', payments=payments) 
 
@bp.route('/reports') 
@login_required 
def reports(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    return render_template('admin/reports.html') 
