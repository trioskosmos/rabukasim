
import os

path = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine\models\ability.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# I need to find the block for MOVE_TO_DISCARD and fix it.
# The corrupted part looks like this:
# 1434:                 src_zone_str = str(eff.params.get("source") or eff.params.get("from") or eff.params.get("zone") or "DECK").upper()
# 1435:                 if "," not in src_zone_str:
# 1436: 
# 1437:                 rem_val = eff.params.get("remainder_zone", 0)

# Also I need to ensure the MOVE_TO_DISCARD block is present and correct.

# Actually, I'll just replace the whole section starting from where it went wrong.

start_marker = '                EffectType.RECOVER_MEMBER,\n            ):'
end_marker = '            if eff.effect_type == EffectType.PLACE_UNDER:'

# Let's find the start.
start_index = content.find(start_marker)
if start_index == -1:
    print("Could not find start_marker")
    exit(1)

# Find the end of the block (before PLACE_UNDER)
end_index = content.find(end_marker)
if end_index == -1:
    print("Could not find end_marker")
    exit(1)

# The new content for this middle section
new_middle = '''                EffectType.RECOVER_MEMBER,
            ):
                attr = self._pack_filter_attr(eff)
                src_zone_str = str(eff.params.get("source") or eff.params.get("from") or eff.params.get("zone") or "DECK").upper()
                if "," not in src_zone_str:
                    if src_zone_str == "HAND":
                        src_val = ZONES.get("HAND", 6)
                    elif src_zone_str == "DISCARD":
                        src_val = ZONES.get("DISCARD", 7)
                    elif src_zone_str in ("YELL", "REVEALED", "CHEER"):
                        src_val = ZONES.get("YELL", 15)
                    elif src_zone_str in ("STAGE", "TARGET_STAGE"):
                        src_val = ZONES.get("STAGE", 4)
                    elif (
                        src_zone_str == "DECK"
                        and eff.effect_type in (EffectType.SELECT_MEMBER, EffectType.MOVE_TO_DISCARD)
                    ):
                        src_val = ZONES.get("STAGE", 4)
                    else:
                        src_val = ZONES.get("DECK_TOP", 1)
                    slot_params["source_zone"] = src_val

                rem_val = eff.params.get("remainder_zone", 0)
                if not rem_val and eff.params.get("raw_val") == "REMAINDER":
                    rem_val = "DISCARD"
                    slot_params["target_slot"] = 0
                if isinstance(rem_val, str):
                    rem_map = {
                        "DISCARD": ZONES.get("DISCARD", 7),
                        "DECK": ZONES.get("DECK_TOP", 1),
                        "HAND": ZONES.get("HAND", 6),
                        "DECK_TOP": EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1),
                        "DECK_BOTTOM": EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2),
                    }
                    rem_val = rem_map.get(rem_val.upper(), 0)
                slot_params["remainder_zone"] = rem_val

            if eff.effect_type == EffectType.MOVE_MEMBER and attr != 99:
                attr = self._pack_filter_attr(eff)
                src_zone_str = str(eff.params.get("source") or eff.params.get("from") or eff.params.get("zone") or "DECK").upper()
                if "," not in src_zone_str:
                    if src_zone_str == "HAND":
                        src_val = ZONES.get("HAND", 6)
                    elif src_zone_str == "DISCARD":
                        src_val = ZONES.get("DISCARD", 7)
                    elif src_zone_str in ("YELL", "REVEALED", "CHEER"):
                        src_val = ZONES.get("YELL", 15)
                    elif src_zone_str in ("STAGE", "TARGET_STAGE"):
                        src_val = ZONES.get("STAGE", 4)
                    else:
                        src_val = ZONES.get("DECK_TOP", 1)
                    slot_params["source_zone"] = src_val

                rem_val = eff.params.get("remainder_zone", 0)
                if not rem_val and eff.params.get("raw_val") == "REMAINDER":
                    rem_val = "DISCARD"
                    slot_params["target_slot"] = 0
                if isinstance(rem_val, str):
                    rem_map = {
                        "DISCARD": ZONES.get("DISCARD", 7),
                        "DECK": ZONES.get("DECK_TOP", 1),
                        "HAND": ZONES.get("HAND", 6),
                        "DECK_TOP": EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1),
                        "DECK_BOTTOM": EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2),
                    }
                    rem_val = rem_map.get(rem_val.upper(), 0)
                slot_params["remainder_zone"] = rem_val

            if eff.effect_type == EffectType.MOVE_TO_DISCARD:
                # REMAINDER handling for LOOK_AND_CHOOSE_ORDER
                if not rem_val and eff.params.get("raw_val") == "REMAINDER":
                    rem_val = "DISCARD"
                    slot_params["target_slot"] = 0
                
                src_val = eff.params.get("source", "stage").upper()
                if src_val == "HAND":
                    src_val = ZONES.get("HAND", 6)
                elif src_val == "DISCARD":
                    src_val = ZONES.get("DISCARD", 7)
                elif any(k in src_val for k in ["DECK", "LOOKED"]):
                    src_val = ZONES.get("DECK_TOP", 1)
                else:
                    src_val = ZONES.get("STAGE", 4)
                slot_params["source_zone"] = src_val

                if isinstance(rem_val, str):
                    rem_map = {
                        "DISCARD": ZONES.get("DISCARD", 7),
                        "DECK_TOP": ZONES.get("DECK_TOP", 1),
                        "DECK_BOTTOM": ZONES.get("DECK_BOTTOM", 2),
                        "HAND": ZONES.get("HAND", 6),
                    }
                    slot_params["remainder_zone"] = rem_map.get(rem_val.upper(), 0)
                
                slot_params["dest_zone"] = ZONES.get("DISCARD", 7)

            '''

new_content = content[:start_index] + new_middle + content[end_index:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Updated successfully")
