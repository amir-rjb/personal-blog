# وبلاگ شخصی Flask — Dark Minimal

## اجرا در ویندوز
1. Python 3.10 یا جدیدتر نصب باشد و هنگام نصب گزینه Add Python to PATH فعال باشد.
2. بار اول روی `first_setup_windows.bat` دوبار کلیک کن؛ وابستگی‌ها نصب می‌شوند و حساب مدیر ساخته می‌شود.
3. برای اجرای بعدی روی `run_windows.bat` دوبار کلیک کن.

سپس سایت: http://127.0.0.1:5000 و پنل: http://127.0.0.1:5000/admin/login

## اجرا در Linux / macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python create_admin.py
python app.py
```

## امکانات
- وبلاگ واکنش‌گرا با Bootstrap RTL و تم تیره
- مدیریت مقاله، پیش‌نویس، انتشار و آرشیو
- جست‌وجوی زنده، فیلتر دسته‌بندی و بارگذاری صفحه بعد با AJAX
- صفحه درباره، تماس و صندوق پیام‌های پنل
- هش رمز عبور، CSRF، محدودیت حجم و بررسی واقعی تصویر

## نکته امنیتی
برای اجرای عمومی، مقدار `SECRET_KEY` را به‌صورت متغیر محیطی امن و پایدار تنظیم کن، HTTPS را فعال کن و `COOKIE_SECURE=1` بگذار. سرور توسعه Flask را برای میزبانی عمومی استفاده نکن.
