@echo off
setlocal

echo ==========================================
echo Love Live! AI - Puzzle Solver Demo
echo ==========================================
echo.
echo This script demonstrates Scenario Mode by:
echo 1. Generating a specific mid-game puzzle (Score 2-2, 1 move to win).
echo 2. Running an untrained AI on it (Baseline).
echo 3. Training a PPO agent specifically on this puzzle.
echo 4. Evaluating the trained agent to show it learned the solution.
echo.

:: Configuration
set USE_SCENARIOS=1
set SCENARIO_REWARD_SCALE=1.0
set OBS_MODE=STANDARD
set TRAIN_ENVS=16

:: 1. Generate Puzzle
echo [1/3] Generating Puzzle State...
python ai/create_puzzle.py
if errorlevel 1 goto error

:: 2. Run Experiment
echo [2/3] Running Experiment (Baseline -> Train -> Eval)...
python ai/train_puzzle_experiment.py
if errorlevel 1 goto error

echo.
echo [3/3] Demo Complete!
echo You should see the Win Rate increase significantly.
goto end

:error
echo.
echo [ERROR] An error occurred during the demo.
pause
exit /b 1

:end
pause
