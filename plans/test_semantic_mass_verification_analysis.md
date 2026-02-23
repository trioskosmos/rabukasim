# Analysis Report: `test_semantic_mass_verification`

## Overview

[`test_semantic_mass_verification`](engine_rust_src/src/semantic_assertions.rs:720) is a comprehensive test function that validates card ability implementations against expected semantic behaviors. It serves as an automated oracle that compares actual game state changes against documented expectations.

## What the Test Does

### 1. Test Setup and Loading

```rust
let engine = SemanticAssertionEngine::load();
```

The engine loads:
- **Semantic Truth** (`reports/semantic_truth.json`): Expected behaviors for each card ability
- **Card Database** (`data/cards_compiled.json`): Production card definitions with bytecode
- **Dummy Cards**: Injects 100 dummy members (IDs 5000-5099) and 50 dummy lives (IDs 15000-15049) for testing

### 2. Test Execution Flow

For each card in the truth set:

```
┌─────────────────────────────────────────────────────────────┐
│                    For Each Card                            │
├─────────────────────────────────────────────────────────────┤
│  For Each Ability:                                          │
│    1. verify_card (positive test)                           │
│       - Create test state with oracle environment           │
│       - Trigger ability based on trigger type               │
│       - Execute ability bytecode                            │
│       - Compare state deltas against expected               │
│    2. verify_card_negative (negative test)                  │
│       - Create minimal state (no resources)                 │
│       - Verify ability does NOT fire inappropriately        │
└─────────────────────────────────────────────────────────────┘
```

### 3. Oracle Environment Setup

[`setup_oracle_environment()`](engine_rust_src/src/semantic_assertions.rs:349) creates a rich game state:

| Zone | Player 0 (Active) | Player 1 (Opponent) |
|------|-------------------|---------------------|
| Energy | 20 cards | 10 cards |
| Hand | 11 cards (same-group + others) | 5 cards |
| Deck | 10 members + real lives | 5 cards |
| Discard | 10 cards + lives | 5 cards |
| Stage | 3 members (card under test at center) | 3 members |
| Success Lives | 3 live cards | - |
| Score | 99 | - |

### 4. Supported Trigger Types

| Trigger | Handling |
|---------|----------|
| `OnPlay` | Card placed on stage, ability triggered |
| `OnLiveStart` | Phase set to PerformanceP1, card in live zone |
| `OnLiveSuccess` | Phase set to LiveResult, card in live zone |
| `Activated` | `activate_ability()` called, cost interactions resolved |
| `Constant` | Direct bonus check (e.g., `live_score_bonus`) |
| `None` | No trigger, direct execution |

### 5. State Delta Verification

[`diff_snapshots()`](engine_rust_src/src/semantic_assertions.rs:532) computes actual state changes:

| Delta Tag | Description | Calculation |
|-----------|-------------|-------------|
| `HAND_DELTA` | Cards drawn | `current.hand_len - baseline.hand_len` |
| `HAND_DISCARD` | Cards discarded from hand | Negative hand change |
| `SCORE_DELTA` | Score change | `current.score - baseline.score` |
| `ENERGY_DELTA` | Energy zone change | `current.energy_len - baseline.energy_len` |
| `STAGE_DELTA` | Stage member count change | Active members difference |
| `MEMBER_SACRIFICE` | Members removed from stage | Negative stage change |
| `HEART_DELTA` | Heart buff total change | Total heart buffs difference |
| `DISCARD_DELTA` | Discard pile change | `current.discard_len - baseline.discard_len` |

### 6. Auto-Bot Interaction Resolution

[`resolve_interaction()`](engine_rust_src/src/semantic_assertions.rs:316) automatically resolves player choices:

