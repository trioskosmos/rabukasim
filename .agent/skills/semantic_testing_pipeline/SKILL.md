# Semantic Testing Pipeline

## Overview

The semantic testing pipeline validates card abilities by comparing expected behavior (from pseudocode) against actual engine execution.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Semantic Testing Pipeline                             │
└─────────────────────────────────────────────────────────────────────────────┘

manual_pseudocode.json  →  pseudocode_oracle.py  →  semantic_truth_v3.json
       (入力)                   (処理)                    (出力)
       769カード                パーサー                  期待値DB
       擬似コード               変換処理                  JSON形式
                                                          │
                                                          ▼
                                              semantic_assertions.rs
                                                      (Rustテスト)
                                                          │
                                                          ▼
                                                   806/926 PASS (87%)
```

## Files

| File | Type | Purpose |
|------|------|---------|
| `data/manual_pseudocode.json` | Input | 769 cards with structured pseudocode |
| `tools/verify/pseudocode_oracle.py` | Code | Parser that converts pseudocode to expectations |
| `reports/semantic_truth_v3.json` | Data | Generated expectations (Rust test input) |
| `engine_rust_src/.../semantic_assertions.rs` | Test | Validates engine behavior against expectations |

## Pseudocode Format

```pseudocode
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: DRAW(2)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE {MIN=1}
EFFECT: BOOST_SCORE(3) -> SELF
```

### Trigger Types
- `ON_PLAY` - When card is played
- `ON_LIVE_START` - At start of Live phase
- `ON_LIVE_SUCCESS` - After successful Live
- `ACTIVATED` - Activated ability
- `CONSTANT` - Passive effect
- `ON_LEAVES` - When leaving play
- `TURN_END` - At end of turn

### Effect Mappings

| Pseudocode | Delta Tag |
|------------|-----------|
| `DRAW(n)` | `HAND_DELTA` |
| `DISCARD_HAND(n)` | `HAND_DISCARD` |
| `TAP_OPPONENT(n)` | `MEMBER_TAP_DELTA` |
| `ADD_BLADES(n)` | `BLADE_DELTA` |
| `BOOST_SCORE(n)` | `SCORE_DELTA` |
| `RECOVER_MEMBER(n)` | `HAND_DELTA` |
| `RECOVER_LIVE(n)` | `LIVE_RECOVER` |
| `ADD_HEARTS(n)` | `HEART_DELTA` |
| `BUFF_POWER(n)` | `POWER_DELTA` |

### Dynamic Values

| Value | Meaning |
|-------|---------|
| `COUNT_STAGE` | Number of cards on stage |
| `COUNT_SUCCESS_LIVE` | Number of successful lives |
| `99` | ALL / unlimited |
| `ALL` | All applicable targets |

## Running Tests

### Generate Truth
```bash
python tools/verify/pseudocode_oracle.py
```

### Run Semantic Audit
```bash
cd engine_rust_src
cargo test test_semantic_mass_verification --lib -- --nocapture
```

### Full Test Suite
```bash
cd engine_rust_src
cargo test --lib
```

## Current Results

| Metric | Value |
|--------|-------|
| Abilities Tested | 926 |
| Pass Rate | 87.0% (806/926) |
| Negative Tests PASS | 628 |
| Negative Tests FAIL | 178 |

## Improvement History

### v2 Improvements (2026-02-23)
- Fixed trigger normalization (preserve underscores: `ON_PLAY` not `ONPLAY`)
- Extended effect mappings (30+ effects)
- Added dynamic value handling (`COUNT_STAGE`, `99=ALL`)
- Added condition block parsing
- Added modal option parsing
- Added filter extraction

### Regression Fix
- **Before**: 54.2% pass rate
- **After**: 87.0% pass rate (+32.8%)

## Adding New Cards

1. Add pseudocode to `data/manual_pseudocode.json`:
```json
{
  "NEW-CARD-ID": {
    "pseudocode": "TRIGGER: ON_PLAY\nEFFECT: DRAW(1)"
  }
}
```

2. Regenerate truth:
```bash
python tools/verify/pseudocode_oracle.py
```

3. Run tests to verify:
```bash
cargo test test_semantic_mass_verification --lib
```

## Troubleshooting

### Empty Sequence
- Check if effect is in `EFFECT_TO_DELTA` mapping
- Verify pseudocode format matches expected pattern

### Wrong Trigger
- Ensure trigger uses underscores: `ON_PLAY` not `ONPLAY`
- Check `TRIGGER_MAP` for valid trigger types

### Condition Not Met
- Some abilities have preconditions that may not be satisfied in test environment
- Check `CONDITION:` block in pseudocode
