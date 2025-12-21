import io
import gzip
import requests
import base64
import logging
import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_mail(subject, recipient, body_text, body_html=None, reply_to=None, sender_name=None):
    """
    Centralized function to send emails via SMTP or Resend API.
    Determined by the EMAIL_PROVIDER environment variable.
    """
    provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()
    smtp_user = os.getenv('SMTP_USER')
    
    if provider == 'resend':
        import resend
        try:
            api_key = os.getenv('RESEND_API_KEY')
            if not api_key:
                logging.error("Resend API Key missing.")
                return False
            
            resend.api_key = api_key
            sender_email = "onboarding@resend.dev" # Default for testing
            # If user has a verified domain, they should update this via env or similar
            
            from_field = f"{sender_name or 'Portfolio'} <{sender_email}>"
            
            params = {
                "from": from_field,
                "to": [recipient],
                "subject": subject,
                "text": body_text,
            }
            if body_html:
                params["html"] = body_html
            if reply_to:
                params["reply_to"] = reply_to
            
            resend.Emails.send(params)
            logging.info(f"Email sent via Resend to {recipient}")
            return True
        except Exception as e:
            logging.error(f"Resend failed: {e}")
            return False
            
    else: # Default to SMTP
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        try:
            # Force IPv4 Resolution to avoid IPv6 timeouts
            raw_ip = socket.getaddrinfo(smtp_server, smtp_port, family=socket.AF_INET, proto=socket.IPPROTO_TCP)[0][4][0]
            
            message = MIMEMultipart()
            message['From'] = f"{sender_name or 'Portfolio'} <{smtp_user}>"
            message['To'] = recipient
            message['Subject'] = subject
            if reply_to:
                message['Reply-To'] = reply_to
            
            message.attach(MIMEText(body_text, 'plain'))
            if body_html:
                message.attach(MIMEText(body_html, 'html'))
                
            with smtplib.SMTP(raw_ip, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(message)
            
            logging.info(f"Email sent via SMTP to {recipient}")
            return True
        except Exception as e:
            logging.error(f"SMTP failed: {e}")
            return False

def compress_file(data):
    """Compresses file data using GZIP."""
    if not data:
        return None
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode='wb') as f:
        f.write(data)
    return out.getvalue()

def decompress_file(data):
    """Decompresses GZIP compressed file data."""
    if not data:
        return b""
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(data), mode='rb') as f:
            return f.read()
    except Exception as e:
        print(f"Error decompressing file: {e}")
        return data  # Return original if not compressed

def get_location_from_ip(ip_address):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'fail':
            return 'Unknown Location'
        
        city = data.get('city', 'Unknown')
        region = data.get('regionName', 'Unknown')
        country = data.get('country', 'Unknown')
        location = f"{city}, {region}, {country}"
        
        return location
    
    except requests.RequestException as e:
        print(f"Error retrieving location: {e}")
        return 'Unknown Location'

def allowed_file(filename, allowed_extensions):
    """Vérifie si le fichier a une extension autorisée."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def to_base32(string):
    return base64.b32encode(string.encode()).decode().rstrip('=')
