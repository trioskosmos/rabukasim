@echo off
setlocal

echo Running AlphaZero Vanilla Training...
cd /d "%~dp0"
uv run python -m alphazero.training.vanilla_training --sims 64 --loop

pause
