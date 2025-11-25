@echo off
REM DuckyTrading Auto-Updater
REM This script pulls the latest code from GitHub and rebuilds the app

echo ========================================
echo    DuckyTrading Auto-Updater
echo ========================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if we're in a git repository
if not exist ".git\" (
    echo [ERROR] Not a git repository
    echo Please run this from the DuckyTrading folder
    pause
    exit /b 1
)

echo [1/5] Checking for updates...
git fetch origin master

REM Check if there are updates
git diff --quiet HEAD origin/master
if %ERRORLEVEL% EQU 0 (
    echo [INFO] You already have the latest version!
    timeout /t 3
    exit /b 0
)

echo [INFO] Updates available!
echo.

REM Show what's new
echo ========================================
echo What's New:
echo ========================================
git log HEAD..origin/master --oneline --decorate
echo.

REM Ask for confirmation
set /p CONFIRM="Do you want to update? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Update cancelled.
    pause
    exit /b 0
)

echo.
echo [2/5] Backing up current version...
if exist "DuckyTrading.exe.backup" del "DuckyTrading.exe.backup"
if exist "DuckyTrading.exe" (
    copy "DuckyTrading.exe" "DuckyTrading.exe.backup" >nul
    echo [OK] Backup created: DuckyTrading.exe.backup
)

echo.
echo [3/5] Pulling latest code from GitHub...
git pull origin master
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to pull updates
    pause
    exit /b 1
)

echo.
echo [4/5] Installing/updating dependencies...
pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some dependencies failed to install
    echo The app may still work, but check for errors
)

echo.
echo [5/5] Rebuilding application...
python package_app.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed
    echo Your backup is available: DuckyTrading.exe.backup
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Update Complete!
echo ========================================
echo.
echo Your app has been updated successfully.
echo You can now run DuckyTrading.exe
echo.
echo Note: Your .env and credentials are preserved.
echo.
pause
