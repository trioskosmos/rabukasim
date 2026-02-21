import json
import os
import sys
from datetime import datetime

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from engine.models.ability import TargetType
from engine.models.opcodes import Opcode

def decompile(bytecode):
    """Decompile a bytecode sequence (list of ints) into pseudocode."""
    if not bytecode:
        return ""

    instructions = [bytecode[i : i + 4] for i in range(0, len(bytecode), 4)]
    conditions = []
    effects = []
    costs = []

    for instr in instructions:
        if len(instr) < 4: continue
        op_val, val, attr, packed_slot = instr
        is_negated = False
        if op_val >= 1000:
            is_negated = True
            op_val -= 1000

        if op_val == Opcode.NOP: continue
        if op_val == Opcode.RETURN: break

        # Conditions (200-299)
        if 200 <= op_val <= 299:
            try:
                opcode_name = Opcode(op_val).name
                cond_type_name = opcode_name.replace("CHECK_", "")
                slot = packed_slot & 0x0F
                comp_val = (packed_slot >> 4) & 0x0F
                comp_map = {0: "GE", 1: "LE", 2: "GT", 3: "LT", 4: "EQ"}
                comp_str = comp_map.get(comp_val, "GE")
                params = []
                if val != 0:
                    params.append(f"MIN={val}" if comp_str == "GE" else f"VALUE={val}")
                if cond_type_name == "COUNT_GROUP":
                    from engine.models.enums import Group
                    try:
                        group_name = Group(attr).to_japanese_name()
                        params.append(f'GROUP="{group_name}"')
                    except:
                        params.append(f"GROUP_ID={attr}")
                if cond_type_name == "HAS_COLOR":
                    colors = {1: "PINK", 2: "RED", 3: "YELLOW", 4: "GREEN", 5: "BLUE", 6: "PURPLE"}
                    params.append(f"COLOR={colors.get(attr, attr)}")
                if cond_type_name == "AREA_CHECK":
                    zones = {106: "HAND", 107: "DISCARD", 108: "DECK_TOP", 112: "SUCCESS_LIVE"}
                    params.append(f"ZONE={zones.get(attr, attr)}")
                if comp_str != "GE":
                    params.append(f"COMPARE={comp_str}")
                prefix = "NOT_" if is_negated else ""
                cond_str = f"{prefix}{cond_type_name}"
                if params:
                    cond_str += " {" + ", ".join(params) + "}"
                conditions.append(cond_str)
            except ValueError:
                conditions.append(f"UNKNOWN_COND({op_val})")

        # Effects (0-99)
        elif 0 <= op_val <= 99:
            if op_val == Opcode.SWAP_CARDS and packed_slot == 1:
                costs.append(f"DISCARD_HAND({val})")
                continue
            try:
                op = Opcode(op_val)
                name = op.name
                target_map = {
                    TargetType.SELF: "SELF", TargetType.PLAYER: "PLAYER",
                    TargetType.OPPONENT: "OPPONENT", TargetType.ALL_PLAYERS: "ALL_PLAYERS",
                    TargetType.CARD_HAND: "CARD_HAND", TargetType.CARD_DISCARD: "CARD_DISCARD",
                    TargetType.MEMBER_SELF: "MEMBER_SELF", TargetType.MEMBER_OTHER: "MEMBER_OTHER",
                }
                target_str = target_map.get(packed_slot, f"TARGET_{packed_slot}")
                params = []
                is_all = (attr & 0x80) != 0
                if is_all: params.append("ALL")
                if name in ["ADD_HEARTS", "BUFF_POWER"]:
                    colors = {1: "PINK", 2: "RED", 3: "YELLOW", 4: "GREEN", 5: "BLUE", 6: "PURPLE"}
                    if (attr & 0x7F) in colors:
                        params.append(f"COLOR={colors[attr & 0x7F]}")
                
                param_str = " {" + ", ".join(params) + "}" if params else ""
                effects.append(f"{name}({val}) -> {target_str}{param_str}")
            except ValueError:
                effects.append(f"UNKNOWN_EFFECT({op_val})")

    lines = []
    if costs: lines.append(f"<span class='logic-cost'>COST:</span> {'; '.join(costs)}")
    if conditions: lines.append(f"<span class='logic-cond'>COND:</span> {', '.join(conditions)}")
    if effects: lines.append(f"<span class='logic-eff'>EFF:</span> {'; '.join(effects)}")
    return "<br>".join(lines)

