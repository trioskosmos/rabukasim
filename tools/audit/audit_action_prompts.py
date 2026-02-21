import json
import os
import sys

# Setup path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import re

from engine.game.desc_utils import get_action_desc
from engine.game.enums import Phase


class MockPlayer:
    def __init__(self, player_id, cards_db):
        self.player_id = player_id
        # Populate with some dummy cards from DB for better descriptions
        self.hand = [int(k) for k in list(cards_db.keys())[:5]]
        self.discard = [int(k) for k in list(cards_db.keys())[5:10]]
        self.stage = [-1, -1, -1]
        self.live_zone = [int(k) for k in list(cards_db.keys())[10:13]]
        self.mulligan_selection = set()


class MockGameState:
    def __init__(self, cards_db):
        self.member_db = cards_db
        self.live_db = cards_db
        self.energy_db = {i: {"color": i % 6, "active": True} for i in range(10)}
        self.current_player = 0
        self.phase = Phase.MAIN
        self.triggered_abilities = []
        self.pending_choices = []
        self.active_player = MockPlayer(0, cards_db)
        self.inactive_player = MockPlayer(1, cards_db)

    def get_player(self, idx):
        return self.active_player if idx == 0 else self.inactive_player


EFFECT_TYPE_MAP = {
    0: "DRAW",
    1: "ADD_BLADES",
    2: "ADD_HEARTS",
    3: "REDUCE_COST",
    4: "LOOK_DECK",
    5: "RECOVER_LIVE",
    6: "BOOST_SCORE",
    7: "RECOVER_MEMBER",
    8: "BUFF_POWER",
    9: "IMMUNITY",
    10: "MOVE_MEMBER",
    11: "SWAP_CARDS",
    12: "SEARCH_DECK",
    13: "ENERGY_CHARGE",
    14: "NEGATE_EFFECT",
    15: "ORDER_DECK",
    16: "META_RULE",
    17: "SELECT_MODE",
    18: "MOVE_TO_DECK",
    19: "TAP_OPPONENT",
    20: "PLACE_UNDER",
    21: "RESTRICTION",
    22: "BATON_TOUCH_MOD",
    23: "SET_SCORE",
    24: "SWAP_ZONE",
    25: "TRANSFORM_COLOR",
    26: "REVEAL_CARDS",
    27: "LOOK_AND_CHOOSE",
    28: "CHEER_REVEAL",
    29: "ACTIVATE_MEMBER",
    30: "ADD_TO_HAND",
    31: "SET_BLADES",
    32: "SET_HEARTS",
    33: "FORMATION_CHANGE",
    34: "REPLACE_EFFECT",
    35: "TRIGGER_REMOTE",
    36: "REDUCE_HEART_REQ",
    37: "COLOR_SELECT",
    38: "MODIFY_SCORE_RULE",
    39: "PLAY_MEMBER_FROM_HAND",
    40: "TAP_MEMBER",
    41: "MOVE_TO_DISCARD",
    42: "GRANT_ABILITY",
    43: "INCREASE_HEART_COST",
    44: "REDUCE_YELL_COUNT",
    45: "PLAY_MEMBER_FROM_DISCARD",
    46: "PAY_ENERGY",
    47: "SELECT_MEMBER",
    48: "DRAW_UNTIL",
    49: "SELECT_PLAYER",
    50: "SELECT_LIVE",
    51: "REVEAL_UNTIL",
    52: "INCREASE_COST",
    53: "PREVENT_PLAY_TO_SLOT",
    54: "SWAP_AREA",
    55: "TRANSFORM_HEART",
    56: "SELECT_CARDS",
    57: "OPPONENT_CHOOSE",
    58: "PLAY_LIVE_FROM_DISCARD",
    59: "REDUCE_LIVE_SET_LIMIT",
    72: "PREVENT_ACTIVATE",
    81: "ACTIVATE_ENERGY",
    99: "FLAVOR_ACTION",
}


