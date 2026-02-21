import sys

try:
    filename = sys.argv[1] if len(sys.argv) > 1 else "batch2_summary.txt"
    outfile = filename.replace(".log", "_clean.txt").replace(".txt", "_clean.txt")
    if outfile == filename:
        outfile += ".clean"

    content = open(filename, encoding="utf-8", errors="replace").read()
    with open(outfile, "w", encoding="ascii", errors="replace") as f:
        f.write(content)
    print(f"File cleaned: {outfile}")
except Exception as e:
    print(e)
except Exception as e:
    print(e)
