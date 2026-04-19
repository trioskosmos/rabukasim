# Frame to Runtime Connection - Comprehensive Report

Generated: April 19, 2026

## Executive Summary

This document describes how ability **frames** (the serialized data format) connect to **runtime execution** in the Loveca game engine. The system uses a unified 5-field frame structure that gets interpreted by a central dispatcher routing to specialized handlers.

---

## 1. Frame Structure

### 1.1 Core Frame Format (`AbilityFrame`)

All ability frames use a **uniform 5-field structure** (plus optional params):

```rust
pub struct AbilityFrame {
    pub opcode: i32,      // Operation code (what to do)
    pub value: i32,       // Packed value/count/offset
    pub attr: u64,        // 64-bit packed filter attribute
    pub slot: i32,        // Packed slot information
    pub is_cost: bool,    // Whether this is a cost frame
    pub params: Value,    // Optional JSON params for complex operations
}
```

**Location**: `engine_rust_src/src/core/logic/models.rs:112-119`

### 1.2 Frame Components (Runtime View)

At runtime, frames are decomposed into `AbilityFrameComponents`:

```rust
pub struct AbilityFrameComponents<'a> {
    pub raw_opcode: i32,      // Original opcode (may include negation)
    pub opcode: i32,          // Effective opcode (negation stripped)
    pub value: i32,           // The value field
    pub filter: CardFilter,   // Decoded attr as CardFilter
    pub slot: DecodedSlot,    // Decoded slot information
    pub raw_attr: u64,        // Original attr value
    pub raw_slot: i32,        // Original slot value
    pub is_negated: bool,     // Whether condition is negated
    pub is_cost: bool,        // Whether this is a cost
    pub params: Option<&'a Value>, // Optional params reference
}
```

**Location**: `engine_rust_src/src/core/logic/models.rs:164-176`

### 1.3 Slot Decoding (`DecodedSlot`)

The `slot` field packs multiple pieces of targeting information:

```rust
pub struct DecodedSlot {
    pub target_slot: u8,           // Which slot to target (0-5)
    pub comparison: u8,            // Comparison mode for conditions
    pub source_zone: Zone,         // Source zone (Hand, Deck, Discard, etc.)
    pub dest_zone: Zone,           // Destination zone
    pub remainder_zone: u8,        // Where remainder cards go
    pub is_opponent: bool,         // Target opponent instead of self
    pub is_reveal_until_live: bool, // Special reveal-until-live flag
    pub is_baton_slot: bool,       // Is this a baton touch slot
    pub is_empty_slot: bool,       // Target empty slot
    pub is_wait: bool,             // Target wait room
    pub is_dynamic: bool,          // Dynamic condition
    pub area_idx: u8,              // Specific area index
}
```

**Location**: `engine_rust_src/src/core/logic/interpreter/instruction.rs:13-28`

---

## 2. Opcode Categories

### 2.1 Control Flow Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_RETURN` | 1 | Return from ability execution | `value`: Optional condition value |
| `O_NOP` | 0 | No operation | None |
| `O_JUMP` | 2 | Unconditional jump | `value`: Jump offset (+1 relative) |
| `O_JUMP_IF_FALSE` | 3 | Conditional jump | `value`: Jump offset if condition false |

### 2.2 Draw/Hand Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_DRAW` | 10 | Draw cards | `value`: Number of cards to draw |
| `O_DRAW_UNTIL` | 66 | Draw until condition | `value`: Target hand size |
| `O_ADD_TO_HAND` | 44 | Add specific card to hand | `value`: Card ID or filter |

