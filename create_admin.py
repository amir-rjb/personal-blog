from getpass import getpass
from app import app
from models import db, User

with app.app_context():
    username = input("Admin username: ").strip()
    password = getpass("Admin password (at least 12 characters): ")
    confirm = getpass("Confirm password: ")
    if not username or len(username) > 80:
        raise SystemExit("Username is required (max 80 characters).")
    if len(password) < 12:
        raise SystemExit("Use a password with at least 12 characters.")
    if password != confirm:
        raise SystemExit("Passwords do not match.")
    user = User.query.filter_by(username=username).first()
    if user:
        user.set_password(password)
        print("Existing admin password updated.")
    else:
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        print("Admin account created.")
    db.session.commit()
