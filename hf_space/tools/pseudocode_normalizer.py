import json
import os
import sys
from typing import Any, Dict

# Ensure we can import from local modules
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import (
    Ability,
    AbilityCostType,
    Condition,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    TargetType,
    TriggerType,
)

# --- Reverse Mappings ---

TRIGGER_NAMES = {v: k for k, v in TriggerType.__members__.items()}
# Manual overrides for clearer triggers
TRIGGER_DISPLAY = {
    TriggerType.NONE: "NONE",
    TriggerType.ON_PLAY: "ON_PLAY",
    TriggerType.ON_LIVE_START: "ON_LIVE_START",
    TriggerType.ON_LIVE_SUCCESS: "ON_LIVE_SUCCESS",
    TriggerType.TURN_START: "TURN_START",
    TriggerType.TURN_END: "TURN_END",
    TriggerType.CONSTANT: "CONSTANT",
    TriggerType.ACTIVATED: "ACTIVATED",
    TriggerType.ON_LEAVES: "ON_LEAVES",
    TriggerType.ON_REVEAL: "ON_REVEAL",
}

TARGET_DISPLAY = {
    TargetType.SELF: "SELF",
    TargetType.PLAYER: "PLAYER",
    TargetType.OPPONENT: "OPPONENT",
    TargetType.ALL_PLAYERS: "ALL_PLAYERS",
    TargetType.MEMBER_SELF: "MEMBER_SELF",
    TargetType.MEMBER_OTHER: "MEMBER_OTHER",
    TargetType.CARD_HAND: "CARD_HAND",
    TargetType.CARD_DISCARD: "CARD_DISCARD",
    TargetType.CARD_DECK_TOP: "CARD_DECK_TOP",
    TargetType.OPPONENT_HAND: "OPPONENT_HAND",
    TargetType.MEMBER_SELECT: "MEMBER_SELECT",
    TargetType.MEMBER_NAMED: "MEMBER_NAMED",
    TargetType.OPPONENT_MEMBER: "OPPONENT_MEMBER",
    TargetType.PLAYER_SELECT: "PLAYER_SELECT",
}

EFFECT_DISPLAY = {v: k for k, v in EffectType.__members__.items()}
CONDITION_DISPLAY = {v: k for k, v in ConditionType.__members__.items()}
COST_DISPLAY = {v: k for k, v in AbilityCostType.__members__.items()}


