file_path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\compiler\parser.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # 1. Remove 'e' prefix if it appears before valid code keywords or comments
    # The corruption seems to be `indent + e + indent` or `indent + e + code`
    # Pattern: match `^\s+e\s+` or `^\s+e` followed by keyword

    # Specific fixes based on observations:

    # "e                    # Capture"
    if "e                    # Capture" in line:
        line = line.replace("e                    # Capture", "                    # Capture")

    # "e                    if match"
    if "e                    if match" in line:
        line = line.replace("e                    if match", "                    if match")

    # "e                        effects"
    if "e                        effects" in line:
        line = line.replace("e                        effects", "                        effects")

    # "eelif" -> "elif"
    if "eelif" in line:
        line = line.replace("eelif", "elif")

    # "e    eff_params"
    if "e    eff_params" in line:
        line = line.replace("e    eff_params", "    eff_params")

    # Group Alias block
    # "e                if "として扱う""
    if 'e                if "として扱う"' in line:
        line = line.replace('e                if "として扱う"', '                if "として扱う"')

    # "e                    # Group Alias"
    if "e                    # Group Alias" in line:
        line = line.replace("e                    # Group Alias", "                    # Group Alias")

    # "e                    groups ="
    if "e                    groups =" in line:
        line = line.replace("e                    groups =", "                    groups =")

    # "e                    for m in"
    if "e                    for m in" in line:
        line = line.replace("e                    for m in", "                    for m in")

    # "e                        groups.append"
    if "e                        groups.append" in line:
        line = line.replace("e                        groups.append", "                        groups.append")

    # "e                    if groups:"
    if "e                    if groups:" in line:
        line = line.replace("e                    if groups:", "                    if groups:")

    # "e                        effects.append"
    if "e                        effects.append" in line:
        line = line.replace("e                        effects.append", "                        effects.append")

    new_lines.append(line)

# Dedup adjacent identical lines which might be caused by double patching
final_lines = []
for i, line in enumerate(new_lines):
    if i > 0 and line.strip() == final_lines[-1].strip() and line.strip() != "":
        # Potential duplicate. Check strict equality or just strip?
        # Safe to dedup strict equals
        if line == final_lines[-1]:
            continue

    # Also check if we have the "elif member" block duplicated in a way that causes syntax errors
    # (multiple elifs checking same thing)
    # But dedup should catch exact duplicates.

    final_lines.append(line)

with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(final_lines)

print("Done v3")
