@echo off
setlocal

for %%I in ("%~dp0..") do set "REPO_ROOT=%%~fI"
if not exist "%REPO_ROOT%\start_server.bat" goto NO_ROOT

call "%REPO_ROOT%\start_server.bat" %*
exit /b %errorlevel%

:NO_ROOT
echo ERROR: Could not find the repo root start_server.bat next to scripts\.
pause
exit /b 1
