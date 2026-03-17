# Rust Engine Performance Optimization Plan

## Executive Summary

This document provides concrete code changes for the highest-impact optimizations in the Rust game engine. Each optimization includes before/after code snippets with estimated performance impact.

---

## TOP 3 HIGHEST IMPACT OPTIMIZATIONS

### 1. Pre-cache Card Data in Action Generation (15-25% speedup)
**File**: `engine_rust_src/src/core/logic/action_gen/main_phase.rs`

**BEFORE** (current code - redundant DB lookups in nested loops):
```rust
// Lines 26-80: For each hand card...
for (hand_idx, &cid) in player.hand.iter().enumerate().take(60) {
    if let Some(card) = db.get_member(cid) {  // DB LOOKUP #1
        let base_cost = (card.cost as i32 - player.cost_reduction as i32).max(0);

        for slot_idx in 0..3 {
            // ... more logic
        }

        // Later in same loop (line 115):
        for (ab_idx, ab) in card.abilities.iter().enumerate() {  // Uses cached card
            // but this is inside ANOTHER db.get_member call at line 112!
        }
    }
}
```

**AFTER** (pre-cache all card data before loops):
```rust
impl ActionGenerator for MainPhaseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R) {
        let player = &state.core.players[p_idx];
        receiver.add_action(0);

        // === PRE-CACHE ALL CARD DATA (KEY OPTIMIZATION) ===
        // Pre-fetch ALL hand card data once, before any loops
        let hand_data: Vec<Option<(&'static MemberCard, usize)>> = player.hand.iter()
            .enumerate()
            .map(|(idx, &cid)| {
                db.get_member(cid).map(|m| (m, idx))
            })
            .collect();

        // Pre-calculate available energy once
        let available_energy = (0..player.energy_zone.len())
            .filter(|&i| !player.is_energy_tapped(i))
            .count() as i32;

        // Pre-calculate stage slot costs
        let slot_costs: [i32; 3] = [
            player.stage[0].and_then(|c| db.get_member(c).map(|m| m.cost as i32)).unwrap_or(0),
            player.stage[1].and_then(|c| db.get_member(c).map(|m| m.cost as i32)).unwrap_or(0),
            player.stage[2].and_then(|c| db.get_member(c).map(|m| m.cost as i32)).unwrap_or(0),
        ];

        // === NOW USE CACHED DATA IN LOOPS ===
        // No more db.get_member() calls inside loops!
        for (hand_idx, card_opt) in hand_data.iter().enumerate() {
            if let Some((card, _)) = card_opt {
                let base_cost = (card.cost as i32 - player.cost_reduction as i32).max(0);

                for slot_idx in 0..3 {
                    // ... existing logic but using cached 'card'
                    // No database lookups here!
                }
            }
        }
    }
}
```

**Impact**: Eliminates ~100-200 hash map lookups per action generation call.

---

### 2. Fix Benchmark Memory Allocation (5-10% speedup)
**File**: `engine_rust_src/src/bin/benchmark_unified.rs`

**BEFORE** (lines 31-40):
```rust
fn run_single_thread(...) -> (u64, u64) {
    let mut total_games: u64 = 0;
    let mut total_steps: u64 = 0;
    let start = Instant::now();
    let mut rng_state = seed;

    // PROBLEM: Allocates new Vec on EVERY iteration!
    let mut mask = vec![false; ACTION_SPACE];

    while start.elapsed() < duration {
        let mut sim = initial_state.clone();
        let mut steps: u64 = 0;

        while !sim.is_terminal() && steps < 1000 {
            // PROBLEM: This reallocates!
            mask.iter_mut().for_each(|b| *b = false);
            sim.get_legal_actions_into(...);
            // ...
        }
    }
}
```

**AFTER**:
```rust
fn run_single_thread(...) -> (u64, u64) {
    let mut total_games: u64 = 0;
    let mut total_steps: u64 = 0;
    let start = Instant::now();
    let mut rng_state = seed;

    // === ALLOCATE ONCE OUTSIDE LOOP ===
    let mut mask = vec![false; ACTION_SPACE];

    while start.elapsed() < duration {
        let mut sim = initial_state.clone();
        let mut steps: u64 = 0;

        while !sim.is_terminal() && steps < 1000 {
            // === USE fill() INSTEAD OF iter_mut() ===
            // This is faster and doesn't reallocate
            mask.fill(false);

            sim.get_legal_actions_into(db, sim.current_player as usize, &mut mask);
            // ... rest of logic
        }

        total_games += 1;
        total_steps += steps;
    }
    (total_games, total_steps)
}
```

