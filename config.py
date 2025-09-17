from dotenv import load_dotenv
import os
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session configuration for multiple concurrent sessions
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_REFRESH_EACH_REQUEST = True
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'app/static/uploads'
    
    # Mail configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587)) if os.getenv('MAIL_PORT') else 587
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # reCAPTCHA Configuration
    # IMPORTANT: Replace these with your actual reCAPTCHA keys from https://www.google.com/recaptcha/admin
    # The current keys are placeholders and will cause "Invalid key type" errors
    # To fix the "Invalid key type" error:
    # 1. Go to https://www.google.com/recaptcha/admin
    # 2. Create a new site or use existing one
    # 3. Choose reCAPTCHA v2 "I'm not a robot" Checkbox
    # 4. Add your domain (localhost for development)
    # 5. Copy the Site Key and Secret Key
    # 6. Set them as environment variables or replace the defaults below
    RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY') or '6LcrR5ErAAAAAE65v9S8r3Rmxa11X2gYbYXWDIWI'
    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY') or '6LcrR5ErAAAAAGmZ1Zkv0XUKVUQokkhSyHqYT-mu'
    

