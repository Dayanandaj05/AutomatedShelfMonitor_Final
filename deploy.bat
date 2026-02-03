@echo off
echo 🚀 Deploying Automated Shelf Monitor...

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.7+
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv shelf_monitor_env

REM Activate virtual environment
call shelf_monitor_env\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Create necessary directories
echo 📁 Creating directories...
if not exist "detections" mkdir detections
if not exist "logs" mkdir logs

echo ✅ Deployment complete!
echo.
echo 🔧 To configure:
echo 1. Edit config.py with your Telegram credentials
echo 2. Run: python main_fin.py
echo.
echo 📋 Login credentials:
echo    Username: admin
echo    Password: admin123
pause