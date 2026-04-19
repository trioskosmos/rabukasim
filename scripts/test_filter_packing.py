#!/usr/bin/env python3
"""Test filter packing by manually calculating expected filter_attr"""

# According to generated_layout.rs:
# A_STANDARD_TARGET_PLAYER_SHIFT: 0
# A_STANDARD_CARD_TYPE_SHIFT: 2
# A_STANDARD_GROUP_ENABLED_SHIFT: 4
# A_STANDARD_GROUP_ID_SHIFT: 5
# A_STANDARD_UNIT_ENABLED_SHIFT: 16
# A_STANDARD_UNIT_ID_SHIFT: 17

# Expected filter for: target_player=1 (SELF), card_type=0, group_enabled=1, group_id=0
target_player = 1  # SELF
card_type = 0
group_enabled = 1
group_id = 0

attr = target_player
attr |= (card_type << 2)
if group_enabled:
    attr |= (1 << 4)
    attr |= (group_id << 5)

print(f"Expected filter_attr: 0x{attr:x} (decimal: {attr})")
print(f"Binary: {bin(attr)}")
print(f"Bit 4 (group_enabled): {(attr >> 4) & 1}")
print(f"Bit 16 (unit_enabled): {(attr >> 16) & 1}")

# Actual from debug output
actual_attr = 0x401000001
print(f"\nActual filter_attr: 0x{actual_attr:x} (decimal: {actual_attr})")
print(f"Binary: {bin(actual_attr)}")
print(f"Bit 4 (group_enabled): {(actual_attr >> 4) & 1}")
print(f"Bit 16 (unit_enabled): {(actual_attr >> 16) & 1}")
