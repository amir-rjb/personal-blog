from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    def set_password(self, password):
        self.password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_field = db.Column(db.String(255))
    category = db.Column(db.String(60), nullable=False, default="یادداشت‌ها")
    created_date = db.Column(db.DateTime, default=utcnow, nullable=False)
    published_date = db.Column(db.DateTime)
    updated_date = db.Column(db.DateTime, onupdate=utcnow)
    status = db.Column(db.String(20), default="draft", nullable=False)
    @property
    def reading_minutes(self):
        return max(1, len(self.description.split()) // 200 + 1)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_date = db.Column(db.DateTime, default=utcnow, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
