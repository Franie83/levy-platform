# generate_qr_codes.py
from app import create_app, db
from app.models import User
from app.utils.qr_utils import generate_user_qr_code
import os

def generate_all_qr_codes():
    """Generate QR codes for all payee users"""
    app = create_app()
    
    with app.app_context():
        # Get all payee users
        users = User.query.filter_by(role='payee').all()
        
        if not users:
            print("No payee users found!")
            return
        
        print(f"Found {len(users)} payee users")
        print("=" * 50)
        
        success_count = 0
        for user in users:
            print(f"Processing: {user.name} (NIN: {user.nin})")
            try:
                result = generate_user_qr_code(user)
                if result:
                    success_count += 1
                    print(f"  ✅ QR code generated: {result}")
                else:
                    print(f"  ❌ Failed to generate QR code")
            except Exception as e:
                print(f"  ❌ Error: {e}")
            print()
        
        print("=" * 50)
        print(f"✅ QR code generation complete! Generated {success_count} out of {len(users)} QR codes")

if __name__ == "__main__":
    generate_all_qr_codes()