### 2.3 Member State Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_ACTIVATE_MEMBER` | 43 | Activate a member | `slot`: Target slot, `attr`: Filter |
| `O_SET_TAPPED` | 51 | Set tapped state | `value`: 0=untap, 1=tap |
| `O_TAP_MEMBER` | 53 | Tap a member | `slot`: Target slot |
| `O_TAP_OPPONENT` | 32 | Tap opponent member | `slot`: Target slot |
| `O_MOVE_MEMBER` | 20 | Move member between zones | `slot`: Source/dest zones |
| `O_FORMATION_CHANGE` | 26 | Change stage formation | `value`: Permutation index |
| `O_PLAY_MEMBER_FROM_HAND` | 57 | Play member from hand | `value`: Card filter |
| `O_PLAY_MEMBER_FROM_DISCARD` | 63 | Play from discard | `value`: Card filter |

### 2.4 Deck/Zone Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_SEARCH_DECK` | 22 | Search deck | `value`: Count, `attr`: Filter |
| `O_LOOK_DECK` | 14 | Look at deck | `value`: Count |
| `O_LOOK_DECK_DYNAMIC` | 91 | Dynamic deck look | `value`: Varies |
| `O_ORDER_DECK` | 28 | Reorder deck | `value`: Number of cards |
| `O_REVEAL_UNTIL` | 69 | Reveal until condition | `value`: Stop condition |
| `O_REVEAL_CARDS` | 40 | Reveal cards | `value`: Count |
| `O_MOVE_TO_DECK` | 31 | Move to deck | `slot`: Destination (top/bottom) |
| `O_MOVE_TO_DISCARD` | 58 | Move to discard | `slot`: Source zone |
| `O_SWAP_CARDS` | 21 | Swap cards | `slot`: Card positions |
| `O_SWAP_ZONE` | 38 | Swap zones | `slot`: Zone specs |
| `O_SWAP_AREA` | 72 | Swap stage areas | `value`: Permutation |

### 2.5 Recovery Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_RECOVER_LIVE` | 15 | Recover live from discard | `value`: Count, `attr`: Filter |
| `O_RECOVER_MEMBER` | 17 | Recover member from discard | `value`: Count, `attr`: Filter |
| `O_PLAY_LIVE_FROM_DISCARD` | 76 | Play live from discard | `value`: Filter |

### 2.6 Energy Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_ENERGY_CHARGE` | 23 | Add energy | `value`: Amount |
| `O_PAY_ENERGY` | 64 | Pay energy cost | `value`: Cost amount |
| `O_PAY_ENERGY_DYNAMIC` | 96 | Dynamic energy cost | `value`: Calculated cost |
| `O_ACTIVATE_ENERGY` | 81 | Activate energy | `slot`: Target |
| `O_PLACE_ENERGY_UNDER_MEMBER` | 97 | Place energy under member | `slot`: Member slot |
| `O_ADD_STAGE_ENERGY` | 50 | Add energy to stage | `value`: Amount, `slot`: Slot |

### 2.7 Score/Heart/Blade Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_BOOST_SCORE` | 16 | Add to score | `value`: Points to add |
| `O_SET_SCORE` | 37 | Set score directly | `value`: Score value |
| `O_REDUCE_SCORE` | 92 | Reduce score | `value`: Amount |
| `O_ADD_BLADES` | 11 | Add blades | `value`: Count |
| `O_SET_BLADES` | 24 | Set blades | `value`: Count |
| `O_ADD_HEARTS` | 12 | Add hearts | `value`: Count, `attr`: Color mask |
| `O_SET_HEARTS` | 25 | Set hearts | `value`: Count, `attr`: Color |
| `O_TRANSFORM_COLOR` | 39 | Transform heart color | `value`: Target color |
| `O_TRANSFORM_HEART` | 73 | Transform heart type | `attr`/`slot`: Source/dest |
| `O_TRANSFORM_BLADES` | 127 | Transform blades | `value`: Target type |
| `O_REDUCE_HEART_REQ` | 48 | Reduce heart requirement | `value`: Amount, `slot`: Color |
| `O_INCREASE_HEART_COST` | 61 | Increase heart cost | `value`: Amount, `slot`: Color |
| `O_SET_HEART_COST` | 83 | Set heart cost | `value`: Cost value |
| `O_LOSE_EXCESS_HEARTS` | 94 | Remove excess hearts | `value`: Threshold |

