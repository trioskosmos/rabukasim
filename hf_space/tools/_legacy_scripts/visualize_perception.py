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


def get_vec(card):
    # Brutal type safety
    try:
        c = float(getattr(card, "cost", 0))
    except:
        c = 0.0

    try:
        b = float(getattr(card, "blades", 0))
    except:
        b = 0.0

    try:
        h = float(getattr(card, "hearts", 0))
    except:
        h = 0.0

    v = np.zeros(16, dtype=np.float32)
    v[0] = c
    v[1] = b
    v[2] = h

    color = getattr(card, "color", None)
    c_name = color.name if color else "NONE"
    color_map = {"PINK": 0, "RED": 1, "YELLOW": 2, "GREEN": 3, "BLUE": 4, "PURPLE": 5, "NONE": 6, "ALL": 7}
    v[3] = float(color_map.get(c_name, 6))

    v[7] = 0.0 if hasattr(card, "role") else 1.0

    v[8] = clean_len(getattr(card, "vol_icons", []))
    v[9] = clean_len(getattr(card, "draw_icons", []))

    abilities = getattr(card, "abilities", [])
    # Ensure abilities is iterable
    try:
        iter(abilities)
    except:
        abilities = []

    if abilities:
        ab = abilities[0]
        trig = getattr(ab, "trigger", None)
        t_name = trig.name if trig else "NONE"
        trig_map = {"ON_PLAY": 1, "ON_LIVE_START": 2, "ON_TURN_END": 3, "ACTIVATED": 4}
        v[10] = float(trig_map.get(t_name, 0))

        effects = getattr(ab, "effects", [])
        # Ensure effects is iterable
        try:
            iter(effects)
        except:
            effects = []

        if effects:
            eff = effects[0]
            v[11] = float(abs(hash(eff.effect_type.name)) % 50)
            v[12] = float(eff.value)
            v[13] = float(abs(hash(eff.target.name)) % 10)

    traits = getattr(card, "traits", [])
    try:
        iter(traits)
    except:
        traits = []

    if traits:
        v[15] = float(sum(hash(str(t)) for t in traits) % 2097152)
    return v


def visualize_card(card, title=""):
    print(f"\n{'=' * 20} {title} {'=' * 20}")
    print(f"ID: {card.card_no}")
    print(f"Name: {card.name}")
    print(f"Text: {getattr(card, 'raw_text', 'N/A')}")

    vec = get_vec(card)

    print("\n[AI Vision (16-dim Normalized)]")
    labels = [
        "Cost",
        "Blade",
        "Heart",
        "Color",
        "Unused",
        "Unused",
        "Unused",
        "Type",
        "VolIcon",
        "DrawIc",
        "Trig",
        "EffTyp",
        "EffVal",
        "EffTgt",
        "Unused",
        "Trait",
    ]

    for i in range(16):
        val = vec[i]
        norm_val = val
        if i == 0:
            norm_val /= 10.0
        elif i == 1:
            norm_val /= 5.0
        elif i == 2:
            norm_val /= 5.0
        elif i == 3:
            norm_val /= 6.0

        active_marker = "<- Active" if val != 0 else ""
        print(f"  {i:02d} {labels[i]:<7}: {val:>6.1f}  ->  {norm_val:>6.3f}   {active_marker}")


def run_vis():
    print("Loading data...")
    loader = CardDataLoader("data/cards_compiled.json")
    members, lives, _ = loader.load()
    print(f"Loaded {len(members)} members, {len(lives)} lives.")

    simple = None
    for m in members.values():
        if not getattr(m, "abilities", []):
            simple = m
            break

    complex_card = None
    # Prioritize Finding a really complex one
    candidate_list = []
    for m in members.values():
        abs = getattr(m, "abilities", [])
        if abs and len(abs[0].effects) > 0:
            candidate_list.append(m)

    # sort by complexity (text length)
    candidate_list.sort(key=lambda x: len(getattr(x, "raw_text", "")), reverse=True)
    if candidate_list:
        complex_card = candidate_list[0]

    if simple:
        visualize_card(simple, "SIMPLE / VANILLA")

    if complex_card:
        visualize_card(complex_card, "COMPLEX / EFFECT")


if __name__ == "__main__":
    run_vis()