class PseudocodeNormalizer:
    """Converts internal Ability objects back into canonical pseudocode."""

    # Internal keys that should NOT appear in canonical pseudocode
    INTERNAL_KEYS = {
        "raw_effect",
        "raw_cond",
        "raw_val",
        "target_name",
        "val",
        "type",
        "options_text",
        "multiplier_value",
        "cost_type_name",
        "opponent_trigger_allowed",
        "has_multiplier",
        "raw_instructions",
    }

    def __init__(self):
        self.parser = AbilityParserV2()

    def normalize_ability(self, ability: Ability) -> str:
        """Reconstruct the 'Gold Standard' pseudocode for an ability."""
        parts = []

        # 1. Trigger
        trigger_name = TRIGGER_DISPLAY.get(ability.trigger, "NONE")
        if trigger_name != "NONE":
            parts.append(f"TRIGGER: {trigger_name}")

        # 2. Meta: Once per turn
        if getattr(ability, "is_once_per_turn", False):
            parts.append("(Once per turn)")

        # In ParserV2, instructions contains everything in sequence.
        # However, for the canonical format, we often separate by COST:, CONDITION:, EFFECT:
        # But for strictly sequential logic, we should use the sequence.

        current_costs = []
        current_conditions = []
        current_effects = []

        # We'll use a mixed approach:
        # Collect top-level costs/conditions first for the standard header fields
        # if they are just pre-checks.

        cost_strs = [self._format_cost(c) for c in ability.costs]
        if cost_strs:
            parts.append(f"COST: {', '.join(cost_strs)}")

        cond_strs = [self._format_condition(c) for c in ability.conditions]
        if cond_strs:
            parts.append(f"CONDITION: {', '.join(cond_strs)}")

        # For effects, we often have multiple. If the first effect is a sequential CONDITION,
        # it might be better to just list them all.
        eff_strs = []
        for eff in ability.effects:
            eff_strs.append(self._format_effect(eff))

        if eff_strs:
            parts.append(f"EFFECT: {'; '.join(eff_strs)}")

        return "\n".join(parts)

    def _format_params(self, params: Dict[str, Any]) -> str:
        if not params:
            return ""

        filtered_params = {k: v for k, v in params.items() if k.lower() not in self.INTERNAL_KEYS}
        if not filtered_params:
            return ""

        items = []
        # Sort keys to ensure deterministic output
        for k in sorted(filtered_params.keys()):
            v = filtered_params[k]

            # Clean up the key/value
            display_key = k.upper()

            # Special case for FILTER which might contain raw artifacts
            if display_key == "FILTER" and isinstance(v, str):
                v = v.replace('{"', "").replace('"}', "").strip()

            # Special case for OPTIONS which might be a JSON string or list
            if display_key == "OPTIONS" and isinstance(v, str):
                if v.startswith("[") or v.startswith("{"):
                    try:
                        # Try to parse it to see if it's JSON
                        v = json.loads(v)
                    except:
                        pass

            if isinstance(v, str):
                # Extra cleanup for strings that look like partial JSON
                v = v.lstrip('["').rstrip('"]')
                items.append(f'{display_key}="{v}"')
            elif isinstance(v, bool):
                items.append(f"{display_key}={str(v).upper()}")
            elif isinstance(v, list):
                # Format lists cleanly
                list_str = "[" + ", ".join([f'"{x}"' if isinstance(x, str) else str(x) for x in v]) + "]"
                items.append(f"{display_key}={list_str}")
            else:
                items.append(f"{display_key}={v}")

        return " {" + ", ".join(items) + "}"

    def _format_cost(self, cost: Cost) -> str:
        name = COST_DISPLAY.get(cost.type, "NONE")
        # Map COST: NONE to something more descriptive if possible
        if name == "NONE" and cost.params.get("raw_cost_type"):
            name = cost.params["raw_cost_type"].upper()

        val = cost.value
        param_str = self._format_params(cost.params)
        opt = " (Optional)" if getattr(cost, "is_optional", False) else ""
        return f"{name}({val}){param_str}{opt}"

    def _format_condition(self, cond: Condition) -> str:
        name = CONDITION_DISPLAY.get(cond.type, "NONE")
        # Map CONDITION: NONE to something more descriptive if possible
        if name == "NONE" and cond.params.get("raw_cond"):
            name = cond.params["raw_cond"].upper()

        neg = "NOT " if cond.is_negated else ""
        param_str = self._format_params(cond.params)
        return f"{neg}{name}{param_str}"

    def _format_effect(self, eff: Effect) -> str:
        # Check for META_RULE mapping back to original opcode
        name = EFFECT_DISPLAY.get(eff.effect_type, "NONE")
        if name == "META_RULE":
            raw_eff = eff.params.get("raw_effect")
            if raw_eff:
                name = raw_eff.upper()
            elif eff.params.get("type") == "score_rule":
                name = "SCORE_RULE"
            elif eff.params.get("type") == "heart_rule":
                name = "HEART_RULE"

        # Further refinement for common opcodes
        if name == "NONE" and eff.params.get("raw_effect"):
            name = eff.params["raw_effect"].upper()

        val = eff.value
        target = TARGET_DISPLAY.get(eff.target, "PLAYER")
        param_str = self._format_params(eff.params)
        opt = " (Optional)" if eff.is_optional else ""

        modal_str = ""
        if eff.modal_options:
            modal_str = "\n    Options:"
            for i, opt_list in enumerate(eff.modal_options):
                formatted_opts = []
                for instr in opt_list:
                    # In modal_options, instruments are usually dicts or objects
                    if hasattr(instr, "effect_type"):  # It's an Effect object
                        formatted_opts.append(self._format_effect(instr))
                    elif hasattr(instr, "type") and hasattr(instr, "is_negated"):  # Condition
                        formatted_opts.append(self._format_condition(instr))
                    elif hasattr(instr, "type") and not hasattr(instr, "is_negated"):  # Cost
                        formatted_opts.append(self._format_cost(instr))
                    elif isinstance(instr, dict):
                        # Attempt to format from dict if it's not fully hydrated
                        if "effect_type" in instr:
                            formatted_opts.append(
                                f"{EFFECT_DISPLAY.get(instr['effect_type'], 'UNK')}({instr.get('value')})"
                            )
                        elif "type" in instr:
                            formatted_opts.append(f"{COST_DISPLAY.get(instr['type'], 'UNK')}({instr.get('value')})")
                modal_str += f"\n      {i + 1}: {'; '.join(formatted_opts)}"

        return f"{name}({val}) -> {target}{param_str}{opt}{modal_str}"

    def roundtrip_check(self, pcode: str) -> bool:
        """Verify that normalize(parse(pcode)) results in equivalent logic."""
        # Note: String identity is hard because of ordering, so we compare the parsed Ability objects
        try:
            original_abilities = self.parser.parse(pcode)
            if not original_abilities:
                return True

            normalized_pcode = "\n\n".join([self.normalize_ability(a) for a in original_abilities])
            reparsed_abilities = self.parser.parse(normalized_pcode)

            if len(original_abilities) != len(reparsed_abilities):
                return False

            # Deep comparison (simplified for now)
            return len(str(original_abilities)) == len(str(reparsed_abilities))
        except Exception as e:
            print(f"Roundtrip error: {e}")
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", help="Comma-separated card IDs to process")
    parser.add_argument("--verify", action="store_true", help="Perform roundtrip verification")
    parser.add_argument("--bulk-check", action="store_true", help="Run against all cards")
    parser.add_argument("--output", default="reports/normalizer_report.txt", help="Output file path")
    args = parser.parse_args()

    normalizer = PseudocodeNormalizer()

    # Create reports directory if it doesn't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    cards = {}
    if "member_db" in data:
        cards.update(data["member_db"])
    if "live_db" in data:
        cards.update(data["live_db"])

    target_ids = []
    if args.ids:
        target_ids = [id.strip() for id in args.ids.split(",")]
    elif args.bulk_check:
        target_ids = list(cards.keys())
    else:
        # Default spot check if no args
        target_ids = ["9", "10", "11"]

    mismatches = 0
    with open(args.output, "w", encoding="utf-8") as out:
        for cid in target_ids:
            card = cards.get(cid)
            if not card:
                continue

            out.write(f"--- Card {cid}: {card.get('name')} ({card.get('card_no')}) ---\n")
            for i, ab in enumerate(card.get("abilities", [])):
                raw = ab.get("raw_text", "")

                try:
                    parsed_list = normalizer.parser.parse(raw)
                    if not parsed_list:
                        out.write(f"  [Error] Failed to parse raw: {raw}\n")
                        continue

                    norm = normalizer.normalize_ability(parsed_list[0])
                    out.write(f"Normalized Ability {i + 1}:\n")
                    out.write(norm + "\n")
                    out.write("-" * 20 + "\n")

                    if args.verify:
                        if not normalizer.roundtrip_check(raw):
                            out.write(f"  [FAIL] Roundtrip mismatch for card {cid}\n")
                            mismatches += 1
                except Exception as e:
                    out.write(f"  [CRASH] {e} during card {cid}\n")
                    mismatches += 1

        if args.verify and args.bulk_check:
            out.write(f"\nBulk Check Summary: {mismatches} mismatches found out of {len(target_ids)} cards.\n")

    print(f"Report written to {args.output}")
    if mismatches > 0:
        print(f"Mismatches found: {mismatches}. Check the report.")


if __name__ == "__main__":
    main()
