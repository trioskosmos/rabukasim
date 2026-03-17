import json
import os
import re
import sys

# Ensure we can import from local modules
sys.path.append(os.getcwd())
from compiler.parser_v2 import AbilityParserV2

# --- Mappings from engine/models/ability.py and engine/game/fast_logic.py ---

TRIGGER_MAP = {
    0: "NONE",
    1: "ON_PLAY",
    2: "ON_LIVE_START",
    3: "ON_LIVE_SUCCESS",
    4: "TURN_START",
    5: "TURN_END",
    6: "CONSTANT",
    7: "ACTIVATED",
    8: "ON_LEAVES",
    9: "ON_REVEAL",
}

TARGET_MAP = {
    0: "SELF",
    1: "PLAYER",
    2: "OPPONENT",
    3: "ALL_PLAYERS",
    4: "MEMBER_SELF",
    5: "MEMBER_OTHER",
    6: "CARD_HAND",
    7: "CARD_DISCARD",
    8: "CARD_DECK_TOP",
    9: "OPPONENT_HAND",
    10: "MEMBER_SELECT",
    11: "MEMBER_NAMED",
    12: "OPPONENT_MEMBER",
    13: "PLAYER_SELECT",
}

EFFECT_MAP = {
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
    99: "FLAVOR_ACTION",
}

CONDITION_MAP = {
    0: "NONE",
    1: "TURN_1",
    2: "HAS_MEMBER",
    3: "HAS_COLOR",
    4: "COUNT_STAGE",
    5: "COUNT_HAND",
    6: "COUNT_DISCARD",
    7: "IS_CENTER",
    8: "LIFE_LEAD",
    9: "COUNT_GROUP",
    10: "GROUP_FILTER",
    11: "OPPONENT_HAS",
    12: "SELF_IS_GROUP",
    13: "MODAL_ANSWER",
    14: "COUNT_ENERGY",
    15: "HAS_LIVE_CARD",
    16: "COST_CHECK",
    17: "RARITY_CHECK",
    18: "HAND_HAS_NO_LIVE",
    19: "COUNT_SUCCESS_LIVE",
    20: "OPPONENT_HAND_DIFF",
    21: "SCORE_COMPARE",
    22: "HAS_CHOICE",
    23: "OPPONENT_CHOICE",
    24: "COUNT_HEARTS",
    25: "COUNT_BLADES",
    26: "OPPONENT_ENERGY_DIFF",
    27: "HAS_KEYWORD",
    28: "DECK_REFRESHED",
    29: "HAS_MOVED",
    30: "HAND_INCREASED",
    31: "COUNT_LIVE_ZONE",
    231: "BATON_PASS_CHECK",
}

COST_MAP = {
    0: "NONE",
    1: "ENERGY",
    2: "TAP_SELF",
    3: "DISCARD_HAND",
    4: "RETURN_HAND",
    5: "SACRIFICE_SELF",
    6: "REVEAL_HAND_ALL",
    7: "SACRIFICE_UNDER",
    8: "DISCARD_ENERGY",
    9: "REVEAL_HAND",
}


def format_params(params):
    if not params:
        return ""

    # Clean up standard params
    out = []

    # Group/Unit
    if "group" in params:
        out.append(f'GROUP="{params["group"]}"')
    if "groups" in params:
        out.append(f"GROUPS={json.dumps(params['groups'], ensure_ascii=False)}")
    if "unit" in params:
        out.append(f'UNIT="{params["unit"]}"')

    # Names
    if "names" in params:
        out.append(f"NAMES={json.dumps(params['names'], ensure_ascii=False)}")

    # Duration
    if "until" in params:
        out.append(f"UNTIL={params['until'].upper()}")

    # Zones
    if "from" in params:
        out.append(f"FROM={params['from'].upper()}")
    if "to" in params:
        out.append(f"TO={params['to'].upper()}")
    if "target" in params and isinstance(params["target"], str):
        out.append(f"TARGET={params['target'].upper()}")

    # Filters
    if "min" in params:
        out.append(f"MIN={params['min']}")
    if "max" in params:
        out.append(f"MAX={params['max']}")
    if "cost_max" in params:
        out.append(f"COST_MAX={params['cost_max']}")
    if "cost_min" in params:
        out.append(f"COST_MIN={params['cost_min']}")

    # Multipliers
    if params.get("has_multiplier"):
        m_types = []
        if params.get("per_member"):
            m_types.append("MEMBER")
        if params.get("per_energy"):
            m_types.append("ENERGY")
        if params.get("per_live"):
            m_types.append("LIVE")
        if m_types:
            out.append(f"MULTIPLIER={'|'.join(m_types)}")
        else:
            out.append("MULTIPLIER=YES")

    # Meta Rule Types
    if "type" in params:
        out.append(f"TYPE={params['type'].upper()}")

    # If we handled everything, return joined string
    # If there are leftovers, append raw JSON for safety
    known_keys = {
        "group",
        "groups",
        "unit",
        "names",
        "until",
        "from",
        "to",
        "target",
        "min",
        "max",
        "cost_max",
        "cost_min",
        "has_multiplier",
        "per_member",
        "per_energy",
        "per_live",
        "type",
        "both_players",
        "all",
    }

    leftovers = {k: v for k, v in params.items() if k not in known_keys}
    if leftovers:
        out.append(json.dumps(leftovers))

    if params.get("both_players"):
        out.append("BOTH_PLAYERS")
    if params.get("all"):
        out.append("ALL")

    return " {" + ", ".join(out) + "}"


