import sys

def remove_broken_chars(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove '破'
    content = content.replace('破', '')

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    remove_broken_chars(sys.argv[1])
