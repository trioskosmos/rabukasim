file_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\compiler\parser.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Patch 1: RECOVER Group Filter (Line ~903)
target1 = """                    if any(kw in content for kw in ["ハート", "heart"]):
                        effects[-1].params["filter"] = "heart_req"
"""
repl1 = """                    if any(kw in content for kw in ["ハート", "heart"]):
                        effects[-1].params["filter"] = "heart_req"
                    # Capture specific group filter if explicitly mentioned near recover target
                    if match := re.search(r"『(.*?)』", content):
                        effects[-1].params["group"] = match.group(1)
"""

# Patch 2: Multiplier Both Players (Line ~1085)
target2 = """                    elif "メンバー" in content or "人につき" in content:
                        eff_params["per_member"] = True
"""
repl2 = """                    if "自分と相手" in content and ("メンバー" in content or "人につき" in content):
                        eff_params["per_member_all"] = True
                    elif "メンバー" in content or "人につき" in content:
                        eff_params["per_member"] = True
"""

# Patch 3: Group Alias (Line ~1180)
target3 = """                if any(kw in content for kw in ["選ばれない", "選べない", "置けない"]):
                    effects.append(Effect(EffectType.IMMUNITY, 1))
"""
repl3 = """                if any(kw in content for kw in ["選ばれない", "選べない", "置けない"]):
                    effects.append(Effect(EffectType.IMMUNITY, 1))

                if "として扱う" in content and "すべての領域" in content:
                    # Group Alias / Multi-Group
                    groups = []
                    for m in re.finditer(r"『(.*?)』", content):
                        groups.append(m.group(1))
                    if groups:
                        effects.append(Effect(EffectType.META_RULE, 1, params={"type": "group_alias", "groups": groups}))
"""


# Normalize Line Endings for matching
def normalize(s):
    return s.replace("\r\n", "\n")


content_norm = normalize(content)
target1_norm = normalize(target1)
target2_norm = normalize(target2)
target3_norm = normalize(target3)

if target1_norm in content_norm:
    content = content.replace(target1.strip(), repl1.strip())  # strip to avoid newline confusion at edges
    print("Patch 1 applied")
else:
    # Try strict replace on normalized content then write back? No, keep original mixed endings if any.
    # But files on Windows usually CRLF.
    # Let's try direct replace without stripping if exact match fails
    if target1 in content:
        content = content.replace(target1, repl1)
        print("Patch 1 applied (exact)")
    else:
        # Fallback: Find location index
        idx = content_norm.find(target1_norm.strip())
        if idx != -1:
            # This is complex because mapping index back to CRLF content is hard.
            # I will just write normalized content back? No, that changes entire file line endings.
            # Better to strip and replace
            if content.replace(target1.strip(), repl1.strip()) != content:
                content = content.replace(target1.strip(), repl1.strip())
                print("Patch 1 applied (strip)")
            else:
                print("Patch 1 FAILED - content not found even with strip")
        else:
            print("Patch 1 FAILED - target not found")

if target2_norm in content_norm:
    # Do simpler replace that is robust
    # Since I am running locally python, I can just use string replace.
    # I'll rely on strict match first.
    if target2 in content:
        content = content.replace(target2, repl2)
        print("Patch 2 applied (exact)")
    else:
        # try matching line by line
        content = content.replace(target2.strip(), repl2.strip())
        print("Patch 2 applied (strip)")
else:
    print("Patch 2 FAILED")

if target3_norm in content_norm:
    if target3 in content:
        content = content.replace(target3, repl3)
        print("Patch 3 applied (exact)")
    else:
        content = content.replace(target3.strip(), repl3.strip())
        print("Patch 3 applied (strip)")
else:
    print("Patch 3 FAILED")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Done")
