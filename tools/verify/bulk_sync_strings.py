import os
import re

# Mapping of Old -> New standardized interaction strings
REPLACEMENTS = {
    '"SELECT_CHOICE"': '"SELECT_DISCARD"',
    # Add other drift-fixes here if discovered during baseline analysis
}

def bulk_sync():
    src_dir = "engine_rust_src/src"
    test_files = [
        "archetype_tests.rs",
        "ability_tests.rs",
        "trigger_tests.rs",
        "coverage_gap_tests.rs",
        "manual_tests.rs"
    ]
    
    modified_count = 0
    
    for filename in test_files:
        path = os.path.join(src_dir, filename)
        if not os.path.exists(path):
            print(f"Skipping {path} (not found)")
            continue
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = content
        for old, new in REPLACEMENTS.items():
            new_content = new_content.replace(old, new)
            
        if new_content != content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {path}")
            modified_count += 1
        else:
            print(f"No changes needed for {path}")
            
    print(f"Bulk sync complete. Modified {modified_count} files.")

if __name__ == "__main__":
    bulk_sync()
