import os
import re

def load_valid_card_nos(path):
    with open(path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def fix_source(root, valid_nos):
    # Pattern for something that looks like a collector number
    # e.g., LL-bp1-001-R, PL!-sd1-001-SD, etc.
    # We include potential trailing pluses and spaces in the match to normalize them.
    pattern = re.compile(r'([A-Z!0-9]+-[a-z0-9]+-[0-9]+-[A-Z0-9+]+)([ +]*)')
    
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith('.rs'):
                path = os.path.join(dirpath, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    def replace_func(match):
                        raw_base = match.group(1)
                        suffix = match.group(2)
                        
                        # Normalize: trim all trailing + and spaces from base
                        base = raw_base.rstrip('+ ')
                        
                        # We want to potentially trim the suffix if it's spaces
                        # but only if we are actually making a fix or if it looks like a typo.
                        
                        def result(final_id):
                            # If we are fixing a card ID, we should probably NOT keep the trailing space
                            # if it's just a space typo.
                            return final_id
                        
                        # 1. Base exactly as-is (but trimmed)
                        if base in valid_nos:
                            return result(base)
                        
                        # 2. Base + '+'
                        if (base + '+') in valid_nos:
                            return result(base + '+')
                        
                        # 3. Base + '++' (Should NOT happen if DB is correct, but safe check)
                        if (base + '++') in valid_nos:
                            return result(base + '++')

                        # If nothing matches, return original
                        return match.group(0)

                    new_content = pattern.sub(replace_func, content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8', newline='\n') as f:
                            f.write(new_content)
                        print(f"Fixed: {path}")
                except Exception as e:
                    print(f"Error {path}: {e}")

if __name__ == "__main__":
    valid_nos = load_valid_card_nos('valid_card_nos.txt')
    fix_source('src', valid_nos)
    fix_source('tests', valid_nos)