| Choice Type | Auto-Action |
|-------------|-------------|
| `MODE`, `CHOICE`, `MODAL`, `SELECT_MODE`, `LOOK_AND_CHOOSE` | Index 8000 (first option) |
| `YES_NO`, `OPTIONAL` | 8000 (Yes) |
| `COLOR` | 580 (Pink) |
| `SLOT`, `SELECT_SLOT`, `TARGET_MEMBER` | 600 (Left slot) |
| `RPS` | 10001 (Rock) |
| `HAND`, `SELECT_HAND`, `SELECT_HAND_DISCARD` | Last card in hand |
| `RECOV_L`, `SEARCH`, `SEARCH_LIVE`, `RECOV_M`, `SEARCH_MEMBER` | 8000 |

### 7. Report Generation

Results are written to [`reports/COMPREHENSIVE_SEMANTIC_AUDIT.md`](reports/COMPREHENSIVE_SEMANTIC_AUDIT.md):

```markdown
| Card No | Status | Details |
| LL-PR-004-PR | ✅ PASS | |
| LL-bp1-001-R＋ | ❌ FAIL | Ab0: Mismatch HAND_DELTA... |
```

---

## Opcode Coverage Analysis

### Opcodes WITH Semantic Tracking

These opcodes produce state changes that `diff_snapshots()` can detect:

| Opcode | Tracked As | Notes |
|--------|------------|-------|
| `O_DRAW` (10) | `HAND_DELTA` | Direct hand increase |
| `O_ADD_TO_HAND` (44) | `HAND_DELTA` | Hand increase |
| `O_DRAW_UNTIL` (66) | `HAND_DELTA` | Hand increase |
| `O_BOOST_SCORE` (16) | `SCORE_DELTA` | Live score bonus |
| `O_SET_SCORE` (37) | `SCORE_DELTA` | Direct score set |
| `O_RECOVER_LIVE` (15) | `LIVE_RECOVER`, `HAND_DELTA` | Recovery from discard |
| `O_RECOVER_MEMBER` (17) | `HAND_DELTA` | Recovery from discard |
| `O_MOVE_TO_DISCARD` (58) | `HAND_DISCARD`, `DISCARD_DELTA` | Discard from hand |
| `O_ENERGY_CHARGE` (23) | `ENERGY_DELTA` | Energy gain |
| `O_PAY_ENERGY` (64) | `ENERGY_DELTA` (active) | Energy consumption |
| `O_MOVE_MEMBER` (20) | `STAGE_DELTA` | Stage movement |
| `O_ADD_HEARTS` (12) | `HEART_DELTA` | Heart buffs |
| `O_SET_HEARTS` (25) | `HEART_DELTA` | Heart buffs |
| `O_ADD_BLADES` (11) | `BLADE_DELTA` | Blade buffs |
| `O_SET_BLADES` (24) | `BLADE_DELTA` | Blade buffs |

### Opcodes WITHOUT Semantic Tracking

These opcodes execute but their effects are **NOT captured** by the current delta system:

#### 1. Prevention/Restriction Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_PREVENT_ACTIVATE` | 82 | Sets `prevent_activate` flag | Flag not in snapshot |
| `O_PREVENT_BATON_TOUCH` | 90 | Sets `prevent_baton_touch` flag | Flag not in snapshot |
| `O_PREVENT_SET_TO_SUCCESS_PILE` | 80 | Sets `prevent_success_pile_set` flag | Flag not in snapshot |
| `O_PREVENT_PLAY_TO_SLOT` | 71 | Sets slot prevention | Flag not in snapshot |
| `O_RESTRICTION` | 35 | Adds restriction to player | Restrictions not tracked |
| `O_IMMUNITY` | 19 | Sets immunity flag | Flag not in snapshot |

#### 2. Meta-Rule/Modifier Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_META_RULE` | 29 | Modifies `cheer_mod_count` | Not in snapshot |
| `O_BATON_TOUCH_MOD` | 36 | Sets `baton_touch_limit` | Not in snapshot |
| `O_REDUCE_YELL_COUNT` | 62 | Sets `yell_count_reduction` | Not in snapshot |
| `O_REDUCE_COST` | 13 | Adds `cost_reduction` | Not in snapshot |
| `O_INCREASE_COST` | 70 | Adds cost modifier | Not in snapshot |
| `O_REDUCE_HEART_REQ` | 48 | Reduces heart requirements | Not in snapshot |
| `O_INCREASE_HEART_COST` | 61 | Increases heart cost | Not in snapshot |
| `O_REDUCE_LIVE_SET_LIMIT` | 77 | Modifies live set limit | Not in snapshot |

