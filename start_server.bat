@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo Rabuka Simulator Startup
echo ==========================================

echo [1/3] Checking dependencies...
where cargo >nul 2>&1
if %errorlevel% neq 0 goto NO_CARGO

where uv >nul 2>&1
if %errorlevel% neq 0 goto NO_UV

echo [2/3] Cleaning up processes...
taskkill /F /IM rabuka_launcher.exe /T 2>nul
:: Simplified PowerShell cleanup
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,8080,8888,3000,5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

echo.
echo [3/3] Preparing Environment...
if not exist "data\cards.json" goto NO_DATA

echo Compiling Card Data...
uv run python -m compiler.main
if %errorlevel% neq 0 goto CMD_FAIL

:: Handle arguments
set DO_FULL=0
set DEBUG_ARG=
for %%a in (%*) do (
    if "%%a"=="--full" set DO_FULL=1
    if "%%a"=="--debug" set DEBUG_ARG=--debug
    if "%%a"=="-d" set DEBUG_ARG=--debug
)

if %DO_FULL% neq 1 goto SKIP_MATURIN
echo Building Python Extension (Maturin)...
uv run maturin develop
if %errorlevel% neq 0 goto CMD_FAIL
goto SYNC_ASSETS

:SKIP_MATURIN
echo Skipping Maturin build (use --full to build Python extension).

:SYNC_ASSETS
echo Synchronizing Frontend Assets...
uv run python tools/sync_launcher_assets.py
if %errorlevel% neq 0 goto CMD_FAIL

echo Running Translation Coverage Analysis...
uv run python tools/analysis/analyze_translation_coverage.py
if %errorlevel% neq 0 goto CMD_FAIL

echo.
echo Starting Rabuka Simulator Server (Rust)...
echo NOTE: Using Rust Launcher as verified Source of Truth.
if "%DEBUG_ARG%"=="--debug" echo [DEBUG MODE ENABLED]
echo.

pushd launcher
cargo run --release --bin rabuka_launcher -- %DEBUG_ARG%
set "EXIT_CODE=%errorlevel%"
popd

:: If it's a normal exit (0) or a Ctrl+C exit (non-zero common codes), go to END
if %EXIT_CODE% equ 0 goto END
if %EXIT_CODE% equ -1073741510 goto END
if %EXIT_CODE% equ 3221225786 goto END

:: Otherwise it's a real failure
goto CMD_FAIL

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