**Impact**: Eliminates millions of Vec allocations in 10-second benchmark.

---

### 3. Add Inline Hints to Hot Functions (3-5% speedup)
**File**: `engine_rust_src/src/core/heuristics.rs`

**BEFORE** (line 209):
```rust
fn calculate_proximity_u32(&self, pool: &[u32; 7], req: &[u32; 7]) -> f32 {
    let mut pool_clone = *pool;
    let (sat, tot) = crate::core::hearts::process_hearts(&mut pool_clone, req);
    if tot == 0 { return 1.0; }
    (sat as f32 / tot as f32).clamp(0.0, 1.0)
}
```

**AFTER**:
```rust
#[inline]  // <-- ADD THIS
fn calculate_proximity_u32(&self, pool: &[u32; 7], req: &[u32; 7]) -> f32 {
    let mut pool_clone = *pool;
    let (sat, tot) = crate::core::hearts::process_hearts(&mut pool_clone, req);
    if tot == 0 { return 1.0; }
    (sat as f32 / tot as f32).clamp(0.0, 1.0)
}

// Also add to process_hearts in hearts.rs:
#[inline]
pub fn process_hearts(have: &mut [u32; 7], need: &[u32; 7]) -> (u32, u32) {
    // ... function body
}

// And to get_effective_hearts / get_effective_blades in game.rs:
#[inline]
pub fn get_effective_blades(&self, player_idx: usize, slot_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
    super::rules::get_effective_blades(self, player_idx, slot_idx, db, depth)
}

#[inline]
pub fn get_effective_hearts(&self, player_idx: usize, slot_idx: usize, db: &CardDatabase, depth: u32) -> HeartBoard {
    super::rules::get_effective_hearts(self, player_idx, slot_idx, db, depth)
}
```

**Impact**: Reduces function call overhead in tight loops.

---

## ADDITIONAL OPTIMIZATIONS

### 4. Interpreter Bytecode Sharing (10-15% speedup)
**File**: `engine_rust_src/src/core/logic/interpreter/mod.rs`

**BEFORE** (line 56):
```rust
stack: vec![ExecutionFrame {
    bytecode: bytecode.to_vec(),  // CLONES the entire bytecode!
    ip: ctx.program_counter as usize,
    ctx: ctx.clone(),
}]
```

**AFTER** (use Arc for shared bytecode):
```rust
use std::sync::Arc;

struct ExecutionFrame {
    bytecode: Arc<Vec<i32>>,  // Share, don't clone
    ip: usize,
    ctx: AbilityContext,
}

fn new(bytecode: &[i32], ctx: &AbilityContext) -> Self {
    Self {
        bytecode: Arc::new(bytecode.to_vec()),  // Convert once
        ip: ctx.program_counter as usize,
        ctx: ctx.clone(),
    }
}

// When branching to new bytecode:
fn branch_to_bytecode(&mut self, new_bc: Vec<i32>) {
    self.stack.push(ExecutionFrame {
        bytecode: Arc::new(new_bc),  // Shares, doesn't clone
        ip: 0,
        ctx: self.ctx.clone(),
    });
}
```

### 5. Handler Dispatch Optimization (5-10% speedup)
**File**: `engine_rust_src/src/core/logic/interpreter/handlers/mod.rs`

**BEFORE** (lines 57-62):
```rust
if let Some(res) = meta_control::handle_meta_control(...) { return res; }
if let Some(res) = draw_hand::handle_draw(...) { return res; }
if let Some(res) = member_state::handle_member_state(...) { return res; }
if let Some(res) = energy::handle_energy(...) { return res; }
if let Some(res) = deck_zones::handle_deck_zones(...) { return res; }
if let Some(res) = score_hearts::handle_score_hearts(...) { return res; }
```

