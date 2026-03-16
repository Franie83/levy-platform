from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify 
from flask_login import login_required, current_user 
from werkzeug.utils import secure_filename 
from app import db 
from app.models import Business, User, AuditLog, BusinessType, IndustrySector 
import os 
import uuid 
from datetime import datetime 
 
bp = Blueprint('business', __name__, url_prefix='/business') 
 
def allowed_file(filename): 
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'} 
 
@bp.route('/register', methods=['GET', 'POST']) 
@login_required 
def register(): 
    # Check if user is allowed to register businesses 
    if current_user.role != 'payee' or current_user.category != 'MSME': 
        flash('Only MSME users can register businesses', 'danger') 
        return redirect(url_for('main.dashboard')) 
 
    if request.method == 'POST': 
        # Generate unique business ID 
        business_id = f"BUS{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}" 
 
        print(f"\n{'='*50}") 
        print(f"BUSINESS REGISTRATION - User: {current_user.name}") 
        print(f"Business Name: {request.form.get('business_name')}") 
 
        # Handle business photo 
        business_photo = None 
        if 'business_photo' in request.files: 
            file = request.files['business_photo'] 
            if file and file.filename and allowed_file(file.filename): 
                filename = secure_filename(f"business_{business_id}_{file.filename}") 
                file.save(os.path.join('app', 'static', 'uploads', filename)) 
                business_photo = filename 
 
        # Get foreign key IDs (can be None if not selected)
        business_type_id = request.form.get('business_type_id')
        if business_type_id == '':
            business_type_id = None
            
        industry_sector_id = request.form.get('industry_sector_id')
        if industry_sector_id == '':
            industry_sector_id = None
 
        # Create business with updated fields - REMOVED amount_due
        business = Business( 
            business_id=business_id, 
            owner_id=current_user.id, 
            business_name=request.form.get('business_name'), 
            # Foreign keys
            business_type_id=business_type_id, 
            industry_sector_id=industry_sector_id, 
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
            # REMOVED: amount_due=request.form.get('amount_due', type=float)
        ) 
 
        db.session.add(business) 
        db.session.commit() 
 
        # Log the action 
        log = AuditLog( 
            user_id=current_user.id, 
            action='BUSINESS_REGISTRATION', 
            resource_type='business', 
            resource_id=business_id, 
            ip_address=request.remote_addr, 
            device=request.user_agent.string 
        ) 
        db.session.add(log) 
        db.session.commit() 
 
        print(f"✅ Business registered: {business.business_name} (ID: {business_id})") 
        print(f"{'='*50}\n") 
 
        flash('Business registered successfully!', 'success') 
        return redirect(url_for('business.view', business_id=business_id)) 
 
    # GET request - fetch dropdown data from database
    business_types = BusinessType.query.filter_by(is_active=True).all()
    industry_sectors = IndustrySector.query.filter_by(is_active=True).all()
    
    return render_template('business/register.html', 
                         business_types=business_types,
                         industry_sectors=industry_sectors) 
 
@bp.route('/list') 
@login_required 
def list(): 
    if current_user.role == 'super_admin': 
        businesses = Business.query.all() 
    elif current_user.role == 'payee': 
        businesses = Business.query.filter_by(owner_id=current_user.id).all() 
    else: 
        businesses = Business.query.filter_by(status='active').all() 
 
    return render_template('business/list.html', businesses=businesses) 
 
@bp.route('/<business_id>') 
@login_required 
def view(business_id): 
    business = Business.query.filter_by(business_id=business_id).first_or_404() 
 
    # Check permissions 
    if current_user.role not in ['super_admin', 'enforcer'] and business.owner_id != current_user.id: 
        flash('Access denied.', 'danger') 
        return redirect(url_for('business.list')) 
 
    return render_template('business/view.html', business=business)