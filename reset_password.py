from getpass import getpass
from app import app
from models import db, User

with app.app_context():

    users = User.query.order_by(User.id).all()

    print("\n--- Existing Admin Accounts ---")

    for user in users:
        print(f"ID: {user.id} | Username: {user.username}")

    if users:
        username = input("\nEnter existing username: ").strip()
        user = User.query.filter_by(username=username).first()

        if not user:
            print("Username not found!")
            raise SystemExit

    else:
        print("No admin account exists.")
        username = input("New username: ").strip()

        if not username:
            raise SystemExit("Invalid username")

        user = User(username=username)
        db.session.add(user)

    password = getpass("New password: ")
    confirm = getpass("Confirm password: ")

    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    if password != confirm:
        raise SystemExit("Passwords do not match.")

    user.set_password(password)
    db.session.commit()

    print("\nAdmin password successfully reset!")