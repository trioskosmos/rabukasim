"""Translate ability frames to semantic human-readable format.

Converts low-level frame data (opcodes, jumps, attrs) into natural language
semantic descriptions like "if heart_04>=2 add 2 blades".
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# Load opcode dictionary for reference
def load_opcode_dictionary(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# Opcode to semantic mappings
CONDITION_SEMANTICS = {
    "COUNT_STAGE": "count(stage)",
    "COUNT_ENERGY": "count(energy)",
    "COUNT_HAND": "count(hand)",
    "COUNT_DISCARD": "count(discard)",
    "COUNT_HEARTS": "count(hearts)",
    "COUNT_LIVE_HEARTS": "count(live_hearts)",
    "COUNT_BLADES": "count(blades)",
    "HAS_MEMBER": "has_member",
    "HAS_KEYWORD": "has_keyword",
    "TYPE_CHECK": "type_check",
    "SCORE_COMPARE": "score_compare",
    "AREA_CHECK": "area_check",
}

EFFECT_SEMANTICS = {
    "DRAW": "draw",
    "MOVE_TO_DISCARD": "discard",
    "ADD_HEARTS": "add_hearts",
    "ADD_BLADES": "add_blades",
    "BOOST_SCORE": "boost_score",
    "ACTIVATE_MEMBER": "activate_member",
    "ACTIVATE_ENERGY": "activate_energy",
    "SELECT_MEMBER": "select_member",
    "SELECT_CARDS": "select_cards",
    "PLAY_MEMBER_FROM_HAND": "play_member",
    "LOOK_AND_CHOOSE": "look_and_choose",
    "PAY_ENERGY": "pay_energy",
    "SET_TAPPED": "tap",
}

COMPARISON_SEMANTICS = {
    "GE": ">=",
    "GT": ">",
    "LE": "<=",
    "LT": "<",
    "EQ": "==",
    "NE": "!=",
}

HEART_TYPE_NAMES = {
    0: "heart_01",
    1: "heart_02",
    2: "heart_03",
    3: "heart_04",
    4: "heart_05",
    5: "heart_06",
}


def format_condition(frame: Dict[str, Any]) -> Optional[str]:
    """Format a condition frame into semantic string."""
    op = frame.get("op", "")
    value = frame.get("value")
    slot = frame.get("slot", {})
    attr = frame.get("attr", {})
    params = frame.get("params", {})

    if op in CONDITION_SEMANTICS:
        base = CONDITION_SEMANTICS[op]
        
        # Special handling for heart types - make more semantic
        if op == "COUNT_LIVE_HEARTS":
            color_mask = attr.get("color_mask", "")
            comparison = slot.get("comparison", "GE")
            comp_symbol = COMPARISON_SEMANTICS.get(comparison, ">=")
            
            if color_mask == "GREEN":
                return f"heart_04 {comp_symbol} {value}"
            elif color_mask == "RED":
                return f"heart_01 {comp_symbol} {value}"
            elif color_mask == "BLUE":
                return f"heart_02 {comp_symbol} {value}"
            elif color_mask == "YELLOW":
                return f"heart_03 {comp_symbol} {value}"
            elif color_mask:
                return f"{color_mask.lower()}_hearts {comp_symbol} {value}"
            return f"live_hearts {comp_symbol} {value}"
        
        # HAS_KEYWORD with character
        if op == "HAS_KEYWORD":
            char = attr.get("char_id_1", "")
            if char:
                return f"has_character({char})"
            return "has_keyword"
        
        # COUNT_STAGE
        if op == "COUNT_STAGE":
            comparison = slot.get("comparison", "GE")
            comp_symbol = COMPARISON_SEMANTICS.get(comparison, ">=")
            return f"stage_members {comp_symbol} {value}"
        
        # COUNT_ENERGY
        if op == "COUNT_ENERGY":
            comparison = slot.get("comparison", "GE")
            comp_symbol = COMPARISON_SEMANTICS.get(comparison, ">=")
            return f"energy {comp_symbol} {value}"
        
        # COUNT_HAND
        if op == "COUNT_HAND":
            comparison = slot.get("comparison", "GE")
            comp_symbol = COMPARISON_SEMANTICS.get(comparison, ">=")
            return f"hand {comp_symbol} {value}"
        
        # COUNT_BLADES
        if op == "COUNT_BLADES":
            comparison = slot.get("comparison", "GE")
            comp_symbol = COMPARISON_SEMANTICS.get(comparison, ">=")
            return f"blades {comp_symbol} {value}"
        
        # Add comparison and value for generic cases
        comparison = slot.get("comparison", "")
        if comparison and value is not None:
            comp_symbol = COMPARISON_SEMANTICS.get(comparison, comparison)
            return f"{base} {comp_symbol} {value}"
        
        return f"{base} >= {value}" if value else base
    
    return None


def format_effect(frame: Dict[str, Any]) -> Optional[str]:
    """Format an effect frame into semantic string."""
    op = frame.get("op", "")
    value = frame.get("value")
    slot = frame.get("slot", {})
    attr = frame.get("attr", {})
    params = frame.get("params", {})

    if op in EFFECT_SEMANTICS:
        base = EFFECT_SEMANTICS[op]
        
        # ADD_HEARTS with heart_type
        if op == "ADD_HEARTS":
            heart_type = params.get("heart_type")
            if heart_type is not None:
                heart_name = HEART_TYPE_NAMES.get(heart_type, f"heart_type_{heart_type}")
                return f"add {heart_name}"
            return f"add {value} hearts" if value else "add hearts"
        
        # ADD_BLADES - make it match user's desired format "add 2 blades"
        if op == "ADD_BLADES":
            duration = attr.get("duration", "")
            if duration:
                return f"add {value} blades (until {duration})"
            return f"add {value} blades"
        
        # BOOST_SCORE
        if op == "BOOST_SCORE":
            return f"boost score {value}" if value else "boost score"
        
        # DRAW
        if op == "DRAW":
            if attr.get("compare_accumulated"):
                return "draw (equal to previous count)"
            return f"draw {value}" if value else "draw"
        
        # MOVE_TO_DISCARD
        if op == "MOVE_TO_DISCARD":
            source = slot.get("source_zone", "")
            if source:
                return f"discard {value} from {source.lower()}"
            return f"discard {value}" if value else "discard"
        
        # ACTIVATE_MEMBER
        if op == "ACTIVATE_MEMBER":
            return f"activate {value} members" if value else "activate member"
        
        # ACTIVATE_ENERGY
        if op == "ACTIVATE_ENERGY":
            return f"activate {value} energy" if value else "activate energy"
        
        # PAY_ENERGY
        if op == "PAY_ENERGY":
            optional = attr.get("is_optional") == 1
            opt_str = "optional " if optional else ""
            return f"{opt_str}pay {value} energy" if value else f"{opt_str}pay energy"
        
        # SELECT operations
        if op.startswith("SELECT"):
            target = slot.get("target_slot", "")
            source = slot.get("source_zone", "")
            if source:
                return f"select {value} from {source.lower()}" if value else f"select from {source.lower()}"
            return f"select {value}" if value else "select"
        
        # PLAY_MEMBER_FROM_HAND
        if op == "PLAY_MEMBER_FROM_HAND":
            return f"play {value} member" if value == 1 else f"play {value} members" if value else "play member"
        
        # LOOK_AND_CHOOSE
        if op == "LOOK_AND_CHOOSE":
            if isinstance(value, dict):
                count = value.get("count", 0)
                reveal = value.get("reveal", 0)
                return f"look {count}, choose {reveal}"
            return f"look {value}" if value else "look"
        
        return f"{base} {value}" if value else base
    
    return None


def translate_frames_to_semantic(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Translate a list of frames to semantic representation."""
    if not frames:
        return {"semantic": [], "summary": "No frames"}
    
    semantic_blocks = []
    i = 0
    n = len(frames)
    
    while i < n:
        frame = frames[i]
        op = frame.get("op", "")
        
        # Handle conditional pattern: CONDITION -> JUMP_IF_FALSE -> EFFECT
        if op in CONDITION_SEMANTICS:
            condition = format_condition(frame)
            if condition and i + 1 < n:
                next_frame = frames[i + 1]
                if next_frame.get("op") == "JUMP_IF_FALSE":
                    jump_offset = next_frame.get("value", 1)
                    # Look for effect after jump
                    effect_idx = i + 2
                    if effect_idx < n:
                        effect_frame = frames[effect_idx]
                        effect = format_effect(effect_frame)
                        if effect:
                            optional = frame.get("attr", {}).get("is_optional") == 1
                            opt_str = "optional " if optional else ""
                            semantic_blocks.append({
                                "type": "conditional",
                                "condition": condition,
                                "effect": effect,
                                "optional": optional,
                                "semantic": f"if {condition}, {opt_str}{effect}"
                            })
                            i = effect_idx + 1
                            continue
        
        # Handle optional pattern: OP(optional) -> JUMP_IF_FALSE
        if frame.get("attr", {}).get("is_optional") == 1:
            effect = format_effect(frame)
            if effect and i + 1 < n and frames[i + 1].get("op") == "JUMP_IF_FALSE":
                semantic_blocks.append({
                    "type": "optional",
                    "effect": effect,
                    "semantic": f"optional: {effect}"
                })
                i += 2
                continue
        
        # Handle simple effect
        effect = format_effect(frame)
        if effect:
            semantic_blocks.append({
                "type": "effect",
                "effect": effect,
                "semantic": effect
            })
        elif op == "RETURN":
            semantic_blocks.append({
                "type": "return",
                "semantic": "end"
            })
        else:
            semantic_blocks.append({
                "type": "unknown",
                "op": op,
                "semantic": f"[{op}]"
            })
        
        i += 1
    
    # Build readable description
    description_parts = []
    for block in semantic_blocks:
        if block.get("type") == "conditional":
            desc = block["semantic"]
        elif block.get("type") == "optional":
            desc = block["semantic"]
        elif block.get("type") == "effect":
            desc = block["semantic"]
        elif block.get("type") == "return":
            continue  # Skip return in description
        else:
            desc = block.get("semantic", "")
        
        if desc:
            description_parts.append(desc)
    
    return {
        "blocks": semantic_blocks,
        "description": "; ".join(description_parts),
        "frame_count": len(frames)
    }


def process_ability(ability: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single ability entry."""
    frames = ability.get("frames", [])
    semantic = translate_frames_to_semantic(frames)
    
    return {
        "ability_index": ability.get("ability_index", 0),
        "trigger": ability.get("trigger", ""),
        "primary_text_jp": ability.get("primary_text_jp", ""),
        "frames": frames,
        "semantic": semantic,
        "card_refs": ability.get("card_refs", [])
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Translate ability frames to semantic format")
    parser.add_argument("--input", default="data/ability_frame_source.json", help="Input frame source file")
    parser.add_argument("--output", default="data/ability_semantic_frames.json", help="Output semantic file")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load input
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    abilities = data.get("abilities", [])
    
    # Process all abilities
    semantic_abilities = []
    for ability in abilities:
        semantic_ability = process_ability(ability)
        semantic_abilities.append(semantic_ability)
    
    # Build output
    output = {
        "schema": "ability_semantic_frames.v1",
        "source": str(input_path),
        "count": len(semantic_abilities),
        "abilities": semantic_abilities
    }
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Translated {len(semantic_abilities)} abilities to semantic format")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    main()
