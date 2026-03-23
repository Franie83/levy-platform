from datetime import datetime 
from flask_login import UserMixin 
from werkzeug.security import generate_password_hash, check_password_hash 
from app import db, login_manager 
 
class User(UserMixin, db.Model): 
    __tablename__ = 'users' 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False) 
    phone = db.Column(db.String(20), nullable=False) 
    nin = db.Column(db.String(20), unique=True, nullable=False) 
    password_hash = db.Column(db.String(200), nullable=False) 
    role = db.Column(db.String(20), nullable=False) 
    category = db.Column(db.String(20)) 
    profile_image = db.Column(db.String(200)) 
    status = db.Column(db.String(20), default='active') 
    qr_code = db.Column(db.String(200))  # ADDED QR CODE FIELD
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 
 
    # Relationships - updated to avoid conflicts
    businesses = db.relationship('Business', backref='owner', lazy=True) 
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True) 
    payments_as_payer = db.relationship('Payment', foreign_keys='Payment.user_id', back_populates='payer', lazy=True) 
    payments_as_verifier = db.relationship('Payment', foreign_keys='Payment.verified_by', back_populates='verifier', lazy=True) 
    payments_as_initiator = db.relationship('Payment', foreign_keys='Payment.initiated_by', back_populates='initiator', lazy=True)
 
    def set_password(self, password): 
        self.password_hash = generate_password_hash(password) 
 
    def check_password(self, password): 
        return check_password_hash(self.password_hash, password) 
    
    def get_qr_code_url(self):
        """Get the URL for the user's QR code"""
        if self.qr_code:
            from flask import url_for
            return url_for('static', filename=f'uploads/qrcodes/users/{self.qr_code}')
        return None

# ==================== ADMIN-CONTROLLED MODELS WITH AMOUNTS ====================

class VehicleType(db.Model):
    __tablename__ = 'vehicle_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    vehicles = db.relationship('Vehicle', backref='vehicle_type_ref', lazy=True)
    
    def __repr__(self):
        return f'<VehicleType {self.name}>'

class BusinessType(db.Model):
    __tablename__ = 'business_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    amount = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    businesses = db.relationship('Business', backref='business_type_ref', lazy=True)
    
    def __repr__(self):
        return f'<BusinessType {self.name}>'

class IndustrySector(db.Model):
    __tablename__ = 'industry_sectors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    businesses = db.relationship('Business', backref='industry_sector_ref', lazy=True)
    
    def __repr__(self):
        return f'<IndustrySector {self.name}>'

# ==================== BUSINESS MODEL ====================

class Business(db.Model): 
    __tablename__ = 'businesses' 
    id = db.Column(db.Integer, primary_key=True) 
    business_id = db.Column(db.String(50), unique=True, nullable=False) 
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    business_name = db.Column(db.String(100), nullable=False) 
    business_type_id = db.Column(db.Integer, db.ForeignKey('business_types.id'), nullable=True) 
    industry_sector_id = db.Column(db.Integer, db.ForeignKey('industry_sectors.id'), nullable=True) 
    registration_number = db.Column(db.String(50), unique=True) 
    tin = db.Column(db.String(50), unique=True) 
    state = db.Column(db.String(50)) 
    lga = db.Column(db.String(50)) 
    ward = db.Column(db.String(50)) 
    address = db.Column(db.String(200)) 
    gps_coordinates = db.Column(db.String(100)) 
    business_phone = db.Column(db.String(20)) 
    business_email = db.Column(db.String(120)) 
    employee_count = db.Column(db.Integer) 
    year_established = db.Column(db.Integer) 
    business_photo = db.Column(db.String(200)) 
    qr_code = db.Column(db.String(200))  # ADD THIS FIELD
    status = db.Column(db.String(20), default='active') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
 
    vehicles = db.relationship('Vehicle', backref='business', lazy=True) 
    payments = db.relationship('Payment', backref='business', lazy=True)

# ==================== VEHICLE MODEL ====================

