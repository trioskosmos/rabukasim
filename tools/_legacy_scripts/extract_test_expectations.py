import json
import re


def extract_expectations(input_path, output_path):
    print(f"Reading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find test functions
    # def test_strict_LL_bp1_001_R_(game):
    test_func_pattern = re.compile(r"def test_strict_(.*?)_\(game\):")

    # Regex for assertions
    # ab0.trigger == 1
    trigger_pattern = re.compile(r"ab(\d+)\.trigger == (\d+)")
    # ab0.effects[0].effect_type == 7
    effect_type_pattern = re.compile(r"ab(\d+)\.effects\[(\d+)\]\.effect_type == (\d+)")
    # ab0.effects[0].value == 1
    effect_value_pattern = re.compile(r"ab(\d+)\.effects\[(\d+)\]\.value == (-?\d+)")

    # Split by functions
    blocks = content.split("def test_strict_")

    expectations = {}

    print(f"Found {len(blocks)} blocks (approx). Processing...")

    for block in blocks[1:]:  # Skip preamble
        # Extract card ID from the start line
        # e.g. "LL_bp1_001_R_(game):"
        line_end = block.find("\n")
        func_sig = block[:line_end]

        # Reconstruct card_no roughly or rely on regex inside the block if present
        # The function name usually maps to card_no with localized replacement?
        # Let's look for `cno = "..."` inside the block, it's safer.
        cno_match = re.search(r'cno = "(.*?)"', block)
        if not cno_match:
            continue

        cno = cno_match.group(1)

        current_abilities = {}

        # Find all triggers
        for m in trigger_pattern.finditer(block):
            ab_idx = int(m.group(1))
            val = int(m.group(2))
            if ab_idx not in current_abilities:
                current_abilities[ab_idx] = {"trigger": val, "effects": {}}
            current_abilities[ab_idx]["trigger"] = val

        # Find effects
        for m in effect_type_pattern.finditer(block):
            ab_idx = int(m.group(1))
            eff_idx = int(m.group(2))
            val = int(m.group(3))

            if ab_idx not in current_abilities:
                current_abilities[ab_idx] = {"trigger": 0, "effects": {}}
            if eff_idx not in current_abilities[ab_idx]["effects"]:
                current_abilities[ab_idx]["effects"][eff_idx] = {}

            current_abilities[ab_idx]["effects"][eff_idx]["type"] = val

        for m in effect_value_pattern.finditer(block):
            ab_idx = int(m.group(1))
            eff_idx = int(m.group(2))
            val = int(m.group(3))

            if ab_idx in current_abilities and eff_idx in current_abilities[ab_idx]["effects"]:
                current_abilities[ab_idx]["effects"][eff_idx]["value"] = val

        # Convert to list
        ability_list = []
        sorted_indices = sorted(current_abilities.keys())
        for idx in sorted_indices:
            ab_data = current_abilities[idx]

            # Convert effects dict to list
            effects_list = []
            if "effects" in ab_data:
                sorted_eff = sorted(ab_data["effects"].keys())
                for ei in sorted_eff:
                    effects_list.append(ab_data["effects"][ei])

            ability_list.append({"trigger": ab_data.get("trigger", 0), "effects": effects_list})

        if ability_list:
            expectations[cno] = ability_list

    print(f"Extracted expectations for {len(expectations)} cards.")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(expectations, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_path}")


if __name__ == "__main__":
    extract_expectations(
        "engine/tests/cards/batches/test_auto_generated_strict_v2.py",
        "engine/tests/cards/batches/test_expectations.json",
    )
