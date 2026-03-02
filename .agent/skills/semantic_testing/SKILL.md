# Semantic Testing Methodology (LovecaSim)

This skill defines the standard for **Meaning-Driven Verification**. Unlike traditional unit tests that use hardcoded expectations, Semantic Testing triangulates logic across three independent sources.

## 1. The Triangulation Principle
Every test must validate parity between:
- **Intent (JP Text)**: What the card *should* do (decoded by the Oracle).
- **Instruction (Bytecode)**: What the engine *tries* to do (compiled logic).
- **Inertia (State Delta)**: What the engine *actually* did to the state zones.

## 2. Segmented Execution (The "Grey Box" Standard)
Abilities must not be verified as single blobs. They must be broken into **Segments** based on Japanese conjunctive logic (e.g., "その後", "さらに").

### The Execution Loop:
1. **Prepare**: Set up a clean GameState with sufficient resources.
2. **Snapshot**: Capture zone lengths and status (Hand, Deck, Energy).
3. **Execute**: Call `state.step()` or `state.resolve_bytecode()`.
4. **Iterate**: If the engine suspends (O_RESPONSE), use a **Choice Resolver** to pick the first valid target/action.
5. **Verify**: Compare the delta (After - Before) against the Segment's expected deltas.

## 3. Standard Semantic Tags
When writing or expanding the Oracle, use these standardized tags to map text to logic:

| Tag | Meaning | Threshold / Logic |
| :--- | :--- | :--- |
| `HAND_DELTA` | Draw/Return to hand | `after.hand - before.hand == value` |
| `ENERGY_COST` | Tapping energy | `before.active_energy - after.active_energy >= value` |
| `HAND_DISCARD`| Discarding for cost/effect | `before.hand - after.hand >= 1` |
| `ZONE_RECOVERY`| From Discard to Hand | `after.hand > before.hand` AND `after.discard < before.discard` |

## 4. Handling Suspensions (The Auto-Bot Rule)
Automated archetypes must be non-blocking.
- If `state.phase == Phase::Response`, the test runner MUST provide an `Action` to clear the stack.
- **Default Resolution**: Always pick `choice_idx: 0` or `hand_idx: 0` unless specifically testing a choice-dependent branch.

## 5. Failure Triage
When a semantic test fails, categorize it immediately:
- **Type A (Oracle Bug)**: The Japanese text was parsed incorrectly (e.g., misunderstood a negative).
- **Type B (Compiler Bug)**: The bytecode translation does not match the JP intent.
- **Type C (Engine Bug)**: The bytecode is correct, but the interpreter opcode logic is flawed.
- **Type D (Environment Bug)**: The test setup lacked cards in a specific zone (e.g., empty deck for draw).
