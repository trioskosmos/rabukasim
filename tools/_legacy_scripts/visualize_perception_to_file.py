import os
import sys

import numpy as np

sys.path.append(os.getcwd())

from engine.game.data_loader import CardDataLoader


def clean_len(val):
    if not val:
        return 0.0
    try:
        return float(len(val))
    except:
        return 0.0


def get_val(obj, key, default=0):
    if hasattr(obj, key):
        return getattr(obj, key)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def get_vec(card):
    # IMAX PRO 80-dim Stride
    v = np.zeros(80, dtype=np.float32)

    is_live = hasattr(card, "score") or "score" in (card if isinstance(card, dict) else {})

    # 0-19: Stats
    v[0] = float(get_val(card, "cost", 1 if not is_live else 0))
    v[1] = float(get_val(card, "blades", 0))

    if is_live:
        v[2] = float(get_val(card, "score", 0))
        # Live Reqs: 12-18
        reqs = get_val(card, "required_hearts", [])
        for r in range(len(reqs)):
            v[12 + r] = float(reqs[r])
    else:
        h = get_val(card, "hearts", 0)
        if hasattr(card, "total_hearts"):
            v[2] = float(card.total_hearts())
        elif isinstance(h, list):
            v[2] = float(sum(h))
        else:
            v[2] = float(h)

    color_map = {"PINK": 0, "RED": 1, "YELLOW": 2, "GREEN": 3, "BLUE": 4, "PURPLE": 5, "NONE": 6, "ALL": 7}
    color_obj = get_val(card, "color", None)
    color_name = "NONE"
    if color_obj:
        if isinstance(color_obj, str):
            color_name = color_obj
        elif hasattr(color_obj, "name"):
            color_name = color_obj.name
    v[3] = float(color_map.get(color_name, 6))

    v[4] = clean_len(get_val(card, "vol_icons", []))
    v[5] = clean_len(get_val(card, "draw_icons", []))
    v[8] = v[4]
    v[9] = v[5]  # Redundant legacy? No, just keep safe.

    v[7] = 2.0 if is_live else 1.0  # Type
    v[10] = v[7]

    # Traits (Index 11)
    mask = 0
    groups = get_val(card, "groups", [])
    units = get_val(card, "units", [])
    for g in groups:
        val = int(g.value) if hasattr(g, "value") else int(g)
        mask |= 1 << (val % 20)
    for u in units:
        val = int(u.value) if hasattr(u, "value") else int(u)
        mask |= 1 << ((val % 20) + 5)
    v[11] = float(mask)

    # --- ABILITY PACKING (Fixed Geography) ---
    # 20-35: Ab1 (16)
    # 36-47: Ab2 (12)
    # 48-59: Ab3 (12)
    # 60-71: Ab4 (12)

    abs_list = get_val(card, "abilities", [])
    trig_map = {"ON_PLAY": 1, "ON_LIVE_START": 2, "ON_TURN_END": 3, "ACTIVATED": 4}

    def pack_ab(ab, base, has_opts=False):
        if not ab:
            return
        t_obj = get_val(ab, "trigger", "NONE")
        t_name = t_obj if isinstance(t_obj, str) else t_obj.name
        v[base] = float(trig_map.get(t_name, 0))

        conds = get_val(ab, "conditions", [])
        if conds:
            v[base + 1] = float(get_val(conds[0], "type", 0))
            params = get_val(conds[0], "params", {})
            v[base + 2] = float(params.get("value", 0) if isinstance(params, dict) else 0)

        effs = get_val(ab, "effects", [])
        eff_start = base + 3
        if has_opts:
            eff_start = base + 9
            if effs:
                m_opts = get_val(effs[0], "modal_options", [])
                if len(m_opts) > 0 and len(m_opts[0]) > 0:
                    o = m_opts[0][0]
                    v[base + 3], v[base + 4], v[base + 5] = (
                        float(get_val(o, "effect_type", 0)),
                        float(get_val(o, "value", 0)),
                        float(get_val(o, "target", 0)),
                    )
                if len(m_opts) > 1 and len(m_opts[1]) > 0:
                    o = m_opts[1][0]
                    v[base + 6], v[base + 7], v[base + 8] = (
                        float(get_val(o, "effect_type", 0)),
                        float(get_val(o, "value", 0)),
                        float(get_val(o, "target", 0)),
                    )

        for k in range(min(len(effs), 3)):
            e = effs[k]
            off = eff_start + k * 3
            v[off] = float(get_val(e, "effect_type", 0))
            v[off + 1] = float(get_val(e, "value", 0))
            v[off + 2] = float(get_val(e, "target", 0))

    if len(abs_list) > 0:
        pack_ab(abs_list[0], 20, has_opts=True)
    if len(abs_list) > 1:
        pack_ab(abs_list[1], 36)
    if len(abs_list) > 2:
        pack_ab(abs_list[2], 48)
    if len(abs_list) > 3:
        pack_ab(abs_list[3], 60)

    v[79] = 1.0  # Simulate Hand Location for viz

    return v


