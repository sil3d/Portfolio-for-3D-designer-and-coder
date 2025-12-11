import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os
from dotenv import load_dotenv
from termcolor import colored

# Charger les variables d'environnement à partir du fichier .env
load_dotenv(".env")

# Récupérer les informations de connexion à partir des variables d'environnement
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def create_connection():
    """Créer une connexion à la base de données MySQL."""
    return mysql.connector.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def update_database():
    """Mettre à jour la base de données pour s'assurer que les tables et les colonnes existent."""
    try:
        connection = create_connection()
        cursor = connection.cursor()

        # Créer les tables si elles n'existent pas
        tables = {
            "admin": """
            CREATE TABLE IF NOT EXISTS admin (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(80) NOT NULL UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                last_login DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """,
            "files": """
            CREATE TABLE IF NOT EXISTS files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
                file_name VARCHAR(255) NOT NULL,
                banner_path LONGBLOB,
                banner_mimetype VARCHAR(50),
                file_path_glb LONGBLOB,
                file_path_zip LONGBLOB,
                added_by VARCHAR(80) NOT NULL,
                location VARCHAR(255),
                year INT
            )
            """,
            "gallery_files": """
            CREATE TABLE IF NOT EXISTS gallery_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                file_id INT NOT NULL,
                file_path LONGBLOB NOT NULL,
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
            """,
            "downloads": """
            CREATE TABLE IF NOT EXISTS downloads (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(120) NOT NULL,
                location VARCHAR(255),
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                comment TEXT,
                download_count INT DEFAULT 0,
                likes INT DEFAULT 0
            )
            """,
            "hdri": """
            CREATE TABLE IF NOT EXISTS hdri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                file_path LONGBLOB NOT NULL,
                preview_path LONGBLOB NOT NULL,
                preview_path_mimetype VARCHAR(50)
            )
            """
        }

        for table_name, create_statement in tables.items():
            cursor.execute(create_statement)

        connection.commit()
        print(colored("Database update completed.", "green"))

    except Error as e:
        print(colored(f"An error occurred: {str(e)}", "red"))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    update_database()