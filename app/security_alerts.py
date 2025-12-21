import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import request

def send_security_alert(alert_type, details):
    from app.utils import send_mail
    recipient = os.getenv('SMTP_USER') 
    
    ip_address = request.remote_addr
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    body = f"""
    SECURITY VIOLATION DETECTED
    ===========================
    Type: {alert_type}
    Time: {timestamp}
    IP Address: {ip_address}
    
    Details:
    {details}
    
    User Agent: {request.headers.get('User-Agent')}
    Path: {request.path}
    Method: {request.method}
    """
    
    success = send_mail(
        subject=f'SECURITY ALERT: {alert_type}',
        recipient=recipient,
        body_text=body,
        sender_name="Portfolio Security"
    )
    
    if success:
        print(f"Security Alert ({alert_type}) sent to {recipient}")
    else:
        print(f"Failed to send security alert: {alert_type}")
