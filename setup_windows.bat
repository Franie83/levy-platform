@echo off
title Levy Platform Setup
echo ========================================
echo    Levy Platform Installation Script
echo ========================================
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator privileges...
    powershell start-process "%0" -verb runas
    exit /b
)

:: Set installation directory
set INSTALL_DIR=%USERPROFILE%\levy-platform
set CURRENT_DIR=%~dp0

echo This script will install:
echo   - Python 3.10 (if not installed)
echo   - Git (if not installed)
echo   - All required Python packages
echo   - Clone/Pull the Levy Platform repository
echo.
echo Installation directory: %INSTALL_DIR%
echo.
pause

:: ========================================
:: Step 1: Check/Create installation directory
:: ========================================
echo.
echo [1/6] Setting up installation directory...
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    echo Created directory: %INSTALL_DIR%
) else (
    echo Directory already exists: %INSTALL_DIR%
)

:: ========================================
:: Step 2: Check and install Python
:: ========================================
echo.
echo [2/6] Checking Python installation...

python --version >nul 2>&1
if %errorLevel% equ 0 (
    python --version
    echo Python is already installed.
) else (
    echo Python not found. Installing Python 3.10...
    
    :: Download Python installer
    echo Downloading Python 3.10.11...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    
    :: Install Python
    echo Installing Python (this may take a few minutes)...
    %TEMP%\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Wait for installation to complete
    timeout /t 10 /nobreak >nul
    
    :: Refresh environment variables
    call refreshenv >nul 2>&1
    
    echo Python 3.10 installed successfully!
)

:: ========================================
:: Step 3: Check and install Git
:: ========================================
echo.
echo [3/6] Checking Git installation...

git --version >nul 2>&1
if %errorLevel% equ 0 (
    git --version
    echo Git is already installed.
) else (
    echo Git not found. Installing Git...
    
    :: Download Git installer
    echo Downloading Git...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.2/Git-2.42.0.2-64-bit.exe' -OutFile '%TEMP%\git-installer.exe'"
    
    :: Install Git
    %TEMP%\git-installer.exe /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh"
    
    echo Git installed successfully!
)

:: ========================================
:: Step 4: Clone/Pull repository
:: ========================================
echo.
echo [4/6] Getting repository...
cd /d "%INSTALL_DIR%"

if exist "%INSTALL_DIR%\.git" (
    echo Repository exists. Pulling latest changes...
    git pull
) else (
    echo Cloning repository...
    git clone https://github.com/Franie83/levy-platform.git .
)

:: ========================================
:: Step 5: Create virtual environment
:: ========================================
echo.
echo [5/6] Setting up Python virtual environment...

if exist "%INSTALL_DIR%\venv" (
    echo Virtual environment already exists.
) else (
    echo Creating virtual environment...
    python -m venv venv
)

:: ========================================
:: Step 6: Install Python packages
:: ========================================
echo.
echo [6/6] Installing Python packages...

call "%INSTALL_DIR%\venv\Scripts\activate.bat"

:: Upgrade pip
python -m pip install --upgrade pip

:: Install requirements
if exist "%INSTALL_DIR%\requirements.txt" (
    echo Installing packages from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Installing default packages...
    pip install flask==2.3.3
    pip install flask-sqlalchemy==3.1.1
    pip install flask-login==0.6.2
    pip install flask-wtf==1.2.1
    pip install werkzeug==2.3.7
    pip install requests==2.31.0
    pip install python-dotenv==1.0.0
    pip install email-validator==2.1.0
    pip install Pillow==10.0.1
    pip install qrcode==7.4.2
    pip install gunicorn==21.2.0
)

:: Create .env file if it doesn't exist
if not exist "%INSTALL_DIR%\.env" (
    echo Creating .env file...
    (
        echo FLASK_APP=app.py
        echo FLASK_ENV=development
        echo SECRET_KEY=your-secret-key-change-this-in-production
        echo DATABASE_URL=sqlite:///levy_platform.db
    ) > "%INSTALL_DIR%\.env"
)

:: Initialize database
echo.
echo Initializing database...
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database created successfully!')"

:: Create default users
echo.
echo Creating default users...
if exist "%INSTALL_DIR%\create_default_users.py" (
    python create_default_users.py
)

:: ========================================
:: Create run script
:: ========================================
echo.
echo Creating run script...

(
    echo @echo off
    echo cd /d "%~dp0"
    echo call venv\Scripts\activate
    echo echo.
    echo echo ========================================
    echo echo    Levy Platform is starting...
    echo echo ========================================
    echo echo.
    echo echo Access the application at: http://127.0.0.1:5000
    echo echo.
    echo python app.py
    echo pause
) > "%INSTALL_DIR%\run.bat"

:: Create desktop shortcut
echo.
echo Creating desktop shortcut...

powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%USERPROFILE%\Desktop\Levy Platform.lnk'); $SC.TargetPath = '%INSTALL_DIR%\run.bat'; $SC.WorkingDirectory = '%INSTALL_DIR%'; $SC.Description = 'Levy Management Platform'; $SC.Save()"

:: ========================================
:: Installation complete
:: ========================================
echo.
echo ========================================
echo    INSTALLATION COMPLETE!
echo ========================================
echo.
echo 📁 Installation directory: %INSTALL_DIR%
echo 🚀 Run script: %INSTALL_DIR%\run.bat
echo 🖥️ Desktop shortcut created: Levy Platform
echo.
echo Default Users:
echo   Super Admin: NIN=00000000001, Password=Admin@123
echo   Enforcer:    NIN=00000000002, Password=Enforcer@123
echo   MSME User:   NIN=00000000003, Password=MSME@123
echo   Transporter: NIN=00000000004, Password=Trans@123
echo.
echo To start the application:
echo   1. Double-click the desktop shortcut
echo   2. Or navigate to %INSTALL_DIR% and run run.bat
echo.
echo ========================================
pause