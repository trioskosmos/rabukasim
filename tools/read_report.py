
import sys

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\reports\debug_126.txt"
try:
    with open(path, "r", encoding="utf-16le") as f:
        print(f.read())
except Exception as e:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())