### 2.8 Selection/Prompt Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_SELECT_MEMBER` | 65 | Select member | `attr`: Filter, `slot`: Zone |
| `O_SELECT_LIVE` | 68 | Select live | `attr`: Filter |
| `O_SELECT_PLAYER` | 67 | Select player | `value`: 0=self, 1=opp |
| `O_SELECT_CARDS` | 74 | Select cards | `value`: Count, `attr`: Filter |
| `O_SELECT_MODE` | 30 | Select mode | `value`: Mode ID |
| `O_LOOK_AND_CHOOSE` | 41 | Look and choose | `value`: Packed look/choose counts |
| `O_COLOR_SELECT` | 45 | Select color | `value`: Color options |
| `O_OPPONENT_CHOOSE` | 75 | Opponent makes choice | `value`: Choice type |

### 2.9 Cost-Related Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_REDUCE_COST` | 13 | Reduce cost | `value`: Amount |
| `O_INCREASE_COST` | 70 | Increase cost | `value`: Amount |
| `O_CALC_SUM_COST` | 106 | Calculate sum cost | `value`: Formula |
| `O_DIV_VALUE` | 126 | Divide value | `value`: Divisor |

### 2.10 Meta/Rule Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_META_RULE` | 29 | Apply meta rule | `value`: Rule type |
| `O_TRIGGER_REMOTE` | 47 | Trigger remote ability | `value`: Trigger type |
| `O_REPEAT_ABILITY` | 93 | Repeat ability | `value`: Times |
| `O_SET_TARGET_SELF` | 78 | Set target to self | None |
| `O_SET_TARGET_OPPONENT` | 79 | Set target to opponent | None |
| `O_NEGATE_EFFECT` | 27 | Negate an effect | `attr`: Effect filter |

### 2.11 State Modifier Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_RESTRICTION` | 35 | Apply restriction | `value`: Restriction type |
| `O_PREVENT_ACTIVATE` | 82 | Prevent activation | `value`: Duration/scope |
| `O_PREVENT_BATON_TOUCH` | 90 | Prevent baton touch | None |
| `O_PREVENT_PLAY_TO_SLOT` | 71 | Prevent play to slot | `slot`: Target slot |
| `O_PREVENT_SET_TO_SUCCESS_PILE` | 80 | Prevent success pile | None |
| `O_REDUCE_LIVE_SET_LIMIT` | 77 | Reduce live set limit | `value`: Amount |
| `O_REDUCE_YELL_COUNT` | 62 | Reduce yell count | `value`: Amount |
| `O_BATON_TOUCH_MOD` | 36 | Modify baton touch | `value`: Modification |
| `O_IMMUNITY` | 19 | Grant immunity | `value`: Immunity type |
| `O_SKIP_ACTIVATE_PHASE` | 95 | Skip activate phase | None |

### 2.12 Other Utility Opcodes

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `O_GRANT_ABILITY` | 60 | Grant ability | `value`: Ability ID |
| `O_PLACE_UNDER` | 33 | Place card under | `slot`: Target |
| `O_FLAVOR_ACTION` | 34 | Flavor text action | `value`: Action ID |
| `O_LOOK_REORDER_DISCARD` | 125 | Look & reorder discard | `value`: Count |
| `O_CHEER_REVEAL` | 42 | Cheer reveal | `value`: Count |
| `O_BUFF_POWER` | 18 | Buff power | `value`: Amount |
| `O_MODIFY_SCORE_RULE` | 49 | Modify scoring rule | `value`: Rule |

---

## 3. Condition Opcodes (C_*)

Condition opcodes evaluate game state and return boolean results:

### 3.1 Presence Checks

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `C_HAS_MEMBER` | 201 | Has member matching filter | `attr`: Filter, `val`: Specific ID |
| `C_HAS_COLOR` | 202 | Has member with color | `attr`: Color mask |
| `C_HAS_LIVE_CARD` | 214 | Has live in live zone | None |
| `C_OPPONENT_HAS` | 210 | Opponent has member | `attr`: Filter |
| `C_IS_IN_DISCARD` | 253 | Source card is in discard | None |

