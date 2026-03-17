file_path = r"frontend\web_ui\js\ui_rendering.js"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_logic = """        Object.keys(playActionsByHand).forEach(hIdx => {
            const actions = playActionsByHand[hIdx];
            const firstA = actions[0];
            const groupDiv = document.createElement('div');
            groupDiv.className = 'action-group-card';

            const header = document.createElement('div');
            header.className = 'action-group-header';
            header.textContent = firstA.name; // Generic name is already provided by serialization
            groupDiv.appendChild(header);

            const btnsDiv = document.createElement('div');
            btnsDiv.className = 'action-group-buttons grid-3';

            // Fixed 3-slot layout
            for (let slotIdx = 0; slotIdx < 3; slotIdx++) {
                const a = actions.find(act => act.slot_idx === slotIdx);
                if (a) {
                    const btn = document.createElement('button');
                    btn.className = 'action-btn mini';
                    btn.dataset.text = Tooltips.getEffectiveActionText(a);

                    const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;
                    let label = `${energyIcon}${a.cost !== undefined ? a.cost : (a.base_cost || 0)}`;

                    const isBaton = (a.name && (a.name.includes('Baton') || a.name.includes('バトン')));
                    if (isBaton) label += ' 🔄';

                    btn.innerHTML = label;
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
        });"""

# Find the block starting with Object.keys(playActionsByHand).forEach and ending with });
start_marker = "Object.keys(playActionsByHand).forEach"
start_pos = content.find(start_marker)

if start_pos != -1:
    # Find the next }); after the start position that belongs to this block
    # We'll look for the first }); that has the correct indentation or follow the structure
    # A simple way is to find the next }); and check if it's the right one.
    # Given the file structure, it should be the one ending the loop.

    # Let's find the closing brace. It spans from 605 to 647.
    # We'll find the next }); after the start_pos.
    end_marker = "});"
    # The block ends after the last }); of the forEach.
    # Finding the correct end is tricky if there are nested ones, but there aren't many here.
    # Let's use a more unique anchor for the end if possible.

    # We know line 647 is the });
    # Let's find the first }); followed by a newline and // Abilities or something.

    search_end = content.find(end_marker, start_pos)
    # The forEach has a nested forEach (actions.forEach), so the first }); will close the inner one.
    second_end = content.find(end_marker, search_end + 3)

    if second_end != -1:
        final_end = second_end + 3
        new_content = content[:start_pos] + new_logic + content[final_end:]
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("Successfully replaced member placement block.")
    else:
        print("Could not find second end marker.")
else:
    print("Could not find start marker.")
