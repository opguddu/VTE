@echo off
setlocal enabledelayedexpansion
title Build Video Text Extractor Windows Installer
color 0b

echo ========================================================
echo     Building Video Text Extractor Setup Installer
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 1. Locate Inno Setup Compiler (ISCC.exe)
set "ISCC_PATH="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
) else if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe"
) else (
    where iscc >nul 2>nul
    if %errorlevel% equ 0 (
        set "ISCC_PATH=iscc"
    )
)

if "%ISCC_PATH%"=="" (
    echo [ERROR] Inno Setup 6 is not installed or ISCC.exe was not found!
    echo Please install Inno Setup 6 from: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo [*] Found Inno Setup Compiler: %ISCC_PATH%

:: 2. Ensure dist\VTE\VTE.exe exists
if not exist "dist\VTE\VTE.exe" (
    echo [*] Standalone build missing. Running build_standalone.bat first...
    call build_standalone.bat
    if %errorlevel% neq 0 (
        echo [ERROR] Standalone build failed!
        pause
        exit /b 1
    )
)

:: 3. Compile Installer
echo [*] Compiling Windows Installer (VideoTextExtractor_Setup.exe)...
"%ISCC_PATH%" installer.iss
if %errorlevel% neq 0 (
    echo [ERROR] Inno Setup compilation failed!
    pause
    exit /b 1
)

:: 4. Package Portable ZIP into release_artifacts
echo [*] Packaging release artifacts...
if not exist "release_artifacts" mkdir "release_artifacts"
copy /y "dist_installer\VideoTextExtractor_Setup.exe" "release_artifacts\" >nul 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -Command "$src = 'dist\VTE\*'; $zip = 'release_artifacts\VideoTextExtractor-Portable-x64.zip'; if (Test-Path $zip) { Remove-Item $zip -Force }; Compress-Archive -Path $src -DestinationPath $zip -CompressionLevel Optimal"

echo.
echo ========================================================
echo   [SUCCESS] Build Complete! Release artifacts ready in:
echo   - release_artifacts\VideoTextExtractor_Setup.exe
echo   - release_artifacts\VideoTextExtractor-Portable-x64.zip
echo ========================================================
echo.
pause

