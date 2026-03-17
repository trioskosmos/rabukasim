# AlphaZero Nitpick Review Report

## Files Reviewed
- [`alphazero/overnight_pure_zero.py`](alphazero/overnight_pure_zero.py) (Main entry point)
- [`alphazero/alphanet.py`](alphazero/alphanet.py) (Neural network architecture)
- [`alphazero/train.py`](alphazero/train.py) (Training utilities)
- [`engine/game/deck_utils.py`](engine/game/deck_utils.py) (Deck parsing)
- `engine_rust` (Compiled PyO3 module - binary only, not reviewed)

---

## 1. [`alphazero/overnight_pure_zero.py`](alphazero/overnight_pure_zero.py) - Nitpicks

### Critical Issues

| Line | Issue | Description |
|------|-------|-------------|
| 94 | **IndexError Risk** | `np.random.randint(0, buf_size, ...)` can return empty array if `buf_size=0`, causing downstream errors |
| 183-184 | **File Handle Leak** | Opens log file but `log_path.stat().st_size` called before flush - could fail if file is new and not yet flushed |
| 225 | **Deprecation Warning** | `np.bool_` is deprecated in NumPy 2.0, use `np.bool_` → `bool` or `np.bool_` → `np.bool_` |

### Potential Bugs

| Line | Issue | Description |
|------|-------|-------------|
| 70-76 | **Logic Error** | Deck loading: `(m + m*4)[:48]` duplicates members 5 times total. Is this intentional for tournament play? |
| 202 | **Variable Shadowing** | `game_history` shadows potential import if added later |
| 254-256 | **Tie Game Handling** | When `winner == -1` (tie), all players get `outcome=0.0`. Should explicitly handle tie case. |
| 271-272 | **Buffer Management** | `master_buffer = master_buffer[-MAX_BUFFER_SIZE:]` creates new list each iteration - inefficient for large buffers |

### Code Quality

| Line | Issue | Description |
|------|-------|-------------|
| 21 | **Magic Number** | `NUM_ITERATIONS = 1000000` - should be configurable via CLI or config |
| 40 | **Late Import** | `UnifiedDeckParser` imported inside module (line 40) - should be at top |
| 90 | **In-Function Import** | `import torch.nn.functional as F` inside function - move to top |
| 116-118 | **Entropy Sign** | Entropy is negated: `ENTROPY_LAMBDA * -entropy`. Comment says "encourage exploration" but negative entropy term *reduces* entropy (encourages exploitation). Check if this is intended. |
| 162-166 | **Silent Failure** | Model loading failure silently continues - could lead to confusion |
| 199 | **Hardcoded Empty Lists** | `[], []` for extra arguments - what are these? Should be documented or configurable |

### Style & Best Practices

| Line | Issue | Description |
|------|-------|-------------|
| 1-7 | **Import Order** | Standard library imports not grouped (random, time, os before json) |
| 41 | **Trailing Import** | `from engine.game.deck_utils import` at line 40 is unusual placement |
| 260-261 | **Inconsistent Types** | `obs_f32` explicitly cast to float32, but `pol_f16` uses float16 - comment says float16 can overflow |

---

## 2. [`alphazero/alphanet.py`](alphazero/alphanet.py) - Nitpicks

### Critical Issues

| Line | Issue | Description |
|------|-------|-------------|
| 218 | **Device Mismatch Risk** | `torch.tensor([4], device=x.device)` creates new tensor every forward pass - should be registered as buffer |

### Potential Bugs

| Line | Issue | Description |
|------|-------|-------------|
| 54-66 | **O(n) Lookup** | `build_action_decomposition_table()` is O(n*m) - could be optimized but runs once at module load |
| 70 | **Global State** | `ACTION_TYPE_TABLE, ACTION_SUB_TABLE = build_action_decomposition_table()` runs at import - any errors here crash entire module |
| 248-259 | **Mask Logic** | `valid_mask` is computed from type_lut but type_lut is a buffer - could have device issues |

### Code Quality

| Line | Issue | Description |
|------|-------|-------------|
| 26 | **Magic Number** | `NUM_ACTIONS = 16384` - should match engine constant (comment says it does) |
| 98 | **super() Style** | `super(AlphaNet, self).__init__()` - outdated, use `super().__init__()` |
| 119 | **Buffer Registration** | `register_buffer('card_zone_ids', ...)` - good practice |
| 184-269 | **Forward Pass Length** | 80+ lines in forward - could be broken into sub-methods |

