import re
import sys


def extract_deck(html_path, output_path):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Pattern: title="CODE : NAME" ... class="num">QTY</span>
    # We match the span with title first if possible, as it's closer to the num span.
    pattern = r'title="([^"]+?) :[^"]*"[^>]*>.*?<span class="num">(\d+)</span>'
    matches = re.findall(pattern, content, re.DOTALL)

    if not matches:
        # Fallback to image titles if spans aren't found
        pattern = r'title="([^"]+?) :[^"]*".*?class="num">(\d+)</span>'
        matches = re.findall(pattern, content, re.DOTALL)

    deck_lines = []
    seen = set()
    for code, qty in matches:
        if code in seen:
            continue  # Avoid duplicates due to img and span having same title
        seen.add(code)
        deck_lines.append(f"{code} x {qty}")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(deck_lines))

    print(f"Extracted {len(deck_lines)} unique cards to {output_path}")
    for line in deck_lines:
        print(f"  {line}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_deck.py <input_html> <output_txt>")
    else:
        extract_deck(sys.argv[1], sys.argv[2])