### 3.2 Count Comparisons

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `C_COUNT_STAGE` | 203 | Count stage members | `val`: Threshold, `attr`: Filter |
| `C_COUNT_HAND` | 204 | Count hand cards | `val`: Threshold, `slot`: Zone |
| `C_COUNT_DISCARD` | 205 | Count discard | `val`: Threshold |
| `C_COUNT_ENERGY` | 213 | Count energy | `val`: Threshold |
| `C_COUNT_GROUP` | 208 | Count group members | `val`: Group ID |
| `C_COUNT_SUCCESS_LIVE` | 218 | Count success lives | `val`: Threshold |
| `C_COUNT_LIVE_ZONE` | 230 | Count live zone | `val`: Threshold |
| `C_COUNT_HEARTS` | 223 | Count hearts | `val`: Threshold, `slot`: Color |
| `C_COUNT_BLADES` | 224 | Count blades | `val`: Threshold |
| `C_SUCCESS_PILE_COUNT` | 307 | Count success pile | `val`: Threshold |
| `C_COUNT_ENERGY_EXACT` | 301 | Exact energy count | `val`: Required count |
| `C_COUNT_BLADE_HEART_TYPES` | 302 | Count unique types | `val`: Threshold |

### 3.3 Position Checks

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `C_IS_CENTER` | 206 | Is in center slot | None |
| `C_AREA_CHECK` | 234 | Check area position | `val`: 1=left, 2=center, 3=right |
| `C_HAS_MOVED` | 228 | Member has moved this turn | None |
| `C_IS_SELF_MOVE` | 308 | Is self move | None |
| `C_IS_WAIT` | 313 | Is wait state | None |

### 3.4 Comparison Conditions

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `C_LIFE_LEAD` | 207 | Success live lead | `val`: Required lead |
| `C_SCORE_COMPARE` | 220 | Score comparison | `val`: Compare value |
| `C_COST_COMPARE` | 241 | Cost comparison | `val`: Compare value |
| `C_COST_LEAD` | 235 | Cost lead | `val`: Required lead |
| `C_SCORE_LEAD` | 236 | Score lead | `val`: Required lead |
| `C_HEART_LEAD` | 237 | Heart lead | `val`: Required lead |
| `C_OPPONENT_HAND_DIFF` | 219 | Hand size difference | `val`: Required diff |
| `C_OPPONENT_ENERGY_DIFF` | 225 | Energy difference | `val`: Required diff |
| `C_BLADE_COMPARE` | 242 | Blade comparison | `val`: Compare value |
| `C_HEART_COMPARE` | 243 | Heart comparison | `val`: Compare value |
| `C_SYNC_COST` | 311 | Sync cost comparison | `val`: Compare value |

### 3.5 State Checks

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `C_TURN_1` | 200 | Is turn 1 | None |
| `C_MAIN_PHASE` | 305 | Is main phase | None |
| `C_DECK_REFRESHED` | 227 | Deck was refreshed | None |
| `C_HAND_INCREASED` | 229 | Hand increased this turn | None |
| `C_BATON` | 251 | Baton touch occurred | `val`: Count |
| `C_DISCARDED_CARDS` | 309 | Cards discarded | `attr`: Filter |
| `C_LIVE_PERFORMED` | 247 | Live performed | None |
| `C_ON_ABILITY_RESOLVE` | 314 | On ability resolve | None |
| `C_HAND_HAS_NO_LIVE` | 217 | Hand has no live | None |

