@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set SCRIPT_PATH=alphazero\training\overnight_vanilla.py
set OUTPUT_DIR=checkpoints\vanilla_mcts_one_position_tiny
set BUFFER_DIR=buffers\vanilla_mcts_one_position_tiny
set LOG_CSV=%OUTPUT_DIR%\training_log.csv
set BENCHMARK_LOG=%OUTPUT_DIR%\benchmark_log.csv
set PROOF_LOG=%OUTPUT_DIR%\single_seed_proof.csv
set PROOF_JSON=%OUTPUT_DIR%\single_seed_proof.json
set RUN_LOCK=%OUTPUT_DIR%\.run_lock
set PYTHONUNBUFFERED=1

echo.
echo ===========================================================
echo Vanilla Overnight Fast-Win Curriculum
echo ===========================================================
echo Mode: Neural MCTS self-play (teacher-free)
echo Goal: Overfit one fixed opening overnight with isolated tiny-model checkpoints and buffers
echo.

REM Detect Python - try multiple methods
set PYTHON=
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else (
    for /f "delims=" %%A in ('where python 2^>nul') do (
        set PYTHON=%%A
        goto found_python
    )
    echo ERROR: Python not found in .venv or system PATH
    echo Please activate your virtual environment first or install Python
    if not defined LOVECA_NO_PAUSE pause
    exit /b 1
)

:found_python
echo [OK] Python: %PYTHON%

REM Verify Python works
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python executable failed to run
    echo Executable: %PYTHON%
    if not defined LOVECA_NO_PAUSE pause
    exit /b 1
)

REM Check training entrypoint exists in the repo
if not exist "%SCRIPT_PATH%" (
    echo ERROR: Training script not found: %SCRIPT_PATH%
    if not defined LOVECA_NO_PAUSE pause
    exit /b 1
)
echo [OK] Training script: %SCRIPT_PATH%

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"
set USE_RUN_LOCK=0
if not defined LOVECA_VANILLA_ARGS set USE_RUN_LOCK=1
if "%USE_RUN_LOCK%"=="1" (
    if exist "%RUN_LOCK%" (
        powershell -NoProfile -Command "$hasLive = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'python*.exe' -and $_.CommandLine -like '*%BUFFER_DIR%*' }).Count -gt 0; if (-not $hasLive) { Remove-Item -LiteralPath '%RUN_LOCK%' -Recurse -Force -ErrorAction SilentlyContinue }" >nul 2>&1
    )
    mkdir "%RUN_LOCK%" 2>nul
    if errorlevel 1 (
        echo ERROR: Another overnight vanilla run is already using %OUTPUT_DIR%
        echo Stop the existing training process or remove %RUN_LOCK% if it is stale.
        if not defined LOVECA_NO_PAUSE pause
        exit /b 1
    )
)

REM Clean the repo root by moving stale proof artifacts into the checkpoint folder.
if exist "single_seed_proof*.csv" move /Y "single_seed_proof*.csv" "%OUTPUT_DIR%\" >nul
if exist "single_seed_proof*.json" move /Y "single_seed_proof*.json" "%OUTPUT_DIR%\" >nul

if defined LOVECA_VANILLA_ARGS (
    set RUN_ARGS=%LOVECA_VANILLA_ARGS%
) else (
    REM Fresh one-position overnight self-play profile with fixed opening seed, no teacher forcing, and uncapped value targets.
    set RUN_ARGS=train --iterations 100000 --games 100 --steps 64 --search-sims 192 --neural-mcts-batch-size 100 --max-turns 10 --model-preset tiny --device cuda --batch-size 2048 --buffer-size 262144 --min-buffer-items 512 --target-replay-ratio 12 --actor-temperature 0.20 --actor-epsilon 0.00 --seed 600005 --curriculum-eval-games 8 --single-seed-target-reward 1.90 --single-seed-target-decisive-rate 1.0 --single-seed-target-fast-win-rate 0.90 --single-seed-target-avg-turns 6 --checkpoint-dir %OUTPUT_DIR% --buffer-dir %BUFFER_DIR% --log-csv %LOG_CSV% --benchmark-log-csv %BENCHMARK_LOG% --proof-log-csv %PROOF_LOG% --proof-output-json %PROOF_JSON% --training-target-mode neural_mcts --selfplay-action-source search_greedy --selfplay-seed-mode fixed_single --deck-rotation-mode single --benchmark-every 25
)

echo.
echo Output dir: %OUTPUT_DIR%
echo Command: %PYTHON% %SCRIPT_PATH% %RUN_ARGS%
echo ===========================================================
echo.

%PYTHON% %SCRIPT_PATH% %RUN_ARGS%
set EXIT_CODE=!ERRORLEVEL!
if "%USE_RUN_LOCK%"=="1" rmdir "%RUN_LOCK%" 2>nul

echo.
if "!EXIT_CODE!"=="0" (
    echo [SUCCESS] Training completed normally
) else (
    echo [ERROR] Training exited with code !EXIT_CODE!
)
echo.
if not defined LOVECA_NO_PAUSE pause
exit /b !EXIT_CODE!