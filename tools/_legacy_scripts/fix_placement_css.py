import os

file_path = r"frontend\web_ui\css\main.css"
with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the line starting with /* Action Group Grid Styling */
start_idx = -1
for i, line in enumerate(lines):
    if "/* Action Group Grid Styling */" in line:
        start_idx = i
        break

if start_idx != -1:
    # Replace from start_idx to the end
    new_css = [
        "/* Action Group Grid Styling */\n",
        ".action-group-buttons.grid-3 {\n",
        "    display: grid !important;\n",
        "    grid-template-columns: repeat(3, 1fr);\n",
        "    gap: 8px;\n",
        "    width: 100%;\n",
        "    padding: 6px;\n",
        "    box-sizing: border-box;\n",
        "}\n",
        "\n",
        ".action-group-buttons.grid-3 .action-btn.mini {\n",
        "    flex: none !important;\n",
        "    width: 100%;\n",
        "    margin: 0;\n",
        "}\n",
        "\n",
        ".action-btn-spacer {\n",
        "    height: 32px; /* Match mini button height approximately */\n",
        "    visibility: hidden;\n",
        "}\n",
    ]
    lines = lines[:start_idx] + new_css
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Successfully replaced CSS block.")
else:
    print("Could not find CSS marker.")
