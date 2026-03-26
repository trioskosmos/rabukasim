import os
import sys

def check_file(path):
    try:
        with open(path, 'rb') as f:
            content = f.read()
        
        # Check if it's valid UTF-8
        content.decode('utf-8')
        
        # Check for non-ASCII characters (optional, but safer for Rust compatibility)
        # Note: UTF-8 is allowed in Rust, but mangled characters often aren't ASCII.
        # Let's just check for non-ASCII to be very strict as requested.
        text = content.decode('utf-8')
        non_ascii = [c for c in text if ord(c) > 127]
        if non_ascii:
            # print(f"  WARNING: {path} contains non-ASCII characters: {set(non_ascii)}")
            return True, True # Valid UTF-8, but contains non-ASCII
        
        return True, False # Valid UTF-8 and ASCII-only
    except UnicodeDecodeError:
        return False, False # Not valid UTF-8

def main():
    src_dir = 'src'
    errors = 0
    warnings = 0
    total = 0
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.rs'):
                total += 1
                is_utf8, has_non_ascii = check_file(os.path.join(root, file))
                if not is_utf8:
                    print(f"ERROR: {os.path.join(root, file)} is NOT valid UTF-8!")
                    errors += 1
                elif has_non_ascii:
                    # Based on user's request to "ensure they stay fixed", 
                    # we might want to flag non-ASCII as a warning or error.
                    # For now, let's just count them.
                    warnings += 1
    
    print(f"\nVerification complete. Total files: {total}")
    print(f"UTF-8 Errors: {errors}")
    print(f"Non-ASCII Warnings: {warnings}")
    
    if errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
