# app/utils/qr_utils.py
import qrcode
import os
from flask import url_for, current_app
from app import db

def generate_entity_qr_code(entity, entity_type):
    """Generate a QR code for a business or vehicle"""
    try:
        # Create QR code data - link to entity verification
        qr_data = f"{current_app.config['BASE_URL']}/enforcement/verify-entity/{entity_type}/{entity.id}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Create filename based on entity type
        if entity_type == 'business':
            identifier = entity.registration_number or entity.id
            filename = f"business_qr_{entity.id}_{identifier}.png"
        else:  # vehicle
            identifier = entity.plate_number
            filename = f"vehicle_qr_{entity.id}_{identifier}.png"
        
        # Save QR code
        qr_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'qrcodes', f'{entity_type}s', filename)
        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        img.save(qr_path)
        
        # Update entity with QR code filename
        entity.qr_code = filename
        db.session.commit()
        
        return filename
    except Exception as e:
        print(f"Error generating QR code for {entity_type} {entity.id}: {e}")
        return None

def generate_business_qr_code(business):
    """Generate QR code for a business"""
    return generate_entity_qr_code(business, 'business')

def generate_vehicle_qr_code(vehicle):
    """Generate QR code for a vehicle"""
    return generate_entity_qr_code(vehicle, 'vehicle')

def generate_user_qr_code(user):
    """Generate a QR code for a user that links to their verification page"""
    try:
        # Create QR code data - link to user verification
        qr_data = f"{current_app.config['BASE_URL']}/enforcement/verify-user/{user.id}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        filename = f"user_qr_{user.id}_{user.nin}.png"
        qr_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'qrcodes', 'users', filename)
        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        img.save(qr_path)
        
        # Update user with QR code filename
        user.qr_code = filename
        db.session.commit()
        
        return filename
    except Exception as e:
        print(f"Error generating QR code for user {user.id}: {e}")
        return None

def generate_all_user_qr_codes():
    """Generate QR codes for all payee users"""
    from app.models import User
    
    users = User.query.filter_by(role='payee').all()
    count = 0
    for user in users:
        if not user.qr_code:
            if generate_user_qr_code(user):
                count += 1
    print(f"Generated QR codes for {count} users")
    return count

def generate_all_business_qr_codes():
    """Generate QR codes for all active businesses"""
    from app.models import Business
    
    businesses = Business.query.filter_by(status='active').all()
    count = 0
    for business in businesses:
        if not business.qr_code:
            if generate_business_qr_code(business):
                count += 1
    print(f"Generated QR codes for {count} businesses")
    return count

def generate_all_vehicle_qr_codes():
    """Generate QR codes for all active vehicles"""
    from app.models import Vehicle
    
    vehicles = Vehicle.query.filter_by(status='active').all()
    count = 0
    for vehicle in vehicles:
        if not vehicle.qr_code:
            if generate_vehicle_qr_code(vehicle):
                count += 1
    print(f"Generated QR codes for {count} vehicles")
    return count
def generate_all_business_qr_codes():
    """Generate QR codes for all active businesses"""
    from app.models import Business
    
    businesses = Business.query.filter_by(status='active').all()
    count = 0
    for business in businesses:
        if not business.qr_code:
            if generate_business_qr_code(business):
                count += 1
    return count

def generate_all_entity_qr_codes():
    """Generate QR codes for all businesses and vehicles"""
    business_count = generate_all_business_qr_codes()
    vehicle_count = generate_all_vehicle_qr_codes()
    print(f"Total: {business_count + vehicle_count} QR codes generated (businesses: {business_count}, vehicles: {vehicle_count})")
    return business_count + vehicle_count

def generate_qr_code_for_entity_by_id(entity_type, entity_id):
    """Generate QR code for a specific entity by ID"""
    from app.models import Business, Vehicle
    
    if entity_type == 'business':
        entity = Business.query.get(entity_id)
        if entity:
            return generate_business_qr_code(entity)
    elif entity_type == 'vehicle':
        entity = Vehicle.query.get(entity_id)
        if entity:
            return generate_vehicle_qr_code(entity)
    return None