import os
import re

# Regex for card numbers that might have been followed by a character replaced by a space
# Format: XX-xx#-000-X
CARD_NO_PATTERN = re.compile(r'([A-Z0-9!]+-[a-z0-9!]+-[0-9]{3}-[A-Z]) ')

def find_and_fix(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.rs'):
                path = os.path.join(dirpath, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    matches = CARD_NO_PATTERN.findall(content)
                    if matches:
                        print(f"Found matches in {path}: {set(matches)}")
                        # For now, let's just print them to see if they should all be '+'
                except Exception as e:
                    print(f"Error reading {path}: {e}")

if __name__ == "__main__":
    find_and_fix('src')
