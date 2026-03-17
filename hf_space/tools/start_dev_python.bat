@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo Loveca Simulator - Python Dev Server
echo ==========================================

echo [1/2] Checking for uv...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: 'uv' command not found in PATH.
    echo Please ensure uv is installed and in your PATH.
    pause
    exit /b 1
)
echo uv found.

echo [2/2] Starting Flask Backend (Dev Mode)...
echo NOTE: Direct UI changes in /frontend/web_ui/ will be served live.
uv run python backend/server.py
