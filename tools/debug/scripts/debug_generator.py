from engine.tests.framework.ability_test_generator import generate_ability_test_cases

cases = generate_ability_test_cases()
print(f"Total cases: {len(cases)}")

# debug conditions
cond_types = {}
for c in cases:
    for cond in c.get("conditions", []):
        ctype = cond.get("condition_type")
        cond_types[ctype] = cond_types.get(ctype, 0) + 1

print("\nCondition Types found:")
for t, count in cond_types.items():
    print(f"  '{t}': {count}")

# Print first raw condition
print("\nFirst raw condition:")
for c in cases:
    if c.get("conditions"):
        print(c["conditions"][0])
        break
