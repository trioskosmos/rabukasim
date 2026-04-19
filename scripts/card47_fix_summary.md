# Card 47 Fix Summary

## Issue
SELECT_MODE heart_type mapping was incorrect for mode 3 (heart06).

## Root Cause
The heart_type_map.get(ht, 0) was using 0 as a fallback, which meant if the heart type string didn't match the map, it defaulted to 0 (heart01).

## Fix
Changed the fallback from 0 to j (the index in the heart_types list):
```python
heart_type_num = heart_type_map.get(ht, j)  # Use j as fallback to preserve heart index
```

Also fixed the JUMP routing to jump to correct branch start indices:
```python
frames[jump_idx]["value"] = branch_frame_indices[j] - jump_idx
```

## Result
- Before: 598 passed; 95 failed
- After: 599 passed; 94 failed
- Reduced failures by 1

## Test Output
```
test test_suite::qa::batch_card_specific::tests::test_card_47_live_start_third_mode_grants_heart06_only_to_selected_self_member ... ok
```
