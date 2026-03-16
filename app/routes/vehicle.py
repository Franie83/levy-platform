from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify 
from flask_login import login_required, current_user 
from werkzeug.utils import secure_filename 
from app import db 
from app.models import Vehicle, User, Business, AuditLog, VehicleType 
import os 
import uuid 
from datetime import datetime 
from sqlalchemy.exc import IntegrityError

bp = Blueprint('vehicle', __name__, url_prefix='/vehicle') 

def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'} 

@bp.route('/register', methods=['GET', 'POST']) 
@login_required 
def register(): 
    # Check if user is allowed to register vehicles 
    # Admin can always register, Transporter users can register for themselves
    is_admin = current_user.role == 'super_admin'
    
    if not is_admin and (current_user.role != 'payee' or current_user.category != 'Transporter'): 
        flash('Only Transporter users and admins can register vehicles', 'danger') 
        return redirect(url_for('main.dashboard')) 

    if request.method == 'POST': 
        # Generate unique vehicle ID 
        vehicle_id = f"VEH{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}" 
        plate_number = request.form.get('plate_number').upper() 
        registration_number = request.form.get('registration_number') 

        # Check if plate number already exists 
        existing_plate = Vehicle.query.filter_by(plate_number=plate_number).first() 
        if existing_plate: 
            flash(f'Vehicle with plate number {plate_number} already exists!', 'danger') 
            return redirect(url_for('vehicle.register')) 

        # Check if registration number already exists (if provided) 
        if registration_number: 
            existing_reg = Vehicle.query.filter_by(registration_number=registration_number).first() 
            if existing_reg: 
                flash(f'Vehicle with registration number {registration_number} already exists!', 'danger') 
                return redirect(url_for('vehicle.register')) 

        print(f"\n{'='*50}") 
        print(f"VEHICLE REGISTRATION - User: {current_user.name}") 
        print(f"Plate Number: {plate_number}") 

        # Handle photos 
        vehicle_photo = None 
        plate_photo = None 

        # Create vehicles directory if it doesn't exist
        os.makedirs(os.path.join('app', 'static', 'uploads', 'vehicles'), exist_ok=True)

        if 'vehicle_photo' in request.files: 
            file = request.files['vehicle_photo'] 
            if file and file.filename and allowed_file(file.filename): 
                filename = secure_filename(f"vehicle_{vehicle_id}_{file.filename}") 
                file.save(os.path.join('app', 'static', 'uploads', 'vehicles', filename)) 
                vehicle_photo = filename 

        if 'plate_photo' in request.files: 
            file = request.files['plate_photo'] 
            if file and file.filename and allowed_file(file.filename): 
                filename = secure_filename(f"plate_{vehicle_id}_{file.filename}") 
                file.save(os.path.join('app', 'static', 'uploads', 'vehicles', filename)) 
                plate_photo = filename 

        # Get business_id if selected (optional) 
        business_id = request.form.get('business_id') 
        if business_id == '': 
            business_id = None 

        # Get vehicle_type_id (can be None if not selected)
        vehicle_type_id = request.form.get('vehicle_type_id')
        if vehicle_type_id == '':
            vehicle_type_id = None

        # Determine owner_id - admin can set it, otherwise use current user
        owner_id = request.form.get('owner_id') if is_admin else current_user.id

        # Create vehicle with updated fields
        vehicle = Vehicle( 
            vehicle_id=vehicle_id, 
            owner_id=owner_id, 
            business_id=business_id, 
            plate_number=plate_number, 
            vin=request.form.get('vin'), 
            vehicle_type_id=vehicle_type_id, 
            brand=request.form.get('brand'), 
            model=request.form.get('model'), 
            year_of_manufacture=request.form.get('year_of_manufacture'), 
            color=request.form.get('color'), 
            engine_capacity=request.form.get('engine_capacity'), 
            seating_capacity=request.form.get('seating_capacity'), 
            registration_number=registration_number, 
            road_worthiness_number=request.form.get('road_worthiness_number'), 
            insurance_policy_number=request.form.get('insurance_policy_number'), 
            vehicle_photo=vehicle_photo, 
            plate_photo=plate_photo, 
            status='active'
            # amount_due removed - comes from vehicle type
        ) 

        try: 
            db.session.add(vehicle) 
            db.session.commit() 

            # Log the action 
            log = AuditLog( 
                user_id=current_user.id, 
                action='VEHICLE_REGISTRATION', 
                resource_type='vehicle', 
                resource_id=vehicle_id, 
                ip_address=request.remote_addr, 
                device=request.user_agent.string 
            ) 
            db.session.add(log) 
            db.session.commit() 

            print(f"✅ Vehicle registered: {vehicle.plate_number} (ID: {vehicle_id})") 
            print(f"{'='*50}\n") 

            flash('Vehicle registered successfully!', 'success') 
            return redirect(url_for('vehicle.view', vehicle_id=vehicle_id)) 

        except IntegrityError as e: 
            db.session.rollback() 
            print(f"❌ IntegrityError: {str(e)}") 
            flash('A vehicle with this plate number or registration number already exists!', 'danger') 
            return redirect(url_for('vehicle.register')) 

    # GET request - fetch dropdown data from database
    vehicle_types = VehicleType.query.filter_by(is_active=True).all()
    
    # Get user's businesses for dropdown (optional) 
    businesses = Business.query.filter_by(owner_id=current_user.id, status='active').all()
    
    # For admin, also get all payee users to assign to
    users = []
    if is_admin:
        users = User.query.filter_by(role='payee').all()
    
    return render_template('vehicle/register.html', 
                         businesses=businesses,
                         vehicle_types=vehicle_types,
                         users=users,
                         is_admin=is_admin) 

@bp.route('/list') 
@login_required 
def list(): 
    if current_user.role == 'super_admin': 
        vehicles = Vehicle.query.all() 
    elif current_user.role == 'payee' and current_user.category == 'Transporter': 
        vehicles = Vehicle.query.filter_by(owner_id=current_user.id).all() 
    else: 
        if current_user.role == 'payee' and current_user.category != 'Transporter':
            flash('Access denied. This section is for Transporter users only.', 'danger')
        vehicles = [] 
 
    return render_template('vehicle/list.html', vehicles=vehicles) 

@bp.route('/<vehicle_id>') 
@login_required 
def view(vehicle_id): 
    vehicle = Vehicle.query.filter_by(vehicle_id=vehicle_id).first_or_404() 

    # Check permissions 
    if current_user.role not in ['super_admin', 'enforcer'] and vehicle.owner_id != current_user.id: 
        flash('Access denied.', 'danger') 
        return redirect(url_for('vehicle.list')) 

    return render_template('vehicle/view.html', vehicle=vehicle)