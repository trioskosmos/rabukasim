import re
import os
import json
from pathlib import Path

def audit_rules(src_dir):
    rule_pattern = re.compile(r'Rule (\d+\.\d+(?:\.\d+)*)')
    log_pattern = re.compile(r'(log|log_rule|log_event|self\.log)')
    
    results = []
    
    for root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith('.rs'):
                continue
            
            file_path = Path(root) / file
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                # print(f"Error reading {file_path}: {e}")
                continue
            
            for i, line in enumerate(lines):
                match = rule_pattern.search(line)
                if match:
                    rule_id = match.group(0)
                    # Check context: +/- 5 lines
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 6)
                    context = "".join(lines[context_start:context_end])
                    
                    is_logged = log_pattern.search(context) is not None
                    
                    # Heuristic refinement
                    if 'log_rule' in line and rule_id in line:
                        is_logged = True
                    if 'log_event' in line and rule_id in line:
                        is_logged = True
                        
                    results.append({
                        'file': str(file_path.relative_to(src_dir)),
                        'line': i + 1,
                        'rule': rule_id,
                        'content': line.strip(),
                        'is_logged': is_logged
                    })
    
    return results

if __name__ == "__main__":
    src = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src"
    audit_data = audit_rules(src)
    
    output_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\tmp\audit_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(audit_data, f, indent=2)
    
    print(f"Audit complete. Results written to {output_path}")
    print(f"Total Rules Found: {len(audit_data)}")
    print(f"Logged: {len([x for x in audit_data if x['is_logged']])}")
    print(f"Missing: {len([x for x in audit_data if not x['is_logged']])}")
