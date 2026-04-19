#!/usr/bin/env python3
"""Check filter constants to understand filter_attr"""

# From the debug output: filter_attr=0x401000001
filter_attr = 0x401000001

print(f"filter_attr: 0x{filter_attr:x} = {filter_attr}")
print(f"Binary: {bin(filter_attr)}")
print()

# Check if this includes passthrough bits
# Looking at the bit layout from filter.rs:
# Bit 0-1: Target Player
# Bit 2-3: Card Type  
# Bit 4: Group Enable
# Bits 5-11: Group ID
# Bit 12: is_tapped
# Bit 13: has_blade_heart
# Bit 14: not_has_blade_heart
# Bit 15: unique_names
# Bit 16: Unit Enable
# Bits 17-23: Unit ID
# Bit 24: Value Enable
# Bits 25-29: Value Threshold
# Bit 30: Cost Mode
# Bit 31: Cost Type
# Bits 32-38: Color Mask
# Bits 39-45: Character ID #1
# Bits 46-52: Character ID #2
# Bits 53-55: Zone Mask
# Bits 56-58: Special ID
# Bit 59: Setsuna flag
# Bit 60: Compare Accumulated
# Bit 61: Optional flag
# Bit 62: Keyword Energy
# Bit 63: Keyword Member

# Extract individual bits
print(f"Bit 0-1 (target_player): {(filter_attr >> 0) & 0x3}")
print(f"Bit 2-3 (card_type): {(filter_attr >> 2) & 0x3}")
print(f"Bit 4 (group_enabled): {(filter_attr >> 4) & 0x1}")
print(f"Bits 5-11 (group_id): {(filter_attr >> 5) & 0x7f}")
print(f"Bit 12 (is_tapped): {(filter_attr >> 12) & 0x1}")
print(f"Bit 13 (has_blade_heart): {(filter_attr >> 13) & 0x1}")
print(f"Bit 14 (not_has_blade_heart): {(filter_attr >> 14) & 0x1}")
print(f"Bit 15 (unique_names): {(filter_attr >> 15) & 0x1}")
print(f"Bit 16 (unit_enabled): {(filter_attr >> 16) & 0x1}")
print(f"Bits 17-23 (unit_id): {(filter_attr >> 17) & 0x7f}")
print(f"Bit 24 (value_enabled): {(filter_attr >> 24) & 0x1}")
print(f"Bits 25-29 (value_threshold): {(filter_attr >> 25) & 0x1f}")
print(f"Bit 30 (is_le): {(filter_attr >> 30) & 0x1}")
print(f"Bit 31 (is_cost_type): {(filter_attr >> 31) & 0x1}")
print(f"Bits 32-38 (color_mask): {(filter_attr >> 32) & 0x7f}")
print(f"Bit 60 (compare_accumulated): {(filter_attr >> 60) & 0x1}")
print(f"Bit 61 (is_optional): {(filter_attr >> 61) & 0x1}")
print(f"Bit 62 (keyword_energy): {(filter_attr >> 62) & 0x1}")
print(f"Bit 63 (keyword_member): {(filter_attr >> 63) & 0x1}")
