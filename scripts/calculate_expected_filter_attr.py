#!/usr/bin/env python3

# Calculate the expected filter_attr for SELECT_MEMBER with:
# target_player: 1 (SELF)
# group_enabled: True
# group_id: 0 (μ's)

# Bit layout from generated_layout.rs:
# Bits 0-1:   Target Player (1=Self, 2=Opponent)
# Bit 4:      Group Enable flag
# Bits 5-11:  Group ID (7 bits, 0-127)

target_player = 1  # SELF
group_enabled = 1  # True
group_id = 0  # μ's

# Pack the bits
# target_player at bits 0-1
attr = target_player

# group_enabled at bit 4
attr |= (group_enabled << 4)

# group_id at bits 5-11
attr |= (group_id << 5)

print(f"Expected filter_attr for SELECT_MEMBER with target_player={target_player}, group_enabled={group_enabled}, group_id={group_id}:")
print(f"  Hex: 0x{attr:X}")
print(f"  Decimal: {attr}")
print(f"  Binary: {bin(attr)}")

# Decode to verify
decoded_target_player = attr & 0x3
decoded_group_enabled = (attr >> 4) & 0x1
decoded_group_id = (attr >> 5) & 0x7F

print(f"\nDecoded:")
print(f"  target_player: {decoded_target_player}")
print(f"  group_enabled: {decoded_group_enabled}")
print(f"  group_id: {decoded_group_id}")
