@echo off
setlocal enabledelayedexpansion
title LovecaSim - START FULL VECTOR TRAINING

:: --- MODE SELECTION (Edit in Wordpad/Notepad) ---
:: Observation Model: COMPRESSED (Fastest), STANDARD (Balanced), IMAX (Pro Vision)
set "OBS_MODE=COMPRESSED"

:: Training Start: TRUE (Start fresh), FALSE (Continue from latest checkpoint)
set "RESTART_TRAINING=FALSE"

:: --- CONFIGURATION ---
set "TRAIN_BATCH_SIZE=32768"
set "TRAIN_ENVS=256"
set "TRAIN_N_STEPS=256"
set "OMP_NUM_THREADS=12"
set "SAVE_FREQ_MINS=60"

:: --- Hyperparameters ---
set "TRAIN_STEPS=10000000000000"
set "LEARNING_RATE=3e-4"
set "NUM_EPOCHS=5"
set "ENT_COEF=0.05"
set "GAMMA=0.98"
set "GAE_LAMBDA=0.95"

:: --- Game Rules/Limits ---
set "GAME_TURN_LIMIT=40"
set "GAME_REWARD_WIN=10.0"
set "GAME_REWARD_LOSE=-10.0"
set "GAME_REWARD_SCORE_SCALE=1.0"
set "GAME_REWARD_TURN_PENALTY=-0.02"

:: --- Checkpoint ---
set "LOAD_CHECKPOINT=LATEST"

echo ========================================================
echo   LovecaSim - FULL VECTOR TRAINING
echo ========================================================
echo   Envs:       %TRAIN_ENVS%
echo   Batch Size: %TRAIN_BATCH_SIZE%
echo   Steps/Env:  %TRAIN_N_STEPS%
echo   Threads:    %OMP_NUM_THREADS%
echo   Start Mode: %RESTART_TRAINING% (TRUE=Restart, FALSE=Continue)
echo   Obs Mode:   %OBS_MODE%
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