### 3.6 Property Checks

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `C_HAS_KEYWORD` | 226 | Has keyword | `val`: Keyword type |
| `C_RARITY_CHECK` | 216 | Rarity check | `val`: Rarity |
| `C_COST_CHECK` | 215 | Cost check | `val`: Cost value |
| `C_TYPE_CHECK` | 252 | Type check | `val`: 1=live, 2=member |
| `C_MODAL_ANSWER` | 212 | Modal choice | `val`: Choice index |
| `C_GROUP_FILTER` | 209 | Group filter | `val`: Group ID |
| `C_SELF_IS_GROUP` | 211 | Self is group | `val`: Group ID |
| `C_UNIQUE_COLORS` | 250 | Unique colors count | `val`: Threshold |
| `C_IS_TAPPED` | 245 | Is tapped | None |
| `C_IS_ACTIVE` | 246 | Is active | None |
| `C_HAS_EXCESS_HEART` | 238 | Has excess heart | `val`: Color |
| `C_NOT_HAS_EXCESS_HEART` | 239 | No excess heart | `val`: Color |
| `C_TARGET_MEMBER_HAS_NO_HEARTS` | 315 | Target has no hearts | None |
| `C_TOTAL_BLADES` | 240 | Total blades | `val`: Threshold |
| `C_SCORE_TOTAL_CHECK` | 304 | Score total check | `val`: Threshold |

### 3.7 Cost Conditions

| Opcode | Value | Description | Inputs |
|--------|-------|-------------|--------|
| `COST_ENERGY` | 1 | Can pay energy | `val`: Amount |
| `COST_TAP_SELF` | 2 | Can tap self | `slot`: Slot |
| `COST_DISCARD_HAND` | 3 | Can discard hand | `val`: Count |
| `COST_RETURN_HAND` | 4 | Can return hand | `val`: Count |
| `COST_SACRIFICE_SELF` | 5 | Can sacrifice | `slot`: Slot |
| `COST_TAP_MEMBER` | 20 | Can tap member | None |
| `COST_TAP_ENERGY` | 21 | Can tap energy | `val`: Count |
| `COST_DISCARD_ENERGY` | 8 | Can discard energy | `val`: Count |

---

## 4. Runtime Execution Flow

### 4.1 Frame Execution Sequence

```
Ability.trigger fires
    ↓
resolve_ability() called
    ↓
ability.resolved_frames() loaded
    ↓
resolve_semantic_frames() iterates frames
    ↓
For each frame:
    1. Extract AbilityFrameComponents
    2. Check if condition frame → evaluate condition
    3. Check control flow (JUMP, RETURN)
    4. dispatch() to handler
    5. Handler executes effect
    ↓
Ability complete or suspended
```

**Location**: `engine_rust_src/src/core/logic/interpreter/mod.rs:559-839`

### 4.2 Dispatch Routing

The `dispatch()` function in `handlers/mod.rs` routes opcodes to handlers:

```rust
match op {
    // Meta/Control
    O_CALC_SUM_COST => unified::handle_calc_sum_cost(...),
    O_NEGATE_EFFECT => unified::handle_negate_effect(...),
    
    // Draw/Hand
    O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => unified::handle_draw(...),
    
    // Energy
    O_PAY_ENERGY => unified::handle_pay_energy(...),
    
    // Member State (all route to state::handle_member_state)
    O_ACTIVATE_MEMBER | O_SET_TAPPED | O_TAP_MEMBER | ... => {
        state::handle_member_state(...)
    }
    
    // Deck/Zones
    O_SEARCH_DECK | O_LOOK_DECK | ... => movement::handle_deck_zones(...),
    
    // Score/Hearts
    O_BOOST_SCORE | O_ADD_HEARTS | ... => state_score_hearts::handle_score_hearts(...),
    
    // Selection
    O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
        flow_select::handle_select_ops(...)
    }
    
    // State modifiers
    O_LOSE_EXCESS_HEARTS | O_RESTRICTION | ... => {
        flow_state_mod::handle_state_modifiers(...)
    }
    
    _ => HandlerResult::Continue, // Unknown opcode
}
```

**Location**: `engine_rust_src/src/core/logic/interpreter/handlers/mod.rs:52-154`

### 4.3 Handler Result Types

Handlers return `HandlerResult`:

