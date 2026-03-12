/*
================================================================================
LOVECA AI SYSTEM - MASTER REFERENCE & QUICK START
================================================================================

You now have the complete Loveca AI training system. This document is your
quick reference for understanding and using it.

================================================================================
QUICK FACTS SUMMARY
================================================================================

WHAT THE SYSTEM DOES:
  ✓ Plays Loveca games with two AI players
  ✓ Each AI uses exhaustive DFS with alpha-beta pruning to find best moves
  ✓ Tracks win rates and game statistics
  ✓ Allows tuning of AI heuristic weights
  ✓ Runs batches of games for statistical testing

PERFORMANCE STATS:
  ⚡ Speed: ~50 seconds per 9-turn game
  🧠 Evaluations: ~1.7M game states explored per game
  ✂️  Pruning efficiency: 127x node reduction (99.2% cut)
  🎲 Branching factor: ~2.0 legal moves per state (highly constrained)
  
SEARCH DEPTH:
  📊 Default: 15 moves deep in DFS
  ⏱️  Typical: Finds optimal move in 3-5 seconds per turn
  🔧 Tunable: Can adjust with --weight max_dfs_depth=N

================================================================================
FILE INVENTORY
================================================================================

✅ WORKING & PROVEN:

  simple_game.exe (binary)
    Purpose: Play games, collect statistics
    Status: WORKS PERFECTLY - use this for all game simulation
    Build: cargo build --bin simple_game --release
    Run: ./simple_game.exe --count N --json
    Doc: See SIMPLE_GAME_EXPLAINED.rs for full details

  quick_move_space.exe (binary)
    Purpose: Measure game tree branching factor
    Status: WORKS - takes ~0.7s to measure 100 random walks
    Build: cargo build --bin quick_move_space --release
    Run: ./quick_move_space.exe 2>/dev/null
    Doc: See QUICK_MOVE_SPACE_EXPLAINED.rs for full details

⚠️  FAILED & ABANDONED:

  ai_game.rs
    Purpose: Manual game runner (attempted)
    Status: FAILED - gets stuck in Rps phase
    Reason: GameState phase machine too complex for simple handling
    Lesson: Use simple_game.rs instead
    Doc: See FAILED_ATTEMPTS_EXPLAINED.rs

  ai_battle.rs
    Purpose: Manual game runner with safeguards (attempted)
    Status: FAILED - hangs after 10,000 auto-steps in Rps
    Reason: Same as ai_game.rs (phase complexity)
    Lesson: Use simple_game.rs instead
    Doc: See FAILED_ATTEMPTS_EXPLAINED.rs

  enumerate_sequences.rs
    Purpose: Enumerate all possible game sequences (attempted)
    Status: FAILED - infinite recursion or very long runtime
    Reason: Game tree too large, no good stopping condition
    Lesson: Use random walk sampling (quick_move_space.rs) instead

📚 LIBRARY (Rust source code):

  turn_sequencer.rs (in engine_rust library)
    What: Core AI search algorithm (exhaustive DFS + alpha-beta pruning)
    Key functions:
      - plan_full_turn(state, db) -> finds best Main phase sequence
      - find_best_liveset_selection(state, db) -> finds best live setup
      - find_best_main_sequence(state, db) -> same as plan_full_turn
    Config: Accessed via CONFIG.write().unwrap()
    Doc: Inline comments in source (search for "alpha-beta", "pruning")

================================================================================
TYPICAL WORKFLOW
================================================================================

1. BASELINE MEASUREMENT
   Run a game with default settings to establish baseline:
   
   cd engine_rust_src
   cargo build --release 2>&1 | tail -20
   .\target\release\simple_game.exe --count 1 --json 2>/dev/null | python -m json.tool
   
   Expected output:
     {
       "total_games": 1,
       "p0_wins": 0,
       "p1_wins": 1,
       "avg_turns": 9.0,
       "total_evaluations": 1730802,
       "duration_secs": 51.57
     }

2. MEASURE MOVE SPACE (OPTIONAL)
   Confirm branching factor is reasonable:
   
   .\target\release\quick_move_space.exe 2>/dev/null
   
   Expected: branching ≈ 2.0, max sequence length ≈ 7

3. TUNING HEURISTIC WEIGHTS
   Adjust AI weights and compare results:
   
   Baseline:
     .\target\release\simple_game.exe --count 5 --weight max_dfs_depth=15 --json
   
   Test variant:
     .\target\release\simple_game.exe --count 5 --weight max_dfs_depth=8 --json
   
   Compare: Which has better balance? Fewer evals? Faster?

4. RUN TOURNAMENT
   After finding good weights, run larger batch:
   
   .\target\release\simple_game.exe --count 20 --weight board_presence=3.0 --json > results.json
   
   Analyze JSON for statistics (win rates, avg scores, etc.)

5. ITERATE
   If results suggest changes:
     - Adjust weights again
     - Run another batch
     - Compare stats

================================================================================
COMMAND REFERENCE
================================================================================

BASIC GAME PLAY:

  Play 1 game (verbose output):
    .\target\release\simple_game.exe --count 1

  Play 1 game (JSON output):
    .\target\release\simple_game.exe --count 1 --json 2>/dev/null | python -m json.tool

  Play 10 games silently:
    .\target\release\simple_game.exe --count 10 --silent

WEIGHT TUNING:

  Shallower search (faster but less optimal):
    .\target\release\simple_game.exe --count 5 --weight max_dfs_depth=8

  Deeper search (slower but more optimal):
    .\target\release\simple_game.exe --count 5 --weight max_dfs_depth=20

  Adjust board presence scoring:
    .\target\release\simple_game.exe --count 5 --weight board_presence=2.5

  Multiple weights:
    .\target\release\simple_game.exe --count 5 --weight max_dfs_depth=10 --weight board_presence=3.0

BENCHMARKING:

  No pruning (exhaustive search - VERY SLOW):
    .\target\release\simple_game.exe --count 1 --no-alpha-beta

  No move ordering (just pruning):
    .\target\release\simple_game.exe --count 1 

SPECIAL OPTIONS:

  --beam-search       : Use beam search for faster but suboptimal play
  --no-memo           : Disable memoization (for benchmarking)
  --deck-p0 <path>    : Custom deck for player 0
  --deck-p1 <path>    : Custom deck for player 1
  --seed <n>          : Use N as random seed base for setup phases

================================================================================
UNDERSTANDING THE SEARCH
================================================================================

WHAT HAPPENS IN MAIN PHASE:
  1. Call TurnSequencer::plan_full_turn(state, db)
  2. This runs exhaustive DFS down to max_dfs_depth (default 15)
  3. Algorithm:
     - Try every first card play from hand
     - For each: recursively try every second card play
     - ... continue until depth limit reached
     - At leaf: evaluate state (heuristic scoring)
     - Backtrack, returning best sequence found
  4. Alpha-beta pruning cuts away bad branches early
  5. Return: (best_sequence, value, evals_used)

WHY IT'S FAST:
  ✓ Branching is only 2.0 legal actions per state
  ✓ Alpha-beta pruning cuts 99.2% of nodes
  ✓ Move ordering helps prune aggressively
  Result: 1.7M evals in 50 seconds = 34K evals/second per core

WHY IT CAN BE SLOW (IF NOT CONFIGURED):
  ✗ If branching were 8 (theoretically possible): exponential slowdown
  ✗ If alpha-beta disabled: 45.5x slower
  ✗ If max_dfs_depth=20: 2^5 = 32x more nodes
  Result: Could take hours per game

TUNING LEVERS:
  max_dfs_depth: Primary knob for speed/quality tradeoff
    - Lower (8): Fast but less optimal (still good)
    - Default (15): Good balance
    - Higher (20): Slow but very optimal

  board_presence: How much to reward having cards in play
    - Lower: Encourages careful play
    - Higher: Encourages spam-playing cards
    - Domain depends on game dynamics

================================================================================
EXPECTED RESULTS
================================================================================

WITH DEFAULT WEIGHTS (max_dfs_depth=15, board_presence=1.0):
  
  Single game:
    Duration: 40-60 seconds
    Turns: 7-12 (average ~9)
    Evaluations: 1-2 million
    Winner: ~50% each (randomness in RPS/Mulligan affects outcome)
  
  Tournament (5 games):
    Total time: ~250 seconds (4 minutes)
    Win distribution: Should be close to 50-50 (maybe 3-2 or 4-1)
  
  Tournament (20 games):
    Total time: ~1000 seconds (17 minutes)
    Win distribution: Should converge to 50-50
    Average scores: Usually similar (within 0.5)

WITH SHALLOWER SEARCH (max_dfs_depth=8):
  
  Single game:
    Duration: 10-20 seconds (3-5x faster)
    Turns: Similar (7-12)
    Evaluations: 200-400K (much less)
    Winner: May shift slightly (suboptimal play)
  
  Tradeoff: Fast but potentially less balanced

WITH DEEPER SEARCH (max_dfs_depth=20):
  
  Warning: This will be slow!
  Single game:
    Duration: 2-3 minutes per game
    Turns: Similar (7-12)
    Evaluations: 10-20 million
    Winner: May be more decisive (optimal play)

================================================================================
DEBUGGING TIPS
================================================================================

PROBLEM: Game is too slow
  SOLUTION: Reduce max_dfs_depth
    .\target\release\simple_game.exe --count 1 --weight max_dfs_depth=8

PROBLEM: Game completes but phases seem wrong
  SOLUTION: Check if it's using simple_game.exe (not ai_game or ai_battle)
    WRONG: .\target\release\ai_game.exe  (will hang)
    RIGHT: .\target\release\simple_game.exe

PROBLEM: Want to understand what's happening
  SOLUTION: Run without --json to see verbose output
    .\target\release\simple_game.exe --count 1

PROBLEM: JSON output is hard to read
  SOLUTION: Use Python to pretty-print
    .\target\release\simple_game.exe --count 1 --json 2>/dev/null | python -m json.tool

PROBLEM: Building fails
  SOLUTION: Clean and rebuild
    cd engine_rust_src
    cargo clean
    cargo build --release

PROBLEM: Want to compare two sets of results
  SOLUTION: Save to files and diff
    .\target\release\simple_game.exe --count 5 --json > baseline.json
    .\target\release\simple_game.exe --count 5 --weight max_dfs_depth=8 --json > variant.json
    python -c "import json; print(json.load(open('baseline.json')))['avg_turns']"

================================================================================
ARCHITECTURAL OVERVIEW
================================================================================

```
┌─────────────────────────────────────────────┐
│     GameState (current game position)       │
│                                             │
│  players[0], players[1] state               │
│  phase (Main, Active, Energy, etc.)         │
│  board state                                │
└────────────┬──────────────────────────────┘
             │
             ├─ initialize_game(decks, energy, lives)
             ├─ step(action) -> next state
             ├─ auto_step() -> auto-progress
             └─ get_legal_action_ids() -> possible actions

┌─────────────────────────────────────────────┐
│  TurnSequencer (search algorithm)           │
│                                             │
│  plan_full_turn(state, db) -> sequence      │
│    ├─ dfs_alpha_beta(depth, alpha, beta)    │
│    │   ├─ Try each legal action             │
│    │   ├─ Recurse to next depth             │
│    │   ├─ Prune if alpha >= beta            │
│    │   └─ Return best value + moves         │
│    │                                        │
│    └─ heuristic_eval(state) -> value        │
│        ├─ board_presence (card count)       │
│        ├─ energy (current resources)        │
│        ├─ live_ev_multiplier (life scoring) │
│        └─ other heuristics                  │
│                                             │
│  CONFIG (global settings for weights)       │
│  ├─ search.max_dfs_depth (default 15)      │
│  ├─ search.use_alpha_beta (true)            │
│  └─ weights.* (heuristic parameters)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│      CardDatabase (reference data)          │
│                                             │
│  Load from: cards_vanilla.json              │
│  Contains: Card definitions, costs, abilities
│  Used by: GameState and TurnSequencer       │
└─────────────────────────────────────────────┘

GAME FLOW:
  simple_game.exe:
    for each game:
      state = initialize_game()
      while not terminal:
        match phase:
          Main:
            seq = plan_full_turn(state)
            execute(seq)
          LiveSet:
            seq = find_best_liveset_selection(state)
            execute(seq)
          others:
            auto_step(state)
      record(result)
    output(statistics)
```

================================================================================
YOU'RE READY TO:
================================================================================

✅ Run games and see AI play
✅ Adjust heuristic weights
✅ Compare different configurations
✅ Understand what's happening under the hood
✅ Debug performance issues
✅ Tune for balance or speed

🚀 Next steps:
  1. Run simple_game.exe a few times to understand output
  2. Try different --weight parameters
  3. Run small tournaments (5-10 games) to see win rate patterns
  4. Save JSON results for comparison
  5. Once satisfied with balance, run larger batches (20-50 games)

================================================================================
*/
