# generate_all_qr_codes.py
import os
import sys

# Add current directory to path
sys.path.insert(0, os.getcwd())

from app import create_app
from app.models import Business, Vehicle
from app.utils.qr_utils import generate_business_qr_code, generate_vehicle_qr_code

app = create_app()
with app.app_context():
    print("=" * 60)
    print("GENERATING QR CODES FOR ALL ENTITIES")
    print("=" * 60)
    
    # Create directories if they don't exist
    upload_folder = app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
    business_qr_dir = os.path.join(upload_folder, 'qrcodes', 'businesses')
    vehicle_qr_dir = os.path.join(upload_folder, 'qrcodes', 'vehicles')
    
    os.makedirs(business_qr_dir, exist_ok=True)
    os.makedirs(vehicle_qr_dir, exist_ok=True)
    
    print(f"Business QR directory: {business_qr_dir}")
    print(f"Vehicle QR directory: {vehicle_qr_dir}")
    print()
    
    # Generate for businesses
    businesses = Business.query.all()
    business_count = 0
    print(f"📊 Businesses ({len(businesses)} found):")
    for business in businesses:
        result = generate_business_qr_code(business)
        if result:
            business_count += 1
            print(f"  ✅ {business.business_name} -> {result}")
        else:
            print(f"  ❌ {business.business_name}")
    
    # Generate for vehicles
    vehicles = Vehicle.query.all()
    vehicle_count = 0
    print(f"\n🚗 Vehicles ({len(vehicles)} found):")
    for vehicle in vehicles:
        result = generate_vehicle_qr_code(vehicle)
        if result:
            vehicle_count += 1
            print(f"  ✅ {vehicle.plate_number} -> {result}")
        else:
            print(f"  ❌ {vehicle.plate_number}")
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {business_count} business QR codes and {vehicle_count} vehicle QR codes")
    print("=" * 60)