```rust
pub enum HandlerResult {
    Continue,              // Continue to next frame
    SetCond(bool),         // Set condition flag
    Suspend,               // Pause for player input
    Return,                // Return from execution
    Branch(usize),         // Jump to specific frame
    BranchToFrames(Vec<AbilityFrame>), // Execute new frame sequence
}
```

---

## 5. Frame Input Interpretation

### 5.1 Value Field Packing

Different opcodes interpret `value` differently:

**Look and Choose** (`O_LOOK_AND_CHOOSE`):
```rust
let pick_count = (v >> 8) & 0xFF;  // High byte = pick count
let look_count = v & 0xFF;          // Low byte = look count
```

**Scalar Dynamic** (boost by count):
```rust
let base = (value >> 16) & 0xFFFF;  // Base value
let divisor = value & 0xFFFF;        // Divisor for calculations
```

**Heart Counts**:
```rust
let red = (value >> 24) & 0xFF;
let yellow = (value >> 16) & 0xFF;
let green = (value >> 8) & 0xFF;
let blue = value & 0xFF;
```

### 5.2 Attr Field (CardFilter)

The `attr` field is a 64-bit packed `CardFilter`:

```rust
pub struct CardFilter {
    pub color_mask: u8,          // Hearts color
    pub card_type: u8,           // Member/Live/Energy
    pub character_id: u8,        // Specific character
    pub group_id: u8,            // Group (Muse, Aqours, etc.)
    pub cost_threshold: u8,      // Cost comparison
    pub cost_compare_mode: u8, // LE/GE/EQ
    pub target_player: u8,       // Self/Opponent/Any
    pub is_center: bool,
    pub is_left: bool,
    pub is_right: bool,
    pub rarity: u8,
    pub is_cost_type: bool,
    pub is_optional: bool,
    pub is_enabled: bool,
    pub is_le: bool,             // Less than or equal
    pub has_structured: bool,
}
```

### 5.3 Slot Field Packing

The `slot` field encodes targeting:

```rust
pub struct DecodedSlot {
    pub target_slot: u8,      // 0-5 = specific slot
    pub comparison: u8,       // Comparison mode
    pub source_zone: Zone,    // Source zone
    pub dest_zone: Zone,      // Destination zone
    pub is_opponent: bool,    // Target opponent
    pub is_empty_slot: bool,  // Target empty
    pub is_baton_slot: bool,  // Baton position
    pub area_idx: u8,         // Specific area
}
```

---

## 6. Frame Families

Frames are grouped into families for routing:

| Family | Opcodes | Handler Module |
|--------|---------|----------------|
| Cost | `O_PAY_ENERGY`, `O_MOVE_TO_DISCARD` | `costs.rs` |
| Movement | `O_DRAW`, `O_RECOVER_*`, `O_MOVE_*` | `handlers/movement*.rs` |
| Score | `O_BOOST_SCORE`, `O_ADD_HEARTS`, etc. | `handlers/state_score_hearts.rs` |
| State | `O_TAP_MEMBER`, `O_ACTIVATE_*` | `handlers/state_member*.rs` |
| Selection | `O_SELECT_*`, `O_LOOK_AND_CHOOSE` | `handlers/flow_select.rs`, `interaction.rs` |
| Control | `O_JUMP`, `O_RETURN` | `mod.rs` (inline) |
| Meta | `O_META_RULE`, `O_TRIGGER_REMOTE` | `handlers/flow_effects.rs` |

---

## 7. Condition Evaluation

### 7.1 Condition Opcode Ranges

- `200-255`: Standard conditions
- `301-399`: Extended conditions

Negated conditions add `1000` to the opcode:
```rust
if op >= 1000 { op - 1000 } else { op }  // Get effective opcode
```

### 7.2 Condition Check Flow

```rust
check_condition_frame(state, db, frame, ctx, depth)
    ↓
Extract ConditionParams from frame
    ↓
check_condition_with_parts_internal()
    ↓
match op {
    C_HAS_MEMBER => check member presence,
    C_COUNT_HAND => count_and_compare(),
    C_COST_COMPARE => compare_costs(),
    ...
}
```

