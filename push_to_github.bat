@echo off
title Push VTE to GitHub
color 0a

echo ========================================================
echo          Pushing VTE Commits to GitHub
echo ========================================================
echo.

cd /d "%~dp0"
echo [*] Pushing main branch to https://github.com/opguddu/VTE.git...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   [SUCCESS] Successfully pushed to GitHub!
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   [NOTICE] If permission was denied:
    echo   1. Make sure you are signed in as 'opguddu' on GitHub.
    echo   2. Or invite your current account 'bappamarathacha'
    echo      as a Collaborator with Write access at:
    echo      https://github.com/opguddu/VTE/settings/access
    echo ========================================================
)
echo.
pause
