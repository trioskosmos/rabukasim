import re
import os

report_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src\reports\semantic_report_v2_utf8.txt"

if not os.path.exists(report_path):
    print(f"Report not found at {report_path}")
    exit(1)

with open(report_path, "rb") as f:
    content = f.read().decode("utf-16le", errors="ignore")

# Look for semantic summary
# Pattern: "Total Passed: X / Y (Z%)"
matches = re.findall(r"Total Passed: (\d+) / (\d+) \(([\d.]+)%\)", content)

if matches:
    print("Semantic Test Summary:")
    for pass_count, total_count, percentage in matches:
        print(f"Passed: {pass_count} / {total_count} ({percentage}%)")
else:
    print("Could not find Semantic Test Summary in report.")
    # Try searching for category summaries
    pattern = r"Category: (\w+)\s+Passed: (\d+) / (\d+) \(([\d.]+)%\)"
    cat_matches = re.findall(pattern, content)
    if cat_matches:
        for cat, passed, total, perc in cat_matches:
            print(f"Category: {cat} - {passed}/{total} ({perc}%)")
    else:
        print("No category summaries found either.")

# List failed tests
failed_tests = re.findall(r"test ([\w:]+) \.\.\. FAILED", content)
if failed_tests:
    print("\nFailed Tests:")
    for test in failed_tests:
        print(f"- {test}")
