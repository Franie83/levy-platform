# add_qr_to_existing_users.py
from app import create_app, db
from app.models import User
from app.utils.qr_utils import generate_user_qr_code
import sys

def add_qr_codes_to_existing_users():
    """Add QR codes to existing users who don't have them"""
    app = create_app()
    
    with app.app_context():
        # First, check if qr_code column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'qr_code' not in columns:
            print("❌ qr_code column not found! Run add_missing_columns first.")
            return False
        
        # Get all payee users without QR codes
        users = User.query.filter(
            User.role == 'payee',
            (User.qr_code == None) | (User.qr_code == '')
        ).all()
        
        if not users:
            print("✅ All users already have QR codes!")
            return True
        
        print(f"📊 Found {len(users)} users without QR codes")
        print("=" * 50)
        
        success_count = 0
        failed_count = 0
        
        for user in users:
            print(f"Generating QR code for {user.name} (NIN: {user.nin})...")
            try:
                result = generate_user_qr_code(user)
                if result:
                    success_count += 1
                    print(f"  ✅ QR code generated: {result}")
                else:
                    failed_count += 1
                    print(f"  ❌ Failed to generate QR code")
            except Exception as e:
                failed_count += 1
                print(f"  ❌ Error: {e}")
        
        print("=" * 50)
        print(f"✅ Successfully generated QR codes for {success_count} users")
        if failed_count > 0:
            print(f"❌ Failed to generate QR codes for {failed_count} users")
        
        return success_count > 0

def verify_qr_codes():
    """Verify that all payee users have QR codes"""
    app = create_app()
    
    with app.app_context():
        users = User.query.filter_by(role='payee').all()
        
        print("\n📊 QR Code Status:")
        print("=" * 50)
        
        users_with_qr = 0
        users_without_qr = 0
        
        for user in users:
            if user.qr_code:
                users_with_qr += 1
                print(f"✅ {user.name}: {user.qr_code}")
            else:
                users_without_qr += 1
                print(f"❌ {user.name}: NO QR CODE")
        
        print("=" * 50)
        print(f"Total payee users: {len(users)}")
        print(f"With QR codes: {users_with_qr}")
        print(f"Without QR codes: {users_without_qr}")
        
        return users_without_qr == 0

if __name__ == "__main__":
    print("🔧 Adding QR Codes to Existing Users")
    print("=" * 50)
    
    # Add QR codes
    add_qr_codes_to_existing_users()
    
    # Verify
    verify_qr_codes()