"""
QA Coverage Auditor
Scans the Rust testing suite for explicit QA references (e.g., 'Q123') and cross-references them
with the official qa_data.json to generate a coverage matrix database.
"""

import json
import os
import re


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run():
    print("Loading QA data...")
    qa_data = load_json("data/qa_data.json")

    # Extract all QA IDs
    all_qas = {}
    for qa in qa_data:
        q_id = qa.get("id", "")
        if q_id.startswith("Q"):
            all_qas[q_id] = {
                "question": qa.get("question", "").replace("\n", " "),
                "answer": qa.get("answer", "").replace("\n", " "),
                "related_cards": [rc.get("card_no") for rc in qa.get("related_cards", [])],
                "found_in_files": set(),
            }

    print(f"Tracking {len(all_qas)} official QA rulings.")

    # Scan Rust src
    rust_dir = "engine_rust_src/src"
    test_files_scanned = 0
    total_q_refs_found = 0

    # Regex to catch "Q123", "Q12", "Q 123" if someone spaced it, but mostly Q\d{1,3}
    q_pattern = re.compile(r"\bQ\d{1,3}\b")

    for root, dirs, files in os.walk(rust_dir):
        for file in files:
            if file.endswith(".rs"):
                test_files_scanned += 1
                filepath = os.path.join(root, file)

                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                content = "".join(lines)
                matches = q_pattern.findall(content)

                for match in matches:
                    if match in all_qas:
                        # Find line numbers and context
                        for i, line in enumerate(lines):
                            if match in line:
                                # Look for a comment describing the test just before or on this line
                                context = ""
                                if "//" in line:
                                    context = line.split("//", 1)[1].strip()
                                elif i > 0 and "//" in lines[i - 1]:
                                    context = lines[i - 1].split("//", 1)[1].strip()

                                # Try to find the enclosing test function
                                func_name = "Unknown Test"
                                for j in range(i, -1, -1):
                                    if "fn test_" in lines[j] or "fn repro_" in lines[j] or "fn " in lines[j]:
                                        m = re.search(r"fn\s+([a-zA-Z0-9_]+)\s*\(", lines[j])
                                        if m:
                                            func_name = m.group(1)
                                            break

                                file_ref = f"{os.path.basename(file)}::{func_name}"
                                if context:
                                    file_ref += f" ({context})"

                                all_qas[match]["found_in_files"].add(file_ref)

                        total_q_refs_found += 1

    print(f"Scanned {test_files_scanned} Rust files, found {total_q_refs_found} valid Q-references.")

    # Generate Database
    tested_qas = {k: v for k, v in all_qas.items() if v["found_in_files"]}
    untested_qas = {k: v for k, v in all_qas.items() if not v["found_in_files"]}

    report = [
        "# QA Coverage Database",
        "This file tracks which official QA rulings have explicit verification tests in the Rust engine.",
        "",
        f"**Overall Coverage:** {len(tested_qas)} / {len(all_qas)} QA items ({len(tested_qas) / len(all_qas) * 100:.1f}%)",
        "",
        "## ✅ Verified QA Items",
        "| QA ID | Source Files | Related Cards | Context (Question) |",
        "|---|---|---|---|",
    ]

    # Sort tested by Q-number
    def extract_q_num(q_id):
        try:
            return int(q_id[1:])
        except:
            return 999

    sorted_tested = sorted(tested_qas.keys(), key=extract_q_num)
    for q_id in sorted_tested:
        qa = tested_qas[q_id]
        files_str = "<br>".join([os.path.basename(f) for f in qa["found_in_files"]])
        cards_str = "<br>".join(qa["related_cards"]) if qa["related_cards"] else "None (General)"
        # Truncate question for matrix
        q_text = qa["question"]
        if len(q_text) > 80:
            q_text = q_text[:77] + "..."

        report.append(f"| **{q_id}** | `{files_str}` | `{cards_str}` | {q_text} |")

    report.append("\n## ❌ Unverified QA Items (Missing Tests)")
    report.append("| QA ID | Related Cards | Context (Question) |")
    report.append("|---|---|---|")

    sorted_untested = sorted(untested_qas.keys(), key=extract_q_num)
    for q_id in sorted_untested:
        qa = untested_qas[q_id]
        cards_str = "<br>".join(qa["related_cards"]) if qa["related_cards"] else "None (General)"
        q_text = qa["question"]
        if len(q_text) > 80:
            q_text = q_text[:77] + "..."

        report.append(f"| **{q_id}** | `{cards_str}` | {q_text} |")

    # Write report
    os.makedirs("reports", exist_ok=True)
    out_path = "reports/qa_coverage_matrix.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"QA Coverage Database written to {out_path}!")


if __name__ == "__main__":
    run()
