import os

FILES = [
    '../data/cards.json',
    '../data/cards_compiled.json'
]

MAPPING = {
    b'\xef\xbc\x8b': b'+', # Fullwidth Plus ＋
}

def fix_db(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    print(f"Fixing {path}...")
    with open(path, 'rb') as f:
        content = f.read()
    
    # We use bytes.replace to keep it clean
    original_content = content
    for j_char_bytes, a_char_bytes in MAPPING.items():
        content = content.replace(j_char_bytes, a_char_bytes)
    
    if content != original_content:
        with open(path, 'wb') as f:
            f.write(content)
        print(f"  RESTORED: {path}")
    else:
        print(f"  No changes needed for {path}")

if __name__ == "__main__":
    for p in FILES:
        fix_db(p)
