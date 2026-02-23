import collections
import re
import os

def analyze():
    filtered_path = 'engine_rust_src/reports/telemetry_filtered.log'
    if not os.path.exists(filtered_path):
        print("Filtered log not found.")
        return

    opcode_to_tests = collections.defaultdict(set)
    with open(filtered_path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re.search(r'\[OPCODE\] (\d+) \| Test: (.*)', line)
            if m:
                op = int(m.group(1))
                test_name = m.group(2).strip()
                opcode_to_tests[op].add(test_name)

    # Sort opcodes by how many unique tests they have
    sorted_ops = sorted(opcode_to_tests.keys(), key=lambda x: len(opcode_to_tests[x]))
    
    report_path = 'engine_rust_src/reports/opcode_test_mapping.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Opcode to Test Mapping (Excluding Dry Runs)\n\n")
        f.write("| Opcode | Unique Test Count | Tests |\n")
        f.write("|---|---|---|\n")
        for op in sorted_ops:
            tests = sorted(list(opcode_to_tests[op]))
            f.write(f"| {op} | {len(tests)} | {', '.join(tests)} |\n")
    
    print(f"Generated {report_path}")

if __name__ == "__main__":
    analyze()
