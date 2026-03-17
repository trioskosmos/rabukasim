@echo off
REM ============================================================================
REM VANILLA STRATEGY COMPARISON - Gaming Session Runner
REM ============================================================================
REM
REM This batch file runs the strategy comparison test suite. Multiple strategies
REM compete against each other over a series of games using the UV Python environment.
REM
REM QUICK START: Just run this file! Default settings will run a comprehensive
REM tournament with all 4 strategies competing.
REM
REM ============================================================================
REM CONFIGURATION - Edit these lines to customize
REM ============================================================================

REM How many games to play per matchup?
REM LOW (3):  Quick test, ~5 minutes for full tournament
REM MED (5):  Standard test, ~15 minutes for full tournament  
REM HIGH (10+): Comprehensive, ~30+ minutes for full tournament
set NUM_GAMES=50

REM Time allowed per move in seconds (balance between speed and decision quality)
REM 0.1s = Fast but poor decisions
REM 0.3s = RECOMMENDED - Good balance
REM 0.5s = Slow but very good decisions
REM MCTS especially benefits from more time
set TIME_PER_MOVE=0.1

REM Mode: "tournament" (all matchups) or "custom" (specific pair)
REM Set to "tournament" to run all 4 strategies against each other
REM Set to "custom" to run just one matchup below
set MODE=tournament

REM For "custom" mode: Which strategies to compare?
REM Available: turnseq, neural, mcts, random
REM Examples:
REM   turnseq vs random    (fast baseline test)
REM   turnseq vs neural    (planning beats neural?)
REM   turnseq vs mcts      (planning vs Monte Carlo search)
REM   neural vs mcts       (high-quality search comparison)
REM   neural vs random     (baseline neural performance)
REM   mcts vs random       (baseline MCTS performance)
set STRATEGY_P0=turnseq
set STRATEGY_P1=neural

REM ============================================================================
REM SETUP (uses uv Python environment)
REM ============================================================================

cd /d "%~dp0"

echo.
echo ============================================================================
echo VANILLA STRATEGY COMPARISON TOURNAMENT
echo ============================================================================
echo.
echo Using uv Python environment (all dependencies auto-managed)
echo.

REM Show tournament mode
echo.
echo ============================================================================
if "%MODE%"=="tournament" (
    echo TOURNAMENT MODE - All 4 strategies vs each other
    echo ============================================================================
    echo.
    echo Matchups: 6 total
    echo   1. TurnSeq vs Random
    echo   2. TurnSeq vs Neural
    echo   3. TurnSeq vs MCTS
    echo   4. Neural vs Random
    echo   5. Neural vs MCTS
    echo   6. MCTS vs Random
) else (
    echo CUSTOM MODE - Single matchup
    echo ============================================================================
)
echo.
echo Settings:
echo   Games per matchup: %NUM_GAMES%
echo   Time per move:     %TIME_PER_MOVE% seconds
if "%MODE%"=="custom" (
    echo   Strategy 1:        %STRATEGY_P0%
    echo   Strategy 2:        %STRATEGY_P1%
)
echo.
echo Starting...
echo ============================================================================
echo.

REM Run the comparison using uv (manages all Python dependencies)
cd /d "%~dp0"

if "%MODE%"=="tournament" (
    REM Tournament mode: run all matchups
    call uv run python tools/compare_vanilla_strategies.py --games %NUM_GAMES% --time-per-move %TIME_PER_MOVE% --verbose
) else (
    REM Custom mode: run specific matchup
    call uv run python tools/compare_vanilla_strategies.py --games %NUM_GAMES% --time-per-move %TIME_PER_MOVE% --players %STRATEGY_P0% %STRATEGY_P1% --verbose
)

set BUILD_ERROR=%ERRORLEVEL%

echo.
echo ============================================================================
if %BUILD_ERROR% EQU 0 (
    echo SUCCESS: Tournament completed!
) else (
    echo ERROR: Something went wrong (exit code %BUILD_ERROR%)
)
echo ============================================================================
echo.

REM Keep window open so you can see results
pause
goto end

:error
echo.
echo ERROR: Setup failed. Please check the error messages above.
echo.
pause

:end
exit /b %BUILD_ERROR%

