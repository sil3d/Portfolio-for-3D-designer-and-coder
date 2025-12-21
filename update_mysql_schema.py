import os
import mysql.connector
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
base_dir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(base_dir, '.env'))

def get_mysql_connection():
    database_url = os.environ.get('DATABASE_URL') or \
                   os.environ.get('MYSQL_URL') or \
                   os.environ.get('SQLALCHEMY_DATABASE_URI')
    
    if not database_url:
        print("No database URL found in environment variables.")
        return None

    if database_url.startswith('mysql://'):
        # Parse mysql://user:password@host:port/database
        result = urlparse(database_url)
        username = result.username
        password = result.password
        database = result.path.lstrip('/')
        hostname = result.hostname
        port = result.port or 3306
        
        try:
            conn = mysql.connector.connect(
                host=hostname,
                user=username,
                password=password,
                database=database,
                port=port
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Error connecting to MySQL: {err}")
            return None
    else:
        print(f"URL is not a MySQL connection string: {database_url}")
        return None

def update_schema():
    conn = get_mysql_connection()
    if not conn:
        return

    cursor = conn.cursor()
    
    # Define columns to add
    columns_to_add = {
        'files': [
            ('banner_url', 'VARCHAR(500)'),
            ('file_path_glb_url', 'VARCHAR(500)'),
            ('file_path_zip_url', 'VARCHAR(500)')
        ],
        'hdri': [
            ('file_path_url', 'VARCHAR(500)'),
            ('preview_path_url', 'VARCHAR(500)')
        ]
    }

    # Define columns to resize to LONGBLOB
    columns_to_resize = {
        'files': ['banner_path', 'file_path_glb', 'file_path_zip'],
        'gallery_files': ['file_path'],
        'hdri': ['file_path', 'preview_path']
    }

    try:
        # Add missing columns
        for table, cols in columns_to_add.items():
            print(f"Checking missing columns for table: {table}")
            cursor.execute(f"DESCRIBE {table}")
            existing_cols = [row[0] for row in cursor.fetchall()]
            
            for col_name, col_type in cols:
                if col_name not in existing_cols:
                    print(f"Adding column {col_name} to {table}...")
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        print(f"Column {col_name} added.")
                    except mysql.connector.Error as e:
                        print(f"Error adding {col_name}: {e}")
                else:
                    print(f"Column {col_name} already exists in {table}.")

        # Resize binary columns
        for table, cols in columns_to_resize.items():
            print(f"Checking binary columns for table: {table}")
            for col_name in cols:
                print(f"Resizing column {col_name} in {table} to LONGBLOB...")
                try:
                    cursor.execute(f"ALTER TABLE {table} MODIFY COLUMN {col_name} LONGBLOB")
                    print(f"Column {col_name} resized.")
                except mysql.connector.Error as e:
                    print(f"Error resizing {col_name}: {e}")
        
        conn.commit()

        print("Schema update completed successfully.")
        
    except mysql.connector.Error as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_schema()
