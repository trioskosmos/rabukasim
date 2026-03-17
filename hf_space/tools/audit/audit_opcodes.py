import re

# Paths
OPCODES_PY_PATH = r"engine/models/opcodes.py"
ABILITY_TRANSLATOR_JS_PATH = r"frontend/web_ui/js/ability_translator.js"


def parse_python_opcodes(path):
    opcodes = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Matches: NAME = VALUE
    matches = re.findall(r"^\s*([A-Z_0-9]+)\s*=\s*(\d+)", content, re.MULTILINE)
    for name, val in matches:
        opcodes[int(val)] = name
    return opcodes


def parse_js_opcodes(path):
    handler_map = {}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find the Translations object structure
    # This assumes a structure like: [EffectType.DRAW]: "Draw {value}"

    # First, let's find the EffectType definition to map JS names to IDs (if they use the enum)
    # or rely on the Fact that the translator typically uses string keys if not using computed properties?
    # Actually, looking at the file provided in context:
    # [EffectType.DRAW]: "..."
    # So we need to map EffectType names to values from the Python side (assuming parity) or parse the JS EffectType object too.

    # Let's parse the EffectType object in JS
    js_effect_types = {}
    effect_type_block = re.search(r"const EffectType = \{([^}]+)\};", content, re.DOTALL)
    if effect_type_block:
        block_content = effect_type_block.group(1)
        # Matches: NAME: VALUE
        matches = re.findall(r"([A-Z_0-9]+):\s*(\d+)", block_content)
        for name, val in matches:
            js_effect_types[name] = int(val)

    # Now find what is actually used in Translations
    # We look for [EffectType.NAME] or "NAME"

    used_opcodes = set()

    # Search for [EffectType.NAME] usage
    matches_enum = re.findall(r"\[EffectType\.([A-Z_0-9]+)\]", content)
    for name in matches_enum:
        if name in js_effect_types:
            used_opcodes.add(js_effect_types[name])

    # Search for direct string keys like "DISCARD_HAND":
    matches_str = re.findall(r'"([A-Z_0-9_]+)":', content)
    # We might need to verify if these strings map to our known opcodes
    # But for now, let's just collect them.
    # Note: Strings might not match python Enum names exactly.

    return js_effect_types, used_opcodes, matches_str


def main():
    print("--- Opcode Audit ---")

    py_opcodes = parse_python_opcodes(OPCODES_PY_PATH)
    print(f"Found {len(py_opcodes)} opcodes in Python.")

    js_map, js_used_enum, js_used_strs = parse_js_opcodes(ABILITY_TRANSLATOR_JS_PATH)
    print(f"Found {len(js_map)} EffectTypes in JS.")
    print(f"Found {len(js_used_enum)} Enum usages in JS Translator.")

    missing_in_js = []

    print("\n--- Mission Opcodes in JS Translator ---")
    for val, name in py_opcodes.items():
        if val == 0:
            continue  # NOP

        # Check if mapped in JS EffectType
        js_name = None
        for k, v in js_map.items():
            if v == val:
                js_name = k
                break

        if not js_name:
            # Maybe it's handled by a raw string that matches the python name?
            if name in js_used_strs:
                continue

            print(f"[MISSING DEFINITION] {name} ({val}) not in JS EffectType")
            missing_in_js.append(name)
            continue

        # If it is defined, is it used in the translation map?
        if val not in js_used_enum:
            # Check if used as string
            if name in js_used_strs or js_name in js_used_strs:
                continue

            print(f"[MISSING TRANSLATION] {name} ({val}) defined but not translated")
            missing_in_js.append(name)

    if not missing_in_js:
        print("\nAll opcodes appear to have frontend definitions!")
    else:
        print(f"\nTotal Missing: {len(missing_in_js)}")


if __name__ == "__main__":
    main()
