# Card-ID Specific Code Removed On 2026-04-03

- `engine_rust_src/src/core/hardcoded_cards.rs`: removed hard-coded energy-cost tables for card IDs `64, 159, 163, 234, 309, 472, 473, 474, 501, 542, 545, 577, 682, 688, 722, 873, 882, 4330, 4597, 4978`; they were overriding activated energy cost by `(card_id, ability_idx)` instead of using authored costs.
- `engine_rust_src/src/core/logic/action_gen/response.rs`: removed card `122` optional-response overrides that always offered pass and inlined hand-card actions into optional prompts; removed card `579` stage-selection fallback that first forced `Liella + green hearts >= 3`, then fell back to any occupied slot.
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_recovery.rs`: removed card `4789` same-name recovery override that forced same-name recovery behavior and fell back to all hand cards when no source cards were captured.
- `engine_rust_src/src/core/logic/interpreter/handlers/movement_discard.rs`: removed cards `122` and `4331` override that marked a one-card hand discard as optional even when the authored frame did not.
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs`: removed card `579` fallback that manufactured selectable stage targets from group and heart state when the filter produced no candidates.
- `engine_rust_src/src/core/logic/action_gen/main_phase.rs`: removed card `8844` activation bypass that ignored condition and cost checks; removed card `4955` deck-size workaround that blocked activation when deck size was under three regardless of authored frames.
- `engine_rust_src/src/core/logic/rules.rs`: removed card-specific cost tracing gate for cards `10` and `4433`; cost tracing is no longer keyed to card IDs.
- `engine_rust_src/src/core/logic/handlers.rs`: removed card `8844` condition-skip during activated ability enforcement.
- `engine_rust_src/src/core/logic/interpreter/suspension.rs`: removed card `4331` debug-print trigger and card `448` optional-cancel override for empty select-member prompts.
- `engine_rust_src/src/core/logic/interpreter/mod.rs`: removed card `579` activation gate and semantic-frame redirect; removed card `4849` pre-resolution forced hand discard; removed card `8844` bespoke activated resolution path; removed card `4331` and `358` debug traces and card `358` multi-effect fallback chooser.
- `engine_rust_src/src/core/logic/interpreter/conditions/opcodes.rs`: removed card `579` branch for opcode `306` that replaced normal target detection with a board-state predicate.
- `engine_rust_src/src/core/logic/interpreter/handlers/interaction_select_cards.rs`: removed card `537` zone override and card `10` optional-selection prompt suppression.
- `engine_rust_src/src/core/logic/interpreter/handlers/select_mode.rs`: removed card `461` opponent-choice override during select-mode suspension.
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member_formation.rs`: removed card `590` fixed-rotation formation-choice override.
- `engine_rust_src/src/core/logic/interpreter/handlers/state_score_requirements.rs`: removed card `4632` heart-color override that forced color `6` when params did not encode a color.
- `engine_rust_src/src/core/logic/interpreter/handlers/flow_select_resolve.rs`: removed card `4196` debug trace gating around tap selection resolution.
- `engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs`: removed card `4196` debug trace gating around tap-state application.
- `engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs`: removed card `4853` debug trace gating around `O_ADD_HEARTS`.
- `engine_rust_src/src/core/logic/interpreter/handlers/state_score_stats.rs`: removed card `4853` debug trace gating around heart-buff application.

The next step after this deletion pass is to identify which authored attrs, filters, or frame semantics were previously being papered over by these branches and restore them generically.