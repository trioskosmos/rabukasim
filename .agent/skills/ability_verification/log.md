# Rust Test Coverage Log

This log tracks the coverage of card abilities in the Rust engine tests.

## Verified Unique Abilities (from all_unique_abilities.md)

| Rank | Representative CID | Ability Summary | Coverage Status | Reference Test | Notes |
|------|--------------------|-----------------|-----------------|----------------|-------|
| 1 | `PL!-sd1-005-SD` | Activated: Recov Live | **COVERED** | `archetype_tests.rs::test_sd01_karin` | Basic recovery logic verified. |
| 2 | `PL!-sd1-002-SD` | Activated: Recov Member | **COVERED** | `archetype_tests.rs::test_sd01_honoka` | |
| 3 | `PL!-sd1-011-SD` | OnPlay: Look 3, Choose 1 | **COVERED** | `ability_tests.rs::test_look_and_choose` | Generic O_LOOK_AND_CHOOSE test. |
| 4 | `PL!HS-PR-018-PR` | OnLiveStart: Pay E -> Blade | **COVERED** | `archetype_tests.rs::test_promo_rurino_pay_energy` | |
| 6 | `PL!N-bp1-019-PR` | OnPlay: Draw 1, Discard 1 | **COVERED** | `archetype_tests.rs::test_draw_discard_representative` | |
| 7 | `PL!-PR-007-PR` | Modal: Draw/Yell mulligan | **COVERED** | `coverage_gap_tests.rs::test_modal_answer` | Tested via modal answer opcode. |
| 8 | `PL!SP-PR-004-PR` | OnPlay: Discard -> Energy | **COVERED** | `archetype_tests.rs::test_draw_discard_representative` | Variant of discard cost. |
| 9 | `PL!N-PR-005-PR` | OnPlay: Draw 2, Discard 2 | **COVERED** | `archetype_tests.rs::test_draw_discard_representative` | Multi-card variant. |
| 10 | `PL!-bp3-014-N` | OnPlay: Order Deck | **COVERED** | `ability_tests.rs::test_order_deck` | |
| 18 | `PL!N-bp1-002-R+` | Play from Discard | **COVERED** | `coverage_gap_tests.rs::test_play_member_from_discard` | |
| 31 | `PL!SP-bp2-001-R+` | Negate Trigger | **COVERED** | `coverage_gap_tests.rs::test_negate` | |
| 34 | `PL!SP-bp2-010-R+` | Increase Heart Cost | **COVERED** | `coverage_gap_tests.rs::test_increase_heart_req` | Opcode 61 verified. |

## Feature Coverage Matrix

| Feature | Opcode(s) | Status | Test File |
|---------|-----------|--------|-----------|
| Draw | 10, 66 | **COVERED** | `ability_tests.rs` |
| Recovery | 15, 17 | **COVERED** | `ability_tests.rs` |
| Discard | 58 | **COVERED** | `archetype_tests.rs` |
| Deck Order | 28 | **COVERED** | `ability_tests.rs` |
| Modal | 30, 212 | **COVERED** | `coverage_gap_tests.rs` |
| Negate | 27 | **COVERED** | `coverage_gap_tests.rs` |
| Swap Area | 72 | **COVERED** | `wave2_tests.rs` |
| Grant Ability| 60 | **COVERED** | `wave2_tests.rs` |
| Energy Mod | 23, 81 | **COVERED** | `coverage_gap_tests.rs` |
| Baton Touch | 36, 90 | **COVERED** | `coverage_gap_tests.rs` |

## Identified Gaps

1. **O_ADD_STAGE_ENERGY (Opcode 50)**:
   - **Status**: **NOT IMPLEMENTED** in Rust Interpreter.
   - **Impact**: Cards that put energy under members (e.g., #42 `PL!N-bp3-001-R+` if correctly compiled) will not function.
   - **Action**: Implement in `interpreter.rs`.

2. **O_SELECT_MEMBER (Opcode 65)**:
   - **Status**: **PARTIAL** in Rust. It exists but complex filtering (by name, group, etc.) might need more edge case tests.
   - **Test**: `opcode_missing_tests.rs::test_select_member`.

3. **C_OPP_ENR_DIF (Condition 225)**:
   - **Status**: **STUBBED/UNTESTED** in some scenarios.
   - **Test**: `coverage_gap_tests.rs::test_opp_enr_dif`.

## Global Verification Status

All 500+ cards in the `cards_compiled.json` are periodically dry-run via `database_tests.rs::test_dry_run_all_cards`. This ensures:
- Bytecode is well-formed.
- Opcodes are recognized (or ignored safely).
- State transitions don't crash the engine.
