@echo off
setlocal enabledelayedexpansion
title LovecaSim - START VANILLA DECK TRAINING

:: --- MODE SELECTION (Edit in Wordpad/Notepad) ---
:: Observation Model: COMPRESSED (Fastest), STANDARD (Balanced), IMAX (Pro Vision)
set "OBS_MODE=ATTENTION"

:: Training Start: TRUE (Start fresh), FALSE (Continue from latest checkpoint)
set "RESTART_TRAINING=FALSE"

:: GPU Environment: 0 (CPU Numba), 1 (GPU CUDA for 5-10x speedup)
:: Requires: pip install cupy-cuda12x (adjust for your CUDA version)
set "USE_GPU_ENV=0"

:: --- CONFIGURATION ---
set "USE_FIXED_DECK=ai/vanilla_deck.md"
set "TRAIN_BATCH_SIZE=512"
set "TRAIN_ENVS=16"
set "TRAIN_N_STEPS=512"
set "OMP_NUM_THREADS=12"
set "SAVE_FREQ_MINS=60"

:: --- Hyperparameters ---
set "TRAIN_STEPS=10000000000000"
set "LEARNING_RATE=3e-4"
set "NUM_EPOCHS=5"
set "ENT_COEF=0.01"
set "GAMMA=0.98"
set "GAE_LAMBDA=0.95"

:: --- Game Rules/Limits ---
set "GAME_TURN_LIMIT=40"
set "GAME_REWARD_TURN_PENALTY=-0.02"

:: --- Checkpoint ---
set "LOAD_CHECKPOINT=LATEST"

echo ========================================================
echo   LovecaSim - VANILLA DECK TRAINING
echo ========================================================
echo   Deck File:  %USE_FIXED_DECK%
echo   Envs:       %TRAIN_ENVS%
echo   Batch Size: %TRAIN_BATCH_SIZE%
echo   Steps/Env:  %TRAIN_N_STEPS%
echo   Threads:    %OMP_NUM_THREADS%
echo   Start Mode: %RESTART_TRAINING% (TRUE=Restart, FALSE=Continue)
echo   Obs Mode:   %OBS_MODE%
echo   GPU Env:    %USE_GPU_ENV% (0=CPU, 1=GPU CUDA)
echo ========================================================
echo.

:: Setup
echo [SETUP] Compiling Numba Bytecode...
uv run python ai/compile_numba_db.py
if %ERRORLEVEL% NEQ 0 ( pause & exit /b )

:: Launch TensorBoard (Background)
start "TensorBoard" /min uv run tensorboard --logdir=./logs/vector_tensorboard/ --port 6007

:: Launch Training
echo [LAUNCH] Starting Training Loop...
uv run python ai/train_vectorized.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Training exited with code %ERRORLEVEL%.
    pause
)
pause
