import os

path = "evaluation_results.txt"
if os.path.exists(path):
    with open(path, "rb") as f:
        data = f.read()
    # Try common encodings
    for enc in ["utf-16", "utf-8", "ascii"]:
        try:
            print(data.decode(enc))
            break
        except:
            continue
else:
    print("File not found.")
