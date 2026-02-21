@echo off
echo Running 100-Game AI Tournament (Parallel - Safe Mode)
echo ====================================================

:: Set path to UV if needed or assume in PATH
:: Run with limited workers (4) to prevent OOM
uv run python ai/arena_tournament_parallel.py --num-games 100 --workers 1 --output benchmarks/tournament_100_lowmem.md

echo ====================================================
echo Tournament Complete. Results saved to benchmarks/tournament_100_lowmem.md
pause