**Location**: `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs:248-309`

---

## 8. Suspension and Resumption

### 8.1 When Execution Suspends

Execution suspends when a handler returns `HandlerResult::Suspend`:

- `O_SELECT_MEMBER` - Need player to choose member
- `O_LOOK_AND_CHOOSE` - Need player to choose from revealed
- `O_COLOR_SELECT` - Need player to pick color
- `O_OPPONENT_CHOOSE` - Need opponent decision

### 8.2 Suspension Flow

```rust
// Handler returns Suspend
HandlerResult::Suspend
    ↓
suspend_interaction(state, ctx, frame, choice_type)
    ↓
Save state to interaction_stack
    ↓
Return Ok(()) to caller
    ↓
Game awaits player response
```

### 8.3 Resumption Flow

```rust
Player submits action
    ↓
restore_response_state(state, action)
    ↓
Pop from interaction_stack
    ↓
Update ctx with player choice
    ↓
Resume execution at suspended frame
```

---

## 9. Complete Opcode Reference

### 9.1 All Opcodes by Number

| Num | Name | Category |
|-----|------|----------|
| 0 | O_NOP | Control |
| 1 | O_RETURN | Control |
| 2 | O_JUMP | Control |
| 3 | O_JUMP_IF_FALSE | Control |
| 10 | O_DRAW | Draw |
| 11 | O_ADD_BLADES | Score |
| 12 | O_ADD_HEARTS | Score |
| 13 | O_REDUCE_COST | Cost |
| 14 | O_LOOK_DECK | Deck |
| 15 | O_RECOVER_LIVE | Recovery |
| 16 | O_BOOST_SCORE | Score |
| 17 | O_RECOVER_MEMBER | Recovery |
| 18 | O_BUFF_POWER | Modifier |
| 19 | O_IMMUNITY | Modifier |
| 20 | O_MOVE_MEMBER | Movement |
| 21 | O_SWAP_CARDS | Deck |
| 22 | O_SEARCH_DECK | Deck |
| 23 | O_ENERGY_CHARGE | Energy |
| 24 | O_SET_BLADES | Score |
| 25 | O_SET_HEARTS | Score |
| 26 | O_FORMATION_CHANGE | Member |
| 27 | O_NEGATE_EFFECT | Meta |
| 28 | O_ORDER_DECK | Deck |
| 29 | O_META_RULE | Meta |
| 30 | O_SELECT_MODE | Selection |
| 31 | O_MOVE_TO_DECK | Deck |
| 32 | O_TAP_OPPONENT | Member |
| 33 | O_PLACE_UNDER | Member |
| 34 | O_FLAVOR_ACTION | Meta |
| 35 | O_RESTRICTION | Modifier |
| 36 | O_BATON_TOUCH_MOD | Modifier |
| 37 | O_SET_SCORE | Score |
| 38 | O_SWAP_ZONE | Deck |
| 39 | O_TRANSFORM_COLOR | Score |
| 40 | O_REVEAL_CARDS | Deck |
| 41 | O_LOOK_AND_CHOOSE | Selection |
| 42 | O_CHEER_REVEAL | Deck |
| 43 | O_ACTIVATE_MEMBER | Member |
| 44 | O_ADD_TO_HAND | Draw |
| 45 | O_COLOR_SELECT | Selection |
| 47 | O_TRIGGER_REMOTE | Meta |
| 48 | O_REDUCE_HEART_REQ | Score |
| 49 | O_MODIFY_SCORE_RULE | Score |
| 50 | O_ADD_STAGE_ENERGY | Energy |
| 51 | O_SET_TAPPED | Member |
| 53 | O_TAP_MEMBER | Member |
| 57 | O_PLAY_MEMBER_FROM_HAND | Member |
| 58 | O_MOVE_TO_DISCARD | Movement |
| 60 | O_GRANT_ABILITY | Meta |
| 61 | O_INCREASE_HEART_COST | Score |
| 62 | O_REDUCE_YELL_COUNT | Modifier |
| 63 | O_PLAY_MEMBER_FROM_DISCARD | Member |
| 64 | O_PAY_ENERGY | Cost |
| 65 | O_SELECT_MEMBER | Selection |
| 66 | O_DRAW_UNTIL | Draw |
| 67 | O_SELECT_PLAYER | Selection |
| 68 | O_SELECT_LIVE | Selection |
| 69 | O_REVEAL_UNTIL | Deck |
| 70 | O_INCREASE_COST | Cost |
| 71 | O_PREVENT_PLAY_TO_SLOT | Modifier |
| 72 | O_SWAP_AREA | Member |
| 73 | O_TRANSFORM_HEART | Score |
| 74 | O_SELECT_CARDS | Selection |
| 75 | O_OPPONENT_CHOOSE | Selection |
| 76 | O_PLAY_LIVE_FROM_DISCARD | Recovery |
| 77 | O_REDUCE_LIVE_SET_LIMIT | Modifier |
| 78 | O_SET_TARGET_SELF | Meta |
| 79 | O_SET_TARGET_OPPONENT | Meta |
| 80 | O_PREVENT_SET_TO_SUCCESS_PILE | Modifier |
| 81 | O_ACTIVATE_ENERGY | Energy |
| 82 | O_PREVENT_ACTIVATE | Modifier |
| 83 | O_SET_HEART_COST | Score |
| 90 | O_PREVENT_BATON_TOUCH | Modifier |
| 91 | O_LOOK_DECK_DYNAMIC | Deck |
| 92 | O_REDUCE_SCORE | Score |
| 93 | O_REPEAT_ABILITY | Meta |
| 94 | O_LOSE_EXCESS_HEARTS | Score |
| 95 | O_SKIP_ACTIVATE_PHASE | Modifier |
| 96 | O_PAY_ENERGY_DYNAMIC | Cost |
| 97 | O_PLACE_ENERGY_UNDER_MEMBER | Energy |
| 106 | O_CALC_SUM_COST | Cost |
| 125 | O_LOOK_REORDER_DISCARD | Deck |
| 126 | O_DIV_VALUE | Cost |
| 127 | O_TRANSFORM_BLADES | Score |

