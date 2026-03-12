# VM Implementation Guide: Opcodes & Fast Logic

This guide documents the high-performance Virtual Machine (VM) updates implemented in `engine/game/fast_logic.py`, specifically targeting the "Critical Gap" opcodes identified for Logic Coverage Speedup.

## 1. New Opcodes Implemented

The following opcodes have been added to the Numba-compiled `fast_logic.py` engine:

| Opcode | ID | Name | Description |
| :--- | :--- | :--- | :--- |
| **SELECT_MODE** | 30 | `O_SELECT_MODE` | Implements branching/modal logic via Jump Tables. |
| **TRIGGER_REMOTE** | 47 | `O_TRIGGER_REMOTE` | Recursively executes an ability from another card (e.g., from Hand or Stage). |
| **SEARCH_DECK** | 22 | `O_SEARCH_DECK` | Moves a specific card (chosen by AI) from Deck to Hand. |
| **LOOK_AND_CHOOSE** | 41 | `O_LOOK_AND_CHOOSE` | Reveals top N cards, adds one to hand, discards rest. |
| **ORDER_DECK** | 28 | `O_ORDER_DECK` | Reorders (reverses/shuffles) the top N cards of the deck. |
| **REDUCE_COST** | 13 | `O_REDUCE_COST` | Adds a cost-reduction modifier to continuous effects. |
| **REDUCE_HEART_REQ** | 48 | `O_REDUCE_HEART_REQ` | Adds a heart-requirement reduction modifier. |
| **REPLACE_EFFECT** | 46 | `O_REPLACE_EFFECT` | Sets a replacement effect flag/modifier. |
| **SWAP_CARDS** | 21 | `O_SWAP_CARDS` | Discards N cards from hand (filtering) and Draws N cards. |
| **PLACE_UNDER** | 33 | `O_PLACE_UNDER` | Moves a card from Hand to a member's Stage Energy. |
| **MOVE_MEMBER** | 20 | `O_MOVE_MEMBER` | Swaps two members (and their states) on the stage. |
| **ACTIVATE_MEMBER** | 43 | `O_ACTIVATE_MEMBER` | Untaps a member. (Fixed mapping from ID 17). |

## 2. Architecture Updates

To support these complex operations within the constraints of Numba (JIT compilation), two major architectural patterns were introduced:

### A. Recursion via Pass-by-Reference (`TRIGGER_REMOTE`)

Numba's type inference engine struggles with recursive function calls when functions return tuples that change state. To solve this for `TRIGGER_REMOTE`:

1.  **Refactored Signature**: `resolve_bytecode` no longer returns `(cptr, state, bonus)`.
2.  **Mutable Arrays**: It now accepts `out_cptr` and `out_bonus` as **Numpy arrays of size 1**.
3.  **In-Place Updates**: The function modifies `out_cptr[0]` and `out_bonus[0]` directly.
4.  **Recursive Call**: When `O_TRIGGER_REMOTE` is encountered, the VM looks up the target's bytecode and calls `resolve_bytecode` recursively, passing the same state arrays.

```python
# Pseudo-code pattern
@njit
def resolve_bytecode(..., out_cptr, out_bonus):
    # ... logic ...
    if op == O_TRIGGER_REMOTE:
        # Save state
        out_cptr[0] = cptr
        # Recursive call
        resolve_bytecode(..., out_cptr, out_bonus)
        # Reload state
        cptr = out_cptr[0]
```

### B. Jump Tables for Branching (`SELECT_MODE`)

Numba functions are linear. To implement "Choose One" modal effects:

1.  **Compiler**: `Ability.compile` (in `engine/models/ability.py`) generates a header block:
    *   `[O_SELECT_MODE, NumOptions, 0, 0]`
    *   Followed by `NumOptions` instructions of `[O_JUMP, Offset, 0, 0]`.
2.  **VM Logic**:
    *   Reads choice index from `flat_ctx[CTX_CHOICE_INDEX]`.
    *   Calculates the target Jump Instruction index: `ip + 1 + choice`.
    *   Reads the offset from that Jump instruction and executes the jump.

## 3. Dynamic Targeting (`MEMBER_SELECT`)

Targeting logic has been decoupled from bytecode hardcoding:

*   **Logic**: `if s == 10: s = int(flat_ctx[CTX_TARGET_SLOT])`
*   **Usage**: Any opcode (e.g., `BUFF`, `TAP`) can set its target slot (`s`) to `10`. The VM will then use the value provided by the Agent (in the Context Vector) at runtime.

## 4. Compiler Usage

The `Ability` class in `engine/models/ability.py` has been updated to automatically compile these structures.

```python
# Example: Creating a Modal Ability
ability = Ability(
    raw_text="Choose one: Draw 1 or Charge 1",
    trigger=TriggerType.ON_PLAY,
    effects=[Effect(EffectType.SELECT_MODE, 1)],
    # Ensure modal_options is set on the Ability or the Effect
    modal_options=[
        [Effect(EffectType.DRAW, 1)],
        [Effect(EffectType.ENERGY_CHARGE, 1)]
    ]
)

# Compiling
bytecode = ability.compile()
# Result: [SELECT_MODE, 2, ... JUMP ... JUMP ... DRAW ... JUMP_END ... CHARGE ... JUMP_END ...]
```

## 5. Additional Opcode Fixes

### Salvage vs. Untap Correction
- Previously, `O_RECOV_M` (ID 17) was incorrectly implemented as "Untap Member". In the official opcode list, ID 17 is `RECOVER_MEMBER` (Salvage from Discard), and `ACTIVATE_MEMBER` (Untap) is ID 43.
- **Fix**: The Untap logic has been moved to `O_ACTIVATE_MEMBER` (43). `O_RECOV_M` (17) and `O_RECOV_L` (15) are now placeholders (pass) because "Salvage" requires access to the Discard pile, which is not currently available in the fast VM state vector.

## 6. Testing

New tests in `tests/test_vm_opcodes.py` verify these features:
*   `test_select_mode_branching`: Verifies jump logic.
*   `test_trigger_remote`: Verifies recursion depth and state preservation.
*   `test_search_deck`: Verifies deck scanning and removal.
*   `test_look_and_choose`: Verifies "Look N, Pick 1, Discard Rest" logic.
*   `test_swap_cards`: Verifies discard/draw cycle.
*   `test_place_under`: Verifies moving cards to stage energy.
*   `test_move_member`: Verifies slot swapping.

Run tests with:
```bash
cargo test --manifest-path engine_rust_src/Cargo.toml test_vm_opcodes -- --nocapture
```
