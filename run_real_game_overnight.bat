@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "SCRIPT=%~dp0run_real_game_overnight.ps1"

if not exist "%SCRIPT%" (
    echo ERROR: Missing runner script "%SCRIPT%"
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
echo ============================================================
if "%EXIT_CODE%"=="0" (
    echo Training finished successfully.
) else (
    echo Training exited with code %EXIT_CODE%.
)
echo ============================================================
echo.
pause
exit /b %EXIT_CODE%
