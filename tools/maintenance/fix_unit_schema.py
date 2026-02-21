import os
import re


def fix_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipping {filepath} (encoding error)")
        return

    original_content = content

    # 1. unit="" -> units=[]
    # This is safe because unit="" meant no unit.
    content = re.sub(r'unit=""', r"units=[]", content)
    content = re.sub(r"unit=''", r"units=[]", content)

    # 2. unit="Something" -> units=["Something"]
    # We use a regex that captures the value inside quotes, ensuring it's not empty
    # unit="([^"]+)" -> units=["\1"]
    content = re.sub(r'unit="([^"]+)"', r'units=["\1"]', content)
    content = re.sub(r"unit='([^']+)'", r"units=['\1']", content)

    # 3. group="..." -> groups=["..."] (Repeat from before, just in case)
    # But adhere to previous fix logic
    # (Already ran, but check for stragglers)

    # 4. Fix duplicate imports of CardType if any

    if content != original_content:
        print(f"Fixing {filepath}")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    root_tests = "tests"
    for root, dirs, files in os.walk(root_tests):
        for filename in files:
            if filename.endswith(".py"):
                fix_file(os.path.join(root, filename))


if __name__ == "__main__":
    main()
