from flask import Blueprint, render_template, request, jsonify
import re
import dns.resolver
from app.models import db, Subscriber
import logging

bp = Blueprint('subscribe',__name__,static_folder='static')

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False
    
    domain = email.split('@')[1]
    
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

@bp.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if request.method == 'POST':
        email = request.form['email']
        if not validate_email(email):
            return jsonify({'status': 'error', 'message': 'Invalid email address.'}), 400

        try:
            # Check if already subscribed
            existing = Subscriber.query.filter_by(email=email).first()
            if existing:
                return jsonify({'status': 'error', 'message': 'Email is already subscribed.'}), 400

            new_sub = Subscriber(email=email)
            db.session.add(new_sub)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Successfully subscribed!'}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error subscribing: {e}")
            return jsonify({'status': 'error', 'message': 'An error occurred.'}), 500

    return render_template('subscribe/subscribe.html')

@bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    email = request.form['email']

    try:
        subscriber = Subscriber.query.filter_by(email=email).first()
        if subscriber:
            db.session.delete(subscriber)
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Successfully unsubscribed!'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Email not found in subscription list.'}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error unsubscribing: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred.'}), 500
