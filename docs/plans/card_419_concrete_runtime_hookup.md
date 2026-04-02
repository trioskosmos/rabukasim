# Card 419 Concrete Runtime Hookup

## Purpose

This document answers two questions directly:

1. What Rust functions are actually used right now to make card `419` (`PL!S-bp2-005-P`) work?
2. What simpler runtime hookup should cards use in general so the engine can reuse existing low-level behavior without forcing everything through legacy-shaped packed fields?

The goal here is not another abstract migration note. The goal is to describe the concrete execution path and then reduce it to the smallest reusable runtime model.

## Short Answer

Card `419` is much simpler than the current runtime representation makes it look.

At the level of game behavior, the card does this:

1. optionally discard `1` card from hand
2. if the player paid that cost, look at the top `7` cards of the deck
3. choose up to `3` member cards matching the filter
4. add the chosen cards to hand
5. move the remainder to discard

The engine already has almost all of the low-level operations needed for that flow. The confusing part is the middle representation.

Right now the card is made to work by:

- hydrating sparse frame data into `Ability.frame_program`
- converting each frame into `AbilityFrameComponents`
- routing by opcode through a wide dispatcher
- decoding packed `value`, `attr`, and `slot` fields inside the handlers

The better model is:

- keep the current low-level zone-move and choice code
- stop treating packed fields as the primary runtime contract
- normalize each loaded ability once into a small semantic action list
- dispatch those actions into the existing handlers or narrower helper functions

## The Card As It Should Be Thought About

This card should not be thought of as `opcode 58 + opcode 41 + packed value bits`.

It should be thought of as:

```rust
AbilityRuntime {
    trigger: TriggerType::OnPlay,
    steps: vec![
        RuntimeStep::OptionalCost(
            CostAction::DiscardFromZone {
                source_zone: Zone::Hand,
                count: 1,
                filter: CardFilter::default(),
            }
        ),
        RuntimeStep::Effect(
            EffectAction::LookAndChoose {
                source_zone: Zone::Deck,
                look_count: 7,
                choose_count: 3,
                destination: Zone::Hand,
                remainder_destination: Zone::Discard,
                reveal: true,
                filter: CardFilter {
                    card_type: 1,
                    color_mask: 0b0011010,
                    ..Default::default()
                },
            }
        ),
    ],
}
```

That representation matches what the card actually does.

## Current Concrete Runtime Path

This section is the current real path through the Rust code.

### 1. Card data load

The compiled card data is loaded into the database in:

- `engine_rust_src/src/core/logic/card_db.rs`

The important functions are:

```rust
fn attach_sparse_ability_index(
    card_no: &str,
    abilities: &mut [Ability],
    index: &HashMap<String, Value>,
    text_index: &HashMap<String, String>,
) -> serde_json::Result<()>

pub fn sparse_entry_to_frame_program(entry: &Value) -> FrameProgram
```

What they actually do for card `419`:

1. build the lookup key `PL!S-bp2-005-P#0`
2. read the sparse/consolidated frame entry
3. create a `FrameProgram`
4. attach that `FrameProgram` to `Ability.frame_program`
5. repair or backfill frame/effect fields such as `choose_count`, `runtime_opcode`, `runtime_attr`, `runtime_slot`, `raw_text`, and `pseudocode`

This is the real hydration boundary today.

### 2. Ability entrypoint

The actual runtime entrypoint is:

- `engine_rust_src/src/core/logic/interpreter/mod.rs`

The key function is:

```rust
pub fn resolve_ability(
    state: &mut GameState,
    db: &CardDatabase,
    ability: &Ability,
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError>
```

This function:

1. fetches the executable frame list with `ability.resolved_frames()`
2. checks top-level `ability.conditions`
3. passes the frames into the sequential frame executor

The important detail is that the real execution input is not the original compiled `effects` list. It is the resolved frame list coming from the hydrated `Ability`.

### 3. Frame resolution

The frame source selected by the engine is:

```rust
pub fn resolved_frames(&self) -> Cow<'_, [AbilityFrame]> {
    if let Some(ref frame_program) = self.frame_program {
        return Cow::Borrowed(&frame_program.frames);
    }

    if !self.effects.is_empty() {
        return Cow::Owned(
            self.effects
                .iter()
                .map(AbilityFrame::from_effect)
                .collect(),
        );
    }

    Cow::Borrowed(&[])
}
```

For card `419`, the important path is the `frame_program.frames` branch.

### 4. Sequential interpreter loop

The actual executor is:

```rust
pub fn resolve_semantic_frames(
    state: &mut GameState,
    db: &CardDatabase,
    frames: &[AbilityFrame],
    ctx_in: &AbilityContext,
) -> Result<(), InterpreterError>
```

