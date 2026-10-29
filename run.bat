@echo off
setlocal enabledelayedexpansion
title VTE - Visual Text Extractor & Translator Launcher
color 0b

echo ========================================================
echo       VTE - Visual Text Extractor & Translator
echo             Fast Desktop OCR & Speech Tool
echo ========================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check or create virtual environment
if not exist ".venv" (
    echo [*] Setting up virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)

:: 3. Activate virtual environment
call .venv\Scripts\activate.bat

:: 4. Verify/Install dependencies
python -c "import PyQt5, pytesseract, PIL, pyttsx3, deep_translator" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing required packages from requirements.txt...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install requirements!
        pause
        exit /b 1
    )
    echo [OK] Packages installed successfully.
)

:: 5. Launch Application
echo [*] Launching VTE Application...
python VTE.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with an error code: %errorlevel%
    pause
)
