import os
import sys


def inspect_file(path, start_line, end_line):
    if not os.path.exists(path):
        print(f"Error: {path} does not exist.")
        return

    with open(path, "rb") as f:
        content = f.read()

    # Detect line endings
    if b"\r\n" in content:
        print("Detected Line Endings: CRLF (Windows)")
    elif b"\n" in content:
        print("Detected Line Endings: LF (Unix)")
    else:
        print("Detected Line Endings: Unknown (or single line)")

    lines = content.splitlines(keepends=True)

    print(f"--- Inspection of {path} (Lines {start_line}-{end_line}) ---")
    for i in range(start_line - 1, min(end_line, len(lines))):
        line = lines[i]
        # Print raw bytes and a visual representation
        raw_repr = repr(line)
        visual = line.decode("utf-8", errors="replace").replace("\n", "\\n").replace("\r", "\\r")
        # Show specific whitespace characters
        detailed = []
        for b in line:
            if b == ord(" "):
                detailed.append(".")
            elif b == ord("\t"):
                detailed.append("\\t")
            elif b == ord("\n"):
                detailed.append("\\n")
            elif b == ord("\r"):
                detailed.append("\\r")
            else:
                detailed.append(chr(b) if 32 <= b <= 126 else f"[{b}]")

        print(f"{i + 1:4} | {''.join(detailed)}")
        print(f"     | Raw: {raw_repr}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python inspect_whitespace.py <file> <start_line> <end_line>")
    else:
        inspect_file(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
