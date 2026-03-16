from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user 
from app import db 
from app.models import User, Business, Vehicle, Payment, AuditLog, VehicleType, BusinessType, IndustrySector
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

bp = Blueprint('admin', __name__, url_prefix='/admin') 
 
# ==================== DASHBOARD ==================== 
@bp.route('/dashboard') 
@login_required 
def dashboard(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    return render_template('admin/dashboard.html') 
 
# ==================== USER MANAGEMENT WITH SEARCH ==================== 
@bp.route('/users') 
@login_required 
def users(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    
    # Get search parameters
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    category = request.args.get('category', '')
    status = request.args.get('status', '')
    date_range = request.args.get('date_range', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start query
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                User.name.contains(search),
                User.email.contains(search),
                User.nin.contains(search),
                User.phone.contains(search)
            )
        )
    
    if role:
        query = query.filter(User.role == role)
    
    if category:
        query = query.filter(User.category == category)
    
    if status:
        query = query.filter(User.status == status)
    
    # Date filtering
    if date_range == 'today':
        today = datetime.now().date()
        query = query.filter(db.func.date(User.created_at) == today)
    elif date_range == 'this_week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(User.created_at >= week_ago)
    elif date_range == 'this_month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(User.created_at >= month_ago)
    elif date_range == 'this_year':
        year_ago = datetime.now() - timedelta(days=365)
        query = query.filter(User.created_at >= year_ago)
    elif date_range == 'custom' and date_from and date_to:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(User.created_at.between(from_date, to_date))
    
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users) 

