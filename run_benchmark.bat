@echo off
setlocal

echo Running AlphaZero Vanilla Benchmark...
cd /d "%~dp0"
uv run python -m alphazero.training.benchmark_vanilla --sims 64

pause
