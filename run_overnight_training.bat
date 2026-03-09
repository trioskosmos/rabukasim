@echo off
setlocal

echo Running AlphaZero Vanilla Training Loop (Overnight)...
cd /d "%~dp0"

REM This runs the training in a continuous loop to generate training data
REM Use --neural-mcts flag for True AlphaZero self-play learning
uv run python -m alphazero.training.vanilla_training --sims 128 --loop --neural-mcts

pause
