@echo off
setlocal
cd /d "%~dp0"
set "UV_CACHE_DIR=%~dp0.uv-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv-python"
where cargo >nul 2>&1
if errorlevel 1 goto NO_CARGO

where uv >nul 2>&1
if errorlevel 1 goto NO_UV

echo [build] Checking for stale processes and syncing metadata...
rem Best-effort cleanup only. Keep startup quiet on systems that restrict process enumeration.
taskkill /F /IM rabuka_launcher.exe /T >nul 2>nul
uv run --isolated --managed-python --python 3.12 python tools/sync_metadata.py

echo [build] Preparing environment...
if not exist "data\cards.json" goto NO_DATA

set "DO_FULL=0"
set "DEBUG_ARG="
set "NN_FEATURES=--features nn"
for %%a in (%*) do (
    if /i "%%~a"=="--full"   set DO_FULL=1
    if /i "%%~a"=="--debug"  set DEBUG_ARG=--debug
    if /i "%%~a"=="-d"       set DEBUG_ARG=--debug
    if /i "%%~a"=="--no-nn"  set NN_FEATURES=
)

if not "%DO_FULL%"=="1" goto FAST_FRAME_SYNC

echo [build] Building Python extension (maturin)...
uv run --isolated --managed-python --python 3.12 maturin develop
if errorlevel 1 goto MATURIN_FAILED

echo [build] Compiling runtime cards and syncing live copies...
uv run --isolated --managed-python --python 3.12 python tools/build_cards.py --force --sync-launcher-assets
if errorlevel 1 goto CMD_FAIL
goto RUN_SERVER

:MATURIN_FAILED
echo [warn] maturin develop failed; continuing without the Python extension.

:FAST_FRAME_SYNC
echo [build] Compiling runtime cards and syncing live copies...
uv run --isolated --managed-python --python 3.12 python tools/build_cards.py --sync-launcher-assets
if errorlevel 1 goto CMD_FAIL

:RUN_SERVER
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
