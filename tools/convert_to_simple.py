"""Convert ability frames to simple readable format and back.

Simple format: Japanese text + logic string like "if heart_04>=4 add heart_04"
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def frames_to_simple(frames: List[Dict[str, Any]]) -> str:
    """Convert frames to simple logic string."""
    if not frames:
        return ""
    
    logic_parts = []
    i = 0
    n = len(frames)
    
    while i < n:
        frame = frames[i]
        op = frame.get("op", "")
        
        # Handle conditional: CONDITION -> JUMP_IF_FALSE -> EFFECT
        if op in ["COUNT_LIVE_HEARTS", "COUNT_HEARTS", "COUNT_BLADES", "COUNT_STAGE", "COUNT_ENERGY", "COUNT_HAND"]:
            condition = format_condition_simple(frame)
            if condition and i + 1 < n and frames[i + 1].get("op") == "JUMP_IF_FALSE":
                # Look for effect after jump
                effect_idx = i + 2
                if effect_idx < n:
                    effect_frame = frames[effect_idx]
                    effect = format_effect_simple(effect_frame)
                    if effect:
                        logic_parts.append(f"if {condition} then {effect}")
                        i = effect_idx + 1
                        continue
        
        # Handle optional: OP(optional) -> JUMP_IF_FALSE
        if frame.get("attr", {}).get("is_optional") == 1:
            effect = format_effect_simple(frame)
            if effect and i + 1 < n and frames[i + 1].get("op") == "JUMP_IF_FALSE":
                logic_parts.append(f"optional: {effect}")
                i += 2
                continue
        
        # Handle simple effect
        effect = format_effect_simple(frame)
        if effect and op != "RETURN":
            logic_parts.append(effect)
        
        i += 1
    
    return " -> ".join(logic_parts) if logic_parts else ""


def format_condition_simple(frame: Dict[str, Any]) -> Optional[str]:
    """Format condition frame to simple string."""
    op = frame.get("op", "")
    value = frame.get("value")
    slot = frame.get("slot", {})
    attr = frame.get("attr", {})
    
    # Heart conditions
    if op == "COUNT_LIVE_HEARTS":
        color = attr.get("color_mask", "")
        comp = slot.get("comparison", "GE")
        comp_sym = {">=": ">=", "GT": ">", "LE": "<=", "LT": "<", "EQ": "==", "NE": "!="}.get(comp, ">=")
        
        if color == "GREEN":
            return f"heart_04{comp_sym}{value}"
        elif color == "RED":
            return f"heart_01{comp_sym}{value}"
        elif color == "BLUE":
            return f"heart_02{comp_sym}{value}"
        elif color == "YELLOW":
            return f"heart_03{comp_sym}{value}"
        return f"hearts{comp_sym}{value}"
    
    # Blade conditions
    if op == "COUNT_BLADES":
        comp = slot.get("comparison", "GE")
        comp_sym = {">=": ">=", "GT": ">", "LE": "<=", "LT": "<", "EQ": "==", "NE": "!="}.get(comp, ">=")
        return f"blades{comp_sym}{value}"
    
    # Stage member conditions
    if op == "COUNT_STAGE":
        comp = slot.get("comparison", "GE")
        comp_sym = {">=": ">=", "GT": ">", "LE": "<=", "LT": "<", "EQ": "==", "NE": "!="}.get(comp, ">=")
        return f"stage{comp_sym}{value}"
    
    # Energy conditions
    if op == "COUNT_ENERGY":
        comp = slot.get("comparison", "GE")
        comp_sym = {">=": ">=", "GT": ">", "LE": "<=", "LT": "<", "EQ": "==", "NE": "!="}.get(comp, ">=")
        return f"energy{comp_sym}{value}"
    
    # Hand conditions
    if op == "COUNT_HAND":
        comp = slot.get("comparison", "GE")
        comp_sym = {">=": ">=", "GT": ">", "LE": "<=", "LT": "<", "EQ": "==", "NE": "!="}.get(comp, ">=")
        return f"hand{comp_sym}{value}"
    
    return None


def format_effect_simple(frame: Dict[str, Any]) -> Optional[str]:
    """Format effect frame to simple string."""
    op = frame.get("op", "")
    value = frame.get("value")
    attr = frame.get("attr", {})
    params = frame.get("params", {})
    
    # ADD_HEARTS
    if op == "ADD_HEARTS":
        heart_type = params.get("heart_type")
        if heart_type is not None:
            heart_names = {0: "heart_01", 1: "heart_02", 2: "heart_03", 3: "heart_04", 4: "heart_05", 5: "heart_06"}
            heart_name = heart_names.get(heart_type, f"heart_type_{heart_type}")
            return f"add {heart_name}"
        return f"add {value} hearts" if value else "add hearts"
    
    # ADD_BLADES
    if op == "ADD_BLADES":
        return f"add {value} blades"
    
    # DRAW
    if op == "DRAW":
        if attr.get("compare_accumulated"):
            return "draw equal to previous"
        return f"draw {value}" if value else "draw"
    
    # MOVE_TO_DISCARD
    if op == "MOVE_TO_DISCARD":
        source = frame.get("slot", {}).get("source_zone", "")
        if source:
            return f"discard {value} from {source.lower()}"
        return f"discard {value}" if value else "discard"
    
    # PAY_ENERGY
    if op == "PAY_ENERGY":
        return f"pay {value} energy"
    
    # SELECT_MEMBER / PLAY_MEMBER
    if op in ["SELECT_MEMBER", "PLAY_MEMBER_FROM_HAND"]:
        return f"play member"
    
    # LOOK_AND_CHOOSE
    if op == "LOOK_AND_CHOOSE":
        if isinstance(value, dict):
            look = value.get("count", 0)
            choose = value.get("reveal", 0)
            return f"look {look} choose {choose}"
        return f"look {value}"
    
    # ACTIVATE_MEMBER
    if op == "ACTIVATE_MEMBER":
        return f"activate {value} members" if value else "activate member"
    
    # ACTIVATE_ENERGY
    if op == "ACTIVATE_ENERGY":
        return f"activate {value} energy" if value else "activate energy"
    
    # BOOST_SCORE
    if op == "BOOST_SCORE":
        return f"boost score {value}"
    
    return None


def simple_to_frames(simple_ability: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert simple ability format back to frames (reverse conversion)."""
    # In v3 format, frames are preserved completely - just extract them
    return simple_ability.get("frames", [])