class Vehicle(db.Model): 
    __tablename__ = 'vehicles' 
    id = db.Column(db.Integer, primary_key=True) 
    vehicle_id = db.Column(db.String(50), unique=True, nullable=False) 
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True) 
    plate_number = db.Column(db.String(20), unique=True, nullable=False) 
    vin = db.Column(db.String(50), unique=True) 
    vehicle_type_id = db.Column(db.Integer, db.ForeignKey('vehicle_types.id'), nullable=True) 
    brand = db.Column(db.String(50)) 
    model = db.Column(db.String(50)) 
    year_of_manufacture = db.Column(db.Integer) 
    color = db.Column(db.String(30)) 
    engine_capacity = db.Column(db.String(20)) 
    seating_capacity = db.Column(db.Integer) 
    registration_number = db.Column(db.String(50), unique=True) 
    road_worthiness_number = db.Column(db.String(50)) 
    insurance_policy_number = db.Column(db.String(50)) 
    vehicle_photo = db.Column(db.String(200)) 
    plate_photo = db.Column(db.String(200)) 
    qr_code = db.Column(db.String(200))  # ADD THIS FIELD
    status = db.Column(db.String(20), default='active') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
# ==================== UPDATED PAYMENT MODEL ====================

class Payment(db.Model): 
    __tablename__ = 'payments' 
    id = db.Column(db.Integer, primary_key=True) 
    payment_reference = db.Column(db.String(100), unique=True, nullable=False) 
    receipt_number = db.Column(db.String(100), unique=True, nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True) 
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True) 
    levy_type = db.Column(db.String(50), nullable=False) 
    amount = db.Column(db.Float, nullable=False) 
    payment_method = db.Column(db.String(50)) 
    payment_channel = db.Column(db.String(50)) 
    payment_status = db.Column(db.String(20), default='pending') 
    verification_status = db.Column(db.String(20), default='unverified') 
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    verification_date = db.Column(db.DateTime) 
    paystack_reference = db.Column(db.String(100)) 
    transaction_id = db.Column(db.String(100)) 
    authorization_code = db.Column(db.String(100)) 
    payment_date = db.Column(db.DateTime) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
    initiated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
 
    # Relationships - fixed to avoid conflicts
    payer = db.relationship('User', foreign_keys=[user_id], back_populates='payments_as_payer')
    verifier = db.relationship('User', foreign_keys=[verified_by], back_populates='payments_as_verifier')
    initiator = db.relationship('User', foreign_keys=[initiated_by], back_populates='payments_as_initiator')

# ==================== EXISTING MODELS ====================

class Receipt(db.Model): 
    __tablename__ = 'receipts' 
    id = db.Column(db.Integer, primary_key=True) 
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id'), nullable=False) 
    receipt_number = db.Column(db.String(100), unique=True, nullable=False) 
    qr_code = db.Column(db.String(200)) 
    generated_at = db.Column(db.DateTime, default=datetime.utcnow) 
 
class Violation(db.Model): 
    __tablename__ = 'violations' 
    id = db.Column(db.Integer, primary_key=True) 
    enforcer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=True) 
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True) 
    violation_type = db.Column(db.String(50), nullable=False) 
    description = db.Column(db.Text) 
    evidence_photo = db.Column(db.String(200)) 
    gps_coordinates = db.Column(db.String(100)) 
    status = db.Column(db.String(20), default='pending') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
 
    # Relationships
    enforcer = db.relationship('User', foreign_keys=[enforcer_id], backref='enforced_violations')
    user = db.relationship('User', foreign_keys=[user_id], backref='user_violations')
    business = db.relationship('Business', backref='business_violations')
    vehicle = db.relationship('Vehicle', backref='vehicle_violations') 
    
class AuditLog(db.Model): 
    __tablename__ = 'audit_logs' 
    id = db.Column(db.Integer, primary_key=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) 
    action = db.Column(db.String(200), nullable=False) 
    resource_type = db.Column(db.String(50)) 
    resource_id = db.Column(db.String(50)) 
    ip_address = db.Column(db.String(50)) 
    device = db.Column(db.String(200)) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) 
 
class LevyType(db.Model): 
    __tablename__ = 'levy_types' 
    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(50), unique=True, nullable=False) 
    description = db.Column(db.Text) 
    amount = db.Column(db.Float, nullable=False) 
    frequency = db.Column(db.String(20), default='daily') 
    category = db.Column(db.String(20)) 
    is_active = db.Column(db.Boolean, default=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 
 
@login_manager.user_loader 
def load_user(user_id): 
    return User.query.get(int(user_id))