import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import request

def send_security_alert(alert_type, details):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    # Send to the admin (same as sender in this config, or can be configured)
    recipient = smtp_user 

    message = MIMEMultipart()
    message['From'] = smtp_user
    message['To'] = recipient
    message['Subject'] = f'SECURITY ALERT: {alert_type}'

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
    
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        print(f"Security Alert ({alert_type}) sent to {recipient}")
    except Exception as e:
        print(f"Failed to send security alert: {str(e)}")
