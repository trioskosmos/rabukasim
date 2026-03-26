import os
import re

# Mapping of known Mojibake patterns (like 笏 which is often EF BB BF mangled as Shift-JIS)
# Instead of replacing, we identify where they originated.
MOJIBAKE_PATTERNS = {
    '笏': 'Potential UTF-8 BOM interpreted as Shift-JIS',
    '笊': 'Problematic UI character',
    '・': 'Middle Dot',
}

def analyze_file(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read()
        
        # 1. Check for UTF-8 validity
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f"❌ INVALID UTF-8 in {path}: {e}")
            return False
        
        # 2. Check for known Mojibake characters
        found = []
        for char, reason in MOJIBAKE_PATTERNS.items():
            if char in text:
                found.append((char, reason))
        
        if found:
            print(f"⚠️  SUSPICIOUS CHARACTERS in {path}:")
            for char, reason in found:
                print(f"    - '{char}' ({reason})")
            return True
        
        return True
    except Exception as e:
        print(f"Error checking {path}: {e}")
        return False

def main():
    dirs = ['src', 'tests']
    for scan_dir in dirs:
        for root, _, files in os.walk(scan_dir):
            for file in files:
                if file.endswith('.rs'):
                    analyze_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
