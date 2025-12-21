from app import create_app
from flask import render_template
from sqlalchemy import text
from app.extensions import db
from termcolor import colored
import sys

app = create_app()

def check_db_connection():
    with app.app_context():
        try:
            # Check what DB we are actually connected to
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            db_type = "MySQL" if "mysql" in db_uri else "SQLite" if "sqlite" in db_uri else "PostgreSQL" if "postgresql" in db_uri else "Unknown"
            
            # Perform a test query
            db.session.execute(text('SELECT 1'))
            
            print(colored(f"\n✅ SUCCESSFULLY CONNECTED TO DATABASE: {db_type}", 'green', attrs=['bold']))
            print(colored(f"   URI: {db_uri.split('@')[-1] if '@' in db_uri else db_uri}\n", 'green')) # Hide password if present
            
        except Exception as e:
            print(colored(f"\n❌ DATABASE CONNECTION FAILED", 'red', attrs=['bold']))
            print(colored(f"   Error: {str(e)}\n", 'red'))
            # sys.exit(1) # Optional: Stop server if DB fails

def check_email_config():
    """Check and display Email configuration on startup."""
    import os
    provider = os.getenv('EMAIL_PROVIDER', 'smtp').upper()
    print(colored(f"\n📧 EMAIL SYSTEM: {provider}", 'cyan', attrs=['bold']))
    
    if provider == 'RESEND':
        key = os.getenv('RESEND_API_KEY')
        if not key:
             print(colored("   ⚠️  RESEND_API_KEY is missing via env vars!", 'yellow'))
        else:
             print(colored("   ✅ API Key loaded", 'green'))
             
    elif provider == 'SMTP':
        # Check specific clouds that block SMTP
        if os.getenv('RAILWAY_ENVIRONMENT'):
            print(colored("   ⚠️  WARNING: You are on Railway which blocks SMTP port 587.", 'yellow'))
            print(colored("   👉 Switch to 'EMAIL_PROVIDER=resend' in variables.", 'yellow'))
        else:
            print(colored("   ✅ Standard SMTP mode ready", 'green'))


# Définir une route pour les erreurs 404
@app.errorhandler(404)
def page_not_found(e):
    # Render a custom 404 page
    return render_template('404.html'), 404

if __name__ == "__main__":
    check_db_connection()
    check_email_config()
    app.run(debug=True)