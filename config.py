import os 
from dotenv import load_dotenv 
 
load_dotenv() 
 
class Config: 
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production' 
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///levy_platform.db' 
    SQLALCHEMY_TRACK_MODIFICATIONS = False 
    UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads') 
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Base URL for generating QR codes (change this for production)
    BASE_URL = os.environ.get('BASE_URL') or 'http://localhost:5000'
    
    # Disable CSRF for testing (enable in production)
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'False').lower() == 'true'
    
    # Payment settings (if using Paystack)
    PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
    
    # Email settings (if using email notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # Session settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    
    # Application settings
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
    
    # Pagination settings
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', 20))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    # Override BASE_URL for production
    BASE_URL = os.environ.get('BASE_URL', 'https://yourdomain.com')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)