@bp.route('/user/<int:user_id>')
@login_required 
def view_user(user_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    user = User.query.get_or_404(user_id) 
    businesses = Business.query.filter_by(owner_id=user.id).all() 
    vehicles = Vehicle.query.filter_by(owner_id=user.id).all() 
    return render_template('admin/view_user.html', user=user, businesses=businesses, vehicles=vehicles) 

@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
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
        return redirect(url_for('admin.view_user', user_id=user.id)) 
    return render_template('admin/edit_user.html', user=user) 

@bp.route('/user/<int:user_id>/toggle', methods=['POST'])
@login_required 
def toggle_user_status(user_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    user = User.query.get_or_404(user_id) 
    user.status = 'suspended' if user.status == 'active' else 'active' 
    db.session.commit() 
    flash(f'User {user.name} {user.status} successfully!', 'success') 
    return redirect(url_for('admin.view_user', user_id=user.id)) 

@bp.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required 
def delete_user(user_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    user = User.query.get_or_404(user_id) 
    if user.id == current_user.id: 
        flash('You cannot delete your own account!', 'danger') 
        return redirect(url_for('admin.users')) 
    db.session.delete(user) 
    db.session.commit() 
    flash('User deleted successfully!', 'success') 
    return redirect(url_for('admin.users')) 
 
# ==================== BUSINESS MANAGEMENT WITH SEARCH ==================== 
@bp.route('/businesses') 
@login_required 
def businesses(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    
    # Get search parameters
    search = request.args.get('search', '')
    owner = request.args.get('owner', '')
    business_type = request.args.get('business_type', '')
    status = request.args.get('status', '')
    date_range = request.args.get('date_range', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start query
    query = Business.query.join(User, Business.owner_id == User.id).outerjoin(BusinessType)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Business.business_name.contains(search),
                Business.business_id.contains(search),
                Business.registration_number.contains(search)
            )
        )
    
    if owner:
        query = query.filter(User.name.contains(owner))
    
    if business_type:
        query = query.filter(BusinessType.name.contains(business_type))
    
    if status:
        query = query.filter(Business.status == status)
    
    # Date filtering
    if date_range == 'today':
        today = datetime.now().date()
        query = query.filter(db.func.date(Business.created_at) == today)
    elif date_range == 'this_week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(Business.created_at >= week_ago)
    elif date_range == 'this_month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(Business.created_at >= month_ago)
    elif date_range == 'this_year':
        year_ago = datetime.now() - timedelta(days=365)
        query = query.filter(Business.created_at >= year_ago)
    elif date_range == 'custom' and date_from and date_to:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Business.created_at.between(from_date, to_date))
    
    businesses = query.order_by(Business.created_at.desc()).all()
    
    return render_template('admin/businesses.html', businesses=businesses) 

@bp.route('/business/<int:business_id>')
@login_required 
def view_business(business_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    business = Business.query.get_or_404(business_id) 
    return render_template('admin/view_business.html', business=business) 

@bp.route('/business/<int:business_id>/toggle', methods=['POST'])
@login_required 
def toggle_business_status(business_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    business = Business.query.get_or_404(business_id) 
    business.status = 'suspended' if business.status == 'active' else 'active' 
    db.session.commit() 
    flash(f'Business {business.business_name} {business.status} successfully!', 'success') 
    return redirect(url_for('admin.view_business', business_id=business.id)) 

@bp.route('/business/<int:business_id>/delete', methods=['POST'])
@login_required 
def delete_business(business_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    business = Business.query.get_or_404(business_id) 
    db.session.delete(business) 
    db.session.commit() 
    flash('Business deleted successfully!', 'success') 
    return redirect(url_for('admin.businesses')) 
 
# ==================== VEHICLE MANAGEMENT WITH SEARCH ==================== 
@bp.route('/vehicles') 
@login_required 
def vehicles(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    
    # Get search parameters
    search = request.args.get('search', '')
    owner = request.args.get('owner', '')
    vehicle_type = request.args.get('vehicle_type', '')
    brand = request.args.get('brand', '')
    year_from = request.args.get('year_from', type=int)
    year_to = request.args.get('year_to', type=int)
    status = request.args.get('status', '')
    date_range = request.args.get('date_range', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start query
    query = Vehicle.query.join(User, Vehicle.owner_id == User.id).outerjoin(VehicleType)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Vehicle.plate_number.contains(search),
                Vehicle.vehicle_id.contains(search),
                Vehicle.vin.contains(search)
            )
        )
    
    if owner:
        query = query.filter(User.name.contains(owner))
    
    if vehicle_type:
        query = query.filter(VehicleType.name.contains(vehicle_type))
    
    if brand:
        query = query.filter(Vehicle.brand.contains(brand))
    
    if year_from:
        query = query.filter(Vehicle.year_of_manufacture >= year_from)
    
    if year_to:
        query = query.filter(Vehicle.year_of_manufacture <= year_to)
    
    if status:
        query = query.filter(Vehicle.status == status)
    
    # Date filtering
    if date_range == 'today':
        today = datetime.now().date()
        query = query.filter(db.func.date(Vehicle.created_at) == today)
    elif date_range == 'this_week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(Vehicle.created_at >= week_ago)
    elif date_range == 'this_month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(Vehicle.created_at >= month_ago)
    elif date_range == 'this_year':
        year_ago = datetime.now() - timedelta(days=365)
        query = query.filter(Vehicle.created_at >= year_ago)
    elif date_range == 'custom' and date_from and date_to:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Vehicle.created_at.between(from_date, to_date))
    
    vehicles = query.order_by(Vehicle.created_at.desc()).all()
    
    return render_template('admin/vehicles.html', vehicles=vehicles) 

@bp.route('/vehicle/<int:vehicle_id>')
@login_required 
def view_vehicle(vehicle_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    vehicle = Vehicle.query.get_or_404(vehicle_id) 
    return render_template('admin/view_vehicle.html', vehicle=vehicle) 

@bp.route('/vehicle/<int:vehicle_id>/toggle', methods=['POST'])
@login_required 
def toggle_vehicle_status(vehicle_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    vehicle = Vehicle.query.get_or_404(vehicle_id) 
    vehicle.status = 'suspended' if vehicle.status == 'active' else 'active' 
    db.session.commit() 
    flash(f'Vehicle {vehicle.plate_number} {vehicle.status} successfully!', 'success') 
    return redirect(url_for('admin.view_vehicle', vehicle_id=vehicle.id)) 

@bp.route('/vehicle/<int:vehicle_id>/delete', methods=['POST'])
@login_required 
def delete_vehicle(vehicle_id): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    vehicle = Vehicle.query.get_or_404(vehicle_id) 
    db.session.delete(vehicle) 
    db.session.commit() 
    flash('Vehicle deleted successfully!', 'success') 
    return redirect(url_for('admin.vehicles')) 

# ==================== ADMIN BUSINESS REGISTRATION ====================
@bp.route('/businesses/register', methods=['GET', 'POST'])
@login_required
def register_business():
    if current_user.role != 'super_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        users = User.query.filter_by(role='payee').all()
        business_types = BusinessType.query.filter_by(is_active=True).all()
        industry_sectors = IndustrySector.query.filter_by(is_active=True).all()
        return render_template('business/register.html', 
                             users=users,
                             business_types=business_types,
                             industry_sectors=industry_sectors,
                             is_admin=True)
    
    elif request.method == 'POST':
        # Generate unique business ID
        business_id = f"BUS{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        
        # Handle business photo
        business_photo = None
        if 'business_photo' in request.files:
            file = request.files['business_photo']
            if file and file.filename:
                filename = secure_filename(f"business_{business_id}_{file.filename}")
                file.save(os.path.join('app', 'static', 'uploads', filename))
                business_photo = filename
        
        # Create business
        business = Business(
            business_id=business_id,
            owner_id=request.form.get('owner_id'),
            business_name=request.form.get('business_name'),
            business_type_id=request.form.get('business_type_id') or None,
            industry_sector_id=request.form.get('industry_sector_id') or None,
            registration_number=request.form.get('registration_number'),
            tin=request.form.get('tin'),
            state=request.form.get('state'),
            lga=request.form.get('lga'),
            ward=request.form.get('ward'),
            address=request.form.get('address'),
            gps_coordinates=request.form.get('gps_coordinates'),
            business_phone=request.form.get('business_phone'),
            business_email=request.form.get('business_email'),
            employee_count=request.form.get('employee_count'),
            year_established=request.form.get('year_established'),
            business_photo=business_photo,
            status='active'
        )
        
        db.session.add(business)
        db.session.commit()
        
        flash(f'Business {business.business_name} registered successfully for {business.owner.name}!', 'success')
        return redirect(url_for('admin.view_business', business_id=business.id))

# ==================== ADMIN VEHICLE REGISTRATION ====================
@bp.route('/vehicles/register', methods=['GET', 'POST'])
@login_required
def register_vehicle():
    if current_user.role != 'super_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        users = User.query.filter_by(role='payee').all()
        vehicle_types = VehicleType.query.filter_by(is_active=True).all()
        businesses = Business.query.filter_by(status='active').all()
        return render_template('vehicle/register.html', 
                             users=users,
                             vehicle_types=vehicle_types,
                             businesses=businesses,
                             is_admin=True)
    
    elif request.method == 'POST':
        # Generate unique vehicle ID
        vehicle_id = f"VEH{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"
        plate_number = request.form.get('plate_number').upper()
        
        # Check if plate number exists
        existing = Vehicle.query.filter_by(plate_number=plate_number).first()
        if existing:
            flash('Vehicle with this plate number already exists!', 'danger')
            return redirect(url_for('admin.register_vehicle'))
        
        # Handle photos
        vehicle_photo = None
        plate_photo = None
        os.makedirs(os.path.join('app', 'static', 'uploads', 'vehicles'), exist_ok=True)
        
        if 'vehicle_photo' in request.files:
            file = request.files['vehicle_photo']
            if file and file.filename:
                filename = secure_filename(f"vehicle_{vehicle_id}_{file.filename}")
                file.save(os.path.join('app', 'static', 'uploads', 'vehicles', filename))
                vehicle_photo = filename
        
        if 'plate_photo' in request.files:
            file = request.files['plate_photo']
            if file and file.filename:
                filename = secure_filename(f"plate_{vehicle_id}_{file.filename}")
                file.save(os.path.join('app', 'static', 'uploads', 'vehicles', filename))
                plate_photo = filename
        
        # Create vehicle
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            owner_id=request.form.get('owner_id'),
            business_id=request.form.get('business_id') or None,
            plate_number=plate_number,
            vehicle_type_id=request.form.get('vehicle_type_id') or None,
            vin=request.form.get('vin'),
            brand=request.form.get('brand'),
            model=request.form.get('model'),
            year_of_manufacture=request.form.get('year_of_manufacture'),
            color=request.form.get('color'),
            engine_capacity=request.form.get('engine_capacity'),
            seating_capacity=request.form.get('seating_capacity'),
            registration_number=request.form.get('registration_number'),
            road_worthiness_number=request.form.get('road_worthiness_number'),
            insurance_policy_number=request.form.get('insurance_policy_number'),
            vehicle_photo=vehicle_photo,
            plate_photo=plate_photo,
            status='active'
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        flash(f'Vehicle {plate_number} registered successfully for {vehicle.owner.name}!', 'success')
        return redirect(url_for('admin.view_vehicle', vehicle_id=vehicle.id))

# ==================== VEHICLE TYPES AJAX ROUTES ====================
@bp.route('/vehicle-types/add', methods=['POST'])
@login_required
def add_vehicle_type():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    name = data.get('name')
    amount = data.get('amount')
    description = data.get('description', '')
    
    if not name or not amount:
        return jsonify({'success': False, 'message': 'Name and amount are required'}), 400
    
    existing = VehicleType.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': 'Vehicle type already exists'}), 400
    
    vehicle_type = VehicleType(
        name=name,
        amount=amount,
        description=description,
        is_active=True
    )
    db.session.add(vehicle_type)
    db.session.commit()
    
    return jsonify({'success': True, 'id': vehicle_type.id})

@bp.route('/vehicle-types/delete', methods=['POST'])
@login_required
def delete_vehicle_type():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    type_id = data.get('id')
    
    vehicle_type = VehicleType.query.get(type_id)
    if not vehicle_type:
        return jsonify({'success': False, 'message': 'Type not found'}), 404
    
    # Check if any vehicles use this type
    if vehicle_type.vehicles:
        return jsonify({'success': False, 'message': 'Cannot delete type that is in use'}), 400
    
    db.session.delete(vehicle_type)
    db.session.commit()
    
    return jsonify({'success': True})

# ==================== BUSINESS TYPES AJAX ROUTES ====================
@bp.route('/business-types/add', methods=['POST'])
@login_required
def add_business_type():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    name = data.get('name')
    amount = data.get('amount')
    description = data.get('description', '')
    
    if not name or not amount:
        return jsonify({'success': False, 'message': 'Name and amount are required'}), 400
    
    existing = BusinessType.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': 'Business type already exists'}), 400
    
    business_type = BusinessType(
        name=name,
        amount=amount,
        description=description,
        is_active=True
    )
    db.session.add(business_type)
    db.session.commit()
    
    return jsonify({'success': True, 'id': business_type.id})

@bp.route('/business-types/delete', methods=['POST'])
@login_required
def delete_business_type():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    type_id = data.get('id')
    
    business_type = BusinessType.query.get(type_id)
    if not business_type:
        return jsonify({'success': False, 'message': 'Type not found'}), 404
    
    # Check if any businesses use this type
    if business_type.businesses:
        return jsonify({'success': False, 'message': 'Cannot delete type that is in use'}), 400
    
    db.session.delete(business_type)
    db.session.commit()
    
    return jsonify({'success': True})

# ==================== INDUSTRY SECTORS AJAX ROUTES ====================
@bp.route('/industry-sectors/add', methods=['POST'])
@login_required
def add_industry_sector():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    existing = IndustrySector.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': 'Industry sector already exists'}), 400
    
    sector = IndustrySector(
        name=name,
        description=description,
        is_active=True
    )
    db.session.add(sector)
    db.session.commit()
    
    return jsonify({'success': True, 'id': sector.id})

@bp.route('/industry-sectors/delete', methods=['POST'])
@login_required
def delete_industry_sector():
    if current_user.role != 'super_admin':
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    data = request.get_json()
    sector_id = data.get('id')
    
    sector = IndustrySector.query.get(sector_id)
    if not sector:
        return jsonify({'success': False, 'message': 'Sector not found'}), 404
    
    # Check if any businesses use this sector
    if sector.businesses:
        return jsonify({'success': False, 'message': 'Cannot delete sector that is in use'}), 400
    
    db.session.delete(sector)
    db.session.commit()
    
    return jsonify({'success': True})

# ==================== PAYMENT MANAGEMENT WITH SEARCH ==================== 
@bp.route('/payments') 
@login_required 
def payments(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    
    # Get search parameters
    search = request.args.get('search', '')
    payer = request.args.get('payer', '')
    levy_type = request.args.get('levy_type', '')
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    payment_status = request.args.get('payment_status', '')
    verification_status = request.args.get('verification_status', '')
    date_range = request.args.get('date_range', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start query
    query = Payment.query.join(User, Payment.user_id == User.id).outerjoin(Business).outerjoin(Vehicle)
    
    # Apply filters
    if search:
        query = query.filter(
            db.or_(
                Payment.payment_reference.contains(search),
                Payment.receipt_number.contains(search)
            )
        )
    
    if payer:
        query = query.filter(User.name.contains(payer))
    
    if levy_type:
        query = query.filter(Payment.levy_type.contains(levy_type))
    
    if min_amount is not None:
        query = query.filter(Payment.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(Payment.amount <= max_amount)
    
    if payment_status:
        query = query.filter(Payment.payment_status == payment_status)
    
    if verification_status:
        query = query.filter(Payment.verification_status == verification_status)
    
    # Date filtering
    if date_range == 'today':
        today = datetime.now().date()
        query = query.filter(db.func.date(Payment.created_at) == today)
    elif date_range == 'this_week':
        week_ago = datetime.now() - timedelta(days=7)
        query = query.filter(Payment.created_at >= week_ago)
    elif date_range == 'this_month':
        month_ago = datetime.now() - timedelta(days=30)
        query = query.filter(Payment.created_at >= month_ago)
    elif date_range == 'this_year':
        year_ago = datetime.now() - timedelta(days=365)
        query = query.filter(Payment.created_at >= year_ago)
    elif date_range == 'custom' and date_from and date_to:
        from_date = datetime.strptime(date_from, '%Y-%m-%d')
        to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(Payment.created_at.between(from_date, to_date))
    
    payments = query.order_by(Payment.created_at.desc()).all()
    
    return render_template('admin/payments.html', payments=payments) 
# ==================== EDIT BUSINESS ====================
@bp.route('/business/<int:business_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_business(business_id):
    if current_user.role != 'super_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    business = Business.query.get_or_404(business_id)
    
    if request.method == 'POST':
        business.business_name = request.form.get('business_name')
        business.business_type_id = request.form.get('business_type_id') or None
        business.industry_sector_id = request.form.get('industry_sector_id') or None
        business.registration_number = request.form.get('registration_number')
        business.tin = request.form.get('tin')
        business.state = request.form.get('state')
        business.lga = request.form.get('lga')
        business.ward = request.form.get('ward')
        business.address = request.form.get('address')
        business.gps_coordinates = request.form.get('gps_coordinates')
        business.business_phone = request.form.get('business_phone')
        business.business_email = request.form.get('business_email')
        business.employee_count = request.form.get('employee_count')
        business.year_established = request.form.get('year_established')
        
        # Handle photo upload
        if 'business_photo' in request.files:
            file = request.files['business_photo']
            if file and file.filename:
                filename = secure_filename(f"business_{business.business_id}_{file.filename}")
                file.save(os.path.join('app', 'static', 'uploads', filename))
                business.business_photo = filename
        
        db.session.commit()
        flash(f'Business {business.business_name} updated successfully!', 'success')
        return redirect(url_for('admin.view_business', business_id=business.id))
    
    # GET request
    users = User.query.filter_by(role='payee').all()
    business_types = BusinessType.query.filter_by(is_active=True).all()
    industry_sectors = IndustrySector.query.filter_by(is_active=True).all()
    
    return render_template('admin/edit_business.html', 
                         business=business,
                         users=users,
                         business_types=business_types,
                         industry_sectors=industry_sectors)

# ==================== EDIT VEHICLE ====================
@bp.route('/vehicle/<int:vehicle_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    if current_user.role != 'super_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        vehicle.owner_id = request.form.get('owner_id')
        vehicle.business_id = request.form.get('business_id') or None
        vehicle.plate_number = request.form.get('plate_number').upper()
        vehicle.vin = request.form.get('vin')
        vehicle.vehicle_type_id = request.form.get('vehicle_type_id') or None
        vehicle.brand = request.form.get('brand')
        vehicle.model = request.form.get('model')
        vehicle.year_of_manufacture = request.form.get('year_of_manufacture')
        vehicle.color = request.form.get('color')
        vehicle.engine_capacity = request.form.get('engine_capacity')
        vehicle.seating_capacity = request.form.get('seating_capacity')
        vehicle.registration_number = request.form.get('registration_number')
        vehicle.road_worthiness_number = request.form.get('road_worthiness_number')
        vehicle.insurance_policy_number = request.form.get('insurance_policy_number')
        
        # Handle photos
        if 'vehicle_photo' in request.files:
            file = request.files['vehicle_photo']
            if file and file.filename:
                filename = secure_filename(f"vehicle_{vehicle.vehicle_id}_{file.filename}")
                file.save(os.path.join('app', 'static', 'uploads', 'vehicles', filename))
                vehicle.vehicle_photo = filename
        
        if 'plate_photo' in request.files:
            file = request.files['plate_photo']
            if file and file.filename:
                filename = secure_filename(f"plate_{vehicle.vehicle_id}_{file.filename}")
                file.save(os.path.join('app', 'static', 'uploads', 'vehicles', filename))
                vehicle.plate_photo = filename
        
        db.session.commit()
        flash(f'Vehicle {vehicle.plate_number} updated successfully!', 'success')
        return redirect(url_for('admin.view_vehicle', vehicle_id=vehicle.id))
    
    # GET request
    users = User.query.filter_by(role='payee').all()
    vehicle_types = VehicleType.query.filter_by(is_active=True).all()
    businesses = Business.query.filter_by(status='active').all()
    
    return render_template('admin/edit_vehicle.html',
                         vehicle=vehicle,
                         users=users,
                         vehicle_types=vehicle_types,
                         businesses=businesses)

# ==================== EDIT PAYMENT ====================
@bp.route('/payment/<int:payment_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payment(payment_id):
    if current_user.role != 'super_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    payment = Payment.query.get_or_404(payment_id)
    
    if request.method == 'POST':
        payment.payment_status = request.form.get('payment_status')
        payment.verification_status = request.form.get('verification_status')
        payment.verified_by = current_user.id
        payment.verification_date = datetime.now()
        
        db.session.commit()
        flash(f'Payment {payment.payment_reference} updated successfully!', 'success')
        return redirect(url_for('admin.payments'))
    
    return render_template('admin/edit_payment.html', payment=payment)

# ==================== VIEW PAYMENT DETAILS ====================
@bp.route('/payment/<int:payment_id>')
@login_required
def view_payment(payment_id):
    if current_user.role != 'super_admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    payment = Payment.query.get_or_404(payment_id)
    return render_template('admin/view_payment.html', payment=payment)
 
# ==================== REPORTS ==================== 
@bp.route('/reports') 
@login_required 
def reports(): 
    if current_user.role != 'super_admin': 
        flash('Access denied. Admin only.', 'danger') 
        return redirect(url_for('main.dashboard')) 
    return render_template('admin/reports.html')