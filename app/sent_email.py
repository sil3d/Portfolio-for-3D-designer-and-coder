from flask import Flask,Blueprint, render_template, request, redirect, url_for, flash, jsonify
import smtplib
import re
import dns.resolver
import os

bp = Blueprint('send_email',__name__,static_folder='static')

def validate_email(email):
    # Expression régulière pour une validation de base
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, email):
        return False
    
    domain = email.split('@')[1]
    
    try:
        # Vérifier l'existence du domaine en effectuant une requête DNS pour les enregistrements MX
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        if not validate_email(email):
            return jsonify({'status': 'error', 'message': 'Invalid email address.'}), 400

        # Email Provider Logic
        email_provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()

        if email_provider == 'resend':
            import resend
            try:
                api_key = os.getenv('RESEND_API_KEY')
                if not api_key:
                     return jsonify({'status': 'error', 'message': 'Resend API Key missing.'}), 500
                
                print("DEBUG: Sending via Resend API...", flush=True)
                resend.api_key = api_key
                
                # Resend requires a verified sender domain or 'onboarding@resend.dev' for testing
                # User needs to verify their domain in Resend dashboard
                sender_email = "onboarding@resend.dev" # Default for testing, User should change this
                
                params = {
                    "from": f"Portfolio Contact <{sender_email}>",
                    "to": [os.getenv('SMTP_USER')], # Send to self
                    "subject": f"New Contact: {name}",
                    "html": f"<p><strong>Name:</strong> {name}</p><p><strong>Email:</strong> {email}</p><p><strong>Message:</strong><br>{message}</p>",
                    "reply_to": email
                }

                email_req = resend.Emails.send(params)
                print(f"DEBUG: Resend response: {email_req}", flush=True)
                return jsonify({'status': 'success', 'message': 'Message sent (Resend)!'}), 200

            except Exception as e:
                 print(f"ERROR: Resend failed: {e}", flush=True)
                 return jsonify({'status': 'error', 'message': f'Resend Error: {str(e)}'}), 500

        else: 
            # Default SMTP (Gmail, etc.)
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_password = os.getenv('SMTP_PASSWORD')

            try:
                print(f"DEBUG: Connecting to SMTP {smtp_server}:{smtp_port}...", flush=True)
                
                # Force IPv4 Resolution to avoid IPv6 timeouts
                import socket
                raw_ip = socket.getaddrinfo(smtp_server, smtp_port, family=socket.AF_INET, proto=socket.IPPROTO_TCP)[0][4][0]
                print(f"DEBUG: Resolved {smtp_server} to IPv4: {raw_ip}", flush=True)

                with smtplib.SMTP(raw_ip, smtp_port, timeout=10) as server:
                    print("DEBUG: Connection established. Starting TLS...", flush=True)
                    server.starttls()
                    print("DEBUG: TLS started. Logging in...", flush=True)
                    server.login(smtp_user, smtp_password)
                    print("DEBUG: Logged in. Sending mail...", flush=True)
                    subject = f"New Contact Form Submission from {name}"
                    body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
                    message = f"Subject: {subject}\n\n{body}"
                    server.sendmail(smtp_user, smtp_user, message)
                    print("DEBUG: Mail sent successfully.", flush=True)
                    return jsonify({'status': 'success', 'message': 'Your message has been sent successfully!'}), 200
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'An error occurred: {e}'}), 500

    return render_template('contact/contact.html')