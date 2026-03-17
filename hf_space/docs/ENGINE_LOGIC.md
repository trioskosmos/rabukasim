# Engine Logic and Phases

This document provides a technical overview of how the game engine (Rust implementation in `engine_rust_src/`) manages the game lifecycle, phase transitions, and ability triggers.

## Core Architecture

The engine is built around a `GameState` struct. The primary entry point for game progression is the `step` function, which maps player actions to state changes based on the current `Phase`.

### GameState Struct
```rust
pub struct GameState {
    pub players: [PlayerState; 2],
    pub phase: Phase,
    pub current_player: u8,
    pub first_player: u8,
    pub turn: u32,
    pub seed: u64,
    // ... (internal state like pending contexts for Response phase)
}
```

### Phase Enum
The game flows through discrete phases defined in `logic.rs`. These align with the **[Comprehensive Rules (v1.04)](file:///C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/rules/rules.txt)**.

| Code | Phase | Rule Ref | Description |
|---|---|---|---|
| `-2` | `Setup` | 6.1 | Initial state before decks are loaded. |
| `-1, 0`| `Mulligan`| 6.2.1.6 | Choosing cards to redraw. |
| `1` | `Active` | 7.4 | Untapping cards (7.4.1) and triggering `TurnStart` (7.4.2). |
| `2` | `Energy` | 7.5 | Playing energy from hand or energy deck. |
| `3` | `Draw` | 7.6 | Drawing the turn card. |
| `4` | `Main` | 7.7 | Main interaction window (Play/Activate). |
| `5` | `LiveSet` | 8.2 | Setting live cards (hidden) and drawing (8.2.2). |
| `6, 7` | `Performance`| 8.3 | Score calculation, Yell (8.3.11), and Judgment. |
| `8` | `LiveResult`| 8.4 | Victory determination (8.4.6) and cleanup. |
| `10` | `Response` | N/A | **Internal**: Engine waiting for selection input (Rule 9.6.2.2). |

---

## Game Lifecycle & Transitions

### 1. Typical Turn Flow
The standard turn sequence is implemented in the `step` function, which dispatches to phase-specific handlers:

```rust
// logic.rs: step() handles the high-level orchestration
match self.phase {
    Phase::Active => { self.do_active_phase(db); },
    Phase::Energy => { /* Handles action IDs 550-555 */ },
    Phase::Draw => { self.do_draw_phase(); },
    Phase::Main => { /* Handles play/activate actions */ },
    Phase::LiveSet => { self.set_live_cards(db, card_ids); },
    // ...
}
```

### 2. Live & Performance (Rule 8.3)
During the Performance phase, the engine calculates:
- **Total Blades**: Sum of `get_effective_blades` from active members.
- **Yell (Rule 8.3.11)**: Moving cards from main deck to resolving area based on blades.
- **Total Hearts (Rule 8.3.14)**: Sum of member hearts and yelled hearts.
- **Icon Check**: Volume icons added to the turn's total score.

```rust
// Rule 11.4: Trigger [ライブ開始時] (On Live Start)
self.trigger_abilities(db, TriggerType::OnLiveStart, &ctx);
```

---

## Ability Trigger System

Abilities are triggered by the `trigger_abilities` function. It checks all members on stage and in specific contexts.

### Trigger Timing

```rust
pub enum TriggerType {
    OnPlay,         // Rule 11.3: When played to stage slot
    OnLiveStart,    // Rule 11.4: [ライブ開始時]
    OnLiveSuccess,  // Rule 11.5: [ライブ成功時]
    TurnStart,      // Rule 7.4.2: Start of Active phase
    TurnEnd,        // Rule 8.4.10: [ターンの終わりに] (Placeholder)
    OnReveal,       // During Yell process (Rule 8.3.11)
    OnLeaves,       // When leaving stage (Placeholder)
    OnPositionChange,// During O_MOVE_MEMBER / O_SWAP_CARDS
    Activated,      // Manual activation in Main phase
    Constant,       // Passive effects (Rule 9.1.1.3)
}
```

### The "Response" Mechanism (Rule 9.6.2.2)
When an ability requires user input (e.g. `O_SELECT_MODE`), the engine sets the phase to `Response` to pause execution:

```rust
// Rule 9.6.2.2: Pausing for choice
if self.phase != Phase::Response && bytecode_needs_early_pause(&ab.bytecode) {
    self.phase = Phase::Response;
    self.pending_ctx = Some(ctx.clone());
    return Ok(());
}
```

---

## Implementation Nuances & Rule Divergences

While the engine follows the **[Rule 1.04](file:///C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/rules/rules.txt)** closely, there relate a few implementation-specific details:

### 1. First Player Toggle (Divergence)
According to **Rule 8.4.13**, the winner of a live performance becomes the first player for the next turn. If no player wins uniquely, the current first player continues.
- **Current Logic**: The engine currently toggles `first_player` every turn in `finalize_live_result` for balance if no specific winner logic overrides it.

### 2. Placeholder Triggers
The following `TriggerType` variants are defined in `enums.rs` and labeled in `logic.rs` but are not yet actively fired by the main loop:
- `TurnEnd`: **Rule 8.4.10** logic is partially implemented but the explicit trigger call is pending.
- `OnLeaves`: Reserved for future "Leaves Stage" abilities.

### 3. Opcode Availability
- **Active**: `O_DRAW`, `O_HEARTS`, `O_MOVE_MEMBER`, `O_SWAP_CARDS`, `O_BATON_MOD`, `O_SELECT_MODE`, etc.
- **Reserved**: `O_META_RULE` (currently a NO-OP), `O_ADD_CONTINUOUS`.

---

## Special Logic: `hardcoded.rs`

Optimized implementations for complex card interactions are in `hardcoded.rs`. This allows the engine to handle edge cases that are difficult to represent in generic bytecode.

```rust
// hardcoded.rs example
match (card_id, ab_idx) {
    (0, 1) => {
        state.players[p_idx].live_score_bonus += 3;
        true
    },
}
```

---

## Technical Resources
- **[Opcodes Mapping](file:///C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/spec/opcode_map.md)**: Full mapping of bytecode to logic.
- **[Rulebook](file:///C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/rules/rules.txt)**: Official Japanese rulebook for cross-reference.
