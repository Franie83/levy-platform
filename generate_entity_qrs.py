# generate_entity_qrs.py
from app import create_app
from app.models import Business, Vehicle
from app.utils.qr_utils import generate_business_qr_code, generate_vehicle_qr_code

app = create_app()
with app.app_context():
    print("=" * 50)
    print("Generating QR codes for businesses and vehicles")
    print("=" * 50)
    
    # Generate for businesses
    businesses = Business.query.all()
    business_count = 0
    print(f"\n📊 Processing {len(businesses)} businesses...")
    for business in businesses:
        if not business.qr_code:
            result = generate_business_qr_code(business)
            if result:
                business_count += 1
                print(f"  ✅ Business: {business.business_name} -> QR code generated")
            else:
                print(f"  ❌ Business: {business.business_name} -> Failed")
        else:
            print(f"  ⏭️ Business: {business.business_name} -> Already has QR code")
    
    # Generate for vehicles
    vehicles = Vehicle.query.all()
    vehicle_count = 0
    print(f"\n📊 Processing {len(vehicles)} vehicles...")
    for vehicle in vehicles:
        if not vehicle.qr_code:
            result = generate_vehicle_qr_code(vehicle)
            if result:
                vehicle_count += 1
                print(f"  ✅ Vehicle: {vehicle.plate_number} -> QR code generated")
            else:
                print(f"  ❌ Vehicle: {vehicle.plate_number} -> Failed")
        else:
            print(f"  ⏭️ Vehicle: {vehicle.plate_number} -> Already has QR code")
    
    print("\n" + "=" * 50)
    print(f"✅ Generated QR codes for {business_count} businesses and {vehicle_count} vehicles")
    print("=" * 50)