@echo off
echo ========================================
echo   LifeOS Build Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

REM Install PyInstaller if not present
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller!
        pause
        exit /b 1
    )
)

REM Clean old builds
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [1/3] Building LifeOS...
pyinstaller lifeos.spec --noconfirm --clean

if errorlevel 1 (
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Copying config files...
copy .env.example dist\lifeos\.env.example >nul 2>&1

echo.
echo [3/3] Build complete!
echo.
echo ========================================
echo   Output: dist\lifeos\lifeos.exe
echo ========================================
echo.
echo To run: dist\lifeos\lifeos.exe --help
echo.
pause