#### 3. Transformation Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_TRANSFORM_COLOR` | 39 | Adds to `color_transforms` | Not in snapshot |
| `O_TRANSFORM_HEART` | 73 | Transforms heart type | Not tracked per-color |
| `O_NEGATE_EFFECT` | 27 | Sets `negated_triggers` | Not in snapshot |

#### 4. Ability/State Modification Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_GRANT_ABILITY` | 60 | Grants temporary ability | Abilities not tracked |
| `O_TRIGGER_REMOTE` | 47 | Triggers another card's ability | Indirect effect |
| `O_ACTIVATE_MEMBER` | 43 | Taps member for ability | Tap state not in snapshot |
| `O_ACTIVATE_ENERGY` | 81 | Taps energy | Tap state not in snapshot |
| `O_SET_TAPPED` | 51 | Sets tap state | Tap state not in snapshot |
| `O_TAP_MEMBER` | 53 | Taps selected member | Tap state not in snapshot |
| `O_TAP_OPPONENT` | 32 | Taps opponent member | Tap state not in snapshot |

#### 5. Zone Manipulation Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_SWAP_CARDS` | 21 | Swaps cards between zones | Net change may be 0 |
| `O_SWAP_AREA` | 72 | Swaps entire areas | Complex to track |
| `O_MOVE_TO_DECK` | 31 | Moves to deck (shuffle) | Deck order not tracked |
| `O_PLACE_UNDER` | 33 | Places card under another | Under cards not tracked |
| `O_ADD_STAGE_ENERGY` | 50 | Adds energy to stage slot | Stage energy not tracked |

#### 6. Selection/Choice Opcodes (Interaction Only)
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_SELECT_MODE` | 30 | Modal choice | Choice itself not a delta |
| `O_SELECT_MEMBER` | 65 | Member selection | Selection not a delta |
| `O_SELECT_LIVE` | 68 | Live selection | Selection not a delta |
| `O_SELECT_PLAYER` | 67 | Player selection | Selection not a delta |
| `O_SELECT_CARDS` | 74 | Card selection | Selection not a delta |
| `O_COLOR_SELECT` | 45 | Color choice | Choice not a delta |
| `O_OPPONENT_CHOOSE` | 75 | Opponent makes choice | Indirect effect |

#### 7. Deck Information Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_LOOK_DECK` | 14 | Looks at deck cards | `looked_cards_len` partially tracked |
| `O_REVEAL_CARDS` | 40 | Reveals cards | Information only |
| `O_CHEER_REVEAL` | 42 | Cheer reveal | Information only |
| `O_REVEAL_UNTIL` | 69 | Reveals until condition | Partially tracked |
| `O_LOOK_AND_CHOOSE` | 41 | Look and choose | Partially tracked |
| `O_ORDER_DECK` | 28 | Orders looked cards | Order not tracked |
| `O_SEARCH_DECK` | 22 | Searches deck | Marked UNUSED |

