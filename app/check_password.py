from flask import (Blueprint, Response, redirect, url_for,
                   request, session, render_template, abort)
# from functools import wraps # No longer needed
from app.extensions import db, limiter
from app.security_alerts import send_security_alert
from flask_login import login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import check_password_hash
from app.models import Admin, TwoFactor

# Charger les variables d'environnement
load_dotenv(".env")
LOGIN_SECRET_KEY = os.getenv("LOGIN_SECRET_KEY")

bp = Blueprint('ckeck_password', __name__, static_folder='static')

def send_verification_email(recipient_email, verification_code):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')

    message = MIMEMultipart()
    message['From'] = smtp_user
    message['To'] = recipient_email
    message['Subject'] = 'Your Verification Code'

    body = f'Your verification code is {verification_code}.'
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

@bp.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('ckeck_password.upload_page'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = Admin.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Generate verification code
            verification_code = str(random.randint(100000, 999999))
            
            # Store temp user id in session for 2FA step
            session['pre_2fa_user_id'] = user.id

            new_2fa = TwoFactor(user_id=user.id, verification_code=verification_code)
            db.session.add(new_2fa)
            db.session.commit()
            
            send_verification_email(username, verification_code)
            return redirect(url_for('ckeck_password.verify_code'))
        else:
            send_security_alert("Failed Admin Login", f"Username: {username}\nAction: Password check failed.")
            return redirect(url_for('ckeck_password.unauthorized'))
            
    return render_template('login.html')

@bp.route('/login/<secret_key>', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login(secret_key):
    if secret_key != os.getenv('LOGIN_SECRET_KEY'):
        abort(404)
        
    if request.method == 'POST':
        # Same logic as admin_login, redirecting to verify_code
        return admin_login()
    
    return render_template('login.html')

@bp.route('/verify_code', methods=['GET', 'POST'])
@limiter.limit("5 per minute") 
def verify_code():
    if 'pre_2fa_user_id' not in session:
        return redirect(url_for('ckeck_password.admin_login'))

    if request.method == 'POST':
        user_code = request.form['verification_code']
        user_id = session['pre_2fa_user_id']

        # Check for valid, unverified code for THIS user
        verification_record = TwoFactor.query.filter_by(
            user_id=user_id, 
            verification_code=user_code, 
            is_verified=False
        ).first()
        
        if verification_record:
            verification_record.is_verified = True
            db.session.commit()
            
            # Log the user in officially
            user = db.session.get(Admin, user_id)
            if user:
                login_user(user)
                session.pop('pre_2fa_user_id', None) # Clear temp session
                return redirect(url_for('ckeck_password.upload_page'))
            
        return redirect(url_for('ckeck_password.unauthorized'))
    
    return render_template('code_check/verify_code.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/upload-page')
@login_required
def upload_page():
    return render_template('upload.html')

@bp.route('/unauthorized')
def unauthorized():
    return render_template('code_check/unauthorized.html')
