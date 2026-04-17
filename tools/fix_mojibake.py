import os

# Logic: Restore Strings that were "UTF-8 read as CP932"
def restore_string(s):
    try:
        # If it contains common mojibake chars...
        if any(c in s for c in "繝繧ｽｸｫ笨・"):
            # We encode as CP932. If we hit a char that CP932 doesn't know (like \ufffd), 
            # we'll use errors='replace' which puts '?' (0x3F). 
            # 0x3F is a valid single-byte UTF-8 char (ASCII '?').
            # This is better than failing the whole line.
            bytes_data = s.encode('cp932', errors='replace')
            return bytes_data.decode('utf-8', errors='replace')
    except:
        pass
    return s

def process_file(path):
    try:
        # Read with UTF-8. If it has invalid UTF-8 sequences, use errors='replace'
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except:
        return False

    new_content = []
    changed = False
    
    for line in content.splitlines(keepends=True):
        restored = restore_string(line)
        if restored != line:
            new_content.append(restored)
            changed = True
        else:
            new_content.append(line)
            
    if changed:
        print(f"Fixed: {path}")
        with open(path, 'w', encoding='utf-8') as f:
            f.write("".join(new_content))
        return True
    return False

def main():
    extensions = {'.rs', '.py', '.js', '.json', '.wgsl', '.md', '.txt', '.log'}
    exclude_dirs = {'.git', 'node_modules', 'target', '.venv', '__pycache__'}
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in extensions:
                if file == 'metadata.json' or file == 'fix_mojibake.py':
                    continue
                process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
