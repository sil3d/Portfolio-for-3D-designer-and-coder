from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db, limiter
from app.models import Rating
from sqlalchemy import func
import re
import dns.resolver
import logging

bp = Blueprint('rating', __name__, static_folder='static')

def validate_email(email):
    """Validate email format and domain"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_regex, email):
        return False
    
    domain = email.split('@')[1]
    
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False

@bp.route('/rating', methods=['GET'])
def rating_page():
    """Display rating submission page"""
    return render_template('rating/rating.html')

@bp.route('/rating/submit', methods=['POST'])
@limiter.limit("5 per hour")
def submit_rating():
    """Submit a new rating"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        rating_value = request.form.get('rating')
        
        # Validation
        if not all([name, email, message, rating_value]):
            return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
        
        if not validate_email(email):
            return jsonify({'status': 'error', 'message': 'Invalid email address.'}), 400
        
        try:
            rating_value = int(rating_value)
            if rating_value < 1 or rating_value > 5:
                return jsonify({'status': 'error', 'message': 'Rating must be between 1 and 5 stars.'}), 400
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid rating value.'}), 400
        
        # Create new rating
        new_rating = Rating(
            name=name,
            email=email,
            message=message,
            rating=rating_value
        )
        
        db.session.add(new_rating)
        db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': 'Thank you for your rating! Your feedback is valuable to us.'
        }), 200
        
    except Exception as e:
        logging.error(f"Error submitting rating: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred. Please try again.'}), 500

@bp.route('/rating/average', methods=['GET'])
def get_average_rating():
    """Get average rating and count"""
    try:
        result = db.session.query(
            func.avg(Rating.rating).label('average'),
            func.count(Rating.id).label('count')
        ).first()
        
        average = float(result.average) if result.average else 0
        count = result.count if result.count else 0
        
        return jsonify({
            'average': round(average, 2),
            'count': count,
            'stars': round(average * 2) / 2  # Round to nearest 0.5
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting average rating: {str(e)}")
        return jsonify({'average': 0, 'count': 0, 'stars': 0}), 500

@bp.route('/rating/all', methods=['GET'])
def get_all_ratings():
    """Get all ratings (for admin or public display)"""
    try:
        ratings = Rating.query.order_by(Rating.date.desc()).limit(50).all()
        
        ratings_list = [{
            'id': r.id,
            'name': r.name,
            'message': r.message,
            'rating': r.rating,
            'date': r.date.strftime('%Y-%m-%d %H:%M')
        } for r in ratings]
        
        return jsonify({'ratings': ratings_list}), 200
        
    except Exception as e:
        logging.error(f"Error getting ratings: {str(e)}")
        return jsonify({'ratings': []}), 500
