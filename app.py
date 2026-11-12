import os, re, uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort, jsonify
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from config import Config
from models import db, User, Post, ContactMessage, utcnow

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
csrf = CSRFProtect(app)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
STATUSES = {"draft", "published", "archived"}
CATEGORIES = ["برنامه‌نویسی", "امنیت", "تکنولوژی", "یادداشت‌ها"]
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

with app.app_context():
    db.create_all()
    # Small, safe additive migration for databases created by the earlier project version.
    columns = {row[1] for row in db.session.execute(db.text("PRAGMA table_info(post)")).all()}
    if "category" not in columns:
        db.session.execute(db.text("ALTER TABLE post ADD COLUMN category VARCHAR(60) NOT NULL DEFAULT 'یادداشت‌ها'"))
        db.session.commit()

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        uid = session.get("user_id")
        if not uid or not db.session.get(User, uid):
            session.clear()
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

def public_posts_query():
    return Post.query.filter_by(status="published").filter(Post.published_date.is_not(None))

def image_url(filename):
    return url_for("uploaded_file", filename=filename) if filename else None

@app.context_processor
def inject_globals():
    return {"categories": CATEGORIES, "image_url": image_url, "current_year": datetime.now().year}

@app.route("/")
def home():
    featured = public_posts_query().order_by(Post.published_date.desc()).first()
    pagination = public_posts_query().order_by(Post.published_date.desc()).paginate(page=1, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    return render_template("home.html", featured=featured, pagination=pagination, posts=pagination.items, selected_category="", search_query="")

@app.route("/posts")
def all_posts():
    return render_template("posts.html", posts=None)

@app.get("/api/posts")
def api_posts():
    page = max(1, request.args.get("page", 1, type=int))
    q = request.args.get("q", "").strip()[:100]
    category = request.args.get("category", "").strip()
    query = public_posts_query()
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Post.title.ilike(like), Post.description.ilike(like)))
    if category in CATEGORIES:
        query = query.filter_by(category=category)
    pagination = query.order_by(Post.published_date.desc()).paginate(page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    html = render_template("_post_cards.html", posts=pagination.items)
    return jsonify(html=html, page=pagination.page, pages=pagination.pages, total=pagination.total, has_next=pagination.has_next, has_prev=pagination.has_prev)

@app.route("/post/<int:post_id>/<slug>")
def post_detail(post_id, slug):
    post = db.get_or_404(Post, post_id)
    if post.status != "published" or not post.published_date:
        abort(404)
    return render_template("post_detail.html", post=post)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not name or len(name) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254 or not message or len(message) > 5000:
            flash("اطلاعات واردشده معتبر نیست. لطفاً فرم را بررسی کنید.", "danger")
            return render_template("contact.html"), 400
        db.session.add(ContactMessage(name=name, email=email, message=message))
        db.session.commit()
        flash("پیامت با موفقیت ثبت شد. ممنون از اینکه پیام دادی.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if session.get("user_id") and db.session.get(User, session["user_id"]):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()
            session["user_id"] = user.id
            session.permanent = True
            target = request.args.get("next", "")
            if not target.startswith("/") or target.startswith("//"):
                target = url_for("dashboard")
            return redirect(target)
        flash("نام کاربری یا رمز عبور اشتباه است.", "danger")
    return render_template("admin/login.html")

@app.post("/admin/logout")
@login_required
def logout():
    session.clear()
    flash("با موفقیت خارج شدی.", "success")
    return redirect(url_for("login"))

@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
def dashboard():
    stats = {"total": Post.query.count(), "published": Post.query.filter_by(status="published").count(), "draft": Post.query.filter_by(status="draft").count(), "archived": Post.query.filter_by(status="archived").count(), "messages": ContactMessage.query.count()}
    recent_posts = Post.query.order_by(Post.created_date.desc()).limit(6).all()
    return render_template("admin/dashboard.html", stats=stats, recent_posts=recent_posts)

@app.get("/admin/posts")
@login_required
def admin_posts():
    page = max(1, request.args.get("page", 1, type=int))
    status = request.args.get("status", "")
    query = Post.query
    if status in STATUSES:
        query = query.filter_by(status=status)
    pagination = query.order_by(Post.created_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template("admin/posts.html", pagination=pagination, current_status=status)

def save_image(file):
    if not file or not file.filename:
        return None
    ext = Path(secure_filename(file.filename)).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("فرمت تصویر باید JPG، PNG یا WEBP باشد.")
    name = uuid.uuid4().hex + ".jpg"
    path = os.path.join(app.config["UPLOAD_FOLDER"], name)
    try:
        file.stream.seek(0)
        with Image.open(file.stream) as im:
            im.verify()
        file.stream.seek(0)
        with Image.open(file.stream) as im:
            im.thumbnail((1800, 1800))
            im.convert("RGB").save(path, "JPEG", quality=88, optimize=True)
        return name
    except (UnidentifiedImageError, OSError, ValueError):
        if os.path.exists(path): os.remove(path)
        raise ValueError("فایل انتخاب‌شده تصویر معتبر نیست.")

def remove_image(name):
    if name:
        path = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(name))
        if os.path.isfile(path): os.remove(path)

def read_post_form():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "یادداشت‌ها").strip()
    status = request.form.get("status", "draft")
    if not title or len(title) > 200 or not description or len(description) > 50000:
        raise ValueError("عنوان و متن مقاله الزامی است و باید در محدوده مجاز باشد.")
    if category not in CATEGORIES or status not in STATUSES:
        raise ValueError("دسته‌بندی یا وضعیت مقاله معتبر نیست.")
    return title, description, category, status

@app.route("/admin/posts/create", methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        try:
            title, description, category, status = read_post_form()
            image_name = save_image(request.files.get("image"))
            post = Post(title=title, description=description, category=category, status=status, image_field=image_name, published_date=utcnow() if status == "published" else None)
            db.session.add(post); db.session.commit()
            flash("مقاله با موفقیت ایجاد شد.", "success")
            return redirect(url_for("admin_posts"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            raise
    return render_template("admin/post_form.html", post=None, page_title="مقاله جدید")

@app.route("/admin/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_post(post_id):
    post = db.get_or_404(Post, post_id)
    if request.method == "POST":
        new_image = None
        try:
            title, description, category, status = read_post_form()
            upload = request.files.get("image")
            if upload and upload.filename: new_image = save_image(upload)
            was_published = post.status == "published" and post.published_date is not None
            old_image = post.image_field
            post.title, post.description, post.category, post.status = title, description, category, status
            if new_image: post.image_field = new_image
            if status == "published" and not was_published: post.published_date = utcnow()
            elif status != "published": post.published_date = None
            db.session.commit()
            if new_image: remove_image(old_image)
            flash("مقاله به‌روزرسانی شد.", "success")
            return redirect(url_for("admin_posts"))
        except ValueError as exc:
            if new_image: remove_image(new_image)
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            if new_image: remove_image(new_image)
            raise
    return render_template("admin/post_form.html", post=post, page_title="ویرایش مقاله")

@app.post("/admin/posts/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    post = db.get_or_404(Post, post_id)
    image_name = post.image_field
    db.session.delete(post); db.session.commit(); remove_image(image_name)
    flash("مقاله حذف شد.", "success")
    return redirect(url_for("admin_posts"))

@app.get("/admin/messages")
@login_required
def admin_messages():
    messages = ContactMessage.query.order_by(ContactMessage.created_date.desc()).all()
    return render_template("admin/messages.html", messages=messages)

@app.post("/admin/messages/<int:message_id>/read")
@login_required
def mark_message_read(message_id):
    message = db.get_or_404(ContactMessage, message_id)
    message.is_read = not message.is_read
    db.session.commit()
    return redirect(url_for("admin_messages"))

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(413)
def too_large(error):
    flash("حجم فایل بیش از ۵ مگابایت است.", "danger")
    return redirect(request.referrer or url_for("home"))

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