Inside that loop, the engine does this for each frame:

```rust
let frame = &frames[effect_idx];
let frame_data = frame.components();
match dispatch(state, db, &mut ctx, &frame_data, effect_idx) {
    ...
}
```

This is the central runtime handoff.

### 5. Dispatch layer

Routing happens in:

- `engine_rust_src/src/core/logic/interpreter/handlers/mod.rs`

The key function is:

```rust
pub fn dispatch(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult
```

For card `419`, the relevant branch is:

```rust
O_MOVE_TO_DISCARD | O_LOOK_AND_CHOOSE => {
    movement::handle_deck_zones(state, db, ctx, frame_data, frame_idx)
}
```

### 6. Deck-zone router

The next router is:

- `engine_rust_src/src/core/logic/interpreter/handlers/movement_deck.rs`

The key function is:

```rust
pub fn handle_deck_zones(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult
```

For this card it routes to:

```rust
O_MOVE_TO_DISCARD => handle_move_to_discard(state, db, ctx, &frame_data, frame_idx),
O_LOOK_AND_CHOOSE => handle_look_and_choose(state, db, ctx, &frame_data, frame_idx),
```

That is the real function-level answer for this card.

### 7. Cost discard behavior

The first real behavior comes from:

- `engine_rust_src/src/core/logic/interpreter/handlers/movement_discard.rs`

The function is:

```rust
pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult
```

What this function actually does for card `419`:

1. derives source zone from the slot data
2. computes discard count
3. detects optionality
4. if selection is needed, calls `suspend_choice(...)`
5. after the player chooses, removes the selected card from hand
6. pushes that card into discard
7. records the selected card in `ctx.selected_cards`

This is already the low-level reusable operation the engine needs.

### 8. Look-and-choose behavior

The second real behavior comes from:

- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_look_choose.rs`

The main function is:

```rust
pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult
```

The important helpers used inside are:

```rust
fn resolve_choose_count(...)
fn apply_look_choice(...)
fn finalize_look_choice(...)
```

What this function actually does for card `419`:

1. decides the source zone, destination, remainder destination, reveal behavior, and choose count
2. pulls the top `7` cards from deck into `state.players[p_idx].looked_cards`
3. prompts the player via `suspend_choice(...)`
4. when a valid card is chosen, moves that card to hand through `apply_look_choice(...)`
5. repeats if the card allows more picks
6. moves all remaining looked-at cards to discard in `finalize_look_choice(...)`

This is the second low-level reusable operation the engine needs.

### 9. Choice boundary

The player interaction boundary is:

- `engine_rust_src/src/core/logic/interpreter/handlers/choice_prompt.rs`

The relevant function is:

```rust
pub fn suspend_choice(
    state: &mut GameState,
    db: &CardDatabase,
    choice_ctx: &AbilityContext,
    suspend_ctx: &AbilityContext,
    frame_idx: usize,
    op: i32,
    s: i32,
    choice_type: ChoiceType,
    attr: u64,
    remaining: i16,
) -> HandlerResult
```

That means the actual execution model already has a clear boundary between:

- pure game-state mutation
- temporary suspension for user input
- resumption of the same low-level action

This is good. It should be preserved.

## What Makes The Current Model Hard To Think About

The difficult part is not the game logic. The difficult part is the representation between load and handler execution.

The current runtime makes this card pass through these abstractions:

1. `Ability`
2. `FrameProgram`
3. `AbilityFrame`
4. `AbilityFrameComponents`
5. `DecodedSlot`
6. `DecodedLookAndChoose`
7. `CardFilter`
8. raw `attr` re-encoding via `to_attr()`
9. raw `slot` re-encoding via `to_raw()`

Some of those are useful. Some are transition baggage.

The parts that are still useful:

- `AbilityContext`
- `CardFilter`
- `DecodedSlot`
- the existing handler functions
- `suspend_choice(...)`

The parts that make the card harder than it needs to be:

- `value` as a pseudo-union of unrelated concepts
- `attr` as a packed field that still acts like runtime API
- `slot` as a packed integer that still acts like runtime API
- repairing dropped semantics after hydration instead of carrying them cleanly

## The Concrete Simpler Hookup

The better runtime hookup is not to delete the current handlers.

The better runtime hookup is:

1. keep the existing low-level handlers that already move cards, prompt, and finalize state
2. insert one normalization layer after DB load
3. normalize each executable frame into a small semantic runtime action
4. dispatch those runtime actions directly

### Proposed runtime boundary

The boundary should be a card-local executable object like this:

```rust
pub struct ExecutableAbility {
    pub trigger: TriggerType,
    pub raw_text: String,
    pub choice_count: u8,
    pub steps: Vec<RuntimeStep>,
}

