import json
import re
import sys

sys.path.insert(0, "game")
from ability import AbilityParser, ConditionType, EffectType, TriggerType

EFFECT_DESCRIPTIONS = {
    EffectType.DRAW: "Draw {value} card(s) from deck to hand",
    EffectType.LOOK_DECK: "Look at top {value} card(s) of deck",
    EffectType.ADD_BLADES: "Gain {value} Blade(s) for member",
    EffectType.ADD_HEARTS: "Gain {value} Heart(s) for live",
    EffectType.REDUCE_COST: "Reduce cost of next card by {value}",
    EffectType.BOOST_SCORE: "Boost score by {value} for live",
    EffectType.RECOVER_LIVE: "Recover {value} Live card(s) {filter} from discard to hand",
    EffectType.RECOVER_MEMBER: "Recover {value} Member card(s) {filter} from discard to hand",
    EffectType.BUFF_POWER: "Buff member power/blade by {value} (until live/turn end)",
    EffectType.IMMUNITY: "Gain immunity for member",
    EffectType.MOVE_MEMBER: "Move member to different zone",
    EffectType.SWAP_CARDS: "Send {value} card(s) to discard from {from}",
    EffectType.SEARCH_DECK: "Search deck for member/live card(s)",
    EffectType.ENERGY_CHARGE: "Add {value} card(s) to energy zone from {from}",
    EffectType.NEGATE_EFFECT: "Negate an effect",
    EffectType.ORDER_DECK: "Reorder {value} {filter} card(s) in deck ({position})",
    EffectType.META_RULE: "[Rule clarification for heart/blade requirements]",
    EffectType.SELECT_MODE: "Choose one effect",
    EffectType.MOVE_TO_DECK: "Move {value} card(s) to deck ({position})",
    EffectType.TAP_OPPONENT: "Tap {value} opponent's member(s) on stage",
    EffectType.PLACE_UNDER: "Place card under member",
    EffectType.RESTRICTION: "Apply restriction to member/live",
    EffectType.BATON_TOUCH_MOD: "Modify baton touch for member",
    EffectType.SET_SCORE: "Set score to {value} for live",
    EffectType.SWAP_ZONE: "Swap zones (member/live card)",
    EffectType.TRANSFORM_COLOR: "Transform heart color to {target_color}",
    EffectType.REVEAL_CARDS: "Reveal {value} member/live card(s) from hand/deck",
    EffectType.LOOK_AND_CHOOSE: "Choose {value} {filter} card(s) from looked deck",
    EffectType.CHEER_REVEAL: "Process cheer-revealed cards for live",
    EffectType.ACTIVATE_MEMBER: "Activate {value} member(s) on stage",
    EffectType.ADD_TO_HAND: "Add {value} member/live card(s) to hand from {from}",
    EffectType.FLAVOR_ACTION: "Flavor action (Ask opponent/Check)",
}

TRIGGER_DESCRIPTIONS = {
    TriggerType.NONE: "",
    TriggerType.ON_PLAY: "[On Play]",
    TriggerType.ON_LIVE_START: "[Live Start]",
    TriggerType.ON_LIVE_SUCCESS: "[Live Success]",
    TriggerType.TURN_START: "[Turn Start]",
    TriggerType.TURN_END: "[Turn End]",
    TriggerType.CONSTANT: "[Constant]",
    TriggerType.ACTIVATED: "[Activated]",
    TriggerType.ON_LEAVES: "[When Leaves]",
}

CONDITION_DESCRIPTIONS = {
    ConditionType.NONE: "",
    ConditionType.TURN_1: "if once per turn",
    ConditionType.HAS_MEMBER: "if have member '{name}'",
    ConditionType.HAS_COLOR: "if have color '{color}'",
    ConditionType.COUNT_STAGE: "if stage count >= {count}",
    ConditionType.COUNT_HAND: "if hand count >= {count}",
    ConditionType.COUNT_DISCARD: "if discard count >= {count}",
    ConditionType.IS_CENTER: "if positioned in center",
    ConditionType.LIFE_LEAD: "if leading opponent in life/score",
    ConditionType.COUNT_GROUP: "if {group} count >= {min}",
    ConditionType.GROUP_FILTER: "for {group} members",
    ConditionType.OPPONENT_HAS: "if opponent has",
    ConditionType.SELF_IS_GROUP: "if self is {group}",
    ConditionType.MODAL_ANSWER: "based on answer choice",
    ConditionType.COUNT_ENERGY: "if energy >= {min}",
    ConditionType.HAS_LIVE_CARD: "if live card present",
}


