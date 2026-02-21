@echo off
setlocal enabledelayedexpansion
title LovecaSim - SMART MATRIX BENCHMARK
cls

echo ========================================================
echo   LovecaSim - SMART MATRIX BENCHMARK
echo ========================================================
echo   This benchmark runs two phases to isolate performance factors:
echo.
echo   [PHASE 1] CPU SCALING (Variable: Envs)
echo     - Finds optimal CPU parallelism (512 vs 1024 vs 2048 Envs)
echo     - Uses safe GPU settings to avoid bottlenecks.
echo.
echo   [PHASE 2] GPU SCALING (Variable: Batch Size)
echo     - Finds max VRAM capacity and Optimization speed.
echo     - Tests 4k, 8k, 16k, 32k batches.
echo.
echo   Results saved to: benchmark_results.csv
echo ========================================================
echo.

if exist benchmark_results.csv (
    echo   [Info] deleting old benchmark_results.csv...
    del benchmark_results.csv
)

:: --- SETTINGS ---
set BENCH_DURATION_SEC=30

:: ==========================================
:: PHASE 1: CPU SCALING (Envs)
:: Fixed: Steps=128, Batch=8192
:: ==========================================

echo [Phase 1] CPU Scaling Test (1/3): 512 Envs
set BENCH_PROFILE_NAME=CPU_512
set TRAIN_ENVS=512
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=4096
uv run python ai/benchmark_train.py

echo.
echo [Phase 1] CPU Scaling Test (2/3): 1024 Envs
set BENCH_PROFILE_NAME=CPU_1024
set TRAIN_ENVS=1024
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=8192
uv run python ai/benchmark_train.py

echo.
echo [Phase 1] CPU Scaling Test (3/3): 2048 Envs
set BENCH_PROFILE_NAME=CPU_2048
set TRAIN_ENVS=2048
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=8192
uv run python ai/benchmark_train.py


:: ==========================================
:: PHASE 2: GPU SCALING (Batch Size)
:: Fixed: Envs=1024 (Standard), Steps=128
:: ==========================================

echo.
echo [Phase 2] GPU Scaling Test (1/4): 4k Batch
set BENCH_PROFILE_NAME=GPU_Batch_4k
set TRAIN_ENVS=1024
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=4096
uv run python ai/benchmark_train.py

echo.
echo [Phase 2] GPU Scaling Test (2/4): 8k Batch
set BENCH_PROFILE_NAME=GPU_Batch_8k
set TRAIN_ENVS=1024
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=8192
uv run python ai/benchmark_train.py

echo.
echo [Phase 2] GPU Scaling Test (3/4): 16k Batch
set BENCH_PROFILE_NAME=GPU_Batch_16k
set TRAIN_ENVS=1024
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=16384
uv run python ai/benchmark_train.py

echo.
echo [Phase 2] GPU Scaling Test (4/4): 32k Batch
set BENCH_PROFILE_NAME=GPU_Batch_32k
set TRAIN_ENVS=1024
set TRAIN_N_STEPS=128
set TRAIN_BATCH_SIZE=32768
uv run python ai/benchmark_train.py


echo.
echo ========================================================
echo   BENCHMARK COMPLETE
echo ========================================================
echo.
if exist benchmark_results.csv (
    column -s, -t < benchmark_results.csv 2>nul || type benchmark_results.csv
) else (
    echo   No results found.
)
echo.
pause
