import os

file_path = r"frontend\web_ui\js\ui_rendering.js"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Updated getActionLabel with more robust stripping
new_helper = """        // Helper for consistent action labels
        const getActionLabel = (a, isMini = false) => {
            const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;
            const cost = a.cost !== undefined ? a.cost : (a.base_cost !== undefined ? a.base_cost : null);
            const isBaton = (a.name && (a.name.includes('Baton') || a.name.includes('バトン')));
            
            // Clean name: remove verbose bracketed prefixes (【...】 or [...]) and card numbers in parentheses (...)
            let name = a.name || "";
            name = name.replace(/[【\\\[].*?[】\\\]]/g, "").replace(/\\(.*?\\)/g, "").trim();
            
            if (isMini) {
                let label = `${energyIcon}${cost !== null ? cost : 0}`;
                if (isBaton) label += ' 🔄';
                return label;
            } else {
                let label = `<div class="action-title">${name}</div>`;
                if (cost !== null) {
                    label += `<div class="action-cost">${energyIcon}${cost}</div>`;
                }
                if (isBaton) label += ' 🔄';
                return label;
            }
        };"""

# Replacement target: replace the old getActionLabel block
start_marker = "const getActionLabel = (a, isMini = false) => {"
# The block ends with };
# We'll search for the first }; after the marker.

start_pos = content.find(start_marker)
if start_pos != -1:
    # We want to replace the whole // Helper for consistent action labels block
    block_start = content.rfind("// Helper for consistent action labels", 0, start_pos)
    if block_start == -1:
        block_start = start_pos

    # End of block is at the next }; that closes the helper
    end_pos = content.find("};", start_pos)
    if end_pos != -1:
        final_end = end_pos + 2
        new_content = content[:block_start] + new_helper + content[final_end:]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully refined getActionLabel in ui_rendering.js")
    else:
        print("Could not find end of getActionLabel")
else:
    print("Could not find getActionLabel start marker")
