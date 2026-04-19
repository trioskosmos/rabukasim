# Decode filter_attr 0x401000001
filter_attr = 0x401000001
print(f"filter_attr = {filter_attr} (0x{filter_attr:x})")
print(f"Binary: {bin(filter_attr)}")

# Based on generated_layout.rs:
# target_player: bits 0-1
# card_type: bits 2-3
# group_enabled: bit 4
# group_id: bits 5-11
# is_tapped: bit 12
# has_blade_heart: bit 13
# not_has_blade_heart: bit 14
# unique_names: bit 15
# unit_enabled: bit 16
# unit_id: bits 17-23
# value_enabled: bit 24
# value_threshold: bits 25-31

target_player = filter_attr & 0x3
card_type = (filter_attr >> 2) & 0x3
group_enabled = (filter_attr >> 4) & 0x1
group_id = (filter_attr >> 5) & 0x7F
is_tapped = (filter_attr >> 12) & 0x1
has_blade_heart = (filter_attr >> 13) & 0x1
not_has_blade_heart = (filter_attr >> 14) & 0x1
unique_names = (filter_attr >> 15) & 0x1
unit_enabled = (filter_attr >> 16) & 0x1
unit_id = (filter_attr >> 17) & 0x7F
value_enabled = (filter_attr >> 24) & 0x1
value_threshold = (filter_attr >> 25) & 0x7F

print(f"\nDecoded fields:")
print(f"target_player: {target_player}")
print(f"card_type: {card_type}")
print(f"group_enabled: {group_enabled}")
print(f"group_id: {group_id}")
print(f"is_tapped: {is_tapped}")
print(f"has_blade_heart: {has_blade_heart}")
print(f"not_has_blade_heart: {not_has_blade_heart}")
print(f"unique_names: {unique_names}")
print(f"unit_enabled: {unit_enabled}")
print(f"unit_id: {unit_id}")
print(f"value_enabled: {value_enabled}")
print(f"value_threshold: {value_threshold}")
