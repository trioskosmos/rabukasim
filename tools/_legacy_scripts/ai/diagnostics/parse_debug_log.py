def parse_log():
    try:
        # Try utf-16 first (powershell default)
        with open("debug_tournament.log", "r", encoding="utf-16") as f:
            lines = f.readlines()
    except:
        with open("debug_tournament.log", "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

    printing = False
    for i, line in enumerate(lines):
        if "FAILED:" in line or "Error:" in line or "Traceback" in line:
            print(f"--- ERROR FOUND at line {i} ---")
            for j in range(max(0, i - 5), min(len(lines), i + 20)):
                print(f"{j}: {lines[j].strip()}")
            print("-" * 20)


if __name__ == "__main__":
    parse_log()
