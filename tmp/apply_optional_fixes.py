import json
import re
import os

def apply_fixes():
    input_file = 'data/consolidated_abilities.json'
    output_file = 'data/consolidated_abilities.json.fixed'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Patterns that indicate an optional effect in JP text
    MAY_PATTERNS = ["してもよい", "支払ってもよい", "置いてもよい", "加えてもよい", "登場させてもよい", "移動させてもよい", "アクティブにしてもよい", "引いてもよい"]
    
    # Pseudocode effect verbs that often correspond to these "may" patterns
    EFFECT_VERBS = ["LOOK_AND_CHOOSE", "RECOVER_MEMBER", "DRAW", "ACTIVATE_MEMBER", "PLAY_MEMBER", "POSITION_CHANGE", "DISCARD_HAND", "ADD_HEARTS", "ADD_BLADES", "RECOVER_LIVE", "SELECT_RECOVER_LIVE", "SELECT_RECOVER_MEMBER"]

    fixed_count = 0
    for jp_text, entry in data.items():
        pseudocode = entry.get('pseudocode', '')
        
        # Split JP text by delimiters
        parts = jp_text.split('：')
        if len(parts) < 2:
            continue
            
        effect_jp = parts[1]
        
        # Check if effect JP has "may"
        has_may_in_effect = any(p in effect_jp for p in MAY_PATTERNS)
        
        if not has_may_in_effect:
            continue
            
        # Check if pseudocode already marks effect as optional
        lines = pseudocode.split('\n')
        new_lines = []
        is_fixed = False
        
        for line in lines:
            if line.startswith('EFFECT:') and '(Optional)' not in line:
                # Check if this effect is the one that corresponds to the "may" in JP
                # We prioritize certain verbs
                has_verb = any(v in line for v in EFFECT_VERBS)
                
                if has_verb:
                    # Apply (Optional)
                    # We need to decide where to put it. 
                    # If there's a target (-> ...), put it before the target or at the end.
                    # Standard: EFFECT: VERB(VAL) {PARAMS} (Optional) -> TARGET
                    
                    if '->' in line:
                        pre_target, post_target = line.split('->', 1)
                        new_line = f"{pre_target.strip()} (Optional) -> {post_target.strip()}"
                    else:
                        new_line = f"{line.strip()} (Optional)"
                    
                    new_lines.append(new_line)
                    is_fixed = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
                
        if is_fixed:
            entry['pseudocode'] = '\n'.join(new_lines)
            fixed_count += 1

    print(f"Applied fixes to {fixed_count} entries.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    apply_fixes()
