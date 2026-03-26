import os

def fix_source(root):
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.rs'):
                path = os.path.join(dirpath, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    patterns = [
                        ('LL-bp2-001-R ', 'LL-bp2-001-R+'),
                        ('LL-bp2-026-R ', 'LL-bp2-026-R+'),
                        ('PL!S-bp2-004-R ', 'PL!S-bp2-004-R+'),
                        ('Card LL-bp2-001-R  not found', 'Card LL-bp2-001-R+ not found'),
                        ('Card LL-bp2-026-R  not found', 'Card LL-bp2-026-R+ not found'),
                    ]
                    
                    new_content = content
                    for old, new in patterns:
                        new_content = new_content.replace(old, new)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8', newline='\n') as f:
                            f.write(new_content)
                        print(f"Fixed: {path}")
                except Exception as e:
                    print(f"Error {path}: {e}")

if __name__ == "__main__":
    fix_source('src')
