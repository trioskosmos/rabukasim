import json
import os
import re

def fix_logic_expr(expr):
    if not isinstance(expr, dict): return expr
    kind = expr.get("kind")
    if kind == "binary":
        expr["kind"] = "condition"
        args = expr.get("args", {})
        if "left" in expr: args["left"] = expr.pop("left")
        if "right" in expr: args["right"] = expr.pop("right")
        expr["args"] = args
    elif kind == "literal":
        # Check if this literal is being used as a condition (string value with uppercase OP)
        val = expr.get("value")
        if isinstance(val, str) and "(" in val and val == val.upper():
            expr["kind"] = "condition"
            # Extract op and args from string "OP(ARGS)"
            match = re.match(r'([A-Z_]+)\((.*)\)', val)
            if match:
                expr["op"] = match.group(1).lower()
                expr["args"] = {"raw": match.group(2)}
                del expr["value"]
            else:
                expr["op"] = val.lower()
                expr["args"] = {}
                del expr["value"]
    elif kind == "reference":
        # A single reference can be a condition (boolean variable)
        # But ConditionStep requires op. Let's use raw op or similar.
        expr["kind"] = "condition"
        expr["op"] = "is_true"
        expr["args"] = {"ref": expr.pop("name")}
    
    # Recurse ...
    for field in ["left", "right"]: # If it's still binary-like
        if field in expr: expr[field] = fix_logic_expr(expr[field])
    for field in ["expr", "expressions"]: # NotExpr, AndOrExpr
        if field in expr:
            if isinstance(expr[field], list):
                expr[field] = [fix_logic_expr(e) for e in expr[field]]
            else:
                expr[field] = fix_logic_expr(expr[field])
    return expr

def fix_step(step):
    new_steps = []
    
    # 1. Early Recursion
    for field in ["branches", "then", "else", "body"]:
        if field in step:
            if field == "branches":
                for branch in step[field]:
                    if "steps" in branch:
                        branch["steps"] = flatten([fix_step(s) for s in branch["steps"]])
            else:
                step[field] = flatten([fix_step(s) for s in step[field]])
    
    if "condition" in step:
        step["condition"] = fix_logic_expr(step["condition"])

    # 2. Argument / Count Migration
    if "args" in step and isinstance(step["args"], dict):
        raw = str(step["args"].get("raw", ""))
        if "VARIABLE" in raw:
            step["count"] = {"kind": "literal", "value": "VARIABLE"}
        elif raw.isdigit():
            step["count"] = {"kind": "literal", "value": int(raw)}
        elif "DRAW(" in raw:
             match = re.search(r'DRAW\((\d+)\)', raw)
             if match: step["count"] = {"kind": "literal", "value": int(match.group(1))}

    # 3. Store_as cleanup & normalization
    if "store_as" in step:
        s = step["store_as"]
        # Handle (Optional) -> Wrap in "if" if it's an effect
        if s == "(Optional)":
            if step.get("kind") == "cost":
                step["optional"] = True
                del step["store_as"]
            else:
                # Wrap this step in an if-step later or now?
                # Let's mark it for wrapping in the entry pass to avoid recursion issues
                if "review_markers" not in step: step["review_markers"] = []
                step["review_markers"].append("WRAP_OPTIONAL")
                del step["store_as"]
        # Handle Filter/Duration in store_as
        elif isinstance(s, str) and "{" in s:
            if "{FILTER=" in s:
                f_match = re.search(r'\{FILTER="(.*?)"\}', s)
                if f_match:
                    f_str = f_match.group(1)
                    if "COST_LE_" in f_str:
                        v = f_str.split("COST_LE_")[1].split(",")[0].split(" ")[0]
                        try: val = int(v)
                        except: val = v
                        step["filter"] = {"all_of": [{"field": "cost", "op": "le", "value": val}]}
                    elif "STATUS=TAPPED" in f_str:
                        step["filter"] = {"all_of": [{"field": "status", "op": "eq", "value": "TAPPED"}]}
            if 'DURATION="' in s:
                d_match = re.search(r'DURATION="(.*?)"', s)
                if d_match: step["duration"] = d_match.group(1)
            
            # Strip the {} part
            step["store_as"] = re.sub(r'\{.*?\}', '', s).strip(" ;")
            if not step["store_as"]: del step["store_as"]

    # 4. Target inference from store_as (ONLY for effects)
    RESERVED_TARGETS = {"SELF", "PLAYER", "OPPONENT", "TARGET", "TARGET_MEMBER", "TARGET_STAGE", "TARGET_DISCARD", "CARD_HAND", "CARD_DISCARD"}
    if step.get("kind") == "effect" and "store_as" in step:
        s = step["store_as"]
        for t in RESERVED_TARGETS:
            if s == t or s.startswith(t + " ") or s.startswith(t + ";"):
                if not step.get("target"): step["target"] = t
                step["store_as"] = s[len(t):].strip(" ;")
                if not step["store_as"]: del step["store_as"]
                break

    # 5. Default Targets & Op-Specific normalization
    if step.get("kind") == "effect":
        op = step.get("op")
        if op in ["DRAW", "DISCARD_HAND", "ACTIVATE_ENERGY"] and not step.get("target"):
            step["target"] = "PLAYER"
        elif op in ["BOOST_SCORE", "ADD_BLADES", "ADD_HEARTS"] and not step.get("target"):
            step["target"] = "SELF"
        elif op == "RECOVER_MEMBER":
            if not step.get("target"): step["target"] = "PLAYER"
            if "args" in step and "raw" in step["args"]:
                r = step["args"]["raw"]
                if "CARD_HAND" in r: step["target"] = "CARD_HAND"

    # 6. Schema Cleanup
    BASE_FIELDS = {"kind", "notes", "review_markers"}
    kind = step.get("kind")
    if kind == "cost": allowed = BASE_FIELDS | {"op", "count", "optional", "target", "zone", "filter", "store_as"}
    elif kind == "effect": allowed = BASE_FIELDS | {"op", "count", "target", "zone", "duration", "filter", "store_as", "args"}
    elif kind == "select": allowed = BASE_FIELDS | {"op", "count", "target", "zone", "filter", "store_as"}
    elif kind in ["if", "while"]: allowed = BASE_FIELDS | {"condition", "then", "else", "body"}
    elif kind == "choose_one": allowed = BASE_FIELDS | {"branches"}
    elif kind == "condition": allowed = BASE_FIELDS | {"op", "args", "negated", "store_as"}
    else: allowed = set(step.keys())

    if "args" in allowed and "args" not in step: step["args"] = {}

    for key in list(step.keys()):
        if key not in allowed: del step[key]

    return [step]

