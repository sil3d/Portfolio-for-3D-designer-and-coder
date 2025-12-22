from app import create_app
from app.extensions import db
from sqlalchemy import text
from termcolor import colored

app = create_app()

def upgrade_schema():
    with app.app_context():
        try:
            # Check if we are using MySQL
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'mysql' not in db_uri.lower():
                print(colored("⚠️  This script is intended for MySQL databases. Skipping...", "yellow"))
                return

            print(colored("🚀 Upgrading MySQL schema to support large files (LONGBLOB)...", "cyan"))

            # List of ALTER TABLE commands
            commands = [
                "ALTER TABLE files MODIFY banner_path LONGBLOB NULL",
                "ALTER TABLE files MODIFY file_path_glb LONGBLOB NULL",
                "ALTER TABLE files MODIFY file_path_zip LONGBLOB NULL",
                "ALTER TABLE gallery_files MODIFY file_path LONGBLOB NOT NULL",
                "ALTER TABLE hdri MODIFY file_path LONGBLOB NULL",
                "ALTER TABLE hdri MODIFY preview_path LONGBLOB NULL"
            ]

            for cmd in commands:
                print(colored(f"   Executing: {cmd}", "white"))
                db.session.execute(text(cmd))
            
            db.session.commit()
            print(colored("\n✅ Schema upgraded successfully! You can now upload large 3D models and HDRIs.", "green", attrs=['bold']))

        except Exception as e:
            print(colored(f"\n❌ Failed to upgrade schema: {str(e)}", "red", attrs=['bold']))
            db.session.rollback()

if __name__ == "__main__":
    upgrade_schema()
