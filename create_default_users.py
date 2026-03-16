from app import create_app, db 
from app.models import User 
from datetime import datetime 
 
app = create_app() 
with app.app_context(): 
    # Clear existing users (optional - remove if you want to keep existing users) 
    # Uncomment the next line if you want to start fresh 
    # db.drop_all() 
    db.create_all() 
 
    # Create default users if they don't exist 
    default_users = [ 
        { 
            'name': 'Super Admin', 
            'email': 'admin@levy.gov', 
            'phone': '08000000001', 
            'nin': '00000000001', 
            'password': 'Admin@123', 
            'role': 'super_admin', 
            'category': None, 
            'status': 'active' 
        }, 
        { 
            'name': 'Enforcer User', 
            'email': 'enforcer@levy.gov', 
            'phone': '08000000002', 
            'nin': '00000000002', 
            'password': 'Enforcer@123', 
            'role': 'enforcer', 
            'category': None, 
            'status': 'active' 
        }, 
        { 
            'name': 'MSME Business Owner', 
            'email': 'business@example.com', 
            'phone': '08000000003', 
            'nin': '00000000003', 
            'password': 'MSME@123', 
            'role': 'payee', 
            'category': 'MSME', 
            'status': 'active' 
        }, 
        { 
            'name': 'Transporter Vehicle Owner', 
            'email': 'transporter@example.com', 
            'phone': '08000000004', 
            'nin': '00000000004', 
            'password': 'Trans@123', 
            'role': 'payee', 
            'category': 'Transporter', 
            'status': 'active' 
        }, 
        { 
            'name': 'Test Payee', 
            'email': 'test@example.com', 
            'phone': '08000000005', 
            'nin': '12345678901', 
            'password': 'password123', 
            'role': 'payee', 
            'category': 'MSME', 
            'status': 'active' 
        } 
    ] 
 
    for user_data in default_users: 
        # Check if user already exists 
        existing_user = User.query.filter_by(nin=user_data['nin']).first() 
        if not existing_user: 
            user = User( 
                name=user_data['name'], 
                email=user_data['email'], 
                phone=user_data['phone'], 
                nin=user_data['nin'], 
                role=user_data['role'], 
                category=user_data['category'], 
                status=user_data['status'] 
            ) 
            user.set_password(user_data['password']) 
            db.session.add(user) 
            print(f"? Created user: {user_data['name']} ({user_data['role']})") 
        else: 
            print(f"?? User already exists: {user_data['name']}") 
 
    db.session.commit() 
