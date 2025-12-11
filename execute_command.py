import subprocess

def reset():
    subprocess.run(["python", "reset-database.py"])

def create_database():
    subprocess.run(["python", "create_database.py"])

if __name__ == "__main__":
    # Appel des fonctions en fonction des arguments passés en ligne de commande
    import sys
    command = sys.argv[1]
    if command == "create_database":
        create_database()
    elif command == "reset_database":
        reset()
  