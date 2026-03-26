import os

def fix_line(path, line_no, new_content):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    if 0 <= line_no < len(lines):
        lines[line_no] = new_content + ('\n' if not new_content.endswith('\n') else '')
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Fixed line {line_no+1} in {path}")
    else:
        print(f"Line number {line_no+1} out of range for {path}")

# Adjust paths to be relative to the engine_rust_src directory or use absolute paths.
base_dir = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\engine_rust_src'
fix_line(os.path.join(base_dir, 'src', 'bin', 'final_diagnostic.rs'), 151, '                "[ERROR] Could not reach Main phase (stuck at {:?})",')
fix_line(os.path.join(base_dir, 'src', 'bin', 'diagnostic_init.rs'), 100, '        println!("\\n[ERROR] Game is immediately terminal after initialize_game!");')
