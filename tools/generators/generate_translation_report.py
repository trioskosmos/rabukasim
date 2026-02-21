import os
import re

JS_PATH = "frontend/web_ui/js/ability_translator.js"
REPORT_PATH = "translation_report.md"


def main():
    if not os.path.exists(JS_PATH):
        print(f"Error: {JS_PATH} not found.")
        return

    with open(JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Parse EffectType
    effect_types = {}
    # Find the EffectType block
    et_match = re.search(r"const EffectType = \{([\s\S]*?)\};", content)
    if et_match:
        et_block = et_match.group(1)
        # Match "KEY: VALUE," or "KEY: VALUE"
        matches = re.finditer(r"(\w+):\s*(\d+)", et_block)
        for m in matches:
            effect_types[m.group(1)] = int(m.group(2))

    print(f"Found {len(effect_types)} EffectTypes.")

    # 2. Parse JP Translations
    jp_opcodes = {}
    # Rough extraction of jp block
    jp_match = re.search(r"jp:\s*\{([\s\S]*?)en:\s*\{", content)
    if jp_match:
        jp_block = jp_match.group(1)
        opcodes_match = re.search(r"opcodes:\s*\{([\s\S]*?)\},", jp_block)
        if opcodes_match:
            opcodes_block = opcodes_match.group(1)
            # Match [EffectType.KEY]: "Value"
            for m in re.finditer(r'\[EffectType\.(\w+)\]:\s*"(.*?)"', opcodes_block):
                jp_opcodes[m.group(1)] = m.group(2)
            # Match "KEY": "Value"
            for m in re.finditer(r'"(\w+)":\s*"(.*?)"', opcodes_block):
                jp_opcodes[m.group(1)] = m.group(2)

    # 3. Parse EN Translations
    en_opcodes = {}
    en_match = re.search(r"en:\s*\{([\s\S]*?)\};", content)
    if en_match:
        en_block = en_match.group(1)
        # For EN, the opcodes block might end with '}' and then the object closes
        opcodes_match = re.search(r"opcodes:\s*\{([\s\S]*?)\}\s*,?\s*params", en_block)
        if not opcodes_match:
            # Try matching until end of block if params is not next (though it is in the file)
            opcodes_match = re.search(r"opcodes:\s*\{([\s\S]*?)\}", en_block)

        if opcodes_match:
            opcodes_block = opcodes_match.group(1)
            # Match [EffectType.KEY]: "Value"
            for m in re.finditer(r'\[EffectType\.(\w+)\]:\s*"(.*?)"', opcodes_block):
                en_opcodes[m.group(1)] = m.group(2)
            # Match "KEY": "Value"
            for m in re.finditer(r'"(\w+)":\s*"(.*?)"', opcodes_block):
                en_opcodes[m.group(1)] = m.group(2)

    # 4. Consolidate
    all_keys = set(jp_opcodes.keys()) | set(en_opcodes.keys()) | set(effect_types.keys())

    rows = []

    missing_jp = []
    missing_en = []

    # Filter out numeric only keys if any slipped in, though keys are strings here

    sorted_keys = sorted(list(all_keys))

    for key in sorted_keys:
        # Check if it's an EffectType
        is_et = key in effect_types
        et_val = effect_types.get(key, "")

        jp = jp_opcodes.get(key, "")
        en = en_opcodes.get(key, "")

        status_flags = []
        if not jp:
            status_flags.append("MISSING_JP")
        if not en:
            status_flags.append("MISSING_EN")

        if not status_flags:
            status = "OK"
        else:
            status = ", ".join(status_flags)
            if "MISSING_JP" in status_flags:
                missing_jp.append(key)
            if "MISSING_EN" in status_flags:
                missing_en.append(key)

        rows.append({"Key": key, "ID": et_val, "JP": jp, "EN": en, "Status": status})

    # 5. Generate MD
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("# Action Translation Report\n\n")
        f.write(f"Generated from `{JS_PATH}`\n\n")

        if missing_jp or missing_en:
            f.write("## ⚠️ Missing Translations\n")
            if missing_jp:
                f.write(f"- **Japanese**: {', '.join(missing_jp)}\n")
            if missing_en:
                f.write(f"- **English**: {', '.join(missing_en)}\n")
            f.write("\n")

        f.write("| Key | ID | Japanese | English | Status |\n")
        f.write("|---|---|---|---|---|\n")
        for row in rows:
            f.write(f"| {row['Key']} | {row['ID']} | {row['JP']} | {row['EN']} | {row['Status']} |\n")

    print(f"Report generated at {os.path.abspath(REPORT_PATH)}")
    print(f"Total Keys: {len(all_keys)}")
    if missing_jp:
        print(f"Missing JP: {len(missing_jp)}")
    if missing_en:
        print(f"Missing EN: {len(missing_en)}")


if __name__ == "__main__":
    main()
