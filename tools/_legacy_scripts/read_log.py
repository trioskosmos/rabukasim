try:
    with open("batch2_failures.log", "r", encoding="utf-8", errors="replace") as f:
        print(f.read())
except Exception as e:
    print(e)
