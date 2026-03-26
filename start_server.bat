@echo off
setlocal
cd /d "%~dp0"
where cargo >nul 2>&1
if errorlevel 1 goto NO_CARGO

where uv >nul 2>&1
if errorlevel 1 goto NO_UV

echo [build] Checking for stale processes and syncing metadata...
powershell -NoProfile -Command "$ppid=(Get-CimInstance Win32_Process -Filter \"ProcessId=$PID\").ParentProcessId; Get-CimInstance Win32_Process -Filter \"Name='cmd.exe'\" | Where-Object { $_.CommandLine -like '*start_server.bat*' -and $_.ProcessId -ne $PID -and $_.ProcessId -ne $ppid } | Stop-Process -Force -ErrorAction SilentlyContinue; taskkill /F /IM rabuka_launcher.exe /T 2>$null; Get-NetTCPConnection -LocalPort 8000,8080,8888,3000,5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
uv run python tools/sync_metadata.py

echo [build] Preparing environment...
if not exist "data\cards.json" goto NO_DATA

set DO_FULL=0
set DEBUG_ARG=
set NN_FEATURES=--features nn
for %%a in (%*) do (
    if /i "%%~a"=="--full"   set DO_FULL=1
    if /i "%%~a"=="--debug"  set DEBUG_ARG=--debug
    if /i "%%~a"=="-d"       set DEBUG_ARG=--debug
    if /i "%%~a"=="--no-nn"  set NN_FEATURES=
)

if %DO_FULL% neq 1 goto FAST_FRAME_SYNC

echo [build] Building Python extension (maturin)...
uv run maturin develop
if errorlevel 1 goto CMD_FAIL

echo [build] Running full frame rebuild...
uv run python tools/build_cards.py %DEBUG_ARG%
if errorlevel 1 goto CMD_FAIL
goto SYNC_ASSETS

:FAST_FRAME_SYNC
echo [build] Syncing frame-native ability artifacts...
uv run python tools/sync_ability_frame_index.py
if errorlevel 1 goto CMD_FAIL
uv run python tools/codegen_abilities.py
if errorlevel 1 goto CMD_FAIL

:SYNC_ASSETS
echo [build] Synchronizing frontend assets...
uv run python tools/sync_launcher_assets.py
if errorlevel 1 goto CMD_FAIL

echo [run] Starting Rust server...
if "%DEBUG_ARG%"=="--debug" echo [run] Debug mode enabled.

start "Rabuka Launcher" /D "%~dp0launcher" cmd /k "cargo run --release %NN_FEATURES% --bin rabuka_launcher -- %DEBUG_ARG%"
if errorlevel 1 goto CMD_FAIL

echo.
echo [run] Server launched in a separate window and will open in your browser shortly.
goto END

:NO_CARGO
echo ERROR: 'cargo' not found. Please install Rust.
pause
exit /b 1

:NO_UV
echo ERROR: 'uv' not found. Please install uv.
pause
exit /b 1

:NO_DATA
echo ERROR: data\cards.json not found!
pause
exit /b 1

:CMD_FAIL
echo.
echo [!] ERROR: A command failed. Check output above for details.
pause
exit /b 1

:END
echo.
echo Server session ended.
exit /b 0
