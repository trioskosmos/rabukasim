# LovecaSim: Interaction Cheat Sheet

> [!NOTE]
> This document details the interaction flow between the **Rust Engine** and the **Frontend**, specifically how abilities pause (suspend) for user input.

## Opcode Categorization

### 1. Automatic (Non-Interactive)
These opcodes resolve immediately without stopping the interpreter.
- `O_DRAW`: Draws cards to hand.
- `O_BOOST`: Adds to score bonus.
- `O_BUFF` / `O_BLADES`: Adds power/blades to members.
- `O_ACTIVATE_ENERGY`: Untaps energy cards.
- `O_NEGATE`: Marks triggers as negated.
- `O_CHARGE`: Untaps energy from deck.

### 2. Mandatory Choices (Suspends)
These opcodes **always** pause and wait for an `ACTION_ID` response.
- `O_SELECT_MODE`: Opens a modal for branching logic. (ID Range: `570+`)
- `O_COLOR_SELECT`: Opens a color picker. (ID Range: `580-585`)
- `O_TAP_O`: Requests selection of an opponent's stage slot. (ID Range: `600-602`)

### 3. Dynamic Choices (Context Dependent)
These opcodes may skip interaction if only one valid target exists, or if certain attributes are set.
- `O_PAY_ENERGY`:
    - **Automatic**: If no optional bit is set, it auto-taps.
    - **Interactive**: If `attr & 0x82` is set, it asks "Pay Energy?" (ID Range: `550-551`).
- `O_LOOK_AND_CHOOSE` (List Selection):
    - Opens a card list overlay. (ID Range: `600+`)
- `O_TAP_M`:
    - **Automatic**: If selecting "Self" or only one member.
    - **Interactive**: If `attr & 0x02` is set, it asks for a specific member.

## Action ID Reference Table

| Range | Context | Usage |
| :--- | :--- | :--- |
| `0` | Global Skip | Discard remaining looked cards, skip optional cost, "No" to promt. |
| `500-559` | Hand | Selecting a card currently in hand. |
| `560-569` | Generic | Resumption signals. |
| `570-579` | Modal Mode | Choosing Option A/B/C from `SELECT_MODE`. |
| `580-585` | Modal Color | Pink(0), Red(1), Yellow(2), Green(3), Blue(4), Purple(5). |
| `600-602` | Stage Slots | Left, Mid, Right (Self or Opponent). |
| `600-659` | List Index | Choosing the N-th card in a "Looked Cards" or "Discard" list. |

## Resumption Logic in `interpreter.rs`
When an opcode calls `suspend_interaction`, the following happens:
1. `state.phase` shifts to `Phase::Response`.
2. A `PendingInteraction` is pushed to the stack containing the `program_counter` (IP) of the CURRENT instruction.
3. The engine returns controle to the caller.
4. The caller (Frontend/Server) must send a `step(action_id)` call to resume.
5. `resolve_bytecode` restarts from the stored IP, injecting the `action_id` into `ctx.choice_index`.

## State Transparency (The Visibility Gap)

The following engine states are **not** currently surfaced through the main Action serialization:

| Gap | Description | Impact |
| :--- | :--- | :--- |
| **Passive Stats** | Constant power/blade buffs from other members. | Card value in sidebar might not match calculated logic. |
| **Queue Depth** | How many abilities are still waiting to resolve. | Player doesn't know "one more popup is coming". |
| **Filter Logic** | Why a specific card is selectable (or not). | Debugging complex filters (e.g., "Member of Unit X with Cost >= 3"). |
| **Progress Count**| "Pick 1 of 3" status during multi-picks. | Action label is generic (e.g., "Select Slot 1"). |

### Recommended Verifications
- **For Passives**: Manually inspect `player.blade_buffs` or `player.heart_buffs` in the engine log.
- **For Filters**: Cross-reference the `filter_attr` bitmask with `logic.rs:card_matches_filter`.
- **For Queue**: Check `gs.pending_abilities.len()` in the debugger.
