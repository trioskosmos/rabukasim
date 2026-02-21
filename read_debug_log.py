try:
    with open("debug_out.txt", "r", encoding="utf-16") as f:
        lines = f.readlines()
        print(f"Total lines: {len(lines)}")
        start = 2590
        end = 2650
        for i in range(start, min(end, len(lines))):
            print(f"{i}: {lines[i].strip()}")
except Exception as e:
    print(f"Error: {e}")
