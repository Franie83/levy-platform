@echo off
title Levy Platform Installer
color 0A
echo ========================================
echo    Levy Platform Installation Script
echo ========================================
echo.
echo This will install the Levy Platform on your computer.
echo.

:: Set installation directory
set INSTALL_DIR=%USERPROFILE%\levy-platform
echo Installation folder: %INSTALL_DIR%
echo.

:: Check if Python is installed
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Python is installed
    python --version
) else (
    echo ❌ Python is NOT installed
    echo.
    echo Please install Python 3.10 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo After installing Python, run this script again.
    pause
    exit /b
)

:: Check if Git is installed
echo.
echo [2/6] Checking Git installation...
git --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Git is installed
    git --version
) else (
    echo ❌ Git is NOT installed
    echo.
    echo Please install Git from:
    echo https://git-scm.com/download/win
    echo.
    echo After installing Git, run this script again.
    pause
    exit /b
)

:: Create project directory
echo.
echo [3/6] Creating project directory...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo ✅ Created directory: %INSTALL_DIR%
) else (
    echo ✅ Directory already exists
)

:: Clone or pull repository
echo.
echo [4/6] Downloading application files...
cd /d "%INSTALL_DIR%"

if exist "%INSTALL_DIR%\.git" (
    echo Updating existing installation...
    git pull
) else (
    echo Cloning repository for the first time...
    git clone https://github.com/Franie83/levy-platform.git .
)

:: Create virtual environment
echo.
echo [5/6] Setting up Python environment...
if not exist "%INSTALL_DIR%\venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

:: Activate venv and install packages
echo Installing required packages (this may take a few minutes)...
call "%INSTALL_DIR%\venv\Scripts\activate.bat"

:: Install requirements
if exist "%INSTALL_DIR%\requirements.txt" (
    echo Found requirements.txt, installing packages...
    pip install -r requirements.txt
) else (
    echo Installing default packages...
    pip install flask flask-sqlalchemy flask-login flask-wtf
    pip install requests python-dotenv email-validator
    pip install Pillow qrcode
)

:: Create .env file if needed
if not exist "%INSTALL_DIR%\.env" (
    echo Creating configuration file...
    (
        echo FLASK_APP=app.py
        echo FLASK_ENV=development
        echo SECRET_KEY=dev-secret-key-change-this
        echo DATABASE_URL=sqlite:///levy_platform.db
    ) > .env
    echo ✅ .env file created
)

:: Initialize database
echo.
echo Creating database...
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
echo ✅ Database created

:: Create default users
echo Creating default users...
if exist "%INSTALL_DIR%\create_default_users.py" (
    python create_default_users.py
    echo ✅ Default users created
)

:: Create run script
echo.
echo [6/6] Creating launcher...
(
    echo @echo off
    echo cd /d "%~dp0"
    echo echo ========================================
    echo echo    Starting Levy Platform
    echo echo ========================================
    echo echo.
    echo echo Access the application at: http://127.0.0.1:5000
    echo echo.
    echo call venv\Scripts\activate
    echo python app.py
    echo pause
) > "%INSTALL_DIR%\start.bat"

echo ✅ Launcher created: %INSTALL_DIR%\start.bat

:: Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\Levy Platform.lnk'); $SC.TargetPath = '%INSTALL_DIR%\start.bat'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.Description = 'Levy Management Platform'; $SC.Save()" >nul 2>&1
echo ✅ Desktop shortcut created

:: Installation complete
echo.
echo ========================================
echo         INSTALLATION COMPLETE!
echo ========================================
echo.
echo 📁 Location: %INSTALL_DIR%
echo 🚀 Launch: Double-click the "Levy Platform" icon on your desktop
echo    or run: %INSTALL_DIR%\start.bat
echo.
echo Default Users:
echo   Super Admin: NIN=00000000001, Password=Admin@123
echo   Enforcer:    NIN=00000000002, Password=Enforcer@123
echo   MSME User:   NIN=00000000003, Password=MSME@123
echo   Transporter: NIN=00000000004, Password=Trans@123
echo.
echo ========================================
pause