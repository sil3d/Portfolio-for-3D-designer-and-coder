import sys
import os
from sqlalchemy import text, inspect

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db

def clean_database():
    app = create_app()
    with app.app_context():
        db_url = str(db.engine.url)
        print(f"Database URL detected: {db_url}")

        if 'sqlite' in db_url:
            print("Detected SQLite. Running VACUUM...")
            try:
                # VACUUM cannot be executed inside a transaction block in some drivers
                # Using raw connection to ensure auto-commit behavior or outside-transaction execution
                with db.engine.connect() as conn:
                    # For SQLAlchemy with SQLite, we might need isolation_level="AUTOCOMMIT"
                    conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("VACUUM"))
                print("VACUUM completed successfully.")
            except Exception as e:
                print(f"Error during VACUUM: {e}")
                # Fallback to raw connection if SQLAlchemy fails
                try:
                    raw_conn = db.engine.raw_connection()
                    cursor = raw_conn.cursor()
                    cursor.execute("VACUUM")
                    cursor.close()
                    raw_conn.close()
                    print("VACUUM completed successfully (via raw connection).")
                except Exception as e2:
                    print(f"Raw connection fallback also failed: {e2}")

        elif 'mysql' in db_url or 'mariadb' in db_url:
            print("Detected MySQL/MariaDB. Running OPTIMIZE TABLE on all tables...")
            try:
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
                
                with db.engine.connect() as conn:
                    for table in tables:
                        print(f"Optimizing table: {table}")
                        conn.execute(text(f"OPTIMIZE TABLE `{table}`"))
                print("Optimization completed successfully.")
            except Exception as e:
                print(f"Error during MySQL optimization: {e}")

        elif 'postgresql' in db_url:
            print("Detected PostgreSQL. Running VACUUM FULL...")
            try:
                with db.engine.connect() as conn:
                    # PostgreSQL VACUUM also cannot run inside a transaction block
                    conn.execution_options(isolation_level="AUTOCOMMIT").execute(text("VACUUM FULL"))
                print("VACUUM FULL completed successfully.")
            except Exception as e:
                print(f"Error during PostgreSQL VACUUM: {e}")

        else:
            print("Unknown database type. No optimization performed.")

if __name__ == '__main__':
    clean_database()
