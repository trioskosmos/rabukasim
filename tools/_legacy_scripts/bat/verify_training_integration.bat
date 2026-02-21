@echo off
setlocal
echo ===================================================
echo  VERIFYING TRAINING INTEGRATION (FAST TEST)
echo ===================================================

:: Fast Config
set TRAIN_ENVS=64
set TRAIN_STEPS=2048
set TRAIN_N_STEPS=32
set TRAIN_BATCH_SIZE=2048
set NUM_EPOCHS=2
set OMP_NUM_THREADS=4

echo [Config] Envs: %TRAIN_ENVS%, Steps: %TRAIN_STEPS%
uv run python ai/train_vectorized.py

echo.
echo [Done] If no crash above, Training Integration is SUCCESS.
pause