#### 8. Play Opcodes
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_PLAY_MEMBER_FROM_HAND` | 57 | Plays member | Stage delta may capture |
| `O_PLAY_MEMBER_FROM_DISCARD` | 63 | Plays from discard | Complex zone changes |
| `O_PLAY_LIVE_FROM_DISCARD` | 76 | Plays live from discard | Complex zone changes |

#### 9. Metadata Opcodes (No Game Effect)
| Opcode | ID | Effect | Why Missed |
|--------|-----|--------|------------|
| `O_FLAVOR` | 34 | Flavor text | No effect |
| `O_REPLACE_EFFECT` | 46 | Effect replacement | Marked UNUSED |
| `O_MODIFY_SCORE_RULE` | 49 | Score rule modification | No direct effect |
| `O_ADD_CONTINUOUS` | 52 | Continuous effect | Marked UNUSED |
| `O_SET_HEART_COST` | 83 | Heart cost setting | Marked UNUSED |
| `O_FORMATION_CHANGE` | 26 | Formation change | Marked UNUSED |
| `O_SWAP_ZONE` | 38 | Zone swap | Marked UNUSED |

---

## Missing Trigger Type Support

The test only supports these triggers:

```rust
match trigger_type {
    TriggerType::OnPlay | TriggerType::OnLiveStart | 
    TriggerType::OnLiveSuccess | TriggerType::Constant | 
    TriggerType::None | TriggerType::Activated => { ... }
    _ => return Err("Trigger type not yet supported")
}
```

**Missing triggers:**
- `OnLeavesStage` - Member leaves stage
- `OnTurnEnd` - End of turn effects
- `OnOpponentTurnEnd` - Opponent's turn end
- `OnLiveFail` - Failed live effects
- `OnBatonTouch` - Baton pass effects
- `OnYell` - Yell support effects
- `OnAttack` - Attack phase effects

---

## Summary Statistics

### Opcode Coverage

| Category | Total | Tracked | Untracked |
|----------|-------|---------|-----------|
| Effect Opcodes | 58 | 15 | 43 |
| Condition Opcodes | 45 | N/A | N/A (conditions don't produce deltas) |
| Cost Types | 100+ | 0 | All (costs are pre-execution checks) |

### Key Gaps

1. **No tap state tracking** - 5 opcodes affect tap state but it's not captured
2. **No prevention flag tracking** - 5 opcodes set prevention flags
3. **No modifier tracking** - 8 opcodes modify game rules/costs
4. **No transformation tracking** - 3 opcodes transform card properties
5. **No stage energy tracking** - Energy placed on stage members
6. **No under-card tracking** - Cards placed under other cards

---

## Recommendations

### 1. Extend ZoneSnapshot

Add fields to [`ZoneSnapshot`](engine_rust_src/src/test_helpers.rs:6):

```rust
pub struct ZoneSnapshot {
    // Existing fields...
    pub tapped_members: [bool; 3],        // Track tap state
    pub prevention_flags: u8,             // Bit flags for prevent_*
    pub cost_reduction: i16,              // Cost modifiers
    pub heart_requirements: [u8; 7],      // Per-color heart reqs
    pub stage_energy: [i32; 3],           // Energy on stage slots
    pub under_cards: Vec<i32>,            // Cards placed under others
    pub color_transforms: Vec<(i32, u8)>, // Active color transforms
}
```

### 2. Add Delta Tags

Extend [`SemanticDelta`](engine_rust_src/src/semantic_assertions.rs:9) with new tags:

```rust
"TAP_DELTA"        // Members tapped/untapped
"PREVENT_SET"      // Prevention flags set
"COST_MOD"         // Cost modification applied
"HEART_REQ_MOD"    // Heart requirement changed
"STAGE_ENERGY"     // Energy added to stage
"TRANSFORM"        // Color/heart transformation
"ABILITY_GRANT"    // Ability granted to card
```

### 3. Support More Triggers

Extend [`verify_card()`](engine_rust_src/src/semantic_assertions.rs:92) to handle:
- `OnLeavesStage` - Simulate member leaving
- `OnTurnEnd` - Advance turn counter
- `OnBatonTouch` - Simulate baton pass

### 4. Improve Auto-Bot Intelligence

Make [`resolve_interaction()`](engine_rust_src/src/semantic_assertions.rs:316) smarter:
- Analyze filter attributes to select valid targets
- Consider game state when making choices
- Support multi-select interactions

---

## Conclusion

`test_semantic_mass_verification` provides valuable end-to-end testing for card abilities but has significant gaps in opcode coverage. Approximately **74% of effect opcodes** (43 of 58) produce state changes that are not captured by the current delta verification system. This means many card abilities may execute correctly but their semantic verification will fail or produce false positives.

The test is most effective for:
- Draw/discard effects
- Score modifications
- Simple recovery effects
- Basic zone movements

The test is least effective for:
- Prevention/restriction effects
- Cost/rule modifications
- Tap state changes
- Transformations
- Complex multi-zone interactions
