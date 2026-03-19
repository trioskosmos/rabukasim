# Canonical Ability Model

This folder is the hub for the pipeline simplification work.

## Target

`Japanese text -> canonical code model -> engine execution`

The goal is to keep one semantic translation layer between source text and game behavior.

## Current progress

### Working now

- dedicated migration hub folder
- first canonical schema in [canonical_schema.py](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_schema.py)
- first semantic validator in [canonical_validator.py](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_validator.py)
- canonical goldens in [tests/canonical_goldens](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens)
- QA-backed migration anchors in [FIRST_MIGRATION_BATCH.md](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/FIRST_MIGRATION_BATCH.md)
- canonical-to-compiled bridge in [compare_canonical_to_compiled.js](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/compare_canonical_to_compiled.js)
- parser drift audit in [audit_parser_v2_inputs.js](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/audit_parser_v2_inputs.js)
- standard-profile checker in [check_standard_pseudocode_profile.js](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/check_standard_pseudocode_profile.js)
- candidate classifier in [classify_standard_profile_candidates.js](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/classify_standard_profile_candidates.js)

### Proven so far

- one real QA-anchored card matched through the comparison bridge:
  - `PL!-bp3-024-L`
- three easy cards also matched through the comparison bridge:
  - `PL!N-sd1-009-SD`
  - `PL!HS-bp1-006-P`
  - `PL!-bp5-013-N`
- `parser_v2.py` is compensating for multiple pseudocode dialects instead of one stable grammar
- strict-profile result: `1138 / 1356` abilities already fit the standard profile
- remaining legacy-normalization tail: `218 / 1356`
- profile-clean candidate split: `73 easy`, `950 medium`, `115 hard`

### Not working yet

- the engine does not execute canonical JSON directly
- there is no full JP-text-to-canonical conversion workflow yet
- the one translation layer is not standardized yet

## Next move

1. Freeze one standard input profile for the translation layer.
2. Split legacy pseudocode normalization away from strict parsing.
3. Broaden canonical lowering beyond the current subset.
4. Run at least one real card from canonical form instead of only comparing structures.

## Evidence

### Design docs

- [Model Samples](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/plans/canonical_ability_model_samples.md)
- [Validation Workflow](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/plans/canonical_model_validation_workflow.md)
- [Structured Operand IR Plan](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/plans/structured_operand_ir_plan.md)
- [Testing Strategy](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/TESTING_STRATEGY.md)
- [First Migration Batch](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/FIRST_MIGRATION_BATCH.md)
- [First Wave Easy Candidates](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/FIRST_WAVE_EASY_CANDIDATES.md)
- [Cheap Model Handoff](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/CHEAP_MODEL_HANDOFF.md)

### Current code

- [Canonical Schema](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_schema.py)
- [Canonical Validator](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_validator.py)
- [Validation CLI](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/validate_canonical_model.py)
- [Static Golden Checker](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/check_canonical_goldens.js)
- [parser_v2 Input Audit](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/audit_parser_v2_inputs.js)
- [Standard Profile Checker](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/check_standard_pseudocode_profile.js)
- [Candidate Classifier](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/classify_standard_profile_candidates.js)
- [Structured IR Helper](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/structured_instruction_ir.py)
- [Ability Hook](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/ability.py)

### Current examples and tracking

- [Golden: Draw One On Play](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/draw_one_on_play.json)
- [Golden: Draw Then Discard On Play](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/draw_then_discard_on_play.json)
- [Golden: Optional Energy Count Blades Live Start](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/optional_energy_count_blades_live_start.json)
- [Golden: Choice Mode Select Member Add Hearts](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/choice_mode_select_member_add_hearts.json)
- [Golden: Real Card Natsuiro Egao Choice Mode](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/pl_bp3_024_l_natsuiro_egao_choice_mode.json)
- [Golden: Tap Opponent Cost LE 4 On Play](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tests/canonical_goldens/tap_opponent_cost_le_4_on_play.json)
- [Manifest](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/MANIFEST.json)

## Key findings

- Pseudocode should not remain the semantic authority.
- Bytecode should be a backend, not the meaning layer.
- `parser_v2.py` is too broad because the pseudocode contract drifted.
- The canonical code model should become the only structured meaning layer.
- Most current abilities already fit a stricter profile; the main migration tail is concentrated in inline condition gating, option blocks, legacy mode aliases, chained destinations, and raw boolean filters.
- "Passes standard profile" means "clean enough to translate," not "already easy"; most of the passing pool still has real semantic work such as costs, conditions, selections, bindings, and multi-step flows.

## Repro commands

```powershell
node tools/check_canonical_goldens.js
node tools/audit_parser_v2_inputs.js
node tools/check_standard_pseudocode_profile.js
node tools/classify_standard_profile_candidates.js
node tools/compare_canonical_to_compiled.js tests/canonical_goldens/draw_one_on_play.json PL!N-sd1-009-SD 0
node tools/compare_canonical_to_compiled.js tests/canonical_goldens/draw_then_discard_on_play.json PL!HS-bp1-006-P 0
node tools/compare_canonical_to_compiled.js tests/canonical_goldens/tap_opponent_cost_le_4_on_play.json PL!-bp5-013-N 0
node tools/compare_canonical_to_compiled.js tests/canonical_goldens/pl_bp3_024_l_natsuiro_egao_choice_mode.json PL!-bp3-024-L 0
cargo test --lib test_q191 -- --nocapture
cargo test --lib test_q144 -- --nocapture
cargo test --lib test_q146 -- --nocapture
```

## Folder rule

Keep this folder small. The README should stay the main dashboard. Add new markdown files only when they are genuinely specialized, not just another status update.
