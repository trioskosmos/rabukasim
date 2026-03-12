/*
================================================================================
SIMPLE_GAME.RS - FULLY ANNOTATED EXPLANATION
================================================================================

WHAT THIS FILE DOES:
  This is the main game simulation engine. It plays complete games between two
  identical AIs and collects statistics about each game (winner, scores, turns,
  number of evaluations, time taken).

WORKFLOW:
  1. Load vanilla card database from JSON
  2. Load/build two identical decks
  3. Run N games (one at a time)
  4. For each game:
     a. Initialize GameState with both players' decks
     b. Auto-step through non-interactive phases (RPS, Mulligan)
     c. In Main phase: Call TurnSequencer::plan_full_turn() to find best moves
     d. Execute best sequence, pass if no more moves
     e. Continue until game reaches Terminal phase
  5. Aggregate statistics and output as JSON

================================================================================
STRUCT: GameResult
================================================================================
This represents ONE completed game's outcome.

  game_id: Which game number this was (0, 1, 2, ... in batch)
  seed: Random seed used for random choices during setup phases
  winner: 0 (P0 wins), 1 (P1 wins), or 2 (Draw)
  score_p0: Final material count player 0 has
  score_p1: Final material count player 1 has
  turns: How many turns were played (each player takes turns)
  duration_secs: Wall-clock time this game took (useful for profiling)
  evaluations: Total number of game states evaluated by DFS (the AI's "thinks")

WHY THIS MATTERS:
  - Lower evaluations = faster AI = preference
  - If two AIs have same win rate, the one with fewer evals is better (faster)
  - Comparing across games shows if optimizations are working

================================================================================
STRUCT: BatchSummary
================================================================================
This aggregates multiple GameResult entries.

  total_games: How many games were played
  p0_wins, p1_wins, draws: Win counts for each player
  avg_score_p0, avg_score_p1: Average final scores per player
  avg_turns: Average game length
  total_evaluations: Sum of all evals across all games
  results: List of individual GameResult entries

WHY THIS MATTERS:
  - Shows overall balance (are wins 50-50?)
  - Shows if one AI is playing faster than the other
  - Data for comparing different heuristic weights

================================================================================
FUNCTION: choose_best_live_result_action()
================================================================================
WHAT: Selects which live card to use during the Live Result phase
  Live Result phase: After a performance, you pick which of your 2 live cards
  takes the damage if it was defeated.

HOW:
  1. Get current player's live zone (the 2 live cards they're using)
  2. Get all legal actions (which are live card selections)
  3. Iterate through legal actions:
     - Actions 600-602 represent which live card to pick
     - Look up that card's "score" value in the database
     - Remember the one with highest score (strategy: save high-score lives)
  4. Return that action

WHY:
  This is a simple strategy during Live Result phase where exhaustive search
  doesn't make sense (phase ends immediately after picking). So we use a heuristic:
  "lose the lowest-scoring live card" to preserve high-value lives.

================================================================================
FUNCTION: load_vanilla_db()
================================================================================
WHAT: Loads the card database from JSON file

HOW:
  1. Try multiple possible paths (current dir, parent, grandparent)
     - Why: Different working directories depending on where you run from
  2. Read cards_vanilla.json
  3. Parse JSON into CardDatabase struct
  4. Mark it as vanilla (not abilities-enabled)
  5. Return it

WHY:
  GameState operations need to know:
  - Which cards are valid?
  - What do they cost?
  - What are their abilities? (if any)
  The CardDatabase provides this.

================================================================================
FUNCTION: load_deck()
================================================================================
WHAT: Reads a deck list from a text file and converts it to card IDs

INPUT FORMAT:
  # Comments start with #
  U1 x2           # Card U1, 2 copies
  U2 x1           # Card U2, 1 copy
  R1              # Card R1 (implicit 1 copy)

OUTPUT:
  (members, lives) - card IDs split into member cards and live cards

HOW:
  1. Parse each line as: card_no [x count]
  2. Convert card_no to internal card ID using CardDatabase::id_by_no()
  3. Determine if card is a live card or member card
  4. Add to appropriate list
  5. Pad/truncate to standard sizes (48 members, 12 lives)

WHY:
  Decks are defined as human-readable card numbers (U1, R2, etc).
  The game engine works with internal IDs. This converts between them.

================================================================================
FUNCTION: run_single_game()
================================================================================
THIS IS THE MAIN GAME LOOP - MOST IMPORTANT FUNCTION

INPUTS:
  game_id: Which game this is (for logging)
  seed: Random number seed (for reproducibility)
  db: Card database
  p0_deck, p1_deck: Both players' deck lists
  silent: Suppress verbose logging

RETURNS:
  GameResult struct with the game outcome

HIGH-LEVEL FLOW:

  1. INITIALIZATION
     - Create blank GameState
     - Initialize with both players' decks, energy, lives
     - Prepare 30-turn timeout

  2. SETUP PHASE LOOP
     - While not Main phase and not Terminal:
       * If phase is Rps, Mulligan, etc: pick random legal action
       * Else: auto_step (let engine progress automatically)
     - This gets past the non-interactive startup phases

  3. MAIN GAME LOOP
     - While game not Terminal and turns <= 20:

       if phase == Main:
         |
         +-- Call TurnSequencer::plan_full_turn()
         |   This runs exhaustive DFS with alpha-beta pruning.
         |   Returns: (best_sequence, value, break_reason, eval_count)
         |   "best_sequence" = vector of card play action IDs
         |   "eval_count" = how many game nodes were evaluated
         |
         +-- Execute each action in sequence
         |   (while phase still Main)
         |
         +-- If still in Main: Pass (end turn)

       if phase == Active/Draw/Energy:
         | Auto-step (automatic progression)

       if phase == LiveSet:
         | Find best live cards to play (search for best setup)
         | Execute the sequence

       if phase == LiveResult:
         | Choose which live card to pick (simple heuristic)

       if phase == PerformanceP1/P2:
         | Auto-step

       if phase == Terminal:
         | Game over - break

  4. RESULT COLLECTION
     - Record: winner, scores, turn count, elapsed time, total evals

COMPLEXITY:
  This function is doing the heavy lifting:
  - Handling all 10+ game phases
  - Calling exhaustive search (TurnSequencer) in Main phase
  - Tracking statistics
  - Respecting time limits

KEY INSIGHT:
  The AI "thinking" only happens in Main phase (TurnSequencer::plan_full_turn).
  All other phases are deterministic (auto_step or simple heuristic).

EXAMPLE EXECUTION TRACE:
  Turn 1: RPS (random action) -> Mulligan (random) -> Main (DFS finds 3 moves)
          Execute moves, Pass. (Collected 50K evals)
  Turn 2: Energy (auto), Main (DFS finds 5 moves). (Collected 120K evals)
  Turn 3: Live phase, Performance, Live Result (heuristic)
  ...
  Turn 9: Terminal phase reached
  Result: P1 wins 1-0, 9 turns, 51.57s, 1.73M total evals

================================================================================
FUNCTION: main()
================================================================================
WHAT: Entry point, parse CLI arguments, run game batch

ARGUMENTS SUPPORTED:

  --count N: Play N games (default 1)
  
  --seed N: Use N as first seed (games use N, N+1, N+2, ...)
  
  --silent: Don't print per-game progress
  
  --json: Output results as machine-readable JSON
  
  --deck-p0 PATH: Custom deck file for player 0
  --deck-p1 PATH: Custom deck file for player 1
  
  --weight key=value: Override heuristic weight in TurnSequencer config
    Examples:
      --weight board_presence=3.0  (increase scoring for card quantity)
      --weight max_dfs_depth=8     (search only 8 moves deep instead of 15)
      --weight energy_penalty=1.0  (penalize low energy more/less)
  
  --no-alpha-beta: Disable pruning (for benchmarking)
  --no-memo: Disable memoization (for benchmarking)
  --beam-search: Use beam search fallback (experimental)

EXECUTION:

  1. Parse all arguments and set config
  2. Load vanilla card database
  3. Load/build deck lists
  4. Run game batch in parallel (actually sequential, but could be parallel)
  5. Collect all GameResult entries
  6. Compute averages and statistics
  7. Output in human-readable or JSON format

OUTPUT EXAMPLES:

  Human readable:
    ╔════════════════════════════════════════╗
    ║ Simple Game Runner - Batch Mode      ║
    ╚════════════════════════════════════════╝
    [DB] Loaded vanilla data
    [DECK] P0: ai/decks/liella_cup.txt | P1: ai/decks/liella_cup.txt
    [BATCH] Running 5 games starting with seed 100

    ╔════════════════════════════════════════╗
    ║ Batch Complete                       ║
    ╚════════════════════════════════════════╝
    Total Time: 254.31s
    Wins: P0=3 (60.0%) | P1=2 (40.0%) | Draws=0
    Avg Score: P0=1.40 | P1=0.60
    Avg Turns: 8.50

  JSON:
    {
      "total_games": 5,
      "p0_wins": 3,
      "p1_wins": 2,
      "draws": 0,
      "avg_score_p0": 1.4,
      "avg_score_p1": 0.6,
      "avg_turns": 8.5,
      "total_evaluations": 8500000,
      "results": [
        {
          "game_id": 0,
          "seed": 100,
          "winner": 0,
          "score_p0": 2,
          "score_p1": 0,
          "turns": 9,
          "duration_secs": 51.57,
          "evaluations": 1730802
        },
        ...
      ]
    }

================================================================================
TYPICAL USAGE
================================================================================

Play 1 game, show JSON:
  ./simple_game.exe --count 1 --json 2>/dev/null | python -m json.tool

Play 5 games, human output:
  ./simple_game.exe --count 5

Play 10 games with custom weights:
  ./simple_game.exe --count 10 --weight board_presence=2.5 --weight max_dfs_depth=8 --json

Compare no-pruning vs pruning (benchmark):
  ./simple_game.exe --count 1 --no-alpha-beta  # Slow!
  ./simple_game.exe --count 1                   # Fast!

================================================================================
WHY THIS APPROACH WORKS
================================================================================

EXHAUSTIVE VS HEURISTIC:
  During Main phase, we try EVERY legal move sequence using DFS.
  This guarantees optimal play (best move found).
  Alpha-beta pruning makes it fast enough (45-50 seconds per 9-turn game).

PHASED ARCHITECTURE:
  The game engine breaks gameplay into phases (Main, Active, Energy, etc).
  Each phase either:
    a) Gets AI decision (Main, LiveSet) - use exhaustive search
    b) Automatic + trivial (Active, Energy, Draw) - auto_step
    c) Simple heuristic (LiveResult) - choose best live card
  This makes the system tractable.

RANDOM SEEDING:
  Setup phases use random choices (RPS, Mulligan).
  Using different seeds shows variance in outcomes.
  But the same seed always gives same initial board state.

STATISTICAL AGGREGATION:
  One game isn't conclusive (luck).
  Multiple games show true win rate.
  Comparing batches with different weights shows which is better.

================================================================================
*/