def generate_mermaid_flow(ab):
    raw_text = ab.get("raw_text", "")
    nodes = []
    edges = []
    node_counter = 0

    def get_id(prefix):
        nonlocal node_counter
        node_counter += 1
        return f"{prefix}{node_counter}"

    # Start with trigger
    start_id = "Start"
    nodes.append(f"{start_id}([Trigger])")
    current_parents = [start_id]

    # helper to add effect nodes recursively
    def add_effects(effect_list, parents, branch_label=None):
        nonlocal nodes, edges
        prev_parents = parents

        for eff in effect_list:
            etype = eff.get("effect_type", -1)
            ename = EFFECT_TYPE_MAP.get(etype, f"Effect_{etype}")
            eff_id = get_id("Eff")

            nodes.append(f"{eff_id}[{ename}]")
            for p in prev_parents:
                edge_label = f' -- "{branch_label}" --> ' if branch_label else " --> "
                edges.append(f"{p}{edge_label}{eff_id}")

            branch_label = None  # Only first node in branch gets the label
            prev_parents = [eff_id]

            # Handle SELECT_MODE branching
            if etype == 17:  # SELECT_MODE
                options = eff.get("params", {}).get("options", [])
                modal_options = eff.get("modal_options", [])

                terminal_nodes = []
                for j, opt_effects in enumerate(modal_options):
                    opt_label = options[j] if j < len(options) else f"Option {j + 1}"
                    # If opt_effects is empty, just point to an end node or placeholder
                    if not opt_effects:
                        placeholder_id = get_id("Opt")
                        nodes.append(f"{placeholder_id}[{opt_label}]")
                        edges.append(f'{eff_id} -- "{opt_label}" --> {placeholder_id}')
                        terminal_nodes.append(placeholder_id)
                    else:
                        branch_ends = add_effects(opt_effects, [eff_id], branch_label=opt_label)
                        terminal_nodes.extend(branch_ends)

                return terminal_nodes  # Entire branch group ends here

        return prev_parents

    # 1. Costs
    for i, cost in enumerate(ab.get("costs", [])):
        cost_type_int = cost.get("type", -1)
        # AbilityCostType mapping (approx)
        ctype_name = f"Cost_{cost_type_int}"
        if cost_type_int == 1:
            ctype_name = "PAY_ENERGY"
        elif cost_type_int == 2:
            ctype_name = "TAP_SELF"
        elif cost_type_int == 3:
            ctype_name = "DISCARD_HAND"
        elif cost_type_int == 5:
            ctype_name = "SACRIFICE_SELF"

        is_optional = cost.get("is_optional", False)
        cost_id = get_id("Cost")

        if is_optional:
            nodes.append(f"{cost_id}{{{ctype_name}?}}")
            for p in current_parents:
                edges.append(f"{p} --> {cost_id}")

            skip_id = get_id("Skip")
            nodes.append(f"{skip_id}([End])")
            edges.append(f'{cost_id} -- "No" --> {skip_id}')
            current_parents = [f"{cost_id}"]
            # Edge label "Yes" will be added by next node
        else:
            nodes.append(f"{cost_id}[{ctype_name}]")
            for p in current_parents:
                edges.append(f"{p} --> {cost_id}")
            current_parents = [cost_id]

    # 2. Effects
    final_parents = add_effects(ab.get("effects", []), current_parents)

    # End
    end_id = "End"
    nodes.append(f"{end_id}([End])")
    for p in final_parents:
        edges.append(f"{p} --> {end_id}")

    mermaid = "```mermaid\ngraph TD\n"
    for n in nodes:
        mermaid += f"    {n}\n"
    for e in edges:
        mermaid += f"    {e}\n"
    mermaid += "```\n"
    return mermaid, bool(node_counter > 2)  # Returns True if it has more than just Start/End


