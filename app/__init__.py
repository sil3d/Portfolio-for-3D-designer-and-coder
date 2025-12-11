from flask import Flask, render_template
from app.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    app.config.from_object(Config)
    
    # Initialize Extensions
    from app.extensions import db, login_manager, limiter, csrf
    db.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'ckeck_password.admin_login' # Redirect here if not logged in
    login_manager.login_message_category = 'warning'

    # Configuration des fichiers
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = {'glb', 'zip', 'png', 'jpg'}
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

    # Error Handlers & Security Alerts
    from flask_wtf.csrf import CSRFError
    from app.security_alerts import send_security_alert
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        send_security_alert("CSRF Violation", f"Reason: {e.description}")
        return render_template('code_check/unauthorized.html'), 400

    @app.errorhandler(429)
    def ratelimit_handler(e):
        send_security_alert("Rate Limit Exceeded", f"Limit Hit: {e.description}")
        return render_template('code_check/unauthorized.html'), 429

    @app.errorhandler(500)
    def internal_error(e):
        # Optional: Alert on 500s too if desired, but can be noisy. 
        # User asked for "violations", mostly implies security. 
        # But 500 could be a crash from an exploit attempt.
        # Let's keep it safe and just log for now or alert if critical.
        return "Internal Server Error", 500

    # Importer et enregistrer les blueprints
    from app import (routes, subscribe, admin_management, sent_email, check_password, rating_routes)
    
    app.register_blueprint(routes.bp)
    app.register_blueprint(admin_management.bp)
    app.register_blueprint(check_password.bp)
    app.register_blueprint(sent_email.bp)
    app.register_blueprint(subscribe.bp)
    app.register_blueprint(rating_routes.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()

    return app