def reconstruct_ability(ability):
    """Reconstruct a human-readable description from parsed ability."""
    parts = []

    # Trigger
    trigger_desc = TRIGGER_DESCRIPTIONS.get(ability.trigger, str(ability.trigger))
    if trigger_desc:
        parts.append(trigger_desc)

    # Costs
    for cost in ability.costs:
        if cost.type == 2:  # TAP_SELF
            parts.append("Cost: Tap this member")
        elif cost.type == 3:  # DISCARD_HAND
            parts.append(f"Cost: Discard {cost.value} card(s) from hand")
        elif cost.type == 4:  # RETURN_HAND
            parts.append("Cost: Return member to hand")
        elif cost.type == 1:  # ENERGY
            parts.append(f"Cost: Pay {cost.value} Energy")
        elif cost.type == 5:  # SACRIFICE_SELF (new)
            parts.append("Cost: Send this member to discard")

    # Conditions
    for cond in ability.conditions:
        template = CONDITION_DESCRIPTIONS.get(cond.type, f"if {cond.type}")
        try:
            desc = template.format(**cond.params) if cond.params else template
        except KeyError:
            desc = f"if {cond.type} ({cond.params})"
        if cond.is_negated:
            desc = "NOT " + desc
        parts.append(desc)

    # Effects
    for eff in ability.effects:
        template = EFFECT_DESCRIPTIONS.get(eff.effect_type, f"Effect: {eff.effect_type}")

        # Build context for formatting
        context = eff.params.copy()
        context["value"] = eff.value

        # Only use eff.target if it's NOT specific logic hiding in params
        if "target" not in context:
            context["target"] = str(eff.target.name).lower() if hasattr(eff.target, "name") else str(eff.target)

        # Normalize target names for clearer output and matching
        if context.get("target") == "card_discard":
            context["target"] = "discard"
        if context.get("target") in ["member_select", "self"]:
            context["target"] = "member"

        context.setdefault("to", "hand")  # Default 'to' for recover effects if not specified
        context.setdefault("from", "zone")
        context.setdefault("position", "top")
        context.setdefault("target_color", "ANY")

        # Filter logic
        filter_val = eff.params.get("filter", "")
        if filter_val == "member":
            context["filter"] = "Member"
        elif filter_val == "live":
            context["filter"] = "Live"
        elif filter_val == "heart_req":
            context["filter"] = "(w/ Heart req)"
        else:
            context["filter"] = ""

        # Custom override for ACTIVATE_MEMBER if target is energy
        if eff.effect_type == EffectType.ACTIVATE_MEMBER and context.get("target") == "energy":
            template = "Activate {value} energy"
        elif eff.effect_type == EffectType.ACTIVATE_MEMBER:
            template = "Activate {value} member(s) on stage"

        # Play Member Override
        if eff.effect_type == EffectType.RECOVER_MEMBER and context.get("auto_play"):
            template = "Play {value} Member card(s) from {from}"

        # Meta Rule Override
        if eff.effect_type == EffectType.META_RULE:
            if context.get("type") == "score_rule":
                template = "[Rule clarification for score]"
            elif context.get("type") == "heart_rule":
                template = "[Rule clarification for heart/blade requirements]"

        try:
            desc = template.format(**context)
        except KeyError as e:
            desc = f"{template} (missing {e})"

        # Append duration if present
        if "until" in eff.params:
            if eff.params["until"] == "live_end":
                desc += " (during live)"
            elif eff.params["until"] == "turn_end":
                desc += " (until turn end)"

        if eff.is_optional:
            desc = "(Optional) " + desc
        parts.append(f"→ {desc}")

    return " ".join(parts) if parts else "[No parsed content]"


def load_cards():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.values()) if isinstance(data, dict) else data


