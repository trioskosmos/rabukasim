@echo off
setlocal

:: ========================================================
:: LovecaSim - ATTENTION MODEL TRAINING
:: ========================================================
:: This script launches training using the Attention-based
:: Feature Extractor for long-term strategic learning.
:: ========================================================

:: --- EDITABLE SETTINGS ---
set OBS_MODE=ATTENTION
set RESTART_TRAINING=0
set TRAIN_ENVS=8
set TRAIN_BATCH_SIZE=2048
set TRAIN_N_STEPS=512
set TRAIN_TOTAL_TIMESTEPS=5000000
set LEARNING_RATE=0.0003
set ENTROPY_COEF=0.01
set GPU_ENV=1
set SAVE_FREQ_MINS=15

:: Log/Checkpoint Settings
set MODEL_NAME=attention_ppo
:: -------------------------

echo ========================================================
echo   LovecaSim - ATTENTION MODEL TRAINING
echo ========================================================
echo   Envs:       %TRAIN_ENVS%
echo   Batch Size: %TRAIN_BATCH_SIZE%
echo   Steps/Env:  %TRAIN_N_STEPS%
echo   Start Mode: %RESTART_TRAINING% (TRUE=Restart, FALSE=Continue)
echo   Obs Mode:   %OBS_MODE%
echo ========================================================

:: Ensure environment is clean
if exist data\cards_numba.json (
    echo [SETUP] Re-compiling Numba Bytecode for safety...
)
uv run python compiler/numba_compiler.py

echo [LAUNCH] Starting Training Loop...
uv run python ai/train_vectorized.py

pause
