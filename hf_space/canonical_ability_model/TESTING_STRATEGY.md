# Testing Strategy

## Short answer

No, we should not assume every Rust test is a perfect semantic authority.

Yes, we should absolutely use the Rust tests, especially QA tests, as one of the main anchors for canonical-model validation.

## Trust ranking

### 1. Official QA ruling tests

Primary file family:

- `engine_rust_src/src/qa/`

Strongest evidence:

- [QA module docs](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/qa/mod.rs)

Why they are high-value:

- they are explicitly intended to encode official rulings
- many tests describe the expected gameplay outcome directly
- they often assert concrete board/hand/zone changes

Why they are not perfect:

- coverage is incomplete
- some tests are coarse or integration-level
- some tests may accidentally encode current-engine behavior rather than ideal semantics

Use them as:

- the strongest automated oracle for covered interactions

### 2. Real DB card-specific QA tests

Primary file family:

- `engine_rust_src/src/qa/batch_card_specific.rs`
- `engine_rust_src/src/qa/batch_card_specific_real_gaps.rs`

Why they are valuable:

- they use real cards from the live database
- they exercise actual card text/conditions/filter behavior
- they are especially good for edge cases and real card identities

Why they are not perfect:

- many are targeted regressions for known gaps
- some are built from test-harness search/setup logic rather than explicit card text only

Use them as:

- the best bridge between abstract rulings and real production cards

### 3. Semantic assertion/oracle tests

Primary file:

- [semantic_assertions.rs](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/semantic_assertions.rs)

Why they are useful:

- broad coverage
- good for mass verification and regression detection

Why they are weaker as authority:

- they rely on pseudocode/oracle truth inputs
- they can inherit mistakes from the current pseudocode pipeline

Use them as:

- secondary consistency checks
- broad smoke tests

### 4. Generic regression/unit tests

Examples:

- engine logic tests
- helper tests
- response flow tests

Why they matter:

- they protect runtime behavior and interpreter mechanics

Why they are weaker for card semantics:

- many do not directly represent real card text
- they may verify implementation details rather than rulings

Use them as:

- backend safety checks, not semantic source-of-truth tests

## Recommended rule

For canonical-model migration:

- treat QA tests as the strongest automated semantic anchor
- treat real card-specific QA tests as the best validation for actual cards
- treat semantic assertions as broad regression support
- do not accept a canonical conversion solely because a generic unit test still passes

## How to test canonical-model cards

For each candidate card:

1. Find whether there is a matching QA or real-card QA test.
2. If yes, make that test part of the acceptance gate.
3. If no, add a focused card-specific test before trusting the migration.
4. Also run general backend tests to ensure no interpreter regression.

## Acceptance ladder

A canonical-model card conversion is strongest when all of these hold:

1. Schema validation passes.
2. Lowering succeeds without opaque fallback.
3. Matching QA/card-specific test passes.
4. Broader semantic or regression tests still pass.

If only 1 and 4 pass, that is not enough.

## What to do with sample cards

For the sample set in:

- [Model Samples](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/docs/plans/canonical_ability_model_samples.md)

we should prefer cards that already have QA coverage first.

That gives us:

- a cleaner migration loop
- better trust in the canonical representation
- less risk of merely preserving an old bug

## Practical policy

When building the canonical-model batch workflow:

- add metadata like:
  - `qa_covered`
  - `qa_test_names`
  - `semantic_oracle_covered`
  - `needs_new_card_test`

That will help us prioritize migrations toward cards whose behavior is already grounded by strong tests.
