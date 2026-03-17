import os
import re


def diag():
    if not os.path.exists("error.txt"):
        print("error.txt not found")
        return

    with open("error.txt", "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # Find last stack frame
    # Pattern: File "...", line ..., in ...
    matches = list(re.finditer(r'File "([^"]+)", line (\d+), in (\w+)', content))
    if not matches:
        print("No stack frames found in error.txt")
        # Print end of file just in case
        print("END OF ERROR.TXT:")
        print(content[-500:])
        return

    last_match = matches[-1]
    file_path = last_match.group(1)
    line_num = int(last_match.group(2))
    func_name = last_match.group(3)

    print(f"CRASH LOCATION: {file_path}:{line_num} in {func_name}")

    # Extract error message (usually after the last frame)
    err_msg = content[last_match.end() :].splitlines()
    if len(err_msg) > 1:
        print(f"ERROR MESSAGE: {err_msg[1].strip()}")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
            start = max(0, line_num - 3)
            end = min(len(lines), line_num + 2)
            print("\nCODE CONTEXT:")
            for i in range(start, end):
                prefix = "=>" if i + 1 == line_num else "  "
                print(f"{i + 1:4d}: {prefix} {lines[i].strip()}")


diag()