---

## 10. File Locations

| Component | Path |
|-----------|------|
| Frame Structure | `engine_rust_src/src/core/logic/models.rs` |
| Interpreter | `engine_rust_src/src/core/logic/interpreter/mod.rs` |
| Dispatch | `engine_rust_src/src/core/logic/interpreter/handlers/mod.rs` |
| Conditions | `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs` |
| Slot Decoding | `engine_rust_src/src/core/logic/interpreter/instruction.rs` |
| Constants | `engine_rust_src/src/core/generated_constants.rs` |
| Filter | `engine_rust_src/src/core/logic/filter.rs` |
| Movement Handlers | `engine_rust_src/src/core/logic/interpreter/handlers/movement*.rs` |
| Score Handlers | `engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs` |
| State Handlers | `engine_rust_src/src/core/logic/interpreter/handlers/state_member*.rs` |
| Selection Handlers | `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs` |

---

## 11. Summary

The frame-to-runtime system works through:

1. **Serialization**: Frames are 5-field JSON objects (`opcode`, `value`, `attr`, `slot`, `is_cost`)
2. **Deserialization**: JSON converts to `AbilityFrame` then `AbilityFrameComponents`
3. **Dispatch**: Central router matches opcode to handler function
4. **Execution**: Handler interprets packed fields and modifies game state
5. **Control Flow**: Jumps, conditions, and suspensions manage execution path
6. **Completion**: Handler returns `HandlerResult` to control flow

The key insight is that the **5-field structure is uniform** but **interpretation is opcode-specific**. The `value`, `attr`, and `slot` fields have different meanings depending on which opcode is executing.
