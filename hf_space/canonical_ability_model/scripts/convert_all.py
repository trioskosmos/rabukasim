
import json
import re
from pathlib import Path

# Metadata for validation
OPCODES = ["DRAW", "ADD_BLADES", "ADD_HEARTS", "REDUCE_COST", "LOOK_DECK", "RECOVER_LIVE", "BOOST_SCORE", 
            "RECOVER_MEMBER", "BUFF_POWER", "IMMUNITY", "MOVE_MEMBER", "SWAP_CARDS", "SEARCH_DECK", 
            "ENERGY_CHARGE", "SET_BLADES", "SET_HEARTS", "FORMATION_CHANGE", "NEGATE_EFFECT", "ORDER_DECK", 
            "META_RULE", "SELECT_MODE", "MOVE_TO_DECK", "TAP_OPPONENT", "PLACE_UNDER", "FLAVOR_ACTION", 
            "RESTRICTION", "BATON_TOUCH_MOD", "SET_SCORE", "SWAP_ZONE", "TRANSFORM_COLOR", "REVEAL_CARDS", 
            "LOOK_AND_CHOOSE", "CHEER_REVEAL", "ACTIVATE_MEMBER", "ADD_TO_HAND", "COLOR_SELECT", 
            "TRIGGER_REMOTE", "REDUCE_HEART_REQ", "MODIFY_SCORE_RULE", "ADD_STAGE_ENERGY", "SET_TAPPED", 
            "TAP_MEMBER", "PLAY_MEMBER_FROM_HAND", "MOVE_TO_DISCARD", "GRANT_ABILITY", "INCREASE_HEART_COST", 
            "REDUCE_YELL_COUNT", "PLAY_MEMBER_FROM_DISCARD", "PAY_ENERGY", "SELECT_MEMBER", "DRAW_UNTIL", 
            "SELECT_PLAYER", "SELECT_LIVE", "REVEAL_UNTIL", "INCREASE_COST", "PREVENT_PLAY_TO_SLOT", 
            "SWAP_AREA", "TRANSFORM_HEART", "SELECT_CARDS", "OPPONENT_CHOOSE", "PLAY_LIVE_FROM_DISCARD", 
            "REDUCE_LIVE_SET_LIMIT", "SET_TARGET_SELF", "SET_TARGET_OPPONENT", "PREVENT_SET_TO_SUCCESS_PILE", 
            "ACTIVATE_ENERGY", "PREVENT_ACTIVATE", "SET_HEART_COST", "PREVENT_BATON_TOUCH", "LOOK_DECK_DYNAMIC", 
            "REDUCE_SCORE", "REPEAT_ABILITY", "LOSE_EXCESS_HEARTS", "SKIP_ACTIVATE_PHASE", "PAY_ENERGY_DYNAMIC", 
            "PLACE_ENERGY_UNDER_MEMBER", "CALC_SUM_COST", "LOOK_REORDER_DISCARD", "DIV_VALUE", "TRANSFORM_BLADES"]

TRIGGERS = ["ON_PLAY", "ON_LIVE_START", "ON_LIVE_SUCCESS", "TURN_START", "TURN_END", "CONSTANT", "ACTIVATED", 
             "ON_LEAVES", "ON_REVEAL", "ON_POSITION_CHANGE", "ON_ABILITY_RESOLVE", "ON_ABILITY_SUCCESS", 
             "ON_MOVE_TO_DISCARD", "ON_MEMBER_TAP"]

RESERVED_TARGET_NAMES = ["SELF", "PLAYER", "OPPONENT", "TARGET", "TARGET_MEMBER", "TARGET_STAGE", "TARGET_DISCARD"]

def parse_expr(s):
    if not s: return None
    s = s.strip()
    if s.isdigit(): return {"kind": "literal", "value": int(s)}
    if s.upper() == "TRUE": return {"kind": "literal", "value": True}
    if s.upper() == "FALSE": return {"kind": "literal", "value": False}
    # Binary expressions like VALUE_GT(X, Y)
    m_bin = re.match(r"VALUE_(GT|LT|GE|LE|EQ|NE)\(([^,]+),\s*([^)]+)\)", s)
    if m_bin:
        op_map = {"GT": "gt", "LT": "lt", "GE": "ge", "LE": "le", "EQ": "eq", "NE": "ne"}
        return {
            "kind": "binary",
            "op": op_map[m_bin.group(1)],
            "left": parse_expr(m_bin.group(2)),
            "right": parse_expr(m_bin.group(3))
        }
    if re.match(r"^[A-Z_0-9]+$", s): return {"kind": "reference", "name": s}
    return {"kind": "literal", "value": s.strip("'").strip('"')}

def parse_filter(s):
    if not s: return None
    clauses = []
    patterns = [
        (r"COST_LE_(\d+)", "cost", "le"),
        (r"COST_GE_(\d+)", "cost", "ge"),
        (r"COST_EQ_(\d+)", "cost", "eq"),
        (r"NAME='([^']*)'", "name", "eq"),
        (r'NAME="([^"]*)"', "name", "eq"),
        (r"COLOR='([^']*)'", "color", "eq"),
        (r"ZONE='([^']*)'", "zone", "eq"),
        (r"NAME_IN=\[([^\]]*)\]", "name", "in"),
        (r"GROUP_ID=(\d+)", "group_id", "eq"),
        (r"TYPE_MEMBER", "type", "eq", "MEMBER"),
    ]
    for pattern_tuple in patterns:
        pattern = pattern_tuple[0]
        field = pattern_tuple[1]
        op = pattern_tuple[2]
        for m in re.finditer(pattern, s):
            if len(pattern_tuple) > 3:
                val = pattern_tuple[3]
            else:
                val = m.group(1)
            if op == "in":
                val = [v.strip().strip("'").strip('"') for v in val.split(",")]
            elif isinstance(val, str) and val.isdigit(): val = int(val)
            clauses.append({"field": field, "op": op, "value": val})
    
    if clauses: return {"all_of": clauses}
    return None

