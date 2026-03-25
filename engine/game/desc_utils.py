from __future__ import annotations

from engine.game.enums import Phase


def get_v(obj, key, default=None):
    """Safely get a value from a dictionary or an object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def get_ability_summary(ab, lang="jp"):
    """Generate a compact human-readable summary of an ability."""
    if not ab:
        return ""

    trigger = int(get_v(ab, "trigger", 0))
    trigger_map = {
        1: "Play",
        2: "LiveStart",
        3: "Success",
        4: "TurnStart",
        5: "TurnEnd",
        6: "Constant",
        7: "Act",
    }
    trigger_name = trigger_map.get(trigger, "")

    effects = get_v(ab, "effects", [])
    if not effects:
        raw = get_v(ab, "raw_text", "").split("\n")[0][:25]
        return f"[{trigger_name}] {raw}".strip() if trigger_name else raw

    eff = effects[0]
    effect_type = int(get_v(eff, "effect_type", -1))
    value = get_v(eff, "value", 0)
    target = int(get_v(eff, "target", 0))

    target_map = {1: "Player", 2: "Opponent", 3: "All", 4: "Self", 12: "OppMem"}
    effect_map = {
        0: "Draw",
        1: "Blades+",
        2: "Hearts+",
        3: "Cost-",
        4: "LookDeck",
        5: "RecLive",
        6: "Score+",
        7: "RecMem",
        8: "Power+",
        9: "Immune",
        10: "Move",
        11: "Swap",
        12: "Search",
        13: "Energy+",
        15: "SortDeck",
        17: "Choice",
        19: "TapOpp",
        20: "PutUnder",
        27: "PickDeck",
        30: "AddToHand",
        31: "SetBlade",
        37: "ColorChoice",
        38: "ScoreMod",
        41: "ToDiscard",
        44: "Yell-",
        46: "Pay",
        48: "DrawUntil",
        81: "ActEnergy",
    }

    parts = []
    if trigger_name:
        parts.append(trigger_name)

    target_name = target_map.get(target, "")
    if target_name and target not in (0, 4):
        parts.append(target_name)

    parts.append(effect_map.get(effect_type, f"Effect{effect_type}"))
    if isinstance(value, int) and value > 0:
        parts.append(str(value))

    return " ".join(parts)


def get_action_desc(a, gs, lang="jp", text=None):
    """Generate a simple action description."""
    if gs is None:
        return f"Action {a}"

    ability_prefix = ""
    if text:
        clean_text = text.split("\n")[0].strip()
        if len(clean_text) > 30:
            clean_text = clean_text[:27] + "..."
        ability_prefix = f"[{clean_text}] "

    if isinstance(a, str):
        return f"{ability_prefix}{a}".strip()

    if hasattr(gs, "phase"):
        _ = gs.phase

    return f"{ability_prefix}Action {a}".strip()