def audit_prompts():
    compiled_path = os.path.join(PROJECT_ROOT, "data", "cards_compiled.json")
    output_path = os.path.join(PROJECT_ROOT, "docs", "audit_action_prompts.md")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if not os.path.exists(compiled_path):
        print(f"Error: {compiled_path} not found. Please run individual compiler or verify data path.")
        return

    with open(compiled_path, "r", encoding="utf-8") as f:
        compiled_data = json.load(f)

    member_db = compiled_data.get("member_db", {})
    live_db = compiled_data.get("live_db", {})

    # Combined DB for the mock GS
    all_cards_db = {}
    all_cards_db.update(member_db)
    all_cards_db.update(live_db)

    # Serializer strings for modal headers (parity with rust_serializer.py)
    MODAL_HEADERS = {
        "jp": {
            "SELECT_COLOR": "ピースの色を選択してください",
            "SELECT_MODE": "モードを選択してください",
            "SELECT_SUCCESS_LIVE": "獲得するライブカードを1枚選んでください",
            "TARGET_OPPONENT_MEMBER": "相手のメンバーを選択してください",
            "SELECT_FROM_LIST": "選択肢を選んでください",
            "SELECT_FROM_DISCARD": "控え室から選択してください",
            "SELECT_STAGE": "メンバーを選択してください",
            "SELECT_FROM_HAND": "手札から選択してください",
            "ORDER_DECK": "デッキの順番を選んでください",
            "GENERIC": "選択してください",
        },
        "en": {
            "SELECT_COLOR": "Select a Color",
            "SELECT_MODE": "Select a Mode",
            "SELECT_SUCCESS_LIVE": "Select a Live card to acquire",
            "TARGET_OPPONENT_MEMBER": "Select an Opponent Member",
            "SELECT_FROM_LIST": "Choose an option",
            "SELECT_FROM_DISCARD": "Select from Discard",
            "SELECT_STAGE": "Select a Member on Stage",
            "SELECT_FROM_HAND": "Select from Hand",
            "ORDER_DECK": "Choose deck order",
            "GENERIC": "Make a selection",
        },
    }

    doc_header = """# Action Bar Prompt Audit Report

> [!IMPORTANT]
> This report is auto-generated by [audit_action_prompts.py](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/tools/audit/audit_action_prompts.py).
> Manual edits to this file will be overwritten next time the script runs.

## Overview
This document serves as a visual audit for all action bar prompts and ability resolution flows in the game. It ensures consistency in localized text across Japanese and English.

## Visualized Components
- **Action Button**: The primary button text appearing on the action bar (e.g., `[Act] Draw 1 (Left)`).
- **Resolution Flowchart**: Mermaid diagram showing the logic path (trun, cost checks, branching).
- **Resolution Details**: Specific labels for modals and choice listings.

---
"""
    report = doc_header

    gs = MockGameState(all_cards_db)

    # Sort all card entries by card_no (CID)
    all_entries = []
    for cid_int, data in member_db.items():
        all_entries.append((data.get("card_no", str(cid_int)), data))
    for cid_int, data in live_db.items():
        all_entries.append((data.get("card_no", str(cid_int)), data))

    all_entries.sort(key=lambda x: x[0])

    # Realistic mocks from DB
    real_cards = []
    for cid_int, data in list(all_cards_db.items())[:10]:
        cname = data.get("name", "Member")
        cno = data.get("card_no", "??")
        real_cards.append(f"{cname} ({cno})")

    if not real_cards:
        real_cards = ["Member A (LL-001)", "Member B (LL-002)"]

    for cid, card_data in all_entries:
        name = card_data.get("name", "Unknown")
        report += f"## {cid}: {name}\n"
        report += f"**Original Japanese:**\n{card_data.get('original_text', 'N/A')}\n\n"

        abilities = card_data.get("abilities", [])
        if not abilities:
            report += "*No explicit triggers/abilities found in compiled logic.*\n\n"
            report += "---\n\n"
            continue

        for i, ab in enumerate(abilities):
            raw_text = ab.get("raw_text", "")
            report += f"### Ability {i + 1}\n"
            report += f"**Logic:** `{raw_text}`\n\n"

            # Flowchart
            report += "**Resolution Flowchart:**\n"
            flow_mermaid, is_interactive = generate_mermaid_flow(ab)
            report += flow_mermaid
            report += "\n"

            if is_interactive:
                report += "> [!NOTE]\n"
                report += "> **Interactive**: This ability contains at least one suspend point (choice/cost).\n\n"
            else:
                report += "> [!TIP]\n"
                report += "> **Automatic**: This ability resolves immediately without user input.\n\n"

            # 1. Activation Button
            card_id_int = int(card_data.get("card_id", 0))
            gs.active_player.stage[0] = card_id_int
            action_id = 200 + 0 * 10 + i
            btn_main_en = get_action_desc(action_id, gs, lang="en")
            btn_main_jp = get_action_desc(action_id, gs, lang="jp")

            report += "**Action Button:**\n"
            if btn_main_en != f"Action {action_id}":
                report += f"- EN: `{btn_main_en}`\n"
                report += f"- JP: `{btn_main_jp}`\n\n"
            else:
                report += "- *(Auto-triggered or Passive)*\n\n"

            # 2. Choice Resolution Flow
            choices = []

            # Extract Mode Options if any
            mode_options = re.findall(r"OPTION: ([^|]+)", raw_text)
            if not mode_options:
                mode_options = ["Option A", "Option B"]

            def scan_effects(effects):
                for eff in effects:
                    etype = eff.get("effect_type", -1)
                    if etype == 17:  # SELECT_MODE
                        choices.append(("SELECT_MODE", mode_options))
                    elif etype == 37:  # COLOR_SELECT
                        choices.append(("SELECT_COLOR", ["赤", "青", "緑", "黄", "紫", "ピンク"]))
                    elif etype in [27, 28, 29, 30]:  # LOOK_AND_CHOOSE variants
                        choices.append(("SELECT_FROM_LIST", real_cards[:3]))
                    elif etype == 7:  # RECOVER_MEMBER (Discard)
                        choices.append(("SELECT_FROM_DISCARD", [real_cards[0]]))
                    elif etype in [19, 40]:  # TARGET_OPPONENT_MEMBER / TAP_MEMBER
                        choices.append(("TARGET_OPPONENT_MEMBER", []))
                    elif etype == 41:  # MOVE_TO_DISCARD (from hand, explicit select)
                        choices.append(("SELECT_FROM_HAND", [real_cards[1]]))

            scan_effects(ab.get("effects", []))

            # Also check costs for selections
            is_optional = False
            for cost in ab.get("costs", []):
                ctype = cost.get("type", -1)
                if cost.get("is_optional"):
                    is_optional = True
                if ctype == 3:  # DISCARD_HAND
                    choices.append(("SELECT_FROM_HAND", ["[Hand Card]"]))
                elif ctype == 45:  # PLAY_MEMBER_FROM_DISCARD
                    choices.append(("SELECT_FROM_DISCARD", ["[Discarded Card]"]))

            if choices:
                report += "**Resolution Details (Modal + Buttons):**\n\n"
                processed_ctypes = set()
                for ctype, mocks in choices:
                    if ctype in processed_ctypes:
                        continue
                    processed_ctypes.add(ctype)

                    header_en = MODAL_HEADERS["en"].get(ctype, MODAL_HEADERS["en"]["GENERIC"])
                    header_jp = MODAL_HEADERS["jp"].get(ctype, MODAL_HEADERS["jp"]["GENERIC"])

                    report += f"#### Choice: {ctype}\n"
                    report += f"- **Modal Header (EN):** `{header_en}`\n"
                    report += f"- **Modal Header (JP):** `{header_jp}`\n"

                    # Get button labels for this choice
                    params = {"source_member": name, "options": mocks, "cards": [1, 2], "is_optional": is_optional}
                    gs.pending_choices = [(ctype, params)]

                    btn_ids = []
                    if ctype == "SELECT_MODE":
                        btn_ids = list(range(570, 570 + len(mocks)))
                    elif ctype == "SELECT_COLOR":
                        btn_ids = [580, 581, 582, 583, 584, 585]
                    elif ctype == "TARGET_OPPONENT_MEMBER":
                        btn_ids = [600, 601, 602]
                    elif ctype == "SELECT_FROM_LIST":
                        btn_ids = [600, 601]
                    elif ctype == "SELECT_FROM_DISCARD":
                        btn_ids = [600]
                    elif ctype == "SELECT_FROM_HAND":
                        btn_ids = [500, 501]
                    elif ctype == "ORDER_DECK":
                        btn_ids = [600, 601]

                    # Add Confirm/Skip for optional choices
                    if is_optional:
                        btn_ids.append(0)

                    btn_labels_en = []
                    btn_labels_jp = []
                    for bid in btn_ids:
                        btn_labels_en.append(get_action_desc(bid, gs, lang="en"))
                        btn_labels_jp.append(get_action_desc(bid, gs, lang="jp"))

                    report += "- **Button Labels:**\n"
                    for en, jp in zip(btn_labels_en, btn_labels_jp):
                        report += f"  - EN: `{en}` | JP: `{jp}`\n"
                    report += "\n"

        report += "---\n\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Audit report generated: {output_path}")


if __name__ == "__main__":
    audit_prompts()