def format_card_output(card, title=""):
    lines = []
    lines.append(f"\n{'=' * 20} {title} {'=' * 20}")
    lines.append(f"ID: {card.card_no} | Name: {card.name}")

    vec = get_vec(card)
    lines.append("\n[IMAX PRO VISION - Stride 80]")

    # Generate labels
    lbl = {}
    # Meta
    lbl[0] = "Cost"
    lbl[1] = "Blade"
    lbl[2] = "Heart"
    lbl[3] = "Color"
    lbl[4] = "Vol"
    lbl[5] = "Draw"
    lbl[7] = "Type"
    lbl[10] = "Type2"
    lbl[11] = "Trait"
    lbl[12] = "Req1"
    lbl[13] = "Req2"
    lbl[14] = "Req3"
    lbl[15] = "Req4"
    lbl[79] = "LOC"

    # Ab 1
    base = 20
    lbl[base] = "T1"
    lbl[base + 1] = "C1T"
    lbl[base + 2] = "C1V"
    lbl[base + 3] = "O1T"
    lbl[base + 4] = "O1V"
    lbl[base + 5] = "O1Tg"
    lbl[base + 9] = "E1.1T"

    # Ab 2
    base = 36
    lbl[base] = "T2"
    lbl[base + 1] = "C2T"
    lbl[base + 2] = "C2V"
    lbl[base + 3] = "E2.1T"

    # Grid Print (5 rows of 16 = 80)
    for row in range(5):
        lines.append("-" * 65)
        for i in range(row * 16, (row + 1) * 16):
            val = vec[i]
            if val == 0:
                continue  # Skip zeros for cleaner report? No, structure matters.
            # Actually, let's print all but minimize noise
            label = lbl.get(i, f"idx{i:02d}")
            active = " <" if val != 0 else "  "
            lines.append(f"  {i:02d} {label:<6}: {val:>10.2f}{active}")

    return "\n".join(lines)


def run_vis():
    loader = CardDataLoader("data/cards_compiled.json")
    members, lives, _ = loader.load()
    output = ["IMAX AI PERCEPTION REPORT\nStride 64 | ObsDim 8192 | 4 Ability Slots\n"]

    # Find a complex card with >1 ability
    complex_card = next((m for m in members.values() if len(getattr(m, "abilities", [])) > 1), None)
    if complex_card:
        output.append(format_card_output(complex_card, "COMPLEX MEMBER"))

    # Ai Scream
    scream = next((l for l in lives.values() if l.card_no == "LL-PR-004-PR"), None)
    if scream:
        output.append(format_card_output(scream, "AI SCREAM"))

    with open("docs/ai_card_vision.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print("IMAX Report Generated.")


if __name__ == "__main__":
    run_vis()