def get_referenced_names(expr):
    names = set()
    if not isinstance(expr, dict): return names
    if expr.get("kind") == "reference":
        names.add(expr.get("name"))
    for v in expr.values():
        if isinstance(v, dict):
            names.update(get_referenced_names(v))
        elif isinstance(v, list):
            for i in v:
                names.update(get_referenced_names(i))
    return names

def flatten(l):
    res = []
    for i in l:
        if isinstance(i, list):
            res.extend(i)
        else:
            res.append(i)
    return res

def fix_entry(entry):
    if "steps" in entry:
        steps = flatten([fix_step(s) for s in entry["steps"]])
        
        last_binding_step = None
        for i, step in enumerate(steps):
            # A. Synchronize bindings based on following conditions
            if step.get("kind") == "if" and i > 0:
                refs = get_referenced_names(step.get("condition"))
                if len(refs) == 1:
                    ref_name = list(refs)[0]
                    prev = steps[i-1]
                    if prev.get("kind") in ["select", "cost"]:
                        prev["store_as"] = ref_name

            # B. Track the most recent binding for effect target substitution
            if "store_as" in step:
                last_binding_step = step
            
            # C. Propagate selection to next effect target
            if step.get("kind") == "effect" and last_binding_step:
                # If effect has no target or generic TARGET, and previous was a select
                if last_binding_step.get("kind") == "select":
                    if not step.get("target") or step.get("target") == "TARGET":
                        step["target"] = last_binding_step.get("store_as", "TARGET")

            # D. Final default store_as for select
            if step.get("kind") == "select" and "store_as" not in step:
                c = step.get("count", {}).get("value")
                if c == "VARIABLE": step["store_as"] = "DISCARD_COUNT"
                elif c == 1: step["store_as"] = "TARGET"
                else: step["store_as"] = "TARGETS"

        # E. Post-fix wrapping (e.g. for (Optional))
        final_steps = []
        for step in steps:
            if "review_markers" in step and "WRAP_OPTIONAL" in step["review_markers"]:
                step["review_markers"].remove("WRAP_OPTIONAL")
                if not step["review_markers"]: del step["review_markers"]
                final_steps.append({
                    "kind": "if",
                    "condition": {"op": "choose_yes"}, # Matches bridge flattening
                    "then": [step]
                })
            else:
                final_steps.append(step)
        
        entry["steps"] = final_steps
    return entry

def main():
    input_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\canonical_ability_model\drafts\canonical_full_draft.json"
    output_path = input_path
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed_data = [fix_entry(e) for e in data]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)
    
    print(f"Fixed {len(fixed_data)} entries.")

if __name__ == "__main__":
    main()
