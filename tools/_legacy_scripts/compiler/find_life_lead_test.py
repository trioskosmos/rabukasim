def find_life_lead_tests():
    file_path = "engine/tests/cards/batches/test_auto_generated_strict.py"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        print("Could not read file")
        return

    print("Tests expecting ConditionType.LIFE_LEAD (type == 8):")
    current_func = None
    for i, line in enumerate(lines):
        if line.strip().startswith("def test_strict_"):
            current_func = line.strip()

        if ("conditions" in line and "type == 8" in line) or ("conditions" in line and "type==8" in line):
            print(f"Line {i + 1}: {current_func}")
            # Print context
            for j in range(max(0, i - 5), min(len(lines), i + 5)):
                print(f"  {lines[j].rstrip()}")
            print("-" * 20)
            break  # Just need one for now


if __name__ == "__main__":
    find_life_lead_tests()
