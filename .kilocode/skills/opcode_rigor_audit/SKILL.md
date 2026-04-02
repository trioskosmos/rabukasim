---
name: opcode_rigor_audit
description: Use when auditing opcodes for edge cases, missing coverage, or rule parity.
---
# Opcode Rigor Audit
## Do
- Check the opcode in isolation and in combination with nearby effects.
- Test boundary values and optional paths.
- Record what is covered and what still needs work.
## Do not
- Do not stop at one happy-path result.
- Do not treat a partial trace as proof.
## Verify
- Confirm the opcode behaves the same in focused and integrated tests.