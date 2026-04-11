---
name: ability_execution_frames
description: Use when changing ability frames, opcodes, pseudocode, or trigger execution.
---
# Ability Execution Frames
## Do
- Start from the current frame program or opcode handler.
- Keep cost, control, selection, and effect order aligned.
- Update runtime behavior and tests together.
## Do not
- Do not reintroduce deprecated bytecode assumptions.
- Do not widen scope when one frame or handler is enough.
## Verify
- Run the smallest relevant test with nocapture output.
- Confirm trace, state, and expected outcome match.