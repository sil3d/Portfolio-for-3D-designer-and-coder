import os
from dotenv import load_dotenv

# Helper to find .env file
base_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.dirname(base_dir) # Go up one level from 'app' to 'portfolio'
load_dotenv(os.path.join(root_dir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfdhdfhjfhjfdhhfjdhjfd'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # Database securely located in instance/ folder (ignored by git, safe from web access)
    # Check for all common Variable names
    database_url = os.environ.get('DATABASE_URL') or \
                   os.environ.get('MYSQL_URL') or \
                   os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url or \
        'sqlite:///' + os.path.join(os.path.dirname(BASE_DIR), 'instance', 'portfolio.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration (still used for temp storage if needed)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2 GB
    
    # Flask-Limiter Configuration
    RATELIMIT_STORAGE_URI = "memory://"

    # Cache Control (1 year)
    SEND_FILE_MAX_AGE_DEFAULT = 31536000
