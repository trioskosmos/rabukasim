import os
import re
from collections import defaultdict

def extract_rules_from_text(file_path):
    rules = set()
    pattern = re.compile(r'^\s*(\d+(\.\d+)+)\.?\s', re.MULTILINE)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        matches = pattern.findall(content)
        for match in matches:
            rules.add(match[0])
    top_pattern = re.compile(r'^\s*(\d+)\.\s', re.MULTILINE)
    matches = top_pattern.findall(content)
    for match in matches:
        rules.add(match)
    return rules

def audit_codebase(src_dir, rules):
    coverage = defaultdict(list)
    rule_patterns = {rule: re.compile(r'Rule\s+' + re.escape(rule)) for rule in rules}
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.rs'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if '//' in line or '/*' in line or '///' in line:
                            for rule, pattern in rule_patterns.items():
                                if pattern.search(line):
                                    coverage[rule].append(f"{file}:{i+1}")
    return coverage

def main():
    rules_txt = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\docs\rules\rules.txt'
    src_dir = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src'
    
    all_rules = extract_rules_from_text(rules_txt)
    covered_rules = audit_codebase(src_dir, all_rules)
    
    sorted_rules = sorted(list(all_rules), key=lambda x: [int(s) for s in x.split('.')])
    
    print(f"Total Rules Identified: {len(all_rules)}")
    print(f"Rules Covered: {len(covered_rules)}")
    
    # Check Section 8, 9, 10, 11, 12, 13
    for rule in sorted_rules:
        if rule.startswith('8.') or rule.startswith('9.') or rule.startswith('10.') or rule.startswith('11.') or rule.startswith('12.') or rule.startswith('13.'):
            if rule in covered_rules:
                print(f"✅ {rule}: {', '.join(covered_rules[rule])}")
            else:
                pass # print(f"❌ {rule}")

if __name__ == "__main__":
    main()
