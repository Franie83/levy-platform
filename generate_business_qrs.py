# generate_business_qrs.py
from app import create_app
from app.models import Business
from app.utils.qr_utils import generate_business_qr_code

app = create_app()
with app.app_context():
    businesses = Business.query.all()
    count = 0
    
    print(f"Found {len(businesses)} businesses")
    print("=" * 50)
    
    for business in businesses:
        if not business.qr_code:
            result = generate_business_qr_code(business)
            if result:
                count += 1
                print(f"✅ Generated QR for {business.business_name}")
            else:
                print(f"❌ Failed to generate QR for {business.business_name}")
        else:
            print(f"⏭️ Already has QR: {business.business_name}")
    
    print("=" * 50)
    print(f"✅ Generated QR codes for {count} businesses")