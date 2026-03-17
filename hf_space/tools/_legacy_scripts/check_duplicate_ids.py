import re
from collections import Counter

with open("frontend/web_ui/index.html", "r", encoding="utf-8") as f:
    content = f.read()

ids = re.findall(r'id="([^"]+)"', content)
counts = Counter(ids)
duplicates = {id: count for id, count in counts.items() if count > 1}

if duplicates:
    print("Duplicate IDs found:")
    for id, count in duplicates.items():
        print(f"  {id}: {count} occurrences")
else:
    print("No duplicate IDs found.")
