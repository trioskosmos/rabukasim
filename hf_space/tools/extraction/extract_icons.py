import re

with open("temp_source_text.html", "r", encoding="utf-8") as f:
    content = f.read()

# Pattern for /wordpress/wp-content/images/texticon/...
# The user example: src="/wordpress/wp-content/images/texticon/toujyou.png"
matches = re.findall(r'src="(/wordpress/wp-content/images/texticon/[^"]+)"', content)

unique_matches = sorted(list(set(matches)))

print(f"Found {len(unique_matches)} unique icons:")
for m in unique_matches:
    print(m)
