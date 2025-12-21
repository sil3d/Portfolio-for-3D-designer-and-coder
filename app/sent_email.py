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

        # Use centralized email logic
        from app.utils import send_mail
        
        success = send_mail(
            subject=f"New Contact: {name}",
            recipient=os.getenv('SMTP_USER'), # Send to self
            body_text=f"Name: {name}\nEmail: {email}\nMessage: {message}",
            body_html=f"<p><strong>Name:</strong> {name}</p><p><strong>Email:</strong> {email}</p><p><strong>Message:</strong><br>{message}</p>",
            reply_to=email,
            sender_name="Portfolio Contact"
        )

        if success:
            return jsonify({'status': 'success', 'message': 'Your message has been sent successfully!'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Failed to send email. Please try again later.'}), 500

    return render_template('contact/contact.html')