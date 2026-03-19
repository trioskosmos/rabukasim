import os

def check_non_ascii(root_dir="."):
    exclude_dirs = {'.git', '.venv', '.uv-cache', '__pycache__', 'node_modules', '.kilocode', '.agent'}
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    if any(c > 127 for c in content):
                        print(f"Non-ASCII found in: {path}")
            except:
                pass

if __name__ == "__main__":
    check_non_ascii()
