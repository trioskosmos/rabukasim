@echo off
setlocal

echo Running AlphaZero Vanilla Benchmark as Training Loop (Overnight)...
cd /d "%~dp0"

REM This runs the benchmark in a continuous loop to generate training data
REM Using the working benchmark logic instead of the broken training loop
uv run python -m alphazero.training.benchmark_vanilla --sims 128 --loop

pause
