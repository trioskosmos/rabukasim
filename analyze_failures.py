"""Analyze cargo test failures by broader categories."""

import re

with open('cargo_test_output.txt', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Extract failed test names
failed_tests = re.findall(r'test .*::tests::(test_\S+) ... FAILED', content)
print(f"Total failed tests: {len(failed_tests)}\n")

# Group by broader categories
categories = {
    "cost_reduction": [],
    "live_start": [],
    "heart_filter": [],
    "multi_pick": [],
    "frame_sequence": [],
    "activation_cost": [],
    "baton_touch": [],
    "multi_name": [],
    "condition": [],
    "other": []
}

for test in failed_tests:
    if 'cost' in test.lower() or 'reduction' in test.lower():
        categories["cost_reduction"].append(test)
    elif 'live_start' in test.lower() or 'live' in test.lower():
        categories["live_start"].append(test)
    elif 'heart' in test.lower() or 'filter' in test.lower():
        categories["heart_filter"].append(test)
    elif 'pick' in test.lower() or 'select' in test.lower():
        categories["multi_pick"].append(test)
    elif 'frame' in test.lower() or 'sequence' in test.lower():
        categories["frame_sequence"].append(test)
    elif 'activation' in test.lower() or 'deploy' in test.lower():
        categories["activation_cost"].append(test)
    elif 'baton' in test.lower():
        categories["baton_touch"].append(test)
    elif 'multi' in test.lower() or 'triple' in test.lower() or 'double' in test.lower():
        categories["multi_name"].append(test)
    elif 'condition' in test.lower():
        categories["condition"].append(test)
    else:
        categories["other"].append(test)

print("Failure Categories:")
for category, tests in categories.items():
    if tests:
        print(f"  {category}: {len(tests)}")
        for test in tests[:5]:
            print(f"    - {test}")
        if len(tests) > 5:
            print(f"    ... and {len(tests) - 5} more")
