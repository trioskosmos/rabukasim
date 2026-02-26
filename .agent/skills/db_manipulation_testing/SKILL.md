---
description: How to create QA tests that manipulate the game database (cards_compiled.json) dynamically for testing complex rules.
---
# Creating Data-Driven QA Verification Tests

This skill describes the workflow for creating highly specific QA verification tests that involve manipulating `cards_compiled.json` in memory during testing. This is particularly useful for simulating edge cases, broken mechanics, or testing rules that would otherwise be difficult to trigger naturally.

## Core Pattern: In-Memory Database Manipulation

When testing specific scenarios (like Q96, Q97, Q103), you often need card abilities to trigger under extremely specific states. Rather than relying entirely on pre-compiled cards, you can load the JSON, convert it into the Rust `CardDatabase`, and then **mutate the database in memory** before passing it to the `GameState`.

### 1. The Setup

Start by loading the database normally.
```rust
use engine_rust::core::logic::{GameState, CardDatabase, AbilityContext};

let json_content = std::fs::read_to_string("../data/cards_compiled.json").expect("Failed to read database");
let mut db = CardDatabase::from_json(&json_content).unwrap();
let mut state = GameState::default();
let p1 = 0;
```

### 2. Modifying Abilities Dynamically

Often, a card's actual ability has complex conditions that are hard to satisfy in a test rig (e.g., "Requires 3 members of Group X"). You can overwrite the bytecode of an ability directly in your test database to isolate the exact mechanic you want to test.

```rust
let card_id = 605; // Example Live Card ID
let mut ability = db.get_live(card_id).unwrap().abilities[0].clone();

// Example: Overwrite the bytecode to skip complex precondition checks
// and jump straight into the logic we care about.
// You can use standard Opcode IDs (found in `constants.rs` or `opcodes.py`)
ability.bytecode = vec![
    27, // O_ACTIVATE_ENERGY
    0, 0, 6, // v = 6
    15, // O_COND
    0, 5, 0, // condition = 5 (CHECK_COUNT_ENERGY)
    20 // O_BOOST_SCORE
    // ...
];

// Update the database
db.update_live_ability(card_id, 0, ability.clone());
```

### 3. Direct Execution vs Suspension

There are two ways to test the logic:

#### Option A: Direct Interpreter Call (Unit Testing Opcodes)
If you want to test how the interpreter handles specific bytecode, you can bypass the normal trigger system and call the interpreter directly.

```rust
let mut ctx = AbilityContext {
    player_id: p1 as u8,
    source_card_id: card_id,
    ..Default::default()
};

// resolve_bytecode signature: (state, db, card_id, bytecode, ctx)
engine_rust::core::logic::interpreter::resolve_bytecode(&mut state, &mut db, card_id, &ability.bytecode, &mut ctx);
```

#### Option B: Full Event Pipeline (E2E Testing)
If you need to test how suspensions, responses, and choices are handled, you must enqueue the ability and step through the game loop.

```rust
// 1. Give the player the card
state.core.players[p1].hand.push(member_id);

// 2. Play the card
state.execute_action(ClientAction::PlayMemberFromHand {
    card_id: member_id,
    slot_idx: 0,
    cost_paid: vec![], // Assuming no cost for the test
});

// 3. Process resulting suspensions
while state.is_suspended() {
    let actions = state.get_legal_actions();
    // Choose the appropriate action to resolve the suspension
    state.execute_action(actions[0].clone()); 
}
```

## Creating the Test File

1.  **File Location**: New tests should be placed in `engine_rust_src/tests/`.
2.  **Naming Convention**: Prefix the file with `repro_` (e.g., `repro_catchu_q103.rs`).
3.  **Registration**: Add the test to the `Cargo.toml` if needed, although Cargo usually autodiscover tests in the `tests/` directory.

## Best Practices

*   **Isolate Variables**: Mutate the database only enough to remove confounding variables. If you are testing score calculation, don't let complex "draw cards if X" conditions fail the ability early.
*   **Clear Assertions**: Write clear assert statements explaining *why* a test might fail.
*   **Run with Output**: When running the test, use `cargo test --test your_test_name -- --nocapture` to see debug prints.

## Common Opcodes for Manipulation

*   `O_COND` (15): Used for conditional branching.
*   `O_ACTIVATE_ENERGY` (27): Untaps energy.
*   `O_BOOST_SCORE` (20): Adds score.

Refer to `engine/models/opcodes.py` or the `interpreter` module for a full list of opcodes and their arguments.