def generate_report():
    print("Generating Visual Ability Audit Report...")
    
    # Load data
    with open("data/cards.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        compiled_data = json.load(f)
    with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
        manual_data = json.load(f)

    # Merge into efficient lookup
    # Map by card_no
    card_map = {}
    for c in raw_data.values():
        if not c.get("card_no"): continue
        no = c["card_no"].replace("+", "＋")
        card_map[no] = {
            "card_no": c["card_no"],
            "name": c["name"],
            "type": c.get("type", "Unknown"),
            "ability_text": c.get("ability", "N/A"),
            "img_path": c.get("_img", ""),
            "manual_pseudo": manual_data.get(c["card_no"], {}).get("pseudocode", ""),
            "abilities": []
        }

    # Add compiled data
    compiled_cards = list(compiled_data.get("member_db", {}).values()) + list(compiled_data.get("live_db", {}).values())
    
    ai_index = {}

    for c in compiled_cards:
        no = c["card_no"]
        if no in card_map:
            card_map[no]["card_id"] = c.get("card_id")
            card_map[no]["abilities"] = c.get("abilities", [])
            
            # For AI Index
            ai_index[no] = {
                "id": c.get("card_id"),
                "abilities": [
                    {
                        "raw_text": ab.get("raw_text", ""),
                        "logic": decompile(ab.get("bytecode", []))
                    } for ab in c.get("abilities", [])
                ]
            }

    # Generate HTML
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>LovecaSim Ability Audit</title>
        <style>
            body {{ font-family: sans-serif; background: #121212; color: #eee; padding: 20px; }}
            .card-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .card-table th, .card-table td {{ border: 1px solid #333; padding: 10px; vertical-align: top; }}
            .card-table th {{ background: #1a1a1a; position: sticky; top: 0; z-index: 10; }}
            .card-row:hover {{ background: #1e1e1e; }}
            .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
            .badge-member {{ background: #2196F3; }}
            .badge-live {{ background: #E91E63; }}
            .jp-text {{ font-size: 0.85em; color: #bbb; line-height: 1.4; white-space: pre-wrap; }}
            .pseudo-text {{ font-family: monospace; font-size: 0.8em; color: #fb7185; background: #2a1111; padding: 5px; border-radius: 4px; margin-top: 5px; white-space: pre-wrap; }}
            .logic-code {{ font-family: monospace; font-size: 0.9em; color: #4ade80; background: #112a1a; padding: 8px; border-radius: 4px; border: 1px solid #225a3a; margin-bottom: 5px; }}
            .logic-cost {{ color: #facc15; font-weight: bold; }}
            .logic-cond {{ color: #60a5fa; font-weight: bold; }}
            .logic-eff {{ color: #4ade80; font-weight: bold; }}
            .card-img {{ width: 80px; height: auto; border-radius: 4px; box-shadow: 0 4px 8px rgba(0,0,0,0.5); }}
            .search-box {{ width: 100%; padding: 12px; font-size: 1.1em; background: #222; border: 2px solid #444; color: white; border-radius: 8px; margin-bottom: 20px; outline: none; }}
            .search-box:focus {{ border-color: #2196F3; }}
            hr {{ border: 0; border-top: 1px solid #444; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>🎴 LovecaSim Ability Audit Report</h1>
            <div style="text-align: right;">
                <p>Generated: {gen_time}</p>
                <p>Total Cards: <b>{total_count}</b></p>
            </div>
        </div>
        <input type="text" class="search-box" id="search" placeholder="Search by name, ID, No, Text, or Logic (e.g. 'MOVE_TO_DISCARD')..." onkeyup="filter()">
        
        <table class="card-table" id="table">
            <thead>
                <tr>
                    <th>Img</th>
                    <th>ID / No</th>
                    <th>Name / Type</th>
                    <th style="width: 35%;">Source (JP & Raw Pseudo)</th>
                    <th style="width: 35%;">Compiled Logic (Bytecode -> Decompiled)</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <script>
            function filter() {{
                var input = document.getElementById("search");
                var filterValue = input.value.toUpperCase();
                var table = document.getElementById("table");
                var tr = table.getElementsByTagName("tr");
                for (var i = 1; i < tr.length; i++) {{
                    var text = tr[i].textContent.toUpperCase();
                    // Custom search logic to include attributes that might not be visible as text
                    tr[i].style.display = text.indexOf(filterValue) > -1 ? "" : "none";
                }}
            }}
        </script>
    </body>
    </html>
    """

    rows = []
    # Sort by ID
    sorted_cards = sorted(card_map.values(), key=lambda x: x.get("card_id", 999999))
    
    for c in sorted_cards:
        # Image handling
        img_src = f"../frontend/{c['img_path']}" if c['img_path'] else f"https://placehold.co/60x84?text={c['card_no']}"
        img_tag = f'<img class="card-img" src="{img_src}" onerror="this.src=\'https://placehold.co/60x84?text=?\'">'
        
        type_badge = "badge-member" if c["type"] == "メンバー" else "badge-live"
        
        # Decompile abilities
        logic_html = []
        for ab in c["abilities"]:
            decompiled = decompile(ab.get("bytecode", []))
            logic_html.append(f'<div class="logic-code">{decompiled}</div>')
        
        logic_display = "".join(logic_html) if logic_html else "<span style='color:#666'>No Compiled Abilities</span>"
        
        # Source display
        pseudo_display = f'<div class="pseudo-text">{c["manual_pseudo"]}</div>' if c["manual_pseudo"] else ""

        row = f"""
        <tr class="card-row" id="card-{c.get('card_id', 'none')}">
            <td>{img_tag}</td>
            <td>
                <b>{c.get('card_id', '???')}</b><br>
                <small style="color:#888">{c['card_no']}</small>
            </td>
            <td>
                <span class="badge {type_badge}">{c['type']}</span><br>
                <b>{c['name']}</b>
            </td>
            <td>
                <div class="jp-text">{c['ability_text']}</div>
                {pseudo_display}
            </td>
            <td>{logic_display}</td>
        </tr>
        """
        rows.append(row)

    # Save outputs
    os.makedirs("reports", exist_ok=True)
    
    # HTML Report
    final_html = html_template.format(
        gen_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_count=len(card_map),
        rows="".join(rows)
    )
    with open("reports/ability_audit_visual.html", "w", encoding="utf-8") as f:
        f.write(final_html)

    # JSON Index (AI friendly)
    with open("reports/ability_index.json", "w", encoding="utf-8") as f:
        json.dump(ai_index, f, indent=2, ensure_ascii=False)

    print(f"Success! Report saved to reports/ability_audit_visual.html")
    print(f"Success! AI Index saved to reports/ability_index.json")

if __name__ == "__main__":
    generate_report()
