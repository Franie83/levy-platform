# generate_all_qrs.py
from app import create_app
from app.models import Business, Vehicle
from app.utils.qr_utils import generate_business_qr_code, generate_vehicle_qr_code

app = create_app()
with app.app_context():
    print("=" * 60)
    print("GENERATING QR CODES")
    print("=" * 60)
    
    # Generate for businesses
    businesses = Business.query.all()
    business_count = 0
    print(f"\n📊 Businesses ({len(businesses)} found):")
    for business in businesses:
        if not business.qr_code:
            if generate_business_qr_code(business):
                business_count += 1
                print(f"  ✅ {business.business_name}")
            else:
                print(f"  ❌ {business.business_name}")
        else:
            print(f"  ⏭️ {business.business_name} (already has QR)")
    
    # Generate for vehicles
    vehicles = Vehicle.query.all()
    vehicle_count = 0
    print(f"\n🚗 Vehicles ({len(vehicles)} found):")
    for vehicle in vehicles:
        if not vehicle.qr_code:
            if generate_vehicle_qr_code(vehicle):
                vehicle_count += 1
                print(f"  ✅ {vehicle.plate_number}")
            else:
                print(f"  ❌ {vehicle.plate_number}")
        else:
            print(f"  ⏭️ {vehicle.plate_number} (already has QR)")
    
    print("\n" + "=" * 60)
    print(f"✅ Generated {business_count} business QR codes and {vehicle_count} vehicle QR codes")
    print("=" * 60)