def find_semantic_gaps(raw_text, reconstruction):
    """Find keywords in original that aren't reflected in reconstruction."""
    gaps = []

    # Key semantic indicators to check
    semantic_checks = [
        (r"\d+枚", "card count"),
        (r"スコア", "score"),
        (r"相手", "opponent"),
        (r"ブレード", "blade"),
        (r"ハート", "heart"),
        (r"デッキ", "deck"),
        (r"控え室", "discard"),
        (r"手札", "hand"),
        (r"ライブ", "live"),
        (r"エネルギー", "energy"),
        (r"メンバー", "member"),
        (r"センター", "center"),
        (r"公開", "reveal"),
        (r"シャッフル", "shuffle"),
    ]

    for pattern, concept in semantic_checks:
        if re.search(pattern, raw_text):
            # Check if concept is reflected in reconstruction
            concept_map = {
                "card count": r"\d+",
                "score": r"score",
                "opponent": r"opponent",
                "blade": r"[Bb]lade",
                "heart": r"[Hh]eart",
                "deck": r"deck",
                "discard": r"discard",
                "hand": r"hand",
                "live": r"[Ll]ive",
                "energy": r"energy",
                "member": r"[Mm]ember",
                "center": r"center",
                "reveal": r"[Rr]eveal",
                "shuffle": r"shuffle|[Oo]rder",
            }
            if concept in concept_map and not re.search(concept_map[concept], reconstruction, re.IGNORECASE):
                gaps.append(f"Missing '{concept}' (pattern: {pattern})")

    return gaps


def main():
    print("Loading cards...")
    cards = load_cards()

    all_gaps = {}
    gap_counts = {}

    for card in cards:
        text = card.get("ability", "")
        if not text:
            continue

        card_id = card.get("card_no") or card.get("cardNumber") or "UNKNOWN"

        try:
            abilities = AbilityParser.parse_ability_text(text)
            reconstructions = [reconstruct_ability(a) for a in abilities]
            full_reconstruction = " | ".join(reconstructions)

            gaps = find_semantic_gaps(text, full_reconstruction)
            if gaps:
                all_gaps[card_id] = {
                    "name": card.get("name", "Unknown"),
                    "raw": text[:150] + ("..." if len(text) > 150 else ""),
                    "reconstruction": full_reconstruction[:150] + ("..." if len(full_reconstruction) > 150 else ""),
                    "gaps": gaps,
                }
                for g in gaps:
                    # Clean up 'Missing 'concept'' key
                    key = g.split("'")[1] if "'" in g else g
                    gap_counts[key] = gap_counts.get(key, 0) + 1
        except Exception as e:
            all_gaps[card_id] = {
                "name": card.get("name", "Unknown"),
                "raw": text[:100],
                "reconstruction": "ERROR",
                "gaps": [str(e)],
            }

    # Write report
    with open("inverse_parse_report.txt", "w", encoding="utf-8") as out:
        out.write("=" * 70 + "\n")
        out.write("INVERSE PARSING VALIDATION REPORT\n")
        out.write(f"Total Cards: {len(cards)}\n")
        out.write(f"Cards with Semantic Gaps: {len(all_gaps)}\n")
        out.write("=" * 70 + "\n\n")

        out.write("GAP SUMMARY (sorted by frequency):\n")
        for concept, count in sorted(gap_counts.items(), key=lambda x: -x[1]):
            out.write(f"  {concept}: {count} cards\n")

        out.write("\n" + "=" * 70 + "\n")
        out.write("DETAILED GAPS (First 30):\n\n")

        for card_id, info in list(all_gaps.items())[:30]:
            out.write(f"[{card_id}] {info['name']}\n")
            out.write(f"  Original: {info['raw']}\n")
            out.write(f"  Parsed:   {info['reconstruction']}\n")
            out.write("  Gaps:\n")
            for g in info["gaps"]:
                out.write(f"    - {g}\n")
            out.write("\n")

    print(f"Validation complete. {len(all_gaps)} cards with semantic gaps.")
    print("Report written to: inverse_parse_report.txt")
    print("\nTop 5 missing concepts:")
    for concept, count in sorted(gap_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  {concept}: {count} cards")


if __name__ == "__main__":
    main()
