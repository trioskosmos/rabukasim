# Rust Compiler Log

This log tracks compilation failures, root causes, and applied fixes to maintain a history of technical debt and common pitfalls in the Rust engine.

## Compilation History

| Date | Task | Error Summary | Root Cause | Fix Applied |
| :--- | :--- | :--- | :--- | :--- |
| 2026-02-07 | Interactive Recovery | 72 Errors (SmallVec/Imports) | Missing `SmallVec` constructor `from_vec` and shifted line numbers. | Re-located opcodes and used `SmallVec::from()`. |

## Common Pitfalls
- **Line Number Shifts**: Editing large files like `logic.rs` leads to line number mismatches in concurrent tasks. Always use `findstr` or `grep` to re-locate symbols before editing.
- **SmallVec API**: `SmallVec` uses different constructor patterns than standard `Vec`. Prefer `SmallVec::from()` for conversions.
- **Phase Transitions**: Forgetting to set `Phase::Response` when pausing for input causes the engine to skip the resumption logic.
