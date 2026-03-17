import re

filepath = "c:\\Users\\trios\\.gemini\\antigravity\\vscode\\loveca-copy\\engine\\game\\mixins\\effect_mixin.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern: self.pending_choices.append((TYPE, { ... }))
# We want to insert `**choice_metadata, ` right after the opening brace `{`.
# But we need to be careful not to break syntax.
# A safer approach: Find `self.pending_choices.append(` and looks for the dictionary start.

# Actually, the user wants me to add `**choice_metadata` to the params dict.
# Most calls look like:
# ("TYPE", {
#    "key": val,
#    ...
# })

# I will replace `self.pending_choices.append` with a wrapper logic? No, that's runtime.
# Static strings:
# Replace `self.pending_choices.append((\n\s*".*",\s*{)` with `self.pending_choices.append((\1 **choice_metadata, `?
# No, easier to just manually add it to the top 5 most common choice types first, manually.

# Wait, I can use a smart regex replacement that affects all of them if they follow standard formatting.
# The code is consistently formatted.

# Logic:
# valid_choices = ["SELECT_FROM_LIST", "TARGET_MEMBER", "TARGET_HAND", "TARGET_MEMBER_SLOT", "SELECT_MODE", "COLOR_SELECT", "TARGET_OPPONENT_MEMBER", "SELECT_FROM_DISCARD", "DISCARD_SELECT", "SELECT_SWAP_SOURCE", "SELECT_ORDER", "SELECT_FORMATION_SLOT", "CHOOSE_FORMATION"]

# For each choice type, I'll update the dictionary construction.
# Example:
# ("SELECT_FROM_LIST", {
#    "cards": ...
#    ...
# })
# Becomes:
# ("SELECT_FROM_LIST", {
#    **choice_metadata,
#    "cards": ...
# })

new_content = content
# Iterate line by line or find matches?
# Pydantic/Python won't like `**choice_metadata` if it's not defined in scope.
# I verified `choice_metadata` is defined in `_resolve_pending_effect`.

# Let's do a targeted replace for the most common ones.

replacements = [
    # 1. ACTIVATE_ENERGY
    (r'("SELECT_FROM_LIST",\s*{)', r"\1 **choice_metadata, "),
    # 2. TARGET_MEMBER
    (r'("TARGET_MEMBER",\s*{)', r"\1 **choice_metadata, "),
    # 3. TARGET_HAND
    (r'("TARGET_HAND",\s*{)', r"\1 **choice_metadata, "),
    # 4. SELECT_MODE
    (r'("SELECT_MODE",\s*{)', r"\1 **choice_metadata, "),
    # 5. COLOR_SELECT
    (r'("COLOR_SELECT",\s*{)', r"\1 **choice_metadata, "),
    # 6. TARGET_OPPONENT_MEMBER
    (r'("TARGET_OPPONENT_MEMBER",\s*{)', r"\1 **choice_metadata, "),
    # 7. SELECT_FROM_DISCARD
    (r'("SELECT_FROM_DISCARD",\s*{)', r"\1 **choice_metadata, "),
    # 8. TARGET_MEMBER_SLOT
    (r'("TARGET_MEMBER_SLOT",\s*{)', r"\1 **choice_metadata, "),
    # 9. DISCARD_SELECT
    (r'("DISCARD_SELECT",\s*{)', r"\1 **choice_metadata, "),
    # 10. SELECT_SWAP_SOURCE
    (r'("SELECT_SWAP_SOURCE",\s*{)', r"\1 **choice_metadata, "),
    # 11. SELECT_ORDER
    (r'("SELECT_ORDER",\s*{)', r"\1 **choice_metadata, "),
    # 12. SELECT_FORMATION_SLOT
    (r'("SELECT_FORMATION_SLOT",\s*{)', r"\1 **choice_metadata, "),
    # 13. CHOOSE_FORMATION (often empty)
    (r'("CHOOSE_FORMATION",\s*{)', r"\1 **choice_metadata, "),
]

for pattern, replacement in replacements:
    new_content = re.sub(pattern, replacement, new_content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(new_content)

print(f"Updated {filepath}")
