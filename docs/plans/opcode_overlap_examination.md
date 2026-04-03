# Opcode Overlap Examination

Date: 2026-04-03

## Scope

This note compares the live Rust opcode runtime with the authored frame index and compiler-side opcode mapping, with an eye toward consolidation that preserves Japanese card-text meaning.

The main question is not only "which opcodes share code?" but also "which distinctions still matter to authored abilities, even if the runtime implementation is similar?"

## Live Runtime Source Of Truth

The active execution path is the interpreter loop in `engine_rust_src/src/core/logic/interpreter/mod.rs` plus the dispatcher in `engine_rust_src/src/core/logic/interpreter/handlers/mod.rs`.

A stale alternate dispatch path exists in `engine_rust_src/src/core/logic/interpreter/handlers/execution.rs`, but it is not called by the live interpreter.

Control-flow opcodes are handled directly by the interpreter loop:

- `O_RETURN`
- `O_JUMP`
- `O_JUMP_IF_FALSE`
- `O_NOP`

## Strong Runtime Overlaps

These opcodes are effectively low-level variants of the same runtime primitive:

- `O_DRAW`, `O_DRAW_UNTIL`, `O_ADD_TO_HAND`
- `O_RECOVER_LIVE`, `O_RECOVER_MEMBER`
- `O_SELECT_MEMBER`, `O_SELECT_LIVE`, `O_SELECT_PLAYER`
- `O_ADD_BLADES`, `O_BUFF_POWER`
- `O_SET_TARGET_SELF`, `O_SET_TARGET_OPPONENT`
- `O_PREVENT_ACTIVATE`, `O_PREVENT_BATON_TOUCH`, `O_PREVENT_SET_TO_SUCCESS_PILE`, `O_PREVENT_PLAY_TO_SLOT`
- `O_PLAY_MEMBER_FROM_HAND`, `O_PLAY_MEMBER_FROM_DISCARD`
- `O_ADD_HEARTS`, `O_SET_HEARTS`
- `O_SET_BLADES`, `O_ADD_BLADES`
- `O_REDUCE_HEART_REQ`, `O_INCREASE_HEART_COST`, `O_SET_HEART_COST`, `O_TRANSFORM_HEART`
- `O_ENERGY_CHARGE`, `O_PAY_ENERGY`, `O_ACTIVATE_ENERGY`, `O_PAY_ENERGY_DYNAMIC`, `O_PLACE_ENERGY_UNDER_MEMBER`

These overlaps are real, but they are not all equally safe to collapse at the authoring layer.

## Overlap That Should Be Preserved In Authoring

Some opcodes share low-level behavior but still encode different text semantics:

- `O_LOOK_DECK`, `O_REVEAL_CARDS`, `O_CHEER_REVEAL`, `O_LOOK_AND_CHOOSE`, `O_ORDER_DECK`, `O_LOOK_REORDER_DISCARD`, `O_REVEAL_UNTIL`, `O_SEARCH_DECK`
- `O_MOVE_TO_DISCARD`, `O_MOVE_TO_DECK`, `O_SWAP_ZONE`, `O_PLAY_LIVE_FROM_DISCARD`, `O_SELECT_CARDS`
- `O_ACTIVATE_MEMBER`, `O_SET_TAPPED`, `O_TAP_MEMBER`, `O_TAP_OPPONENT`, `O_MOVE_MEMBER`, `O_FORMATION_CHANGE`, `O_PLACE_UNDER`, `O_ADD_STAGE_ENERGY`, `O_GRANT_ABILITY`, `O_INCREASE_COST`
- `O_BOOST_SCORE`, `O_REDUCE_COST`, `O_SET_SCORE`, `O_REDUCE_SCORE`, `O_LOSE_EXCESS_HEARTS`, `O_SKIP_ACTIVATE_PHASE`
- `O_META_RULE`, `O_TRIGGER_REMOTE`
- `O_SELECT_MODE`, `O_COLOR_SELECT`, `O_OPPONENT_CHOOSE`

These are good candidates for shared internal helpers, but not necessarily for merging authored frame representations.

## Compiler And Authored Frame Picture

The compiler-side semantic processor in `engine/compiler/semantic_processor.py` still maps opcode names directly to `EffectType` values.

That is important: the compiler currently wants a rich semantic vocabulary. The runtime can share code aggressively underneath, but the authored model still needs distinct names so Japanese text can be translated faithfully.

The authored frame index shows a strong concentration in a small core of motifs:

- `RETURN`
- `JUMP_IF_FALSE`
- `MOVE_TO_DISCARD`
- `JUMP`
- `DRAW`
- `SELECT_MEMBER`
- `ADD_BLADES`
- `ADD_HEARTS`
- `BOOST_SCORE`
- `NOP`
- `LOOK_AND_CHOOSE`
- `PAY_ENERGY`

This suggests the authored language is usually built from short frame phrases like:

- condition, then effect
- selection, then movement
- cost payment, then branch

## Quantitative Notes

The most common adjacent authored frame pairs are patterns like:

- `MOVE_TO_DISCARD -> JUMP_IF_FALSE`
- `ADD_BLADES -> RETURN`
- `BOOST_SCORE -> RETURN`
- `SUM_VALUE -> JUMP_IF_FALSE`
- `JUMP_IF_FALSE -> BOOST_SCORE`
- `JUMP_IF_FALSE -> DRAW`
- `NOP -> JUMP_IF_FALSE`
- `PAY_ENERGY -> JUMP_IF_FALSE`
- `LOOK_AND_CHOOSE -> RETURN`
- `SELECT_MEMBER -> MOVE_MEMBER`

This means consolidation should probably be built around motifs and shared frame decoding, not just opcode name reduction.

## Practical Consolidation Guidance

What looks safe to consolidate first:

- Shared attr and slot decoding in `AbilityFrameComponents`
- Shared prompt and suspension code for selection/recovery/reveal families
- Shared movement helpers for zone transfer, look/reveal, and discard finalization
- Shared state-modifier helpers for prevent, restriction, and immunity-like operations

What should probably stay separate in authored frames:

- Selection ops with different player-facing meaning
- Reveal/look/search ops with different information flow
- Score versus heart requirement ops
- Card movement versus card selection semantics

A useful rule of thumb is:

- If two opcodes only differ in how the runtime mutates state, share implementation.
- If two opcodes differ in what the Japanese text promises to the player, keep distinct authored opcodes and normalize only the low-level plumbing.

## Concrete Gap

`O_MODIFY_SCORE_RULE` is defined and still referenced by compiler-side mapping, but it has no live interpreter handler in the current runtime dispatch path. That looks like a real runtime gap, not just harmless duplication.

## Bottom Line

The overlap is real, but it is not a reason to collapse the authored model aggressively.

The best consolidation target is the semantic-frame decoding layer and the shared runtime helpers underneath it. That keeps the low-level implementation smaller while preserving the authored distinctions needed for Japanese text translation and debugging.