def simple_from_frames(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert frames to simple ability format (reverse of above)."""
    complete_frames = [extract_complete_frame_info(frame) for frame in frames]
    readable_frames = [format_frame_readable(frame) for frame in complete_frames]
    readable_summary = " -> ".join(readable_frames)
    
    return {
        "frames": complete_frames,
        "readable": readable_summary
    }


def parse_condition(condition: str, frame_index: int) -> Optional[Dict[str, Any]]:
    """Parse condition string like 'heart_04>=4' to frame."""
    # Heart conditions
    if "heart_01" in condition:
        return {
            "op": "COUNT_LIVE_HEARTS",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "attr": {"color_mask": "RED"},
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "heart_02" in condition:
        return {
            "op": "COUNT_LIVE_HEARTS",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "attr": {"color_mask": "BLUE"},
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "heart_03" in condition:
        return {
            "op": "COUNT_LIVE_HEARTS",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "attr": {"color_mask": "YELLOW"},
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "heart_04" in condition:
        return {
            "op": "COUNT_LIVE_HEARTS",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "attr": {"color_mask": "GREEN"},
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "heart_05" in condition:
        return {
            "op": "COUNT_LIVE_HEARTS",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "attr": {"color_mask": "PURPLE"},
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "heart_06" in condition:
        return {
            "op": "COUNT_LIVE_HEARTS",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "attr": {"color_mask": "WHITE"},
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "blades" in condition:
        return {
            "op": "COUNT_BLADES",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "stage" in condition:
        return {
            "op": "COUNT_STAGE",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "energy" in condition:
        return {
            "op": "COUNT_ENERGY",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    elif "hand" in condition:
        return {
            "op": "COUNT_HAND",
            "frame_index": frame_index,
            "value": extract_number(condition),
            "slot": {"target_slot": "STAGE_0", "comparison": extract_operator(condition)}
        }
    
    return None


def parse_effect(effect: str, frame_index: int) -> List[Dict[str, Any]]:
    """Parse effect string like 'add heart_04' or 'draw 2' to frame(s)."""
    frames = []
    
    # ADD_HEARTS
    if "add heart_01" in effect:
        frames.append({
            "op": "ADD_HEARTS",
            "frame_index": frame_index,
            "value": 1,
            "slot": {"target_slot": "CONTEXT"},
            "params": {"heart_type": 0}
        })
    elif "add heart_02" in effect:
        frames.append({
            "op": "ADD_HEARTS",
            "frame_index": frame_index,
            "value": 1,
            "slot": {"target_slot": "CONTEXT"},
            "params": {"heart_type": 1}
        })
    elif "add heart_03" in effect:
        frames.append({
            "op": "ADD_HEARTS",
            "frame_index": frame_index,
            "value": 1,
            "slot": {"target_slot": "CONTEXT"},
            "params": {"heart_type": 2}
        })
    elif "add heart_04" in effect:
        frames.append({
            "op": "ADD_HEARTS",
            "frame_index": frame_index,
            "value": 1,
            "slot": {"target_slot": "CONTEXT"},
            "params": {"heart_type": 3}
        })
    elif "add heart_05" in effect:
        frames.append({
            "op": "ADD_HEARTS",
            "frame_index": frame_index,
            "value": 1,
            "slot": {"target_slot": "CONTEXT"},
            "params": {"heart_type": 4}
        })
    elif "add heart_06" in effect:
        frames.append({
            "op": "ADD_HEARTS",
            "frame_index": frame_index,
            "value": 1,
            "slot": {"target_slot": "CONTEXT"},
            "params": {"heart_type": 5}
        })
    # ADD_BLADES
    elif "add " in effect and "blades" in effect:
        count = extract_number(effect)
        frames.append({
            "op": "ADD_BLADES",
            "frame_index": frame_index,
            "value": count if count else 1,
            "slot": {"target_slot": "CONTEXT"}
        })
    # DRAW
    elif "draw" in effect:
        if "equal to previous" in effect:
            frames.append({
                "op": "DRAW",
                "frame_index": frame_index,
                "attr": {"compare_accumulated": 1},
                "slot": {"target_slot": "CONTEXT"}
            })
        else:
            count = extract_number(effect)
            frames.append({
                "op": "DRAW",
                "frame_index": frame_index,
                "value": count if count else 1,
                "slot": {"target_slot": "CONTEXT"}
            })
    # DISCARD
    elif "discard" in effect:
        count = extract_number(effect)
        source = "HAND"
        if "from deck" in effect.lower():
            source = "DECK_TOP"
        elif "from hand" in effect.lower():
            source = "HAND"
        
        frames.append({
            "op": "MOVE_TO_DISCARD",
            "frame_index": frame_index,
            "value": count if count else 1,
            "slot": {"source_zone": source, "dest_zone": "DISCARD"}
        })
    # PAY_ENERGY
    elif "pay" in effect and "energy" in effect:
        count = extract_number(effect)
        frames.append({
            "op": "PAY_ENERGY",
            "frame_index": frame_index,
            "value": count if count else 1,
            "slot": {"target_slot": "CONTEXT"}
        })
    # LOOK_AND_CHOOSE
    elif "look" in effect and "choose" in effect:
        look_count = extract_number(effect.split("choose")[0])
        choose_count = extract_number(effect.split("choose")[1])
        frames.append({
            "op": "LOOK_AND_CHOOSE",
            "frame_index": frame_index,
            "value": {"count": look_count if look_count else 3, "reveal": choose_count if choose_count else 1},
            "slot": {"source_zone": "DECK_TOP", "remainder_zone": "DISCARD"}
        })
    
    return frames


def extract_number(s: str) -> Optional[int]:
    """Extract first number from string."""
    import re
    match = re.search(r'\d+', s)
    return int(match.group()) if match else None


def extract_operator(s: str) -> str:
    """Extract comparison operator from string."""
    if ">=" in s:
        return "GE"
    elif ">" in s:
        return "GT"
    elif "<=" in s:
        return "LE"
    elif "<" in s:
        return "LT"
    elif "==" in s:
        return "EQ"
    elif "!=" in s:
        return "NE"
    return "GE"  # default


def extract_complete_frame_info(frame: Dict[str, Any]) -> Dict[str, Any]:
    """Extract complete frame information including all attributes, slots, params that runtime needs."""
    frame_info = {
        "op": frame.get("op", ""),
        "frame_index": frame.get("frame_index")
    }
    
    # Only include value if it exists and is not None
    if "value" in frame and frame["value"] is not None:
        frame_info["value"] = frame["value"]
    
    # Only include attr/slot/params if they exist in original
    if frame.get("attr"):
        frame_info["attr"] = frame["attr"].copy()
    if frame.get("slot"):
        frame_info["slot"] = frame["slot"].copy()
    if frame.get("params"):
        frame_info["params"] = frame["params"].copy()
    
    return frame_info


def format_frame_readable(frame_info: Dict[str, Any]) -> str:
    """Format complete frame info into readable string for display."""
    op = frame_info.get("op", "")
    value = frame_info.get("value")
    attr = frame_info.get("attr", {})
    slot = frame_info.get("slot", {})
    params = frame_info.get("params", {})
    
    parts = [op]
    
    # Add value
    if value is not None:
        parts.append(f"value={value}")
    
    # Add key attributes
    if attr:
        key_attrs = []
        if attr.get("is_optional"):
            key_attrs.append("optional")
        if attr.get("once_per_turn"):
            key_attrs.append("once_per_turn")
        if attr.get("target_player"):
            key_attrs.append(f"target={attr['target_player']}")
        if attr.get("card_type"):
            key_attrs.append(f"type={attr['card_type']}")
        if attr.get("group_enabled"):
            key_attrs.append(f"group={attr.get('group_id', '?')}")
        if attr.get("unit_enabled"):
            key_attrs.append(f"unit={attr.get('unit_id', '?')}")
        if attr.get("char_id_1"):
            key_attrs.append(f"char={attr['char_id_1']}")
        if key_attrs:
            parts.append(f"[{', '.join(key_attrs)}]")
    
    # Add slot info
    if slot:
        slot_info = []
        if slot.get("target_slot"):
            slot_info.append(f"target={slot['target_slot']}")
        if slot.get("source_zone"):
            slot_info.append(f"from={slot['source_zone']}")
        if slot.get("dest_zone"):
            slot_info.append(f"to={slot['dest_zone']}")
        if slot.get("comparison"):
            slot_info.append(f"cmp={slot['comparison']}")
        if slot_info:
            parts.append(f"({', '.join(slot_info)})")
    
    # Add params
    if params:
        param_info = []
        for key, val in params.items():
            param_info.append(f"{key}={val}")
        if param_info:
            parts.append(f"{{{', '.join(param_info)}}}")
    
    return " ".join(parts)


def merge_filters(all_filters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge filters from multiple frames into a single filter dict."""
    merged = {}
    for filters in all_filters:
        for key, value in filters.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(value, bool) and value:
                merged[key] = True  # Keep true flags
    return merged


def convert_ability_source_to_simple(input_path: Path, output_path: Path):
    """Convert ability_frame_source.json to ability_simple.json preserving complete frame data."""
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    simple_abilities = []
    
    for ability in abilities:
        frames = ability.get("frames", [])
        
        # Extract complete frame info for all frames
        complete_frames = [extract_complete_frame_info(frame) for frame in frames]
        
        # Generate readable summary
        readable_frames = [format_frame_readable(frame) for frame in complete_frames]
        readable_summary = " -> ".join(readable_frames)
        
        # Split Japanese text by trigger markers to detect multi-trigger abilities
        japanese_text = ability.get("primary_text_jp", "")
        trigger_markers = ["{{kidou.png|起動}}", "{{toujyou.png|登場}}", "{{live_start.png|ライブ開始時}}", "{{jidou.png|自動}}", "{{live_success.png|ライブ成功時}}"]
        
        # Check if this is a multi-trigger ability (has multiple trigger markers)
        trigger_count = sum(1 for marker in trigger_markers if marker in japanese_text)
        
        card_refs = ability.get("card_refs", [])
        card_names = [ref.get("card_no", "") for ref in card_refs]
        trigger = ability.get("trigger", "")
        
        simple_abilities.append({
            "japanese_text": japanese_text,
            "trigger": trigger,
            "trigger_count": trigger_count,
            "frames": complete_frames,  # Complete frame data - no information loss
            "readable": readable_summary,  # Human-readable summary
            "cards": card_names,
            "frame_verification": ability.get("frame_verification", {})
        })
    
    output = {
        "schema": "ability_simple.v3",
        "description": "Complete ability format with full frame data preservation. Includes Japanese text, complete frame data (all attributes/slots/params), readable summary, and card references. Convertible to/from frame format with no data loss.",
        "format": {
            "japanese_text": "Original Japanese ability text",
            "trigger": "Trigger type",
            "trigger_count": "Number of triggers (for multi-trigger abilities)",
            "frames": "Complete frame data array with all op, attr, slot, params - no information loss",
            "readable": "Human-readable summary of frames",
            "cards": "List of cards that use this ability",
            "frame_verification": "Original frame verification data"
        },
        "frame_structure": {
            "op": "Operation opcode (required)",
            "frame_index": "Sequential frame index (required)",
            "value": "Integer or object value (optional)",
            "attr": "Object with all attributes (optional)",
            "slot": "Object with all slot information (optional)",
            "params": "Object with all parameters (optional)"
        },
        "abilities": simple_abilities
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(simple_abilities)} abilities to simple format (v3 with complete frame preservation)")
    print(f"Output written to {output_path}")


def test_two_way_conversion():
    """Test two-way conversion on sample abilities with v3 format."""
    # Test with actual frame data
    test_frames = [
        [
            {
                "op": "DRAW",
                "frame_index": 0,
                "value": 1,
                "slot": {"target_slot": "CONTEXT"}
            },
            {
                "op": "MOVE_TO_DISCARD",
                "frame_index": 1,
                "value": 1,
                "attr": {"target_player": "SELF", "zone_mask": "Guest+Friend"},
                "slot": {"target_slot": "STAGE_1", "source_zone": "HAND", "dest_zone": "DISCARD"}
            },
            {
                "op": "RETURN",
                "frame_index": 2
            }
        ],
        [
            {
                "op": "COUNT_LIVE_HEARTS",
                "frame_index": 0,
                "value": 4,
                "attr": {"card_type": "LIVE", "color_mask": "GREEN"},
                "slot": {"target_slot": "STAGE_0", "comparison": "GE"}
            },
            {
                "op": "JUMP_IF_FALSE",
                "frame_index": 1,
                "value": 1
            },
            {
                "op": "ADD_HEARTS",
                "frame_index": 2,
                "value": 1,
                "slot": {"target_slot": "CONTEXT"},
                "params": {"heart_type": 3}
            },
            {
                "op": "RETURN",
                "frame_index": 3
            }
        ]
    ]
    
    print("Testing v3 format round-trip conversion...")
    for i, frames in enumerate(test_frames):
        # Convert frames to simple format
        simple = simple_from_frames(frames)
        
        # Convert back to frames
        back_to_frames = simple_to_frames(simple)
        
        # Check if frames match
        frames_match = frames == back_to_frames
        
        print(f"\nTest case {i + 1}:")
        print(f"  Original frames: {len(frames)}")
        print(f"  Readable: {simple.get('readable', '')[:80]}...")
        print(f"  Round-trip frames match: {frames_match}")
        
        if not frames_match:
            print(f"  Original: {frames}")
            print(f"  Round-trip: {back_to_frames}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert ability frames to simple format")
    parser.add_argument("--input", default="data/ability_frame_source.json", help="Input frame source file")
    parser.add_argument("--output", default="data/ability_simple.json", help="Output simple format file")
    parser.add_argument("--test", action="store_true", help="Run two-way conversion test")
    args = parser.parse_args()
    
    if args.test:
        test_two_way_conversion()
    else:
        convert_ability_source_to_simple(Path(args.input), Path(args.output))


if __name__ == "__main__":
    main()
