# Ability Runtime Cleanup Audit

Date: 2026-04-04

## Biggest Concerns

1. Authored frame programs are not authoritative at runtime.
The loader hydrates authored frames from `data/ability_frame_index.json`, but `Ability::resolved_frames()` can still fall back to effect-derived frames when the frame/effect overlap heuristic decides the authored program is "unmatched". That allows control flow, conditions, and ordering authored in frames to be ignored.

2. The interpreter still executes a packed VM shape rather than a typed semantic IR.
`opcode/value/attr/slot` are repeatedly packed and unpacked across hydration, action generation, and execution. The runtime works, but too much meaning is recovered indirectly.

3. Condition handling has become a catch-all for data gaps and bespoke semantics.
`conditions/opcodes.rs` mixes stable conditions with card-specific workarounds and several opaque 300-series handlers. This makes it hard to tell which behavior is generic engine logic and which is compatibility debt.

4. Raw-text fallbacks still influence legality and effect interpretation.
Several paths still inspect `raw_text` or `original_text` to infer costs, tapped entry, thresholds, or heart colors. Those shims should shrink over time as authored frames become complete.

## Changes In This Pass

1. Make authored frame programs the runtime source of truth whenever present and non-empty.
2. Keep the frame/effect overlap heuristic only as a diagnostic signal, not as the selector for execution.
3. Pull opaque condition-opcode behavior into named helpers so the main condition table is easier to reason about.
4. Reword the known card 557 compatibility note to describe it as a hydrated-frame data gap rather than "bytecode".

## Follow-Up Still Needed

1. Replace raw-text-derived activation-cost and tapped-entry heuristics with authored frame metadata.
2. Replace opcode-sequence pattern matching in `ability_patterns.rs` with structured modal/choice metadata.
3. Move remaining known-card compatibility shims out of generic opcode handlers into data repair or focused compatibility modules.