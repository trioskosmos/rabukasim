# First Migration Batch

## Goal

Pick canonical-model pilot cards that are both:

- representative of the model we want
- already covered by stronger QA or card-specific tests when possible

## Recommended first batch

### Tier A: Strongly anchored by QA/card-specific coverage

These are the best first migration candidates because the repo already has stronger semantic checks for them or close neighboring rulings.

1. `PL!-bp3-024-L` / `夏色えがおで1,2,Jump!`

- Sample role: choose-one branch model
- Card record: live `id=47`
- Why first: this is an important branching pattern for the canonical model
- Related QA coverage:
  - [Q144 real-card selection flow](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/qa/batch_card_specific_real_gaps.rs)
  - [Q191 mode-selection behavior](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/qa/batch_4_unmapped_qa.rs)

2. `PL!S-bp3-006-P` / `津島善子`

- Sample role: chained activated ability with stored values and slot-sensitive follow-up
- Card record: member `id=444`
- Why first: this is a realistic medium-complexity activated ability
- Related QA coverage:
  - [Q144 target-selection handling](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/qa/batch_card_specific_real_gaps.rs)

3. `PL!-pb1-004-P+` / `園田海未`

- Sample role: precondition + computed value + conditional grant ability
- Why first: this pressures binding and conditional grant modeling
- Related QA coverage:
  - [Q146 source member counting](C:/Users/trios/.gemini/antigravity/vscode/loveca-copy/engine_rust_src/src/qa/batch_card_specific_real_gaps.rs)

4. `PL!SP-bp5-009-AR` / `鬼塚夏美`

- Sample role: long repeated live-start structure
- Card record: member `id=862`
- Why first: tests whether canonical model can compress repeated subroutines
- Related QA coverage:
  - no direct matching Q-test found yet
- Status:
  - important design sample
  - should migrate only after adding a focused card-specific test

### Tier B: Good schema shakedown, weaker direct QA anchor

5. `PL!N-sd1-009-SD` / `天王寺璃奈`

- Sample role: trivial `DRAW(1)`
- Card record: member `id=377`
- Why first: easy schema sanity check
- Related QA coverage:
  - no direct card-specific QA match found
- Use as:
  - schema/lowering smoke test

6. `PL!HS-bp1-006-P` / `藤島 慈`

- Sample role: sequential effects
- Card record: member `id=171`
- Why first: confirms simple ordered multi-step lowering
- Related QA coverage:
  - no direct card-specific QA match found

7. `PL!HS-bp2-005-P` / `大沢瑠璃乃`

- Sample role: optional cost + stored success/value bindings
- Card record: member `id=192`
- Why first: exposes missing boolean-combinator support in schema
- Related QA coverage:
  - no direct card-specific QA match found
- Status:
  - keep as schema-pressure sample
  - not ideal as first fully accepted migration target

8. `PL!N-bp3-009-P` / `天王寺璃奈`

- Sample role: aggregate calculation over chosen cards
- Card record: member `id=277`
- Why first: important for `store_as` and sum/value logic
- Related QA coverage:
  - no direct card-specific QA match found

9. `PL!N-bp3-011-P` / `ミア・テイラー`

- Sample role: selected target reused across repeated conditional bonuses
- Card record: member `id=279`
- Why first: pressures target binding reuse
- Related QA coverage:
  - no direct card-specific QA match found

## Practical order

### Pass 1

- `PL!N-sd1-009-SD`
- `PL!HS-bp1-006-P`
- `PL!-bp3-024-L`

Reason:

- two low-risk schema checks
- one branch-heavy high-value card

### Pass 2

- `PL!S-bp3-006-P`
- `PL!-pb1-004-P+`

Reason:

- stronger value/binding/slot logic
- closer to real migration difficulty

### Pass 3

- `PL!HS-bp2-005-P`
- `PL!N-bp3-009-P`
- `PL!N-bp3-011-P`

Reason:

- stored values and aggregate/value-expression gaps

### Pass 4

- `PL!SP-bp5-009-AR`

Reason:

- long repeated pattern
- probably needs either repeat-block schema support or a targeted helper abstraction

## Acceptance policy for this batch

For each card:

1. Canonical JSON validates.
2. Lowering works without opaque packed fallback.
3. Matching QA or card-specific test passes if one exists.
4. If no matching QA test exists, add one before declaring the migration trustworthy.

## Immediate next action

Start by adding focused canonical-model goldens and acceptance hooks for:

- `PL!-bp3-024-L`
- `PL!S-bp3-006-P`
- `PL!-pb1-004-P+`

Those give the best balance of:

- real card semantics
- useful complexity
- existing rule/test anchors
