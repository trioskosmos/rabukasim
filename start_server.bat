@echo off
setlocal
cd /d "%~dp0"
set "UV_CACHE_DIR=%~dp0.uv-cache"
set "UV_PYTHON_INSTALL_DIR=%~dp0.uv-python"
where cargo >nul 2>&1
if errorlevel 1 goto NO_CARGO
where uv >nul 2>&1
if errorlevel 1 goto NO_UV
if not exist "data\cards.json" goto NO_DATA

set "DEBUG_ARG="
set "NN_FEATURES=--features nn"
set "BUILD_PROFILE="
for %%a in (%*) do (
    if /i "%%~a"=="--debug"  set DEBUG_ARG=--debug
    if /i "%%~a"=="-d"       set DEBUG_ARG=--debug
    if /i "%%~a"=="--no-nn"  set NN_FEATURES=
    if /i "%%~a"=="--release" set BUILD_PROFILE=--release
)

echo [build] Running metadata sync and card compilation through uv before Cargo startup.

echo [build] Syncing metadata.
uv run --no-sync --python 3.12 python tools\sync_metadata.py
if errorlevel 1 goto CMD_FAIL

echo [build] Building compiled card artifacts.
uv run --no-sync --python 3.12 python tools\build_cards.py --quiet
if errorlevel 1 goto CMD_FAIL

set "LOVECA_SKIP_ABILITY_PIPELINE=1"

:RUN_SERVER
echo [run] Starting launcher through Cargo...
if "%BUILD_PROFILE%"=="--release" (
    echo [run] Release build enabled.
) else (
    echo [run] Debug build enabled for faster iteration.
)
echo [wait] Waiting for Cargo build and server startup. First run may take a while.
if "%DEBUG_ARG%"=="--debug" echo [run] Debug mode enabled.

cargo run --manifest-path launcher\Cargo.toml %BUILD_PROFILE% %NN_FEATURES% --bin rabuka_launcher -- %DEBUG_ARG%
if errorlevel 1 goto CMD_FAIL

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
pause
exit /b 0
