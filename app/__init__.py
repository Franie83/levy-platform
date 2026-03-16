from flask import Flask 
from flask_sqlalchemy import SQLAlchemy 
from flask_login import LoginManager 
import os 
 
db = SQLAlchemy() 
login_manager = LoginManager() 
 
def create_app(config_class=None): 
    app = Flask(__name__) 
 
    if config_class: 
        app.config.from_object(config_class) 
    else: 
        app.config.from_object('config.Config') 
 
    # Disable CSRF for testing 
    app.config['WTF_CSRF_ENABLED'] = False 
 
    # Ensure upload directories exist 
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'qrcodes'), exist_ok=True) 
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'violations'), exist_ok=True) 
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profiles'), exist_ok=True) 
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'businesses'), exist_ok=True) 
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'vehicles'), exist_ok=True) 
 
    db.init_app(app) 
    login_manager.init_app(app) 
 
    login_manager.login_view = 'auth.login' 
    login_manager.login_message = 'Please log in to access this page.' 
 
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
 
    return app 
