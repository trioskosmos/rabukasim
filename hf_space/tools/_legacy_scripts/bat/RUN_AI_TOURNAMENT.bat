@echo off
title LovecaSim - RUN AI TOURNAMENT
cls

echo ========================================================
echo   LovecaSim - PARALLEL AI TOURNAMENT
echo ========================================================
echo   Running round-robin tournament between different eras.
echo   - 8192-dim (Real Vision - IMAX PRO)
echo   - 320-dim  (Tactical/Legacy)
echo   - 128-dim  (Global/Historic)
echo ========================================================
echo.

set /p "NUM_GAMES=Enter games per pairing (default 10): "
if "%NUM_GAMES%"=="" set NUM_GAMES=10

set /p "PARALLEL=Enter parallel workers (default %NUMBER_OF_PROCESSORS%): "
if "%PARALLEL%"=="" set PARALLEL=%NUMBER_OF_PROCESSORS%

echo [LAUNCH] Starting Tournament...
uv run python ai/arena_tournament.py --num-games %NUM_GAMES% --parallel %PARALLEL% --output benchmarks/tournament_results_formatted.md

echo.
echo [DONE] Results saved to benchmarks/tournament_results_formatted.md
pause
