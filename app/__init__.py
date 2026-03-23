from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager, current_user
import os 
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy() 
login_manager = LoginManager() 

def create_app(config_class=None): 
    app = Flask(__name__) 

    if config_class: 
        app.config.from_object(config_class) 
    else: 
        # Load from config.py
        from config import get_config
        app.config.from_object(get_config())
    
    # Ensure upload directories exist 
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(os.path.join(upload_folder, 'qrcodes'), exist_ok=True) 
    os.makedirs(os.path.join(upload_folder, 'qrcodes', 'users'), exist_ok=True)
    os.makedirs(os.path.join(upload_folder, 'violations'), exist_ok=True) 
    os.makedirs(os.path.join(upload_folder, 'profiles'), exist_ok=True) 
    os.makedirs(os.path.join(upload_folder, 'businesses'), exist_ok=True) 
    os.makedirs(os.path.join(upload_folder, 'vehicles'), exist_ok=True) 

    db.init_app(app) 
    login_manager.init_app(app) 

    login_manager.login_view = 'auth.login' 
    login_manager.login_message = 'Please log in to access this page.' 
    login_manager.login_message_category = 'info'

    # Setup logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/levy_platform.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Levy Platform startup')

    # Register blueprints 
    from app.routes import auth, main, business, vehicle, payment, enforcement, simple, admin 

    app.register_blueprint(auth.bp) 
    app.register_blueprint(main.bp) 
    app.register_blueprint(business.bp) 
    app.register_blueprint(vehicle.bp) 
    app.register_blueprint(payment.bp) 
    app.register_blueprint(enforcement.bp) 
    app.register_blueprint(simple.bp) 
    app.register_blueprint(admin.bp) 

    # Add template context processors
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return dict(datetime=datetime)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    # Add before request handler to check for suspended users
    @app.before_request
    def before_request():
        # Skip login page, static files, and public routes
        public_endpoints = ['auth.login', 'static', 'auth.logout', 'auth.api_check_status']
        
        if request.endpoint in public_endpoints:
            return None
        
        # Check if user is suspended
        if current_user.is_authenticated and hasattr(current_user, 'status') and current_user.status == 'suspended':
            # Don't allow suspended users to access any page except logout
            if request.endpoint != 'auth.logout':
                flash('Your account has been suspended. Please contact support.', 'danger')
                return redirect(url_for('auth.logout'))
        
        return None

    return app

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))

# Create tables function
def create_tables(app):
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

# Add missing columns to users table
def add_missing_columns(app):
    """Add missing suspension and QR code columns to users table"""
    from sqlalchemy import text
    
    with app.app_context():
        inspector = db.inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add missing suspension columns
            if 'suspended_at' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN suspended_at DATETIME'))
                print("✅ Added suspended_at column")
            
            if 'suspended_by' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN suspended_by INTEGER REFERENCES users(id)'))
                print("✅ Added suspended_by column")
            
            if 'unsuspended_at' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN unsuspended_at DATETIME'))
                print("✅ Added unsuspended_at column")
            
            if 'unsuspended_by' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN unsuspended_by INTEGER REFERENCES users(id)'))
                print("✅ Added unsuspended_by column")
            
            if 'suspension_reason' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN suspension_reason TEXT'))
                print("✅ Added suspension_reason column")
            
            # Add QR code column
            if 'qr_code' not in columns:
                db.session.execute(text('ALTER TABLE users ADD COLUMN qr_code VARCHAR(200)'))
                print("✅ Added qr_code column")
            
            db.session.commit()
            print("✅ Database columns updated successfully!")

# Add QR codes to existing users
def add_qr_codes_to_existing_users(app):
    """Add QR codes to existing payee users"""
    from app.models import User
    from app.utils.qr_utils import generate_user_qr_code
    
    with app.app_context():
        # Get all payee users without QR codes
        users = User.query.filter(
            User.role == 'payee',
            (User.qr_code == None) | (User.qr_code == '')
        ).all()
        
        if not users:
            print("✅ All users already have QR codes!")
            return True
        
        print(f"📊 Found {len(users)} users without QR codes")
        success_count = 0
        
        for user in users:
            try:
                result = generate_user_qr_code(user)
                if result:
                    success_count += 1
                    print(f"  ✅ QR code generated for {user.name}")
                else:
                    print(f"  ❌ Failed to generate QR code for {user.name}")
            except Exception as e:
                print(f"  ❌ Error for {user.name}: {e}")
        
        print(f"✅ Generated QR codes for {success_count} out of {len(users)} users")
        return success_count > 0

