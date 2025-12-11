import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hfdhdfhjfhjfdhhfjdhjfd'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    # Database securely located in instance/ folder (ignored by git, safe from web access)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(BASE_DIR), 'instance', 'portfolio.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload configuration (still used for temp storage if needed)
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2 GB
    
    # Flask-Limiter Configuration
    RATELIMIT_STORAGE_URI = "memory://"
