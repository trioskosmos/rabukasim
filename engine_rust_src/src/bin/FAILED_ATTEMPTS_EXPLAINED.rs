/*
================================================================================
AI_GAME.RS - WHY IT FAILED (FAILED ATTEMPT #1)
================================================================================

WHAT THIS WAS SUPPOSED TO DO:
  Create a simple game runner that plays a single AI game by manually handling
  each game phase and calling search in the Main phase.

HOW IT WAS SUPPOSED TO WORK:
  1. Load database and initialize game
  2. Auto-step through non-interactive phases (like Energy, Active)
  3. In interactive phases (like Main), use TurnSequencer to find best moves
  4. Execute those moves and continue
  5. Output results (winner, scores, turns)

THE CODE:
  It's mostly clean. The structure looks reasonable:
  
  - Main loop: while not terminal and turns < 100:
    - Auto-step non-interactive phases
    - In Main phase: call TurnSequencer::find_best_main_sequence()
    - Execute the sequence
    - Pass if still in Main phase
    - Similar for LiveSet phase
  
  The logic seems sound!

WHY IT FAILED (IN PRACTICE):
  ----------------------------------------
  [PROBLEM] The code got stuck in the RPS phase for hours
  ----------------------------------------
  
  Observation:
    - Start: phase is Rps (Rock-Paper-Scissors)
    - is_interactive() returns true (because RPS is interactive - you choose)
    - But the code tries to handle it in the match statement
    - Match doesn't have a specific case for Rps
    - Falls through to generic case: "get legal action ids and step"
    - But stepping in Rps doesn't seem to progress it to next phase
    - Loops forever
  
  Root Cause:
    The game engine's phase machine has internal logic for progressing 
    phases that isn't exposed well. Simply calling step() with a legal 
    action doesn't guarantee phase progression. The engine might need:
    - Multiple steps in some phases
    - Auto-step() calls for internal progression
    - Proper sequencing that simple.rs handles correctly
  
  Why simple_game.rs Works:
    It doesn't try to be clever. It:
    1. Auto-steps ALL non-Main/LiveSet/LiveResult phases blindly
    2. Only handles those 3 special phases
    3. Trusts the engine to handle the rest
    4. Never gets stuck

THE LESSON:
  ❌ Don't reinvent phase handling - use the engine's intended API
  ❌ Don't make assumptions about phase progression
  ✓ Trust simple_game.rs which already works

STATUS: ABANDONED - Use simple_game.exe instead

================================================================================
AI_BATTLE.RS - WHY IT FAILED (FAILED ATTEMPT #2)
================================================================================

WHAT THIS WAS SUPPOSED TO DO:
  Similar to ai_game.rs but with a twist:
  - Distinguishes between interactive and non-interactive phases
  - Non-interactive: Get legal actions, step first one (or auto_step)
  - Interactive: Handle specially (Main, LiveSet, etc)
  - Has max_auto_steps safeguard (10,000 steps max before terminating)

THE CODE LOGIC:
  ```
  while phase != Terminal and turn < 200:
    if phase.is_interactive():
      // Handle Main, LiveSet, etc.
      turn += 1
    else:
      // Non-interactive: try get_legal_action_ids, else auto_step
      auto_steps += 1
      
      // After 500 steps, print progress
      if auto_steps % 500 == 0:
        log progress
  ```

WHY IT FAILED:
  Output when we ran it:
    [auto] Phase: Rps Count: 500
    [auto] Phase: Rps Count: 1000
    [auto] Phase: Rps Count: 1500
    ... (continuing forever)
    [auto] Phase: Rps Count: 10000
    [ERROR] Too many auto-steps, terminating

  WHAT'S HAPPENING:
    - The code gets into "non-interactive" check for Rps
    - Rps is NOT actually non-interactive (you need to choose)
    - But is_interactive() might be returning false
    - Or the phase isn't progressing when we call step()
    - Stuck in Rps phase, looping 500+ times per second
    - Eventually hits auto_steps limit and gives up

ROOT CAUSE (SAME AS AI_GAME.RS):
  The game engine's phase machine is more complex than these attempts
  understood. Rps doesn't progress correctly with:
    - Simple step() calls
    - Choosing random legal actions
    - Or auto_step()
  
  The real issue: GameState's internal state machine for phases is
  sophisticated and has implicit rules these simple approaches don't follow.

WHY SIMPLE_GAME.EXE Works:
  It handles the startup phases completely differently:
  
  ```
  while not Main and not Terminal:
    match phase:
      Rps | Mulligan | TurnChoice | Response:
        legal = get_legal_action_ids()
        action = random choice from legal
        step(action)
      _:
        auto_step()
  ```
  
  This EXPLICITLY handles the phases that can get stuck, and uses random
  selection for them (not just "first action").
  
  After this loop, it's guaranteed to be in Main phase or Terminal.

THE LESSON:
  ❌ Trying to be "generic" with phase handling fails
  ❌ Assuming is_interactive() or simple step() progression fails
  ✓ Explicitly handle known-tricky phases (Rps, Mulligan, etc.)
  ✓ Trust simple_game.s which has battlefield-tested phase handling

STATUS: ABANDONED - Use simple_game.exe instead

================================================================================
COMPARISON - WHY SIMPLE_GAME.RS IS THE RIGHT APPROACH
================================================================================

DESIGN PHILOSOPHY:

simple_game.rs:
  - Don't try to be clever or generic
  - Explicitly handle the ~10 known game phases
  - Trust the engine for its internal logic
  - Focus on the game loop, not phase architecture
  - Result: WORKS reliably

ai_game.rs:
  - Tries to be generic ("is_interactive()")
  - Fall-through logic for unknown phases
  - Assumes step() always progresses correctly
  - Result: Gets stuck in Rps

ai_battle.rs:
  - Similar generic approach
  - Adds safeguards (auto_steps limit)
  - Safeguards help fail gracefully, but don't fix root problem
  - Result: Gets stuck in Rps after 10,000 steps

================================================================================
WHY THIS MATTERS
================================================================================

WHAT YOU LEARNED:
  1. Game engines are complex - don't assume simple APIs work
  2. Having a working reference implementation (simple_game.rs) is invaluable
  3. When stuck, use the reference (don't reinvent the wheel)
  4. Explicit > Implicit for phase handling

FOR YOUR NEXT WORK:
  - All game simulation should use simple_game.exe
  - Don't write custom game runners (high failure risk)
  - Focus on the AI (heuristic weights, search depth, etc.)
  - simple_game.rs is battle-tested; don't mess with it

================================================================================
*/
