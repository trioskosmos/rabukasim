file_path = r"frontend\web_ui\js\ui_rendering.js"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Helper function to be used inside the script to construct the new block
new_logic = """        // Helper for consistent action labels
        const getActionLabel = (a, isMini = false) => {
            const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;
            const cost = a.cost !== undefined ? a.cost : (a.base_cost !== undefined ? a.base_cost : null);
            const isBaton = (a.name && (a.name.includes('Baton') || a.name.includes('バトン')));

            if (isMini) {
                let label = `${energyIcon}${cost !== null ? cost : 0}`;
                if (isBaton) label += ' 🔄';
                return label;
            } else {
                // Clean name: remove verbose prefixes like 【左に置く】 if they exist
                let name = a.name || "";
                name = name.replace(/【.*?】/g, "").trim();

                let label = `<div class="action-title">${name}</div>`;
                if (cost !== null) {
                    label += `<div class="action-cost">${energyIcon}${cost}</div>`;
                }
                if (isBaton) label += ' 🔄';
                return label;
            }
        };

        // Play Grouped Actions
        Object.keys(playActionsByHand).forEach(hIdx => {
            const actions = playActionsByHand[hIdx];
            const firstA = actions[0];
            const groupDiv = document.createElement('div');
            groupDiv.className = 'action-group-card';

            const header = document.createElement('div');
            header.className = 'action-group-header';
            header.textContent = firstA.name;
            groupDiv.appendChild(header);

            const btnsDiv = document.createElement('div');
            btnsDiv.className = 'action-group-buttons grid-3';

            for (let slotIdx = 0; slotIdx < 3; slotIdx++) {
                const a = actions.find(act => act.slot_idx === slotIdx);
                if (a) {
                    const btn = document.createElement('button');
                    btn.className = 'action-btn mini';
                    btn.dataset.text = Tooltips.getEffectiveActionText(a);
                    btn.innerHTML = getActionLabel(a, true);
                    btn.onclick = () => { if (window.doAction) window.doAction(a.id); };
                    btnsDiv.appendChild(btn);
                } else {
                    const spacer = document.createElement('div');
                    spacer.className = 'action-btn-spacer';
                    btnsDiv.appendChild(spacer);
                }
            }
            groupDiv.appendChild(btnsDiv);
            listDiv.appendChild(groupDiv);
        });

        // Abilities
        abilityActions.forEach(a => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.dataset.text = Tooltips.getEffectiveActionText(a);
            btn.innerHTML = getActionLabel(a);
            btn.onclick = () => { if (window.doAction) window.doAction(a.id); };
            listDiv.appendChild(btn);
        });

        // Other actions
        otherActions.forEach(a => {
            const btn = document.createElement('button');
            btn.className = 'action-btn';
            btn.dataset.text = a.raw_text || a.text || "";
            btn.innerHTML = getActionLabel(a);
            btn.onclick = () => { if (window.doAction) window.doAction(a.id); };
            listDiv.appendChild(btn);
        });"""

# Replacement targets
start_marker = "// Play Grouped Actions"
end_marker = "});"  # The very last }); for otherActions

# We need to find the specific block starting with // Play Grouped Actions
# and ending after otherActions.forEach(...) });

start_pos = content.find(start_marker)
if start_pos != -1:
    # Find the end of otherActions loop
    search_from = content.find("otherActions.forEach", start_pos)
    if search_from != -1:
        end_pos = content.find(end_marker, search_from)
        if end_pos != -1:
            final_end = end_pos + len(end_marker)
            new_content = content[:start_pos] + new_logic + content[final_end:]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("Successfully refined action labels in ui_rendering.js")
        else:
            print("Could not find end of otherActions")
    else:
        print("Could not find otherActions loop")
else:
    print("Could not find start marker")
