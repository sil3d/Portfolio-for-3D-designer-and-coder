from werkzeug.security import generate_password_hash
from app import create_app
from app.models import db, Admin
from termcolor import colored

def add_admin(username, password):
    app = create_app()
    with app.app_context():
        try:
            # Check if user exists
            if Admin.query.filter_by(username=username).first():
                print(colored(f"User {username} already exists.", "yellow"))
                return

            password_hash = generate_password_hash(password)
            new_admin = Admin(username=username, password_hash=password_hash)
            db.session.add(new_admin)
            db.session.commit()
            print(colored(f"User {username} registered successfully.", "green"))
            
        except Exception as e:
            print(colored(f"An error occurred: {str(e)}", "red"))
            db.session.rollback()

if __name__ == "__main__":
    email = input("Enter the Google email to register: ")
    password = input("Enter the password: ")
    add_admin(email, password)