pub enum RuntimeStep {
    Condition(ConditionAction),
    OptionalCost(CostAction),
    Effect(EffectAction),
    Return,
    JumpIfFalse { offset: i32 },
    Jump { offset: i32 },
}
```

For this specific card, the runtime steps should look like this:

```rust
ExecutableAbility {
    trigger: TriggerType::OnPlay,
    raw_text: "...",
    choice_count: 3,
    steps: vec![
        RuntimeStep::OptionalCost(
            CostAction::DiscardFromZone {
                source_zone: Zone::Hand,
                count: 1,
                filter: CardFilter::default(),
            }
        ),
        RuntimeStep::JumpIfFalse { offset: 2 },
        RuntimeStep::Effect(
            EffectAction::LookAndChoose {
                source_zone: Zone::Deck,
                look_count: 7,
                choose_count: 3,
                destination: Zone::Hand,
                remainder_destination: Zone::Discard,
                reveal: true,
                filter: CardFilter { ..Default::default() },
            }
        ),
        RuntimeStep::Return,
    ],
}
```

The important point is that the card should become readable in terms of actions, not packed transport fields.

## How To Reuse Current Code Without Rewriting Everything

The engine does not need a giant rewrite to get this simpler model.

### Reuse strategy

#### 1. Keep these current functions

These are already the right place for real game logic:

- `handle_move_to_discard(...)`
- `handle_look_and_choose(...)`
- `suspend_choice(...)`
- `apply_look_choice(...)`
- `finalize_look_choice(...)`

#### 2. Stop using packed fields as the primary handoff

Instead of handing `dispatch(...)` a structure whose most important values are still raw packed transport fields, normalize them once.

For example, replace this style of thinking:

```rust
let a = frame_data.raw_attr as i64;
let s = frame_data.raw_slot;
let lc = frame_data.look_choose();
```

with this style of thinking:

```rust
match action {
    EffectAction::LookAndChoose {
        source_zone,
        look_count,
        choose_count,
        destination,
        remainder_destination,
        reveal,
        filter,
    } => { ... }
}
```

#### 3. Make the old frame model an adapter, not the runtime model

The current `AbilityFrame` and `AbilityFrameComponents` can stay temporarily, but they should be treated as:

- loader compatibility
- debug projection
- transition adapters

They should stop being the main representation humans have to reason about.

## General Rule For How Cards Should Run

In general, a card should run through these layers only:

### Layer 1. Data load

Load card data and authored frame source.

Current file:

- `engine_rust_src/src/core/logic/card_db.rs`

Output:

- `ExecutableAbility`

### Layer 2. Trigger queue

Queue the ability based on trigger type.

Current files:

- `engine_rust_src/src/core/logic/game_trigger.rs`
- `engine_rust_src/src/core/logic/performance.rs`

Output:

- `AbilityContext + ExecutableAbility`

### Layer 3. Step executor

Walk `RuntimeStep` entries sequentially.

Current analog:

- `resolve_semantic_frames(...)`

Output:

- repeated calls into reusable action handlers

### Layer 4. Action handlers

Perform real gameplay work.

Examples:

- discard from zone
- choose cards
- move member
- recover live
- boost score

Those handlers are where the actual game engine lives.

### Layer 5. Suspension boundary

If the player must choose, suspend and resume.

Current function:

- `suspend_choice(...)`

This part is already good and should remain explicit.

## The Main Architectural Change

The main change needed is this:

### Current

```text
authored frame
-> hydrated AbilityFrame
-> AbilityFrameComponents
-> decode packed fields inside handlers
-> real game behavior
```

### Better

```text
authored frame
-> ExecutableAbility / RuntimeStep / EffectAction
-> direct action handler call
-> real game behavior
```

That is the simplification.

It keeps:

- the current interpreter loop idea
- the current suspension model
- the current low-level state mutation functions

It removes the need to keep thinking in:

- raw `attr`
- raw `slot`
- packed `value`
- rehydration patches that exist only because typed meaning was flattened too early

## Concrete Recommendation

If the repo wants one concrete next step, it should be this:

1. Define `ExecutableAbility`, `RuntimeStep`, `CostAction`, and `EffectAction` in Rust.
2. Add a loader-side conversion in `card_db.rs` from `FrameProgram` to those runtime actions.
3. Convert card `419` first as the pilot shape.
4. Make the executor run those actions while reusing the existing choice and movement helpers.
5. Keep old `AbilityFrame` packing only as a transitional adapter for cards or tools that still need it.

If that is done, card `419` stops being "a frame with packed slot/attr/value semantics" and becomes what it really is: one optional discard cost followed by one filtered multi-pick deck search.

That is the right level to build reusable engine code around.