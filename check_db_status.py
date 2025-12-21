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
        print("No database URL found.")
        return None

    if database_url.startswith('mysql://'):
        result = urlparse(database_url)
        try:
            conn = mysql.connector.connect(
                host=result.hostname,
                user=result.username,
                password=result.password,
                database=result.path.lstrip('/'),
                port=result.port or 3306
            )
            return conn
        except Exception as e:
            print(f"Connection error: {e}")
            return None
    return None

def check_status():
    conn = get_mysql_connection()
    if not conn: return
    
    cursor = conn.cursor()
    try:
        print("--- Table Sizes ---")
        cursor.execute("""
            SELECT 
                table_name AS `Table`, 
                round(((data_length + index_length) / 1024 / 1024), 2) `Size (MB)` 
            FROM information_schema.TABLES 
            WHERE table_schema = DATABASE();
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} MB")
            
        print("\n--- InnoDB Status (Variables) ---")
        vars_to_check = ['innodb_data_file_path', 'max_allowed_packet', 'innodb_file_per_table', 'innodb_buffer_pool_size']
        for v in vars_to_check:
            cursor.execute(f"SHOW VARIABLES LIKE '{v}';")
            print(cursor.fetchone())

        print("\n--- Database Storage Info ---")
        cursor.execute("SELECT @@datadir;")
        print(f"Data directory: {cursor.fetchone()[0]}")


        print("\n--- Table Engines ---")
        cursor.execute("SELECT table_name, engine FROM information_schema.tables WHERE table_schema = DATABASE();")
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]}")


    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_status()
