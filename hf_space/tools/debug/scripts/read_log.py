try:
    with open("debug_error.log", "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
        print(content[:3000])  # First 3000
        if len(content) > 3000:
            print("\n... [SKIPPING MID] ...\n")
            print(content[-3000:])  # Last 3000
except Exception as e:
    print(f"Error reading file: {e}")
