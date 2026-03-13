import os
import re

# Regex for emojis (broad range)
EMOJI_PATTERN = re.compile(
    '['
    '\U0001f300-\U0001f64f'  # emoticons
    '\U0001f680-\U0001f6ff'  # transport & map symbols
    '\U0001f1e0-\U0001f1ff'  # flags (iOS)
    '\U00002702-\U000027b0'
    '\U000024c2-\U0001f251'
    ']+', re.UNICODE
)

# Alternative regex for all non-ASCII characters to find anything missed
NON_ASCII_PATTERN = re.compile(r'[^\x00-\x7F]')

EXCLUDE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', '.agent', '.gemini'}
EXCLUDE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.bin', '.exe', '.dll', '.so', '.pyc'}

def scan_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            matches = EMOJI_PATTERN.findall(content)
            if matches:
                return matches
    except Exception as e:
        pass
    return []

def main():
    results = {}
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if any(file.endswith(ext) for ext in EXCLUDE_EXTENSIONS):
                continue
            
            filepath = os.path.join(root, file)
            filepath = os.path.normpath(filepath)
            
            # Skip the script itself
            if 'scan_emojis.py' in filepath:
                continue
                
            found = scan_file(filepath)
            if found:
                results[filepath] = found

    if results:
        print("Found emojis in the following files:")
        for path, emoticons in results.items():
            print(f"{path}: {', '.join(set(emoticons))}")
    else:
        print("No emojis found.")

if __name__ == "__main__":
    main()
