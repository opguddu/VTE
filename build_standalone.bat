@echo off
setlocal enabledelayedexpansion
title Build Standalone VTE Windows Application
color 0a

echo ========================================================
echo       Building VTE (Video Text Extractor) Standalone
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: Locate Python
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    set "PYINSTALLER_CMD=.venv\Scripts\pyinstaller.exe"
) else (
    set "PYTHON_CMD=python"
    set "PYINSTALLER_CMD=pyinstaller"
)

echo [*] Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

:: Ensure PyInstaller is installed
%PYTHON_CMD% -c "import PyInstaller" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing PyInstaller...
    %PYTHON_CMD% -m pip install pyinstaller
)

:: Run PyInstaller Build
echo [*] Compiling standalone application with PyInstaller...
%PYINSTALLER_CMD% VTE.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)

:: Ensure Desktop Shortcut script is in dist\VTE
if exist "dist\VTE" (
    echo [*] Adding Create Desktop Shortcut script to dist\VTE...
    (
        echo @echo off
        echo title Create VTE Desktop Shortcut
        echo powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [Environment]::GetFolderPath('Desktop'^); $s = $ws.CreateShortcut(\"$desktop\Video Text Extractor.lnk\"^); $s.TargetPath = \"$PSScriptRoot\VTE.exe\"; $s.WorkingDirectory = \"$PSScriptRoot\"; if (Test-Path \"$PSScriptRoot\app.ico\"^) { $s.IconLocation = \"$PSScriptRoot\app.ico\" }; $s.Save()"
        echo echo.
        echo echo ========================================================
        echo echo   [SUCCESS] Video Text Extractor shortcut created on Desktop!
        echo echo ========================================================
        echo echo.
        echo pause
    ) > "dist\VTE\Create Desktop Shortcut.bat"

    copy /y "app.ico" "dist\VTE\" >nul 2>nul
)

echo.
echo ========================================================
echo   [SUCCESS] VTE Standalone build complete in dist\VTE!
echo ========================================================
echo.
pause

