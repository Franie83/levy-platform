from flask import Blueprint, render_template, redirect, url_for, flash, request 
from flask_login import login_required, current_user 
from app import db 
from app.models import User, Business, Vehicle, Payment 
 
bp = Blueprint('admin_working', __name__, url_prefix='/admin-working') 
 
# ==================== DASHBOARD ==================== 
@bp.route('/dashboard') 
@login_required 
def dashboard(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    return render_template('admin/dashboard.html') 
 
# ==================== USER MANAGEMENT ==================== 
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
    businesses = Business.query.filter_by(owner_id=user.id).all() 
    vehicles = Vehicle.query.filter_by(owner_id=user.id).all() 
    return render_template('admin/view_user.html', user=user, businesses=businesses, vehicles=vehicles) 
 
@login_required 
def edit_user(user_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    user = User.query.get_or_404(user_id) 
    if request.method == 'POST': 
        user.name = request.form.get('name') 
        user.email = request.form.get('email') 
        user.phone = request.form.get('phone') 
        user.role = request.form.get('role') 
        user.category = request.form.get('category') if request.form.get('role') == 'payee' else None 
        user.status = request.form.get('status') 
        db.session.commit() 
        flash(f'User {user.name} updated successfully!', 'success') 
        return redirect(url_for('admin_working.view_user', user_id=user.id)) 
    return render_template('admin/edit_user.html', user=user) 
 
@login_required 
def toggle_user_status(user_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    user = User.query.get_or_404(user_id) 
    user.status = 'suspended' if user.status == 'active' else 'active' 
    db.session.commit() 
    flash(f'User {user.name} {user.status} successfully!', 'success') 
    return redirect(url_for('admin_working.view_user', user_id=user.id)) 
 
# ==================== BUSINESS MANAGEMENT ==================== 
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
 
@login_required 
def toggle_business_status(business_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    business = Business.query.get_or_404(business_id) 
    business.status = 'suspended' if business.status == 'active' else 'active' 
    db.session.commit() 
    flash(f'Business {business.business_name} {business.status} successfully!', 'success') 
    return redirect(url_for('admin_working.view_business', business_id=business.id)) 
 
# ==================== VEHICLE MANAGEMENT ==================== 
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
 
@login_required 
def toggle_vehicle_status(vehicle_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    vehicle = Vehicle.query.get_or_404(vehicle_id) 
    vehicle.status = 'suspended' if vehicle.status == 'active' else 'active' 
    db.session.commit() 
    flash(f'Vehicle {vehicle.plate_number} {vehicle.status} successfully!', 'success') 
    return redirect(url_for('admin_working.view_vehicle', vehicle_id=vehicle.id)) 
 
# ==================== PAYMENT MANAGEMENT ==================== 
@bp.route('/payments') 
@login_required 
def payments(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    payments = Payment.query.all() 
    return render_template('admin/payments.html', payments=payments) 
 
# ==================== REPORTS ==================== 
@bp.route('/reports') 
@login_required 
def reports(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    return render_template('admin/reports.html') 
