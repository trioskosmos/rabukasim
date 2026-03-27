import os
import re
import json

def get_rules():
    rules = []
    rules_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\docs\rules\rules.txt"
    with open(rules_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.search(r"^(\d+(\.\d+)*)\.", line)
            if match:
                rules.append(match.group(1))
    return sorted(list(set(rules)))

def get_qas():
    qa_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\data\qa_data.json"
    with open(qa_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return [item["id"] for item in data]

def scan_codebase():
    coverage = {}
    logic_dir = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\src\core\logic"
    
    for root, dirs, files in os.walk(logic_dir):
        for file in files:
            if file.endswith(".rs"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Find Rules
                    rule_matches = re.findall(r"Rule (\d+(?:\.\d+)*)", content)
                    for rid in rule_matches:
                        if rid not in coverage: coverage[rid] = []
                        coverage[rid].append(file)
                    
                    # Find QAs
                    qa_matches = re.findall(r"(Q\d+)", content)
                    for qm in qa_matches:
                        if qm not in coverage: coverage[qm] = []
                        coverage[qm].append(file)
    return coverage

def main():
    rules = get_rules()
    qas = get_qas()
    coverage = scan_codebase()
    
    report_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\docs\rules\RuleCoverage.md"
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Engine Rule & Q&A Logging Coverage\n\n")
        f.write("Generated automatically to track systematic logging of official rules and rulings within the engine.\n\n")
        f.write(f"> [!NOTE]\n")
        f.write(f"> **Generator:** `tools/rule_coverage_gen.py`\n")
        f.write(f"> **Rule Source:** `docs/rules/rules.txt`\n")
        f.write(f"> **Q&A Source:** `data/qa_data.json`\n")
        f.write(f"> **Scan Directory:** `engine_rust_src/src/core/logic`\n\n")
        
        f.write("## Summary Statistics\n")
        total_rules = len(rules)
        logged_rules = sum(1 for r in rules if r in coverage)
        total_qas = len(qas)
        logged_qas = sum(1 for q in qas if q in coverage)
        
        f.write(f"- **Rules Logged:** {logged_rules} / {total_rules} ({logged_rules/total_rules:.1%})\n")
        f.write(f"- **Q&A Logged:** {logged_qas} / {total_qas} ({logged_qas/total_qas:.1%})\n\n")
        
        f.write("## Rules Checklist\n\n")
        f.write("| Rule ID | Status | Files |\n")
        f.write("| :--- | :--- | :--- |\n")
        for r in rules:
            status = "✅" if r in coverage else "❌"
            files = ", ".join(list(set(coverage[r]))) if r in coverage else "-"
            f.write(f"| {r} | {status} | {files} |\n")
            
        f.write("\n## Q&A Checklist\n\n")
        f.write("| Q&A ID | Status | Files |\n")
        f.write("| :--- | :--- | :--- |\n")
        for q in qas:
            status = "✅" if q in coverage else "❌"
            files = ", ".join(list(set(coverage[q]))) if q in coverage else "-"
            f.write(f"| {q} | {status} | {files} |\n")

if __name__ == "__main__":
    main()
