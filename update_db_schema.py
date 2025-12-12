import sqlite3
import os

# Database path
DB_PATH = 'instance/portfolio.db'

def update_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
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

    try:
        for table, cols in columns_to_add.items():
            print(f"Checking table: {table}")
            cursor.execute(f"PRAGMA table_info({table})")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            for col_name, col_type in cols:
                if col_name not in existing_cols:
                    print(f"Adding column {col_name} to {table}...")
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        print("Done.")
                    except sqlite3.OperationalError as e:
                        print(f"Error adding {col_name}: {e}")
                else:
                    print(f"Column {col_name} already exists.")
                    
        # Add index
        print("Checking index idx_file_year...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_year ON files (year)")
            print("Index ensured.")
        except Exception as e:
            print(f"Error creating index: {e}")

        conn.commit()
        print("Database schema update completed.")
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_db()
