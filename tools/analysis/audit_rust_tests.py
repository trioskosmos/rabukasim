"""
Rust Test Suite Auditor
Scans the engine_rust_src/src directory for all #[test] functions.
Extracts the test name, any leading documentation comments (/// or //), 
and checks for specific card ID (PL!...) or QA (Q123) references.
Generates a comprehensive dictionary markdown file.
"""
import os
import re

def run():
    rust_dir = "engine_rust_src/src"
    
    card_pattern = re.compile(r'PL![A-Za-z!-]+[-_][a-zA-Z0-9＋+]+[-_][a-zA-Z0-9＋+]+')
    qa_pattern = re.compile(r'\bQ\d{1,3}\b')
    
    test_dict = []
    
    if not os.path.exists(rust_dir):
        print(f"Error: Directory {rust_dir} not found.")
        return

    for root, sorted_dirs, files in os.walk(rust_dir):
        # Sort for deterministic output
        sorted_dirs.sort()
        files.sort()
        
        for file in files:
            if file.endswith(".rs"):
                filepath = os.path.join(root, file)
                
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    
                in_test = False
                test_comments = []
                test_name = ""
                test_cards = set()
                test_qas = set()
                
                # Parsing state
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    
                    # Accumulate preceding comments
                    if stripped.startswith("///") or stripped.startswith("//"):
                        if not stripped.startswith("//!"): # ignore module level
                            comment_text = stripped.lstrip("/ ").strip()
                            if comment_text:
                                test_comments.append(comment_text)
                    elif stripped == "#[test]" or stripped.startswith("#[rstest]"):
                        in_test = True
                    elif in_test and stripped.startswith("fn "):
                        m = re.match(r'fn\s+([a-zA-Z0-9_]+)', stripped)
                        if m:
                            test_name = m.group(1)
                            
                            # We found a test! Let's scan its body until the closing brace for cards/QA
                            # This is a naive bracket counter, good enough for test functions
                            bracket_count = 0
                            body_started = False
                            for j in range(i, len(lines)):
                                body_line = lines[j]
                                test_cards.update(card_pattern.findall(body_line))
                                test_qas.update(qa_pattern.findall(body_line))
                                
                                if "{" in body_line:
                                    bracket_count += body_line.count("{")
                                    body_started = True
                                if "}" in body_line:
                                    bracket_count -= body_line.count("}")
                                    
                                if body_started and bracket_count <= 0:
                                    break
                            
                            # Record test
                            file_context = os.path.relpath(filepath, rust_dir).replace("\\", "/")
                            desc = " ".join(test_comments) if test_comments else "*(No description provided. Inspect function logic.)*"
                            
                            test_dict.append({
                                "file": file_context,
                                "name": test_name,
                                "description": desc,
                                "cards": sorted(list(test_cards)),
                                "qas": sorted(list(test_qas))
                            })
                            
                        # Reset for next test
                        in_test = False
                        test_comments = []
                        test_name = ""
                        test_cards = set()
                        test_qas = set()
                    elif not stripped:
                        # Blank line, keep accumulating comments if we haven't hit #[test]
                        pass
                    else:
                        # Some other code, reset comments
                        if not in_test:
                            test_comments = []
                            
    print(f"Found {len(test_dict)} individual tests in the Rust suite.")
    
    # Generate Output Report
    report = [
        "# Rust Test Suite Dictionary",
        "An audit of every `#[test]` function in the Rusty Engine, its documented purpose, and associated references.",
        "",
        f"**Total Tests Found:** {len(test_dict)}",
        ""
    ]
    
    # Group by file
    tests_by_file = {}
    for t in test_dict:
        tests_by_file.setdefault(t["file"], []).append(t)
        
    for file, tests in tests_by_file.items():
        report.append(f"## File: `{file}`")
        report.append(f"*(Contains {len(tests)} tests)*\n")
        
        for t in tests:
            report.append(f"### `fn {t['name']}()`")
            report.append(f"> {t['description']}")
            
            meta = []
            if t['cards']:
                meta.append(f"**Cards Tested:** {', '.join([f'`{c}`' for c in t['cards']])}")
            if t['qas']:
                meta.append(f"**QA Rules:** {', '.join([f'`{q}`' for q in t['qas']])}")
                
            if meta:
                report.append(" | ".join(meta))
            report.append("")
            
        report.append("---\n")
        
    os.makedirs("reports", exist_ok=True)
    out_path = "reports/rust_test_dictionary.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"Test audit written to: {out_path}")

if __name__ == "__main__":
    run()
