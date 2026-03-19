# Canonical Ability Model Skill

Use this folder when the task is about reducing the JP-text-to-engine pipeline, defining the canonical ability model, validating generated canonical JSON, or planning migration away from packed bytecode as the source of truth.

## Mission

Help move the project toward:

`Japanese text -> canonical code model -> engine execution`

without adding permanent duplicate meaning layers.

## Principles

1. Keep exactly one semantic translation layer.
2. Pseudocode is a helper or compatibility surface, not the final semantic authority.
3. The canonical code model is the single structured meaning layer.
4. Bytecode is a backend encoding, not the primary authored representation.
5. Cheap model output must be validated, never trusted blindly.
6. Unknown or ambiguous semantics must be marked for review, not guessed.

## Start here

- [README](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/README.md)
- [First Migration Batch](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/FIRST_MIGRATION_BATCH.md)
- [Testing Strategy](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/canonical_ability_model/TESTING_STRATEGY.md)

## Main code entry points

- [Schema](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_schema.py)
- [Validator](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/compiler/canonical_validator.py)
- [Validation CLI](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/validate_canonical_model.py)
- [Structured IR Helper](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine/models/structured_instruction_ir.py)

## Expected workflow

1. Pick a card family or golden sample.
2. Express it in canonical JSON.
3. Validate schema and semantic rules.
4. Compare lowered behavior against the current backend.
5. Only then expand the batch.

## Current focus

Right now the most important work is:

1. standardizing the one translation layer
2. isolating legacy pseudocode normalization from parsing
3. proving real cards can be lowered from canonical form into matching runtime behavior

## Review policy

If output is ambiguous, preserve uncertainty using:

- `needs_review`
- `unknown_operand`
- `unknown_filter_fragment`
- `unknown_binding`
- `unsupported_pattern`

Do not invent missing semantics.
