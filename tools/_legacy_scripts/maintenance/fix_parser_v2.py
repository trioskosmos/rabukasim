file_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\compiler\parser.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip_count = 0

for i, line in enumerate(lines):
    if skip_count > 0:
        skip_count -= 1
        continue

    stripped = line.strip()
    indent = line[: len(line) - len(stripped)]  # preserve indent

    # Patch 1: Capture specific group filter
    # Look for: effects[-1].params["filter"] = "heart_req"
    if 'effects[-1].params["filter"] = "heart_req"' in stripped:
        new_lines.append(line)
        # Add insertion
        new_lines.append(
            indent + "                    # Capture specific group filter if explicitly mentioned near recover target\n"
        )
        new_lines.append(indent + '                    if match := re.search(r"『(.*?)』", content):\n')
        new_lines.append(indent + '                        effects[-1].params["group"] = match.group(1)\n')
        continue

    # Patch 2: Multiplier "Both Players"
    # Look for: elif "メンバー" in content or "人につき" in content:
    if 'elif "メンバー" in content or "人につき" in content:' in stripped:
        # Replacement
        new_lines.append(
            indent + 'elif "自分と相手" in content and ("メンバー" in content or "人につき" in content):\n'
        )
        new_lines.append(indent + '    eff_params["per_member_all"] = True\n')
        new_lines.append(
            indent + 'elif "メンバー" in content or "人につき" in content:\n'
        )  # Original logic as fallback/else
        # Actually my target logic was:
        # if "自分と相手"...
        # elif "メンバー"...
        # But this is inside an `if/elif` chain already?
        # The surrounding block is `if any(kw in content for kw in ["につき"...]): ...`
        # Inside that, there are `if ... elif ...`.
        # So I can just insert the higher priority check before the original check?
        # No, replacing the line `elif ...` with `if ... elif ...` converts it to nested or requires changing `elif` to `if`?
        # Wait, the original code is:
        # eff_params = {"multiplier": True}
        # if "成功ライブ"...
        # elif "エネ"...
        # elif "メンバー"...  <-- This is where we are.
        # So we can replace this `elif` with:
        # elif "自分と相手" ...:
        #     eff_params["per_member_all"] = True
        # elif "メンバー" ...:
        #     eff_params["per_member"] = True
        # YES.

        # But wait, logic in python: `elif` matches if previous `if` failed.
        # So I should change `elif` to `elif` for the first branch, and `elif` for the second?
        # Yes.
        # The replacement block:
        # elif "自分と相手" in content and ...:
        #     ...
        # elif "メンバー" ...:
        #     ...

        # NOTE: `stripped` check matches the line.
        new_lines.append(
            indent + 'elif "自分と相手" in content and ("メンバー" in content or "人につき" in content):\n'
        )
        new_lines.append(indent + '    eff_params["per_member_all"] = True\n')
        new_lines.append(indent + 'elif "メンバー" in content or "人につき" in content:\n')
        continue

        # Wait, I don't need to skip lines because I am replacing 1 line with 3 lines starting with the replaced line content (modified).
        # Actually I am replacing `elif "member"` with `elif "both_member" ... elif "member"`.
        # So I append my new lines AND the original line (effectively).
        # The logic is sound.

    # Patch 3: Group Alias
    # Look for: effects.append(Effect(EffectType.IMMUNITY, 1))
    if "effects.append(Effect(EffectType.IMMUNITY, 1))" in stripped:
        new_lines.append(line)
        # Insert block
        new_lines.append("\n")
        new_lines.append(indent + '                if "として扱う" in content and "すべての領域" in content:\n')
        new_lines.append(indent + "                    # Group Alias / Multi-Group\n")
        new_lines.append(indent + "                    groups = []\n")
        new_lines.append(indent + '                    for m in re.finditer(r"『(.*?)』", content):\n')
        new_lines.append(indent + "                        groups.append(m.group(1))\n")
        new_lines.append(indent + "                    if groups:\n")
        new_lines.append(
            indent
            + '                        effects.append(Effect(EffectType.META_RULE, 1, params={"type": "group_alias", "groups": groups}))\n'
        )
        continue

    new_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Done v2")
