import os

def fix_repro_files():
    repro_dir = os.path.join('src', 'repro')
    if not os.path.exists(repro_dir):
        print("repro_dir not found")
        return

    for root, dirs, files in os.walk(repro_dir):
        for file in files:
            if file.endswith('.rs'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Remove 'use engine_rust as _;'
                new_content = content.replace('use engine_rust as _;\n', '')
                # Handle cases without newline if any
                new_content = new_content.replace('use engine_rust as _;', '')
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Fixed {filepath}")

if __name__ == "__main__":
    fix_repro_files()
