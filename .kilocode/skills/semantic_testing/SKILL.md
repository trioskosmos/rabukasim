---
name: semantic_testing
description: Use when testing behavior by meaning rather than literal opcode sequences.
---
# Semantic Testing
## Do
- State the rule in plain language first.
- Build a minimal scenario that proves the semantic outcome.
- Compare expected vs actual behavior, not just implementation details.
## Do not
- Do not hide a mismatch behind incidental success.
- Do not rely only on opcode shape.
## Verify
- Make the semantic outcome visible in the final state or trace.