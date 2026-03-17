@echo off
setlocal enabledelayedexpansion
title LovecaSim - SPEED DEMON TRAINING

:: --- SPEED DEMON SETTINGS ---
:: 1. ENABLE GPU ENV (Performance Tuning)
:: Set to 0 (CPU) for < 8192 envs (Lower overhead, faster rollouts)
:: Set to 1 (GPU) for > 8192 envs (Massive parallelism)
set "USE_GPU_ENV=0"

:: 2. ATTENTION MODE (2240 dims)
:: Rich features with multi-head attention.
set "OBS_MODE=ATTENTION"

:: 3. MASSIVE PARALLELISM
:: 2048 is sweet spot for CPU Numba on 8-16 threads
set "TRAIN_ENVS=2048"

:: 4. HUGE BATCH SIZE
:: Saturation of Tensor Cores
set "TRAIN_BATCH_SIZE=8192"

:: 5. SHORT ROLLOUTS
:: Faster updates, less lag
set "TRAIN_N_STEPS=256"

:: --- CONFIGURATION ---
set "USE_FIXED_DECK="
set "OMP_NUM_THREADS=12"
set "SAVE_FREQ_MINS=30"

:: --- Hyperparameters ---
set "TRAIN_STEPS=10000000000000"
set "LEARNING_RATE=5e-4"
set "NUM_EPOCHS=4"
set "ENT_COEF=0.05"
set "GAMMA=0.98"
set "GAE_LAMBDA=0.95"

:: --- Game Rules ---
set "GAME_TURN_LIMIT=40"
set "GAME_REWARD_WIN=10.0"
set "GAME_REWARD_LOSE=-10.0"
set "GAME_REWARD_SCORE_SCALE=1.0"
set "GAME_REWARD_TURN_PENALTY=-0.02"

:: --- Checkpoint ---
set "LOAD_CHECKPOINT=LATEST"
:: Set to TRUE when changing OBS_MODE or Action Space
set "RESTART_TRAINING=FALSE"

echo ========================================================
echo   LovecaSim - SPEED DEMON MODE (GPU + AMP)
echo ========================================================
if "%USE_FIXED_DECK%"=="" (
    echo   Deck:       Random Verified Pool
) else (
    echo   Deck:       %USE_FIXED_DECK%
)
echo   Envs:       %TRAIN_ENVS%
echo   Batch:      %TRAIN_BATCH_SIZE%
echo   Steps:      %TRAIN_N_STEPS%
echo   Obs Mode:   %OBS_MODE% (Optimized)
echo   GPU Env:    %USE_GPU_ENV% (Native CUDA)
echo ========================================================
echo.

:: Setup
echo [SETUP] Extracting Verified Card Pool...
uv run python ai/extract_verified.py
if %ERRORLEVEL% NEQ 0 ( pause & exit /b )

echo [SETUP] Compiling Numba Bytecode...
uv run python ai/compile_numba_db.py
if %ERRORLEVEL% NEQ 0 ( pause & exit /b )

:: Launch TensorBoard
start "TensorBoard" /min uv run tensorboard --logdir=./logs/vector_tensorboard/ --port 6007

:: Launch Training
echo [LAUNCH] Igniting boosters...
uv run python ai/train_vectorized.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Training exited with code %ERRORLEVEL%.
    pause
)
pause
