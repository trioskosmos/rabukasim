import sys

from engine.tests.framework.ability_test_generator import generate_ability_test_cases

cases = list(generate_ability_test_cases())
if len(sys.argv) > 1:
    idx = int(sys.argv[1])
    if idx < len(cases):
        print(cases[idx])
    else:
        print("Index out of range")
else:
    # Just list some
    for i in range(370, 390):
        if i < len(cases):
            print(f"{i}: {cases[i]['card_id']} - {cases[i]['card_name']} ({cases[i]['trigger']})")