### Style & Best Practices

| Line | Issue | Description |
|------|-------|-------------|
| 10-51 | **Constants Block** | Action constants should be in separate file or enum |
| 273-280 | **Duplicate Functions** | `save_model` and `load_model` - consider class methods or torch.save/load directly |

---

## 3. [`alphazero/train.py`](alphazero/train.py) - Nitpicks

### Critical Issues

| Line | Issue | Description |
|------|-------|-------------|
| 58 | **AttributeError Bug** | `model.policy_head` doesn't exist in AlphaNet! Should be `model.policy_type_head` or combined head. This will crash at runtime. |
| 125 | **Same Bug** | `model.policy_head` also used in `run_training()` |

### Potential Bugs

| Line | Issue | Description |
|------|-------|-------------|
| 8 | **Import Path** | `from alphanet import AlphaNet` - relative import should be `from .alphanet` or `from alphazero.alphanet` |
| 83 | **Type Check** | `isinstance(l1_loss, torch.Tensor)` check is fragile - could be 0-value tensor |

### Code Quality

| Line | Issue | Description |
|------|-------|-------------|
| 31 | **Unused Parameter** | `l1_lambda` parameter in `train_epoch()` defined but L1 loss is calculated (line 57-60) - entropy_lambda also defined but entropy term is handled differently |
| 55-60 | **L1 Calculation** | L1 sparsity targeting `policy_head` which doesn't exist - will crash |
| 65-67 | **Entropy Sign** | `entropy_loss = -entropy` then added with `entropy_lambda * entropy_loss` - double negative increases entropy (encourages exploration). Different sign from overnight_pure_zero.py! |
| 98 | **Debug Flag** | `torch.autograd.set_detect_anomaly(True)` - should be conditional debug flag |

### Style & Best Practices

| Line | Issue | Description |
|------|-------|-------------|
| 1-9 | **Import Order** | Standard library, third-party, local imports not grouped |
| 69 | **Loss Components** | Loss calculation mixes MSE, KL, L1, and negative entropy - complex, consider separating into distinct terms with clearer names |

---

## 4. [`engine/game/deck_utils.py`](engine/game/deck_utils.py) - Nitpicks

### Critical Issues

| Line | Issue | Description |
|------|-------|-------------|
| 101 | **Regex DoS Risk** | `re.findall` with complex pattern on untrusted input could cause ReDoS |

### Potential Bugs

| Line | Issue | Description |
|------|-------|-------------|
| 30-31 | **Mutation Risk** | `v_with_type = v.copy()` creates shallow copy - nested dicts still shared |
| 54-56 | **O(n) Search** | Linear search for internal ID - could be O(1) with pre-built index |
| 74 | **Regex Edge Case** | `re.split` with capture group includes separators in result - indexing assumes specific structure |

### Code Quality

| Line | Issue | Description |
|------|-------|-------------|
| 18 | **Optional Type** | `card_db: Optional[Dict] = None` - should use `Dict[str, Any]` for nested structure |
| 93 | **Naming** | `_parse_single_deck` returns dict with `errors` key but errors list is always empty (line 97, 161) |

### Style & Best Practices

| Line | Issue | Description |
|------|-------|-------------|
| 118 | **Complex Regex** | Long regex pattern hard to read - consider breaking into composed patterns |
| 165-174 | **Legacy Function** | `extract_deck_data` wrapper function - consider deprecating |

---

## Summary

### Must Fix
1. **train.py line 58, 125**: `model.policy_head` → `model.policy_type_head` or implement combined head
2. **overnight_pure_zero.py line 94**: Guard against empty buffer
3. **overnight_pure_zero.py line 225**: Replace deprecated `np.bool_`

### Should Fix
1. **train.py line 8**: Fix import path
2. **overnight_pure_zero.py**: Consistent entropy sign with train.py
3. **deck_utils.py**: Build index for O(1) card ID lookup

### Nice to Have
1. Add CLI argument parsing for configuration
2. Move imports to proper locations
3. Add type hints throughout
4. Document deck duplication logic (lines 70-76)

---

*Generated by Architect Mode Nitpick Review*
