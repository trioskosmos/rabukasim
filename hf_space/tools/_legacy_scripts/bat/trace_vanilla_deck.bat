@echo off
setlocal

:: Set Environment Variables for Fixed Deck Vanilla Training
set USE_FIXED_DECK=ai/vanilla_deck.md
set OBS_MODE=COMPRESSED
set GAME_TURN_LIMIT=40

echo ==================================================
echo  Running Vanilla Deck Trace (Verbose)
echo  Output: fixed_deck_trace.txt
echo ==================================================

:: Run the Python trace script and redirect output to a standard text file
uv run python ai/trace_fixed_game.py > fixed_deck_trace.txt

echo.
echo Trace Complete!
echo Open 'fixed_deck_trace.txt' to view the full game breakdown.
echo.

pause
