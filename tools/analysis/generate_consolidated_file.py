import json
import os
import re
from collections import defaultdict

def normalize_ability(text):
    if not text:
        return ""
    return text.strip()

def consolidate_abilities():
    cards_path = r"data\cards.json"
    pseudocode_path = r"data\manual_pseudocode.json"
    
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
        
    with open(pseudocode_path, "r", encoding="utf-8") as f:
        manual_pseudocode = json.load(f)
        
    # Group cards by normalized ability text
    ability_groups = defaultdict(list)
    for card_id, card_data in cards.items():
        ability = card_data.get("ability", "")
        if ability:
            norm_ability = normalize_ability(ability)
            ability_groups[norm_ability].append(card_id)
    # Scan for tests
    rust_dir = "engine_rust_src/src"
    card_test_map = defaultdict(set)
    # Match card IDs like PL!HS-bp1-002-R, allowing variations
    card_pattern = re.compile(r'PL![A-Za-z!-]+[-_][a-zA-Z0-9＋+]+[-_][a-zA-Z0-9＋+]+')
    
    if os.path.exists(rust_dir):
        for root, dirs, files in os.walk(rust_dir):
            for file in files:
                if file.endswith(".rs"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        matches = card_pattern.findall(line)
                        for match in matches:
                            func_name = "Unknown Test"
                            for j in range(i, -1, -1):
                                if "fn test_" in lines[j] or "fn repro_" in lines[j] or "fn " in lines[j]:
                                    m = re.search(r'fn\s+([a-zA-Z0-9_]+)\s*\(', lines[j])
                                    if m:
                                        func_name = m.group(1)
                                        break
                            context = ""
                            if "//" in line:
                                context = line.split("//", 1)[1].strip()
                            elif i > 0 and "//" in lines[i-1]:
                                context = lines[i-1].split("//", 1)[1].strip()
                            
                            ref = f"{file}::{func_name}"
                            if context:
                                ref += f" ({context})"
                            card_test_map[match].add(ref)
                            
    # Normalize map values to sets across full match and stripped match
    normalized_test_map = defaultdict(set)
    for k, v in card_test_map.items():
        base = k.replace("＋", "+")
        for item in v:
            normalized_test_map[base].add(item)
            
    # Markdown output for human review
    report_lines = [
        "# Consolidated Ability Reference\n",
        "This file lists unique card abilities, the cards that share them, and the consolidated pseudocode.\n"
    ]
    
    # JSON output for compiler consumption
    # Map normalized ability text (JP) -> pseudocode string
    json_mapping = {}
    
    for ability, card_ids in ability_groups.items():
        group_pcodes = {}
        for cid in card_ids:
            if cid in manual_pseudocode:
                pcode = manual_pseudocode[cid].get("pseudocode", "").strip()
                if pcode:
                    group_pcodes[cid] = pcode
                    
        unique_pcodes = list(set(group_pcodes.values()))
        
        report_lines.append(f"### Ability\n{ability}\n")
        report_lines.append(f"**Cards:** {', '.join(card_ids)}\n")
        
        # Test Matches
        group_tests = set()
        for cid in card_ids:
            # Fallback exact and stripped mapping
            base = cid.replace("＋", "+")
            group_tests.update(normalized_test_map.get(base, set()))
            group_tests.update(normalized_test_map.get(cid, set()))
            
        if group_tests:
            report_lines.append("**Known Rust Tests:**")
            for t in sorted(group_tests):
                report_lines.append(f"- `{t}`")
            report_lines.append("")
        else:
            report_lines.append("**Known Rust Tests:** *None found* \n")
        
        if unique_pcodes:
            # Selection logic: pick longest as it usually has more detail/metadata
            best_pcode = max(unique_pcodes, key=len)
            report_lines.append(f"**Pseudocode:**\n```\n{best_pcode}\n```")
            json_mapping[ability] = best_pcode
        else:
            report_lines.append("**Pseudocode:** *[No pseudocode defined]*")
            
        report_lines.append("\n---\n")
        
    # Write Markdown
    md_file = r"data\consolidated_abilities.md"
    with open(md_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    # Write JSON
    json_file = r"data\consolidated_abilities.json"
    # Sort keys for deterministic output
    sorted_json = {k: json_mapping[k] for k in sorted(json_mapping.keys())}
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(sorted_json, f, ensure_ascii=False, indent=2)
        
    print(f"Consolidated Markdown created: {md_file}")
    print(f"Consolidated JSON created: {json_file}")
    print(f"Total unique abilities mapped to pseudocode: {len(json_mapping)}")

if __name__ == "__main__":
    consolidate_abilities()