def generate_pseudocode(ability_data):
    parts = []

    # Trigger
    trigger_id = ability_data.get("trigger", 0)
    trigger_name = TRIGGER_MAP.get(trigger_id, f"UNKNOWN({trigger_id})")
    parts.append(f"TRIGGER: {trigger_name}")

    # Once per turn
    if ability_data.get("is_once_per_turn"):
        parts.append("(Once per turn)")

    # Costs
    costs = ability_data.get("costs", [])
    if costs:
        cost_strs = []
        for c in costs:
            ctype = c.get("type")
            cval = c.get("value", 0)
            cname = COST_MAP.get(ctype, f"UNKNOWN({ctype})")
            opt = " (Optional)" if c.get("is_optional") else ""
            params = c.get("params", {})
            param_str = format_params(params)
            cost_strs.append(f"{cname}({cval}){param_str}{opt}")
        parts.append(f"COST: {', '.join(cost_strs)}")

    # Conditions
    conditions = ability_data.get("conditions", [])
    if conditions:
        cond_strs = []
        for c in conditions:
            ctype = c.get("type")
            cname = CONDITION_MAP.get(ctype, f"UNKNOWN({ctype})")
            neg = "NOT " if c.get("is_negated") else ""
            params = c.get("params", {})
            param_str = format_params(params)
            cond_strs.append(f"{neg}{cname}{param_str}")
        parts.append(f"CONDITION: {', '.join(cond_strs)}")

    # Effects
    effects = ability_data.get("effects", [])
    if effects:
        eff_strs = []
        for e in effects:
            etype = e.get("effect_type")
            ename = EFFECT_MAP.get(etype, f"UNKNOWN({etype})")
            eval_val = e.get("value", 0)
            etarget = e.get("target", 0)
            etarget_name = TARGET_MAP.get(etarget, f"UNKNOWN({etarget})")
            params = e.get("params", {})
            param_str = format_params(params)
            opt = " (Optional)" if e.get("is_optional") else ""

            # Modal options
            modal_str = ""
            if e.get("modal_options"):
                modal_str = "\n    Options:"
                for i, opt_list in enumerate(e["modal_options"]):
                    opt_descs = []
                    for sub_eff in opt_list:
                        sub_ename = EFFECT_MAP.get(sub_eff.get("effect_type"), "UNK")
                        sub_val = sub_eff.get("value")
                        sub_target = TARGET_MAP.get(sub_eff.get("target", 0), "UNK")
                        sub_params = format_params(sub_eff.get("params", {}))
                        opt_descs.append(f"{sub_ename}({sub_val})->{sub_target}{sub_params}")
                    modal_str += f"\n      {i + 1}: {', '.join(opt_descs)}"

            eff_strs.append(f"{ename}({eval_val}) -> {etarget_name}{param_str}{opt}{modal_str}")
        parts.append(f"EFFECT: {'; '.join(eff_strs)}")

    # Ability Modal Options (Legacy style - usually handled inside effects now but kept for safety)
    modal_options = ability_data.get("modal_options", [])
    if modal_options:
        parts.append("MODAL OPTIONS (Legacy):")
        for i, opt_list in enumerate(modal_options):
            opt_descs = []
            for sub_eff in opt_list:
                sub_ename = EFFECT_MAP.get(sub_eff.get("effect_type"), "UNK")
                sub_val = sub_eff.get("value")
                opt_descs.append(f"{sub_ename}({sub_val})")
            parts.append(f"  {i + 1}: {', '.join(opt_descs)}")

    return "\n".join(parts)


