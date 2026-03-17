# LovecaSim Opcode Reference

This document provides a technical breakdown of all opcodes used by the LovecaSim game engine. Opcodes are processed by the bytecode interpreter in `engine_rust_src/src/core/logic/interpreter.rs`.

## 1. Flow Control & Meta
| ID | Name | Description | Example Cards |
|---|---|---|---|
| 1 | RETURN | Ends the current ability execution and returns to the calling state. | LL-bp1-001-R＋ |
| 2 | JUMP | Unconditionally jumps to a specific instruction offset in the bytecode. | PL!-PR-005-PR |
| 3 | JUMP_IF_FALSE | Jumps to an offset if the last conditional check (cond) failed. | - |
| 29 | META_RULE | Modifies global gameplay rules (e.g., Cheer mod count). | PL!-pb1-018-P＋ |
| 34 | FLAVOR_ACTION | Placeholder for actions that have no mechanical effect but show text/UI. | - |

## 2. State Modification (Direct)
| ID | Name | Description | Example Cards |
|---|---|---|---|
| 10 | DRAW | Draws `X` cards from the deck to the hand. | PL!-PR-005-PR |
| 11 | ADD_BLADES | Adds `X` Blades to the targeted member slot. | LL-bp2-001-R＋ |
| 12 | ADD_HEARTS | Adds `X` Hearts of color `C` to the targeted slot. | PL!-bp3-008-P |
| 13 | REDUCE_COST | Reduces the cost of the next member played by `X`. | LL-bp2-001-R＋ |
| 18 | BUFF_POWER | Temporarily increases the power/stats of a member. | LL-bp2-001-R＋ |
| 23 | ENERGY_CHARGE | Adds `X` cards from the top of the deck to the energy zone. | PL!N-bp3-007-P |
| 37 | SET_SCORE | Sets the player's current score to exactly `X`. | PL!S-bp3-019-L |
| 50 | ADD_STAGE_ENERGY | Adds raw energy pips directly to a member slot. | - |
| 81 | ACTIVATE_ENERGY | Forces an energy card to become "Active" (untapped). | LL-bp3-001-R＋ |

## 3. Complex Interactions (Response Required)
| ID | Name | Description | Example Cards |
|---|---|---|---|
| 15 | RECOVER_LIVE | Moves a Live card from the discard pile to the Live Zone. | PL!-PR-003-PR |
| 17 | RECOVER_MEMBER | Moves a Member card from the discard pile to the Hand. | LL-bp1-001-R＋ |
| 41 | LOOK_AND_CHOOSE | Looks at `X` cards from `Zone`, picks `Y` to move to `Dest`. | LL-bp4-001-R＋ |
| 45 | COLOR_SELECT | Prompts the player to choose a heart color (Pink, Red, etc.). | PL!-sd1-003-SD |
| 58 | MOVE_TO_DISCARD | Prompts player to discard `X` cards from `Source`. | PL!-sd1-007-SD |
| 63 | PLAY_FROM_DISCARD | Plays a member directly from the discard pile to a slot. | PL!HS-bp1-002-P |
| 65 | SELECT_MEMBER | Prompts player to select a member on the stage. | PL!-pb1-018-P＋ |
| 68 | SELECT_LIVE | Prompts player to select a Live card in the Live Zone. | - |

## 4. Targeting Opcodes
These opcodes set the `target` register for subsequent instructions.
- **100**: SET_TARGET_SELF
- **101**: SET_TARGET_PLAYER
- **102**: SET_TARGET_OPPONENT
- **104**: SET_TARGET_MEMBER_SELF
- **110**: SET_TARGET_MEMBER_SELECT

## 5. Triggers
| ID | Name | Description |
|---|---|---|
| 1 | ON_PLAY | Fires when the member is played to the stage. |
| 2 | ON_LIVE_START | Fires at the beginning of a Live performance. |
| 3 | ON_LIVE_SUCCESS | Fires when a Live is successfully completed. |
| 6 | CONSTANT | Active as long as the card is in the correct zone. |
| 7 | ACTIVATED | Requires manual activation by the player. |
| 8 | ON_LEAVES | Fires when the member leaves the stage. |

## 6. Conditions (Check Logic)
Used within abilities to determine if an effect should execute.
- **201**: CHECK_HAS_MEMBER (Does the player have a specific member?)
- **204**: CHECK_COUNT_HAND (Does the player have `X` cards in hand?)
- **206**: CHECK_IS_CENTER (Is the member in the Center slot?)
- **213**: CHECK_COUNT_ENERGY (Does the player have `X` energy?)
- **221**: CHECK_HAS_CHOICE (Did the player make a specific choice in a previous step?)
