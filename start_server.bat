@echo off
setlocal
cd /d "%~dp0"
where cargo >nul 2>&1
if errorlevel 1 goto NO_CARGO

where uv >nul 2>&1
if errorlevel 1 goto NO_UV

uv run python tools/sync_metadata.py
powershell -NoProfile -Command "$ppid = (Get-CimInstance Win32_Process -Filter \"ProcessId = $PID\").ParentProcessId; Get-CimInstance Win32_Process -Filter \"Name = 'cmd.exe'\" | Where-Object { $_.CommandLine -like '*start_server.bat*' -and $_.ProcessId -ne $PID -and $_.ProcessId -ne $ppid } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

taskkill /F /IM rabuka_launcher.exe /T 2>nul
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,8080,8888,3000,5000 -ErrorAction SilentlyContinue | ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; if ($p -and $p.ProcessName -notmatch 'chrome|msedge|firefox|brave|browser') { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } }"

echo [build] Preparing environment...
if not exist "data\cards.json" goto NO_DATA

echo [build] Checking card data parity...
uv run python -m compiler.main --check
if not errorlevel 1 goto SKIP_CARD_BUILD

echo [build] Compiling card data...
uv run python -m compiler.main --export-profile runtime
if errorlevel 1 goto CMD_FAIL

echo [build] Syncing authored ability frames into runtime index...
uv run python tools/sync_ability_frame_index.py --input data/ability_frames.json --metadata data/metadata.json --output data/ability_frame_index.json
if errorlevel 1 goto CMD_FAIL

echo [build] Generating Rust optimizations...
uv run python tools/codegen_abilities.py
if errorlevel 1 goto CMD_FAIL

goto SYNC_ASSETS

:SKIP_CARD_BUILD
echo [build] Card data is up to date. Skipping compiler, frame sync, and codegen.

set DO_FULL=0
set DEBUG_ARG=
for %%a in (%*) do (
    if /i "%%~a"=="--full" set DO_FULL=1
    if /i "%%~a"=="--debug" set DEBUG_ARG=--debug
    if /i "%%~a"=="-d" set DEBUG_ARG=--debug
)

if %DO_FULL% neq 1 goto SKIP_MATURIN
echo [build] Building Python extension (maturin)...
uv run maturin develop
if errorlevel 1 goto CMD_FAIL
goto SYNC_ASSETS

:SKIP_MATURIN
echo [build] Skipping Python extension build (use --full).

:SYNC_ASSETS
echo [build] Synchronizing frontend assets...
uv run python tools/sync_launcher_assets.py
if errorlevel 1 goto CMD_FAIL

echo [run] Starting Rust server...
if "%DEBUG_ARG%"=="--debug" echo [run] Debug mode enabled.

start "Rabuka Launcher" /D "%~dp0launcher" cmd /k "cargo run --release --features nn --bin rabuka_launcher -- %DEBUG_ARG%"
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