def process_faqs(card_faqs, card_abilities_map):
    """Enhance FAQs with pseudocode for discussed abilities or rulings."""
    processed = []
    parser = AbilityParserV2()

    # Common ruling patterns
    RULING_PATTERNS = {
        "TIMING": [r"まで", r"終了時", r"期限", r"いつ", r"タイミング", r"フェイズ"],
        "TARGETING": [r"選ぶ", r"まで", r"対象", r"枚数", r"人", r"組み合わせ"],
        "COST": [r"コスト", r"支払", r"。払"],
        "RESOLUTION": [r"解決", r"処理", r"効果", r"できない", r"できますか", r"？"],
        "INTERACTION": [r"別の", r"カード", r"含む", r"名称"],
    }

    for faq in card_faqs:
        new_faq = faq.copy()
        question = faq.get("question", "")
        answer = faq.get("answer", "")

        ruling_pcode = ""

        # Categorize ruling based on keywords
        categories = []
        full_text = question + " " + answer
        for cat, keywords in RULING_PATTERNS.items():
            if any(re.search(kw, full_text) for kw in keywords):
                categories.append(cat)

        if categories:
            # Create a simplified ruling summary
            # In a real scenario, we might want more complex logic or an LLM call here
            # But for now, we'll provide the category and the first few words of the answer logic
            cat_str = "|".join(categories)
            summary = answer.split("。")[0] if "。" in answer else answer[:30]
            summary = simplify_text(summary).strip()
            ruling_pcode = f"RULING: {cat_str} -> {summary}"

        # Look for ability text in 『 ... 』 to provide context
        match = re.search(r"『(.*?)』", question, re.DOTALL)
        ability_pcode = ""
        if match:
            ability_text = match.group(1).strip()

            # 1. Try to find match in card's own abilities
            if ability_text in card_abilities_map:
                ability_pcode = card_abilities_map[ability_text]
            else:
                # 2. Try to parse on the fly
                try:
                    parsed = parser.parse(ability_text)
                    if parsed:

                        def ability_to_dict(ab):
                            return {
                                "trigger": int(ab.trigger),
                                "is_once_per_turn": ab.is_once_per_turn,
                                "costs": [
                                    {
                                        "type": int(c.type),
                                        "value": c.value,
                                        "is_optional": c.is_optional,
                                        "params": c.params,
                                    }
                                    for c in ab.costs
                                ],
                                "conditions": [
                                    {"type": int(c.type), "is_negated": c.is_negated, "params": c.params}
                                    for c in ab.conditions
                                ],
                                "effects": [
                                    {
                                        "effect_type": int(e.effect_type),
                                        "value": e.value,
                                        "target": int(e.target),
                                        "is_optional": e.is_optional,
                                        "params": e.params,
                                    }
                                    for e in ab.effects
                                ],
                            }

                        ability_pcode = generate_pseudocode(ability_to_dict(parsed[0]))
                except Exception:
                    pass

        # Combine ruling and ability context
        if ruling_pcode and ability_pcode:
            new_faq["pseudocode"] = f"{ruling_pcode}\nCONTEXT:\n{ability_pcode}"
        elif ruling_pcode:
            new_faq["pseudocode"] = ruling_pcode
        elif ability_pcode:
            new_faq["pseudocode"] = ability_pcode

        processed.append(new_faq)
    return processed


def simplify_text(text):
    if not text:
        return ""
    simplified = re.sub(r"\{\{.*?\|(.*?)\}\}", r"[\1]", text)
    simplified = simplified.replace("<br>", "\n")
    return simplified


def main():
    input_path = "data/cards_compiled.json"
    output_path = "simplified_cards.json"

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return

    simplified_cards = []

    # Process member_db
    if "member_db" in data:
        for card_id, card_data in data["member_db"].items():
            card_no = card_data.get("card_no", "Unknown")
            name = card_data.get("name", "Unknown")

            abilities_pseudocode_map = {}
            processed_abilities = []
            if "abilities" in card_data:
                for ab in card_data["abilities"]:
                    pcode = generate_pseudocode(ab)
                    raw = ab.get("raw_text", "")
                    abilities_pseudocode_map[raw] = pcode
                    processed_abilities.append({"original": raw, "simplified": simplify_text(raw), "pseudocode": pcode})

            simplified_cards.append(
                {
                    "type": "Member",
                    "card_no": card_no,
                    "name": name,
                    "abilities": processed_abilities,
                    "q_and_a": process_faqs(card_data.get("faq", []), abilities_pseudocode_map),
                }
            )

    # Process live_db
    if "live_db" in data:
        for card_id, card_data in data["live_db"].items():
            card_no = card_data.get("card_no", "Unknown")
            name = card_data.get("name", "Unknown")

            abilities_pseudocode_map = {}
            processed_abilities = []
            if "abilities" in card_data:
                for ab in card_data["abilities"]:
                    pcode = generate_pseudocode(ab)
                    raw = ab.get("raw_text", "")
                    abilities_pseudocode_map[raw] = pcode
                    processed_abilities.append({"original": raw, "simplified": simplify_text(raw), "pseudocode": pcode})

            simplified_cards.append(
                {
                    "type": "Live",
                    "card_no": card_no,
                    "name": name,
                    "abilities": processed_abilities,
                    "q_and_a": process_faqs(card_data.get("faq", []), abilities_pseudocode_map),
                }
            )

    # Sort by card_no
    simplified_cards.sort(key=lambda x: x["card_no"])

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(simplified_cards, f, ensure_ascii=False, indent=2)

    print(f"Successfully processed {len(simplified_cards)} cards.")
    print(f"Output saved to {output_path}")


if __name__ == "__main__":
    main()
