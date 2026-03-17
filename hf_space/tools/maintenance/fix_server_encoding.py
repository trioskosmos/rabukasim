def fix_file():
    target = "pr_server.py"
    with open(target, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    skipping = False

    start_marker = "            for ab in m.abilities:"
    end_marker = "def serialize_player"

    deleted_count = 0

    for line in lines:
        if not skipping:
            if start_marker in line:
                # Double check indentation/context to be safe??
                # The line in file view had 12 spaces.
                if line.startswith("            for ab in m.abilities:"):
                    skipping = True
                    deleted_count += 1
                    continue
            new_lines.append(line)
        else:
            if end_marker in line:
                skipping = False
                new_lines.append(line)
            else:
                deleted_count += 1

    print(f"Deleted {deleted_count} lines.")

    with open(target, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    fix_file()
