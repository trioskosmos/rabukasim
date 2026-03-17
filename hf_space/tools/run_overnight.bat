@echo off
REM =============================================================================
REM run_overnight.bat - Overnight Training Launcher
REM Opens a visible terminal window with live training output
REM =============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Create logs directory if missing
if not exist logs (
    mkdir logs
)

REM Check Python is available
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found in PATH
    echo Please install uv or add it to your PATH
    pause
    exit /b 1
)

REM Build paths and args
set REPO_ROOT=%cd%
set SCRIPT=%REPO_ROOT%\alphazero\training\overnight_vanilla.py
set DEFAULT_ARGS=overfit --run-name vanilla_compact_abilityless_h20_onegame_overfit --cycles 1000000 --device cuda --model-preset small --batch-size 256 --train-steps-per-cycle 128 --min-buffer-samples 1 --buffer-dir alphazero/training/experience_vanilla_compact_h20_onegame_overfit --checkpoint-dir alphazero/training/vanilla_checkpoints_compact_h20_onegame_overfit --checkpoint-every-cycles 1 --max-hours 0 --seed 1337 --fixed-cycle-seed --reset-run

if defined LOVECA_OVERNIGHT_ARGS (
    set RUN_ARGS=%LOVECA_OVERNIGHT_ARGS%
) else (
    set RUN_ARGS=%DEFAULT_ARGS%
)

REM Show startup info in console
echo.
echo ============================================================
echo  Loveca Overnight Training
echo ============================================================
echo.
echo Training output will appear below. Close this window to stop.
echo.
echo Running: uv run python overnight_vanilla.py
echo %RUN_ARGS%
echo.
echo ============================================================
echo.

REM Run training directly (visible in console)
uv run python "%SCRIPT%" %RUN_ARGS%

if errorlevel 1 (
    echo.
    echo Training exited with an error. Review the traceback above.
    pause
    exit /b 1
)

echo.
echo Training exited normally.
pause

exit /b 0