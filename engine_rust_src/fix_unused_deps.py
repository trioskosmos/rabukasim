import os

# List of dependencies that often trigger 'unused_crate_dependencies' in bins/tests
DEPS_TO_SILENCE = [
    "bincode",
    "rand",
    "rand_pcg",
    "serde",
    "serde_json",
    "serde_repr",
    "smallvec",
    "engine_rust"
]

def silence_deps_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find existing 'use ... as _;' lines to avoid duplicates
    existing_silenced = set()
    for line in lines:
        if line.strip().startswith('use ') and line.strip().endswith('as _;'):
            parts = line.strip().split()
            if len(parts) >= 4:
                existing_silenced.add(parts[1])

    new_silencers = []
    for dep in DEPS_TO_SILENCE:
        # Don't add if it's the file's own crate (e.g. engine_rust in src/lib.rs)
        # But we only scan bins and tests, so engine_rust is almost always an external crate there.
        if dep not in existing_silenced:
            new_silencers.append(f"use {dep} as _;\n")
    
    if not new_silencers:
        return False
    
    # Insert at the very top
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_silencers)
        f.writelines(lines)
    return True

def main():
    base_dir = r'.'
    dirs_to_scan = [
        os.path.join(base_dir, 'src', 'bin'),
        os.path.join(base_dir, 'src', 'repro'),
        os.path.join(base_dir, 'tests')
    ]
    
    fixed_count = 0
    total_count = 0
    
    for scan_dir in dirs_to_scan:
        if not os.path.exists(scan_dir):
            continue
        for root, dirs, files in os.walk(scan_dir):
            for file in files:
                if file.endswith('.rs'):
                    total_count += 1
                    if silence_deps_in_file(os.path.join(root, file)):
                        fixed_count += 1
                        
    # Also check src/lib.rs and src/main.rs if they exist
    for root_file in ['src/lib.rs', 'src/main.rs']:
        path = os.path.join(base_dir, root_file)
        if os.path.exists(path):
            total_count += 1
            if silence_deps_in_file(path):
                fixed_count += 1

    print(f"Fixed {fixed_count} files out of {total_count} scanned.")

if __name__ == "__main__":
    main()