# Initialize database with sample data
def init_db(app):
    """Initialize database with sample data"""
    from app.models import User, Business, Vehicle, LevyType, BusinessType, VehicleType
    
    with app.app_context():
        # First, add missing columns
        add_missing_columns(app)
        
        # Check if we already have data
        existing_users = User.query.first()
        
        if existing_users:
            print("Database already has data. Adding QR codes to existing users...")
            add_qr_codes_to_existing_users(app)
            return
        
        # Create admin user
        admin = User(
            name="System Administrator",
            nin="00000000001",
            email="admin@levyplatform.com",
            phone="08000000001",
            role="super_admin",
            category=None,
            status="active"
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        
        # Create enforcer user
        enforcer = User(
            name="Enforcer User",
            nin="00000000002",
            email="enforcer@levyplatform.com",
            phone="08000000002",
            role="enforcer",
            category=None,
            status="active"
        )
        enforcer.set_password("Enforcer@123")
        db.session.add(enforcer)
        
        # Create MSME user
        msme = User(
            name="MSME Business Owner",
            nin="00000000003",
            email="msme@example.com",
            phone="08000000003",
            role="payee",
            category="MSME",
            status="active"
        )
        msme.set_password("MSME@123")
        db.session.add(msme)
        
        # Create Transporter user
        transporter = User(
            name="Transporter User",
            nin="00000000004",
            email="transporter@example.com",
            phone="08000000004",
            role="payee",
            category="Transporter",
            status="active"
        )
        transporter.set_password("Trans@123")
        db.session.add(transporter)
        
        db.session.commit()
        
        # Create levy types
        levy_types = [
            LevyType(name="Business Levy", amount=5000, description="Annual business registration levy", is_active=True),
            LevyType(name="Vehicle Levy", amount=3000, description="Annual vehicle registration levy", is_active=True),
            LevyType(name="Special Levy", amount=10000, description="Special development levy", is_active=True)
        ]
        
        for levy in levy_types:
            db.session.add(levy)
        
        # Create business types
        business_types = [
            BusinessType(name="Retail", description="Retail business", amount=5000, is_active=True),
            BusinessType(name="Wholesale", description="Wholesale business", amount=8000, is_active=True),
            BusinessType(name="Services", description="Service provider", amount=4000, is_active=True),
            BusinessType(name="Manufacturing", description="Manufacturing business", amount=10000, is_active=True)
        ]
        
        for bt in business_types:
            db.session.add(bt)
        
        # Create vehicle types
        vehicle_types = [
            VehicleType(name="Car", description="Passenger car", amount=3000, is_active=True),
            VehicleType(name="SUV", description="Sports Utility Vehicle", amount=5000, is_active=True),
            VehicleType(name="Bus", description="Public transport bus", amount=8000, is_active=True),
            VehicleType(name="Truck", description="Commercial truck", amount=10000, is_active=True),
            VehicleType(name="Motorcycle", description="Two-wheeler", amount=1000, is_active=True)
        ]
        
        for vt in vehicle_types:
            db.session.add(vt)
        
        db.session.commit()
        
        # Generate QR codes for users
        try:
            from app.utils.qr_utils import generate_all_user_qr_codes
            generate_all_user_qr_codes()
            print("✅ QR codes generated for all users")
        except ImportError:
            print("⚠️ QR utils not found. QR code generation skipped.")
        except Exception as e:
            print(f"⚠️ Error generating QR codes: {e}")
        
        print("=" * 50)
        print("Database initialized with sample data!")
        print("=" * 50)
        print("\n📊 Default Users:")
        print("  Admin: NIN=00000000001, Password=Admin@123")
        print("  Enforcer: NIN=00000000002, Password=Enforcer@123")
        print("  MSME: NIN=00000000003, Password=MSME@123")
        print("  Transporter: NIN=00000000004, Password=Trans@123")
        print("\n💰 Levy Types Created:")
        for levy in levy_types:
            print(f"  - {levy.name}: ₦{levy.amount}")
        print("\n🏢 Business Types Created:")
        for bt in business_types:
            print(f"  - {bt.name}: ₦{bt.amount}")
        print("\n🚗 Vehicle Types Created:")
        for vt in vehicle_types:
            print(f"  - {vt.name}: ₦{vt.amount}")
        print("\n" + "=" * 50)
        print("✅ Database initialization complete!")
        print("=" * 50)

# Reset database function (for development)
def reset_db(app):
    """Reset database - DANGER: This will delete all data!"""
    with app.app_context():
        confirm = input("Are you sure you want to reset the database? This will delete ALL data! (yes/no): ")
        if confirm.lower() == 'yes':
            db.drop_all()
            db.create_all()
            print("Database reset successfully!")
            init_db(app)
        else:
            print("Database reset cancelled.")