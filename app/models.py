from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

# db is initialized in extensions.py

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship for 2FA
    two_factor = db.relationship('TwoFactor', backref='user', uselist=False)

class TwoFactor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    verification_code = db.Column(db.String(10))
    is_verified = db.Column(db.Boolean, default=False)

class File(db.Model):
    __tablename__ = 'files'
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    file_name = db.Column(db.String(255), nullable=False)
    
    # Binary Storage
    banner_path = db.Column(db.LargeBinary, nullable=False)
    banner_mimetype = db.Column(db.String(50))
    file_path_glb = db.Column(db.LargeBinary, nullable=False)
    file_path_glb_mimetype = db.Column(db.String(50))
    file_path_zip = db.Column(db.LargeBinary, nullable=False)
    file_path_zip_mimetype = db.Column(db.String(50))
    
    added_by = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(255))
    year = db.Column(db.Integer)
    
    # Counters
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)

    # Relationships
    gallery_images = db.relationship('GalleryFile', backref='file', lazy=True)
    comments = db.relationship('Comment', backref='file', lazy=True)
    likes = db.relationship('Like', backref='file', lazy=True)
    downloads = db.relationship('Download', backref='file', lazy=True)

class GalleryFile(db.Model):
    __tablename__ = 'gallery_files'
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    file_path = db.Column(db.LargeBinary, nullable=False)
    images_mimetype = db.Column(db.String(50))

class Download(db.Model):
    __tablename__ = 'downloads'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    location = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint for like per user per file
    __table_args__ = (db.UniqueConstraint('email', 'file_id', name='unique_like'),)

class HDRI(db.Model):
    __tablename__ = 'hdri'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.LargeBinary, nullable=False)
    file_path_mimetype = db.Column(db.String(50))
    preview_path = db.Column(db.LargeBinary, nullable=False)
    preview_path_mimetype = db.Column(db.String(50))

class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    video_id = db.Column(db.String(255), nullable=False)

class Subscriber(db.Model):
    __tablename__ = 'subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)

# New model for Accomplishments
class Accomplishment(db.Model):
    __tablename__ = 'accomplishments'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(100)) # e.g. "2024 - Present" or "Jan 2023"
    category = db.Column(db.String(100)) # 'Education', 'Work', 'Award'
    link = db.Column(db.String(255)) # Optional link to certificate or project

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __init__(self, **kwargs):
        super(Rating, self).__init__(**kwargs)
        # Validate rating is between 1 and 5
        if self.rating is not None and (self.rating < 1 or self.rating > 5):
            raise ValueError("Rating must be between 1 and 5")