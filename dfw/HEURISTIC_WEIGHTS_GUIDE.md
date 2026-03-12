/*
================================================================================
HEURISTIC WEIGHTS & TUNING GUIDE
================================================================================

This document explains what each heuristic weight does and how to tune them
for different AI playstyles.

================================================================================
WHAT ARE HEURISTIC WEIGHTS?
================================================================================

The AI plays by exhaustive search, but at the end (leaf nodes), it needs to
score game positions to decide "is this a good position or bad?"

These weights control that scoring:
  - High weight on board_presence -> encourage playing cards
  - High weight on energy_penalty -> encourage saving energy
  - Etc.

Different weight combinations produce different playstyles and win rates.

FORMAT TO USE:
  ./simple_game.exe --weight key=value --weight key2=value2 ...

================================================================================
WEIGHT: max_dfs_depth
================================================================================

WHAT IT DOES:
  How many card plays to explore into the future
  
  Example:
    Value 5: "I'll search 5 moves ahead"
    Value 15: "I'll search 15 moves ahead"

RANGE: 1-25 typical
  1-5:   Shallow, very fast, low quality
  8-10:  Balance point, fast but decent quality
  12-15: Deep search, good quality, moderate speed
  20+:   Very deep search, optimal play, SLOW

DEFAULT: 15

EFFECT ON GAMEPLAY:
  Lower (5-8):
    - Faster decisions (1-5 seconds per turn)
    - Plays greedily (short-term thinking)
    - May miss combo opportunities
    - Total game time: 10-20 seconds
  
  Default (15):
    - Balanced speed/quality
    - Sees medium-term consequences
    - Can plan and react
    - Total game time: 40-60 seconds
  
  Higher (20-25):
    - Slower decisions (30-120 seconds per turn)
    - Plays strategically (considers future)
    - Finds subtle tactics
    - Total game time: 3-5+ minutes

TUNING ADVICE:
  Start with 15 for testing.
  If too slow, reduce to 8-10.
  If AI seems dumb, increase to 18-20.

COMMAND EXAMPLE:
  # Fast AI
  ./simple_game.exe --count 5 --weight max_dfs_depth=8
  
  # Slow optimal AI
  ./simple_game.exe --count 5 --weight max_dfs_depth=18

================================================================================
WEIGHT: board_presence
================================================================================

WHAT IT DOES:
  Bonus for having cards in play (in your board zone)
  
  High value: "I really want lots of cards out"
  Low value: "Cards in hand are fine, don't rush to play"

RANGE: 0.5-5.0 typical
  <1.0:   Discourages playing cards (hoarding strategy)
  1.0:    Neutral (play if beneficial)
  >2.0:   Encourages playing cards (spam strategy)

DEFAULT: 1.0

EFFECT ON GAMEPLAY:
  Low (0.5-0.8):
    - Keeps cards in hand
    - Careful, defensive play
    - Waits for perfect moment to play
    - Lower board presence but better card selection
  
  Default (1.0):
    - Plays cards opportunistically
    - Balanced hand/board
    - Natural gameplay
  
  High (2.0-3.0):
    - Plays cards aggressively
    - Full board quickly
    - May deplete hand
    - Can run out of moves

TUNING ADVICE:
  1.0 is usually good default.
  If one AI consistently wins, try:
    - Winning AI: lower board_presence (more careful)
    - Losing AI: higher board_presence (more aggressive)

COMMAND EXAMPLE:
  # Conservative AI
  ./simple_game.exe --count 5 --weight board_presence=0.7
  
  # Aggressive AI
  ./simple_game.exe --count 5 --weight board_presence=2.5

================================================================================
WEIGHT: blades / hearts
================================================================================

WHAT IT DOES:
  Bonuses for having Blade cards or Heart cards in specific zones
  
  These are game-specific card types in Loveca.
  Higher value -> more attracted to those card types

RANGE: 0.0-2.0 typical
  0.0:    Don't care about this card type
  1.0:    Neutral weighting
  >1.5:   Strongly prefer this card type

DEFAULT: 1.0 each

EFFECT ON GAMEPLAY:
  Blades > Hearts:
    - AI prioritizes Blade cards
    - Blade-focused deck strategy
    - May ignore Hearts
  
  Hearts > Blades:
    - AI prioritizes Heart cards
    - Heart-focused deck strategy
    - May ignore Blades
  
  Equal:
    - AI treats them neutrally
    - Balanced strategy

TUNING ADVICE:
  Leave at 1.0 unless you want to force a specific card type strategy.
  These are more for meta-game tuning than AI balance.

COMMAND EXAMPLE:
  # Blade-focused AI (higher Blade weight)
  ./simple_game.exe --count 5 --weight blades=2.0 --weight hearts=0.8

================================================================================
WEIGHT: saturation_bonus
================================================================================

WHAT IT DOES:
  Bonus when cards in play match each other (all same type or color)
  
  High value: "Mix tokens are bad, I want all matching cards"
  Low value: "It's okay to have mixed types"

RANGE: 0.0-3.0 typical
  0.0:    No bonus for matching (any card type is fine)
  1.0:    Mild bonus for saturation
  >2.0:   Strong preference for matching

DEFAULT: Found in code; typically 1.0-1.5

EFFECT ON GAMEPLAY:
  Low (0.0-0.5):
    - Plays any card that's playable
    - No preference for matching
    - Chaotic board state
  
  Medium (1.0):
    - Mild preference for matching types
    - Natural balance
  
  High (2.0-3.0):
    - Strong push toward single type
    - Can miss opportunities if board doesn't match
    - Tunnel-vision toward "pure" boards

TUNING ADVICE:
  Leave at default unless you want to experiment.
  Higher values make AI more "rigid" (good or bad depending on meta).

================================================================================
WEIGHT: energy_penalty
================================================================================

WHAT IT DOES:
  Penalty for having low energy (resources)
  
  High penalty: "Never let energy drop, it's critical"
  Low penalty: "Energy is less important"

RANGE: 0.5-3.0 typical
  <1.0:   Energy is not very important
  1.0:    Energy is somewhat important
  >2.0:   Energy is very important (don't spend recklessly)

DEFAULT: 1.0

EFFECT ON GAMEPLAY:
  Low (0.5):
    - Spends energy freely
    - Can run out and be stuck
    - Aggressive play
  
  Default (1.0):
    - Balances energy spending
    - Plans ahead for energy needs
    - Normal play
  
  High (2.0-3.0):
    - Hoards energy
    - Conservative spending
    - Can miss opportunities to win due to being too cautious

TUNING ADVICE:
  1.0 is usually good.
  If games stall out (both AIs running low on energy), try 0.8-0.9.
  If one AI dies due to energy starvation, increase penalty to 1.5-2.0.

COMMAND EXAMPLE:
  # Energy-conscious AI (hoards energy)
  ./simple_game.exe --count 5 --weight energy_penalty=2.0
  
  # Reckless AI (spends freely)
  ./simple_game.exe --count 5 --weight energy_penalty=0.7

================================================================================
WEIGHT: live_ev_multiplier
================================================================================

WHAT IT DOES:
  Multiplier for the value of live cards (your special cards)
  
  High multiplier: "Live cards are precious, protect them"
  Low multiplier: "Live cards aren't that important"

RANGE: 0.5-3.0 typical
  <1.0:   Live cards not as valued
  1.0:    Live cards are fairly important
  >2.0:   Live cards are very important

DEFAULT: 1.0

EFFECT ON GAMEPLAY:
  Low (0.5-0.8):
    - AI doesn't fear losing live cards
    - Risky play with lives exposed
    - Trades lives aggressively
  
  Default (1.0):
    - AI protects lives appropriately
    - Balanced strategy
  
  High (2.0-3.0):
    - AI is overly cautious with lives
    - May make suboptimal plays to protect lives
    - Very defensive

TUNING ADVICE:
  1.0 is usually right.
  If games seem to hinge heavily on live card luck, try 1.5+.
  If lives seem undervalued, increase to 1.5-2.0.

================================================================================
WEIGHT: uncertainty_penalty_pow
================================================================================

WHAT IT DOES:
  How much to penalize uncertain outcomes
  
  High value: "Avoid risky plays, prefer safe ones"
  Low value: "Take risks if potential payoff is high"

RANGE: 0.5-2.0 typical
  <1.0:   Risk-taker (gambler)
  1.0:    Neutral risk assessment
  >1.5:   Risk-averse (cautious)

DEFAULT: 1.0

EFFECT ON GAMEPLAY:
  Low (0.5):
    - Goes for high-variance plays
    - Sometimes wins big, sometimes loses spectacularly
    - Exciting but unpredictable
  
  Default (1.0):
    - Assesses risk fairly
    - Plays solid moves
    - Good balance
  
  High (1.5-2.0):
    - Avoids risky plays
    - Prefers guaranteed small gains over risky big gains
    - Safe but possibly slow

TUNING ADVICE:
  Leave at 1.0 for most testing.
  Only adjust if you notice AI being overly risky or overly cautious.

================================================================================
WEIGHT: liveset_placement_bonus
================================================================================

WHAT IT DOES:
  Bonus for having good live card setup (which live cards to use)
  
  High value: "Getting the right lives in play is critical"
  Low value: "Any live setup is fine"

RANGE: 0.5-3.0 typical
  <1.0:   Live placement doesn't matter much
  1.0:    Live placement is important
  >2.0:   Live placement is very important

DEFAULT: 1.0

EFFECT ON GAMEPLAY:
  Low (0.5-0.8):
    - Doesn't care about live card synergy
    - Plays lives randomly
    - Board state less coordinated
  
  Default (1.0):
    - Tries to set up good live combinations
    - Balanced setup strategy
  
  High (2.0-3.0):
    - Obsesses over perfect live setup
    - May waste cards trying to synergize lives
    - Can get stuck trying to optimize placement

TUNING ADVICE:
  1.0 is usually right.
  If live cards have strong synergies in your deck, increase to 1.5-2.0.
  If lives are mostly independent, decrease to 0.8.

================================================================================
PREDEFINED CONFIGURATION PROFILES
================================================================================

AGGRESSIVE:
  max_dfs_depth=8
  board_presence=2.0
  energy_penalty=0.7
  live_ev_multiplier=0.8
  
  Playstyle: Fast, risky, plays lots of cards

BALANCED (DEFAULT):
  max_dfs_depth=15
  board_presence=1.0
  energy_penalty=1.0
  live_ev_multiplier=1.0
  
  Playstyle: Good speed and decision quality

CONSERVATIVE:
  max_dfs_depth=15
  board_presence=0.7
  energy_penalty=2.0
  live_ev_multiplier=2.0
  
  Playstyle: Slow, careful, protective

DEEP_TACTICAL:
  max_dfs_depth=20
  board_presence=1.0
  energy_penalty=1.0
  live_ev_multiplier=1.0
  
  Playstyle: Optimal play but SLOW (3-5 min per game)

FAST_TACTICAL:
  max_dfs_depth=8
  board_presence=1.0
  energy_penalty=1.0
  live_ev_multiplier=1.0
  
  Playstyle: Good balance of speed and quality

================================================================================
HOW TO TUNE FOR BALANCE
================================================================================

GOAL: Make two AIs play close to 50-50

STEP 1: Run baseline
  ./simple_game.exe --count 10 --json > baseline.json
  Result: Check if wins are close to 50-50

STEP 2: If not balanced, identify issue
  If AI A wins consistently:
    CAUSE: AI A is better strategist OR gets lucky more
    FIX: Make AI A play worse or AI B play better
  
STEP 3: Make AI A play worse
  Reduce its search depth:
    --weight max_dfs_depth=10 (vs default 15)
  
  OR reduce its aggression:
    --weight board_presence=0.8 (vs default 1.0)
  
STEP 4: Re-test
  ./simple_game.exe --count 10 --weight max_dfs_depth=10 --json
  Check if closer to 50-50

STEP 5: Fine-tune
  Repeat until both AIs win ~50% of games

COMMAND EXAMPLE:
  Baseline:
    ./simple_game.exe --count 20 --json > baseline.json
    # Shows P0 wins 14/20, P1 wins 6/20 (P0 too strong)
  
  Handicap P0:
    ./simple_game.exe --count 20 --weight max_dfs_depth=8 --json > variant.json
    # Re-test for balance

================================================================================
ADVANCED: CREATING SPECIFIC PLAYSTYLES
================================================================================

DEFENSIVE LIVE-FOCUSED:
  max_dfs_depth=12
  board_presence=0.6
  live_ev_multiplier=3.0
  energy_penalty=2.0
  saturation_bonus=2.0
  
  Playstyle: Protect lives at all costs, coordinated board

AGGRESSIVE SPAM:
  max_dfs_depth=8
  board_presence=3.0
  energy_penalty=0.5
  live_ev_multiplier=0.5
  uncertainty_penalty_pow=0.5
  
  Playstyle: Play lots of cards fast, take risks

SURGICAL OPTIMAL:
  max_dfs_depth=18
  board_presence=1.0
  energy_penalty=1.2
  live_ev_multiplier=1.0
  uncertainty_penalty_pow=1.1
  
  Playstyle: Optimal play accounting for slight uncertainty

================================================================================
TROUBLESHOOTING WEIGHT ISSUES
================================================================================

PROBLEM: AI seems random/doesn't improve over time
  CHECK: Is max_dfs_depth too low? (Try 12-15)
  CHECK: Is board_presence 0? (Try 1.0)

PROBLEM: AI plays cards constantly, runs out of resources
  SOLUTION: Increase energy_penalty (1.5-2.0)
  SOLUTION: Decrease board_presence (0.5-0.8)

PROBLEM: AI is too cautious, never takes risks
  SOLUTION: Decrease energy_penalty (0.7)
  SOLUTION: Increase uncertainty_penalty_pow (0.5-0.8)

PROBLEM: AI doesn't value live cards enough
  SOLUTION: Increase live_ev_multiplier (1.5-2.0)

PROBLEM: One AI always wins despite seemingly equal weights
  CAUSE: Probably due to phase initialization RNG (RPS luck)
  SOLUTION: Run more games to average out luck (20+ games)
  SOLUTION: Or add small handicap to winning AI

================================================================================
MEASURING THE EFFECT OF WEIGHT CHANGES
================================================================================

BEFORE:
  10 games with default weights
  P0 wins: 6, P1 wins: 4
  Avg evals: 1.5M per game

AFTER:
  10 games with max_dfs_depth=8
  P0 wins: 5, P1 wins: 5 (more balanced)
  Avg evals: 0.4M per game (3.75x faster)

ANALYSIS:
  - Shallower search DID hurt P0 specifically
  - P0 must rely on deep lookahead
  - Shallower search made it more balanced
  - Trade-off: faster but less optimal for both

================================================================================
*/
