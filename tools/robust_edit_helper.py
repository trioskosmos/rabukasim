import sys
import os

def get_exact_text(path, start_line, end_line):
    if not os.path.exists(path):
        print(f"Error: {path} does not exist.")
        return

    with open(path, 'rb') as f:
        lines = f.readlines()
        
    chunk = lines[start_line - 1 : end_line]
    
    # We want to print this in a way that preserves EVERYTHING.
    # Printing raw bytes might be messy in some terminals.
    # Printing utf-8 string is usually okay for my tool input.
    full_text = b"".join(chunk).decode('utf-8', errors='replace')
    
    print("--- START OF EXACT TEXT ---")
    sys.stdout.write(full_text)
    print("--- END OF EXACT TEXT ---")
    
    # Also print a version with visible whitespace for debugging
    print("\n--- VISIBLE WHITESPACE VERSION ---")
    for i, line in enumerate(chunk):
        l_str = line.decode('utf-8', errors='replace')
        visible = l_str.replace(' ', '.').replace('\t', '\\t').replace('\r', '\\r').replace('\n', '\\n')
        print(f"{start_line + i:4} | {visible}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python robust_edit_helper.py <file> <start_line> <end_line>")
    else:
        get_exact_text(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
