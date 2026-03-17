@echo off
echo Stopping all Python processes (Training workers)...
taskkill /F /IM python.exe >nul 2>&1
echo Done.
pause
