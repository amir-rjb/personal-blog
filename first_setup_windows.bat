@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (echo Python Launcher not found. Install Python 3.10+ first.& pause& exit /b 1)
if not exist ".venv\Scripts\python.exe" py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (echo Dependency installation failed.& pause& exit /b 1)
python create_admin.py
if errorlevel 1 (pause& exit /b 1)
echo Setup complete. Run run_windows.bat to start the blog.
pause
