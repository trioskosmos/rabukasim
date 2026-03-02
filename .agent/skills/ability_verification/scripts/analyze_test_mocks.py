import os
import glob
import re

def analyze_test_mocks():
    src_dir = os.path.join("engine_rust_src", "src")
    test_files = glob.glob(os.path.join(src_dir, "**", "*.rs"), recursive=True)
    
    total_tests = 0
    mocked_tests = 0
    mocked_tests_list = []
    
    # Regex to find #[test] blocks and their contents
    test_pattern = re.compile(r'#\[test\]\s*(?:#\[\w+\]\s*)*fn\s+(\w+)\s*\(\)\s*\{([^#]*?)(?=#\[test\]|$)', re.DOTALL)
    
    # Signatures that indicate bytecode is being manually constructed
    mock_signatures = [
        r'\.bytecode\s*=\s*vec!\[',
        r'Ability\s*\{\s*bytecode\s*:\s*vec!\[',
        r'let\s+mut\s+mock_ability\s*=\s*Ability::default\(\);'
    ]
    
    for file_path in test_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
            
        tests = test_pattern.finditer(content)
        
        for match in tests:
            test_name = match.group(1)
            test_body = match.group(2)
            total_tests += 1
            
            # Check if this test mocks bytecode
            is_mocked = any(re.search(sig, test_body) for sig in mock_signatures)
            
            if is_mocked:
                # Exclude tests that are specifically designed to test the interpreter with raw opcodes,
                # rather than testing card integration.
                if "interpreter_test" not in file_path and "test_opcodes" not in test_name:
                    mocked_tests += 1
                    mocked_tests_list.append(f"- `{os.path.basename(file_path)}::{test_name}`")

    report_path = os.path.join("reports", "mocked_bytecode_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# Rust Engine Test Analysis: Mocked Bytecode usage\n\n")
        f.write(f"**Total Tests Analyzed**: {total_tests}\n")
        f.write(f"**Tests Using Mocked Bytecode**: {mocked_tests} ({mocked_tests/total_tests*100:.1f}%)\n\n")
        
        f.write("## Why is this a problem?\n")
        f.write("As the USER pointed out, tests that define their own `ability.bytecode = vec![...]` bypass the compiler (`compiler/main.py`). ")
        f.write("If the compiler logic changes (or is bugged), these tests will still pass because they are testing against a hardcoded, assumed ideal state rather than the actual output produced by the game's data pipeline.\n\n")
        
        f.write("## Tests identified:\n")
        for test in mocked_tests_list:
            f.write(f"{test}\n")
            
        f.write("\n## Recommendation\n")
        f.write("These tests should be refactored to use `test_helpers::load_real_db()` and fetch the real bytecode for the cards they are testing, ")
        f.write("similar to the recent fix applied to `test_repro_pb1_001_r_all_combinations`.\n")
        
    print(f"Report generated at {report_path}")

if __name__ == "__main__":
    analyze_test_mocks()
