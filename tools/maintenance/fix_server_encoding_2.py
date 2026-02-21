def fix_action_desc():
    target = "pr_server.py"
    clean_src = "tools/clean_action_desc.txt"

    with open(target, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(clean_src, "r", encoding="utf-8") as f:
        clean_lines = f.readlines()

    new_lines = []
    skipping = False
    injected = False

    start_marker = "def get_action_desc(a, gs):"
    end_marker = '@app.route("/")'

    for line in lines:
        if not skipping:
            if start_marker in line:
                skipping = True
                # Inject clean content here
                new_lines.extend(clean_lines)
                injected = True
                continue
            new_lines.append(line)
        else:
            if end_marker in line:
                skipping = False
                new_lines.append("\n\n")  # Ensure spacing
                new_lines.append(line)
            else:
                pass  # Skip corrupted lines

    if not injected:
        print("Error: Start marker not found!")
        return

    with open(target, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print("Successfully replaced get_action_desc.")


if __name__ == "__main__":
    fix_action_desc()
