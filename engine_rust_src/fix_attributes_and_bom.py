import os

def clean_file(filepath):
    print(f"Cleaning {filepath}...")
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Remove BOM if present
    if data.startswith(b'\xef\xbb\xbf'):
        data = data[3:]
    
    try:
        content = data.decode('utf-8')
    except UnicodeDecodeError:
        print(f"  Warning: Could not decode {filepath} as UTF-8, skipping.")
        return

    lines = content.splitlines()
    if not lines:
        return

    # Identify silencers added by my script
    silencer_prefixes = ["use bincode as _;", "use rand as _;", "use rand_pcg as _;", 
                         "use serde as _;", "use serde_json as _;", "use serde_repr as _;", 
                         "use smallvec as _;", "use engine_rust as _;"]
    
    silencers = []
    other_lines = []
    for line in lines:
        if any(line.strip() == p for p in silencer_prefixes):
            silencers.append(line)
        else:
            other_lines.append(line)
    
    if not silencers:
        return

    # Now we need to put inner attributes (#!) and doc comments (//!) at the very top.
    top_lines = []
    final_lines = []
    
    i = 0
    while i < len(other_lines):
        line = other_lines[i].strip()
        if line.startswith('#![') or line.startswith('//!'):
            top_lines.append(other_lines[i])
            i += 1
        elif not line: # skip empty lines at start
            top_lines.append(other_lines[i])
            i += 1
        else:
            break
    
    final_lines = top_lines + silencers + other_lines[i:]
    
    new_content = '\n'.join(final_lines) + '\n'
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(new_content)

def main():
    # Files to fix specifically
    files_to_fix = [
        'tests/mod.rs',
        'src/repro/repro_flags.rs',
        'src/repro/yell_persistence_repro.rs',
        'src/lib.rs'
    ]
    
    for f in files_to_fix:
        if os.path.exists(f):
            clean_file(f)

    # Also scan examples/ for unused deps since they generated warnings
    example_dir = 'examples'
    if os.path.exists(example_dir):
        for root, dirs, files in os.walk(example_dir):
            for file in files:
                if file.endswith('.rs'):
                    clean_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
