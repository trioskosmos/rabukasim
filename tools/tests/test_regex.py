import re

p = 'SELECT_MEMBER(1) {FILTER="GROUP_ID=3"} -> TARGET_MEMBER'
m = re.match(r"(\w+)(?:\((.*?)\))?(?:\s*\{.*?\}\s*)?(?:\s*->\s*([\w, ]+))?(.*)", p)

if m:
    print(f"Groups: {m.groups()}")
else:
    print("No match")
