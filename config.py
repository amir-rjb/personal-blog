import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
SECRET_FILE = INSTANCE_DIR / "secret_key"
if not SECRET_FILE.exists():
    SECRET_FILE.write_text(os.urandom(32).hex(), encoding="utf-8")
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or SECRET_FILE.read_text(encoding="utf-8").strip()
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(BASE_DIR / "blog.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"
    POSTS_PER_PAGE = 6
