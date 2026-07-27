@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================
echo   ATEK RF MODULES UI - AUTO BUILD
echo ============================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python and add it to PATH.
    echo         https://www.python.org/downloads/  ^(check "Add to PATH" during install^)
    pause
    exit /b 1
)

REM --- Main python file (fixed name) ---
set MAIN_FILE=ATEK_RF_MODULES_USER_INTERFACE_v2.0.py

if not exist "%MAIN_FILE%" (
    echo [ERROR] %MAIN_FILE% not found in this folder.
    echo         Place the main file in the same folder as this script.
    pause
    exit /b 1
)

echo Main file found : %MAIN_FILE%

REM --- Check assets.py ---
if not exist "assets.py" (
    echo.
    echo [WARNING] assets.py not found in this folder!
    echo           Logo and PDF datasheets may not load.
    echo           Press any key to continue, or close this window to cancel...
    pause >nul
) else (
    echo assets.py found : OK
)

REM --- Check icon ---
set ICON_PARAM=
if exist "ATEK_MIDAS.ico" (
    echo Icon found      : ATEK_MIDAS.ico
    set ICON_PARAM=--icon=ATEK_MIDAS.ico
) else (
    echo [WARNING] ATEK_MIDAS.ico not found, building without an icon.
)

echo.
echo ------------------------------------------------
echo Checking / installing required packages
echo ------------------------------------------------
python -m pip install --upgrade pip >nul 2>&1
python -m pip install customtkinter pyserial pillow pyinstaller
if errorlevel 1 (
    echo [ERROR] Package installation failed.
    pause
    exit /b 1
)

echo.
echo ------------------------------------------------
echo Cleaning previous build files
echo ------------------------------------------------
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
del /q "*.spec" >nul 2>&1

echo.
echo ------------------------------------------------
echo Building  (--onedir --noupx  =^> AV friendly)
echo ------------------------------------------------
echo.

python -m PyInstaller ^
    --name "ATEK_RF_MODULES_UI" ^
    --onedir ^
    --noupx ^
    --clean ^
    --noconsole ^
    %ICON_PARAM% ^
    "%MAIN_FILE%"

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   BUILD COMPLETE!
echo   Output folder : dist\ATEK_RF_MODULES_UI\
echo   Executable    : dist\ATEK_RF_MODULES_UI\ATEK_RF_MODULES_UI.exe
echo.
echo   Send the ENTIRE "dist\ATEK_RF_MODULES_UI" folder
echo   to the customer (the exe alone is not enough).
echo ============================================
echo.
pause
