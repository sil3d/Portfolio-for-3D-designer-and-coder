import mysql.connector
from dotenv import load_dotenv
from termcolor import colored
import os

# Charger les variables d'environnement à partir du fichier .env
load_dotenv(".env")

# Récupérer les informations de connexion à partir des variables d'environnement
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def reset_database():
    try:
        # Se connecter à la base de données
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        # Créer un curseur pour exécuter des requêtes SQL
        cursor = connection.cursor()

        # Désactiver les vérifications de clé étrangère
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

        # Supprimer toutes les tables de la base de données
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS `{table[0]}`")

        # Réactiver les vérifications de clé étrangère
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

        # Valider les changements et afficher un message de succès
        connection.commit()
        print(colored("Database reset successfully.", "green"))

    except Exception as e:
        # En cas d'erreur, afficher un message d'erreur
        print(colored(f"An error occurred: {str(e)}", "red"))

    finally:
        # Fermer la connexion à la base de données
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    reset_database()