def convert_fragment_to_steps(fragment, default_kind="effect"):
    fragment = fragment.strip()
    if not fragment: return []
    
    # Handle EFFECT: CONDITION: ... pattern (Legacy conditional)
    if fragment.startswith("CONDITION:"):
        content = fragment[10:].strip()
        parts = content.split(";", 1)
        if len(parts) == 2:
            cond_str, then_str = parts
            return [{
                "kind": "if",
                "condition": parse_expr(cond_str),
                "then": convert_fragment_to_steps(then_str),
                "args": {}
            }]
        else:
            # Single line condition
            return [{
                "kind": "condition",
                "op": "CHECK", # Standard op for generic check or use the content
                "args": {"raw": content}
            }]

    # Regex for Op(Args) {Filter} -> Binding1 -> Binding2
    m = re.match(r"^([A-Z_0-9]+)(?:\(([^)]*)\))?\s*(?:\{([^}]*)\})?\s*(.*)", fragment)
    if not m:
        return [{"kind": default_kind, "op": fragment, "args": {}, "review_markers": ["unsupported_pattern", "needs_review"]}]
        
    op, args_str, filters_str, remainder = m.groups()
    
    # Parse bindings from remainder
    bindings = []
    if remainder:
        binding_parts = remainder.split("->")
        for b in binding_parts:
            b = b.strip()
            if b: bindings.append(b)
    
    step_kind = default_kind
    if op and op.startswith("SELECT_"): step_kind = "select"
    
    step = {"kind": step_kind, "op": op or fragment, "args": {}}
    
    if bindings:
        # Last binding is usually the one stored, others might be intermediate steps in legacy
        # But for canonical, let's take the first non-reserved as store_as, and any reserved as target
        has_stored = False
        for b in bindings:
            if b in RESERVED_TARGET_NAMES:
                step["target"] = b
            elif not has_stored:
                step["store_as"] = b
                has_stored = True
    
    if args_str:
        if args_str.isdigit():
            step["count"] = parse_expr(args_str)
        else:
            step["args"] = {"raw": args_str}
    
    if filters_str:
        f = parse_filter(filters_str)
        if f: step["filter"] = f
        else: step["review_markers"] = ["unknown_filter_fragment"]

    return [step]

def convert_to_canonical(entry):
    text = entry["text"]
    japanese_text = entry.get("japanese_text", "")
    card_no = entry["card_no"]
    
    lines = text.split("\n")
    trigger_line = lines[0].replace("TRIGGER:", "").strip()
    once_per_turn = "(Once per turn)" in trigger_line or "{ONCE_PER_TURN}" in trigger_line
    trigger = trigger_line.replace("(Once per turn)", "").replace("{ONCE_PER_TURN}", "").strip()
    
    steps = []
    review_reasons = []
    confidence = "high"
    
    options = [l for l in lines if l.strip().startswith("OPTION:")]
    if options:
        choose_step = {"kind": "choose_one", "branches": [], "args": {}}
        for opt in options:
            m = re.match(r"OPTION:\s*(.*?)\s*(?:\|?\s*EFFECT:\s*(.*))?$", opt)
            if m:
                label, effect_str = m.groups()
                branch = {"label": label, "steps": []}
                if effect_str:
                    branch["steps"] = convert_fragment_to_steps(effect_str)
                choose_step["branches"].append(branch)
        steps.append(choose_step)
    else:
        for line in lines[1:]:
            line = line.strip()
            if not line: continue
            
            if line.startswith("COST:"):
                steps.extend(convert_fragment_to_steps(line[5:], default_kind="cost"))
            elif line.startswith("CONDITION:"):
                steps.extend(convert_fragment_to_steps(line[10:], default_kind="condition"))
            elif line.startswith("EFFECT:"):
                steps.extend(convert_fragment_to_steps(line[7:], default_kind="effect"))
            elif line.startswith("SELECT_"):
                steps.extend(convert_fragment_to_steps(line, default_kind="select"))
            else:
                steps.extend(convert_fragment_to_steps(line))

    # Propagation
    entry_issues = False
    for step in steps:
        if "review_markers" in step: entry_issues = True
        if "then" in step:
            if any("review_markers" in s for s in step["then"]): entry_issues = True
        if "branches" in step:
            for b in step["branches"]:
                if any("review_markers" in s for s in b["steps"]): entry_issues = True
                
    if entry_issues:
        confidence = "low"
        if "needs_review" not in review_reasons:
            review_reasons.append("needs_review")

    if trigger not in TRIGGERS:
        review_reasons.append(f"unknown_trigger: {trigger}")
        confidence = "low"

    return {
        "card_no": card_no,
        "schema_version": "v0",
        "trigger": trigger,
        "once_per_turn": once_per_turn,
        "pseudocode": entry.get("pseudocode", text),
        "raw_text": japanese_text if japanese_text else text,
        "confidence": confidence,
        "review_reasons": list(set(review_reasons)),
        "steps": steps
    }

def main():
    try:
        input_path = Path("canonical_ability_model/all_abilities_list.json")
        with open(input_path, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except Exception as e:
        print(f"Error loading: {e}")
        return

    batch = [convert_to_canonical(e) for e in entries]
    output_path = Path("canonical_ability_model/canonical_full_draft.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)
    print(f"Converted {len(batch)} abilities to {output_path}.")

if __name__ == "__main__": main()
