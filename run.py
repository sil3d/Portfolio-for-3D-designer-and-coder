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

# Définir une route pour les erreurs 404
@app.errorhandler(404)
def page_not_found(e):
    # Render a custom 404 page
    return render_template('404.html'), 404

if __name__ == "__main__":
    check_db_connection()
    app.run(debug=True)