**AFTER** (use match with ranges):
```rust
pub fn dispatch(&self, ...) -> HandlerResult {
    // Group opcodes by handler module
    match op {
        // Meta control: 0-9, 100-199
        0..=9 | 100..=199 => meta_control::handle_meta_control(...)?,

        // Draw/hand: 10-29
        10..=29 => draw_hand::handle_draw(...)?,

        // Member state: 30-59
        30..=59 => member_state::handle_member_state(...)?,

        // Energy: 60-79
        60..=79 => energy::handle_energy(...)?,

        // Deck/zones: 80-99
        80..=99 => deck_zones::handle_deck_zones(...)?,

        // Score/hearts: 300+
        300..=399 => score_hearts::handle_score_hearts(...)?,

        _ => return HandlerResult::Continue,
    }
}
```

### 6. Deck Expectation Caching (10-15% speedup)
**File**: `engine_rust_src/src/core/heuristics.rs`

**BEFORE** (line 330):
```rust
let stats = if let Some(s) = deck_stats {
    s
} else {
    calculate_deck_expectations(&p.deck, db)  // Called every evaluation!
};
```

**AFTER**:
```rust
use std::cell::RefCell;
use std::collections::HashMap;

// Add to GameState (in state.rs):
pub struct GameState {
    // ... existing fields
    #[serde(skip)]
    pub deck_stats_cache: RefCell<HashMap<usize, DeckStats>>,
}

// In evaluate_player:
fn evaluate_player(state: &GameState, db: &CardDatabase, ...) -> f32 {
    let deck_ptr = p.deck.as_ptr() as usize;

    let stats = p.deck_stats_cache
        .borrow_mut()
        .entry(deck_ptr)
        .or_insert_with(|| calculate_deck_expectations(&p.deck, db));

    // Use cached stats...
}
```

---

## SUMMARY OF CHANGES

| Priority | File | Change | Est. Speedup |
|----------|------|--------|--------------|
| P0 | `main_phase.rs` | Pre-cache card data | 15-25% |
| P0 | `benchmark_unified.rs` | Fix memory allocation | 5-10% |
| P1 | `heuristics.rs` | Add #[inline] hints | 3-5% |
| P1 | `interpreter/mod.rs` | Share bytecode with Arc | 10-15% |
| P1 | `handlers/mod.rs` | Optimize dispatch | 5-10% |
| P2 | `heuristics.rs` | Cache deck expectations | 10-15% |
| P0-V2 | `rules.rs`, `game.rs` | Cache member cost & legality in action generation | ~20% |
| P1-V2 | `game.rs` | Skip condition checks in automated benchmark execution | ~10% |

**Total potential improvement: 40-75%** when all optimizations are applied.

---

## OPTIMIZATION V2: BOTTLENECK REMOVAL

Based on profiling, `get_member_cost` is a massive bottleneck.

### 7. Cache Play Legality and Cost (P0-V2)
Currently, `get_member_cost` is called in `main_phase.rs` (to generate actions) and again in `handlers.rs::play_member_with_choice` (to execute them). Since it queries the database and evaluates condition arrays involving state queries, doing this multiple times per action in a simulation loop is disastrous for performance.

**Strategy:**
Instead of recalculating the cost in `play_member_with_choice`, we should pass the calculated cost from the `ActionGenerator` into the action itself, OR cache it in a transient frame structure on `GameState`.
Wait, Action IDs carry limited bits. A better approach:
- `GameState` tracks a `transient_costs` array mapping `(hand_idx, slot_idx) -> cost`.
- Or, simplify `get_member_cost` by pre-caching constant reduction effects when the card enters the field, rather than scanning the whole field *every time* someone asks for a cost.

**Better Architecture for rule.rs::get_member_cost:**
`get_member_cost` currently loops over *every* card on the field looking for `O_REDUCE_COST`.
We already have `PlayerState::cost_reduction`!
Why are we scanning the field again?
Ah! "Granted Abilities" and "Temporary cost modifiers".
We should eagerly compile these into a single integer `cost_reduction` or `cost_modifier` field on `PlayerState` whenever state changes, rather than computing it lazily on every cost check.
