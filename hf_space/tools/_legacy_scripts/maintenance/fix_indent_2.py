path = r"c:\Users\trios\/.gemini\antigravity\vscode\loveca-copy\engine\game\fast_logic.py"
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()


def fix_indent(lines, line_indices):
    modified = False
    for idx in line_indices:
        line = lines[idx]
        prev_line = lines[idx - 1]
        # Skip if previous line is empty or just whitespace
        if not prev_line.strip():
            prev_line = lines[idx - 2]

        indent = prev_line[: len(prev_line) - len(prev_line.lstrip())]
        new_line = indent + line.lstrip()
        if new_line != line:
            print(f"Index {idx}: Fixing line from {repr(line)} to {repr(new_line)}")
            lines[idx] = new_line
            modified = True
    return modified


# 1343 index is 1342
# 1344 index is 1343
indices_to_fix = [1342, 1343]

if fix_indent(lines, indices_to_fix):
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Fixes applied.")
else:
    print("No changes needed or lines not found.")
