"""Analyze cargo test failures to identify patterns."""

import re

# Try multiple encodings to handle BOM issues
encodings = ['utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1']
content = None
for encoding in encodings:
    try:
        with open('cargo_test_output.txt', 'r', encoding=encoding) as f:
            content = f.read()
        print(f"Successfully read with encoding: {encoding}")
        break
    except UnicodeDecodeError:
        continue

if content is None:
    print("Failed to read file with any encoding")
    exit(1)

# Extract test results
test_result_match = re.search(r'test result: FAILED\. (\d+) passed; (\d+) failed; (\d+) ignored', content)
if test_result_match:
    passed = int(test_result_match.group(1))
    failed = int(test_result_match.group(2))
    ignored = int(test_result_match.group(3))
    print(f"Test Results:")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Ignored: {ignored}")
    print()

# Extract all FAILED test names
failed_tests = re.findall(r'test .*::tests::(test_\S+) ... FAILED', content)
print(f"Total failed tests: {len(failed_tests)}")
print()

# Group failures by test name pattern
patterns = {}
for test in failed_tests:
    # Extract pattern (e.g., card_10, card_459, q203, etc.)
    match = re.search(r'test_(card_\d+|q\d+|test_\d+|live_\d+|multi_\w+)', test)
    if match:
        pattern = match.group(1)
    else:
        pattern = test
    
    if pattern not in patterns:
        patterns[pattern] = []
    patterns[pattern].append(test)

print("Failure patterns:")
for pattern, tests in sorted(patterns.items(), key=lambda x: -len(x[1])):
    print(f"  {pattern}: {len(tests)} failures")
print()

# Extract assertion failures
assertion_matches = re.findall(r'assertion `left == right` failed: (.+)', content)
print(f"Total assertion failures: {len(assertion_matches)}")
print("\nSample assertion failures:")
for i, assertion in enumerate(assertion_matches[:10]):
    print(f"  {i+1}. {assertion[:100]}...")
