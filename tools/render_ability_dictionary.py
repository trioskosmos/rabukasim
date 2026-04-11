"""Render a working ability dictionary from `data/opcode_dictionary.json`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


COMPARISON_TO_SYMBOL = {
    "GE": ">=",
    "GT": ">",
    "LE": "<=",
    "LT": "<",
    "EQ": "==",
    "NE": "!=",
}

SYMBOL_TO_COMPARISON = {symbol: code for code, symbol in COMPARISON_TO_SYMBOL.items()}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def top_values(section: dict[str, Any] | None, limit: int = 3) -> list[dict[str, Any]]:
    if not isinstance(section, dict):
        return []
    values = []
    for key, entries in section.items():
        if not isinstance(entries, list):
            continue
        if not entries:
            continue
        values.append(
            {
                "key": key,
                "values": entries[:limit],
            }
        )
    return values


def phrase_for_opcode(entry: dict[str, Any]) -> dict[str, str]:
    name = str(entry.get("name", "")).upper()
    kind = str(entry.get("kind", "")).lower()

    if name == "NOP":
        return {"family": "control", "template": "no-op", "value_role": "none"}
    if name == "RETURN":
        return {"family": "control", "template": "end ability", "value_role": "none"}
    if name == "JUMP":
        return {"family": "control", "template": "jump +{value}", "value_role": "offset"}
    if name == "JUMP_IF_FALSE":
        return {"family": "control", "template": "if check fails, jump +{value}", "value_role": "offset"}

    if name == "DRAW":
        return {"family": "draw", "template": "draw {value}", "value_role": "count"}
    if name == "DRAW_UNTIL":
        return {"family": "draw", "template": "draw until {value}", "value_role": "target"}
    if name == "LOOK_DECK":
        return {"family": "search", "template": "look at top {value} of deck", "value_role": "count"}
    if name == "LOOK_AND_CHOOSE":
        return {
            "family": "search",
            "template": "look {value}, choose {choose_count}",
            "value_role": "count",
        }
    if name == "LOOK_REORDER_DISCARD":
        return {
            "family": "search",
            "template": "look top {value} of deck, reorder and discard the rest",
            "value_role": "count",
        }
    if name == "REVEAL_CARDS":
        return {"family": "search", "template": "reveal {value} cards", "value_role": "count"}
    if name == "REVEAL_UNTIL":
        return {"family": "search", "template": "reveal until {value}", "value_role": "count"}
    if name == "ORDER_DECK":
        return {"family": "search", "template": "order deck", "value_role": "mode"}
    if name == "BOTTOM_DECK":
        return {"family": "search", "template": "put to bottom of deck", "value_role": "none"}

    if name == "SELECT_MODE":
        return {
            "family": "selection",
            "template": "choose mode {option_names}",
            "value_role": "branch_count",
        }
    if name == "SELECT_PLAYER":
        return {"family": "selection", "template": "select player", "value_role": "count"}
    if name == "SELECT_LIVE":
        return {"family": "selection", "template": "select live {value}", "value_role": "count"}
    if name == "SELECT_MEMBER":
        return {"family": "selection", "template": "select member {value}", "value_role": "count"}
    if name == "SELECT_CARDS":
        return {"family": "selection", "template": "select cards {value}", "value_role": "count"}
    if name == "COLOR_SELECT":
        return {"family": "selection", "template": "choose color", "value_role": "count"}
    if name == "OPPONENT_CHOOSE":
        return {"family": "selection", "template": "opponent chooses", "value_role": "none"}

    if name == "MOVE_TO_DISCARD":
        return {
            "family": "movement",
            "template": "move {value} from {source_zone} to discard",
            "value_role": "count",
        }
    if name == "MOVE_TO_DECK":
        return {
            "family": "movement",
            "template": "move {value} to deck",
            "value_role": "count",
        }
    if name == "MOVE_TO_HAND":
        return {
            "family": "movement",
            "template": "move {value} to hand",
            "value_role": "count",
        }
    if name == "ADD_TO_HAND":
        return {
            "family": "movement",
            "template": "add {value} to hand",
            "value_role": "count",
        }
    if name == "MOVE_MEMBER":
        return {
            "family": "movement",
            "template": "move member {value}",
            "value_role": "count",
        }
    if name == "SWAP_ZONE":
        return {"family": "movement", "template": "swap zones", "value_role": "none"}
    if name == "SWAP_AREA":
        return {"family": "movement", "template": "swap areas", "value_role": "none"}
    if name == "PLACE_ENERGY_UNDER_MEMBER":
        return {
            "family": "movement",
            "template": "place energy under member {value}",
            "value_role": "count",
        }
    if name == "PLAY_MEMBER_FROM_HAND":
        return {
            "family": "movement",
            "template": "play member from hand {value}",
            "value_role": "count",
        }
    if name == "PLAY_MEMBER_FROM_DISCARD":
        return {
            "family": "movement",
            "template": "play member from discard {value}",
            "value_role": "count",
        }
    if name == "PLAY_LIVE_FROM_DISCARD":
        return {
            "family": "movement",
            "template": "play live from discard {value}",
            "value_role": "count",
        }

    if name == "ACTIVATE_MEMBER":
        return {
            "family": "activation",
            "template": "activate member {value}",
            "value_role": "count",
        }
    if name == "ACTIVATE_ENERGY":
        return {
            "family": "activation",
            "template": "activate energy {value}",
            "value_role": "count",
        }
    if name == "SET_TAPPED":
        return {"family": "activation", "template": "tap / set tapped", "value_role": "state"}
    if name == "TAP_OPPONENT":
        return {"family": "activation", "template": "tap opponent", "value_role": "count"}
    if name == "BATON_TOUCH_MOD":
        return {"family": "activation", "template": "modify baton touch", "value_role": "none"}
    if name == "PREVENT_BATON_TOUCH":
        return {"family": "activation", "template": "prevent baton touch", "value_role": "none"}
    if name == "FORMATION_CHANGE":
        return {"family": "activation", "template": "formation change", "value_role": "none"}

    if name == "PAY_ENERGY":
        return {"family": "resource", "template": "pay energy {value}", "value_role": "count"}
    if name == "PAY_ENERGY_DYNAMIC":
        return {"family": "resource", "template": "pay dynamic energy {value}", "value_role": "count"}
    if name == "ENERGY_CHARGE":
        return {"family": "resource", "template": "charge energy {value}", "value_role": "count"}
    if name == "REDUCE_COST":
        return {"family": "resource", "template": "reduce cost {value}", "value_role": "count"}
    if name == "INCREASE_COST":
        return {"family": "resource", "template": "increase cost {value}", "value_role": "count"}
    if name == "SET_HEART_COST":
        return {"family": "resource", "template": "set heart cost {value}", "value_role": "count"}
    if name == "INCREASE_HEART_COST":
        return {"family": "resource", "template": "increase heart cost {value}", "value_role": "count"}
    if name == "INCREASE_HEART_REQ":
        return {"family": "resource", "template": "increase heart requirement {value}", "value_role": "count"}
    if name == "REDUCE_HEART_REQ":
        return {"family": "resource", "template": "reduce heart requirement {value}", "value_role": "count"}
    if name == "REDUCE_LIVE_SET_LIMIT":
        return {"family": "resource", "template": "reduce live set limit {value}", "value_role": "count"}
    if name == "REDUCE_YELL_COUNT":
        return {"family": "resource", "template": "reduce yell count {value}", "value_role": "count"}
    if name == "SET_SCORE":
        return {"family": "resource", "template": "set score {value}", "value_role": "value"}
    if name == "BOOST_SCORE":
        return {"family": "resource", "template": "boost score {value}", "value_role": "count"}
    if name == "ADD_BLADES":
        return {"family": "resource", "template": "add blades {value}", "value_role": "count"}
    if name == "ADD_HEARTS":
        return {"family": "resource", "template": "add hearts {value}", "value_role": "count"}
    if name == "IN_SUCCESS_PILE":
        return {"family": "resource", "template": "put in success pile", "value_role": "none"}
    if name == "CALC_SUM_COST":
        return {"family": "resource", "template": "calculate sum cost", "value_role": "none"}
    if name == "DIV_VALUE":
        return {"family": "resource", "template": "divide value", "value_role": "count"}

    if name == "RECOVER_LIVE":
        return {"family": "recovery", "template": "recover live {value}", "value_role": "count"}
    if name == "RECOVER_MEMBER":
        return {"family": "recovery", "template": "recover member {value}", "value_role": "count"}
    if name == "GRANT_ABILITY":
        return {"family": "recovery", "template": "grant ability", "value_role": "none"}

    if name == "TRANSFORM_COLOR":
        return {"family": "transform", "template": "transform color", "value_role": "none"}
    if name == "TRANSFORM_HEART":
        return {"family": "transform", "template": "transform heart", "value_role": "none"}
    if name == "TRANSFORM_BLADES":
        return {"family": "transform", "template": "transform blades", "value_role": "none"}
    if name == "SET_TARGET_SELF":
        return {"family": "targeting", "template": "set target self", "value_role": "none"}
    if name == "SET_TARGET_OPPONENT":
        return {"family": "targeting", "template": "set target opponent", "value_role": "none"}
    if name == "TRIGGER_REMOTE":
        return {"family": "targeting", "template": "trigger remote ability", "value_role": "count"}
    if name == "NEGATE_EFFECT":
        return {"family": "control", "template": "negate effect", "value_role": "none"}
    if name == "RESTRICTION":
        return {"family": "control", "template": "apply restriction", "value_role": "none"}
    if name == "PREVENT_PLAY_TO_SLOT":
        return {"family": "control", "template": "prevent play to slot", "value_role": "none"}
    if name == "PREVENT_SET_TO_SUCCESS_PILE":
        return {"family": "control", "template": "prevent set to success pile", "value_role": "none"}

    if name == "HAS_MEMBER":
        return {"family": "condition", "template": "has member", "value_role": "none"}
    if name.startswith("COUNT_"):
        zone = name.removeprefix("COUNT_").lower()
        return {"family": "condition", "template": f"count({zone}) {{comparison}} {{value}}", "value_role": "threshold"}
    if name == "IS_CENTER":
        return {"family": "condition", "template": "is center", "value_role": "none"}
    if name == "COUNT_GROUP":
        return {"family": "condition", "template": "count(group) {comparison} {value}", "value_role": "threshold"}
    if name == "GROUP_FILTER":
        return {"family": "condition", "template": "group filter", "value_role": "none"}
    if name == "SCORE_COMPARE":
        return {"family": "condition", "template": "compare score", "value_role": "threshold"}
    if name == "OPPONENT_ENERGY_DIFF":
        return {"family": "condition", "template": "opponent energy difference", "value_role": "threshold"}
    if name == "HAS_KEYWORD":
        return {"family": "condition", "template": "has keyword {keyword}", "value_role": "none"}
    if name == "DECK_REFRESHED":
        return {"family": "condition", "template": "deck refreshed", "value_role": "none"}
    if name == "BATON":
        return {"family": "condition", "template": "baton", "value_role": "none"}
    if name == "TYPE_CHECK":
        return {"family": "condition", "template": "type check", "value_role": "none"}
    if name == "AREA_CHECK":
        return {"family": "condition", "template": "area check", "value_role": "none"}
    if name == "HEART_LEAD":
        return {"family": "condition", "template": "heart lead", "value_role": "none"}
    if name == "HAS_EXCESS_HEART":
        return {"family": "condition", "template": "has excess heart", "value_role": "none"}
    if name == "NOT_HAS_EXCESS_HEART":
        return {"family": "condition", "template": "does not have excess heart", "value_role": "none"}
    if name == "TOTAL_BLADES":
        return {"family": "condition", "template": "total blades", "value_role": "none"}
    if name == "COUNT_ENERGY_EXACT":
        return {"family": "condition", "template": "count(energy) == {value}", "value_role": "exact"}
    if name == "COUNT_BLADE_HEART_TYPES":
        return {"family": "condition", "template": "count blade/heart types", "value_role": "none"}
    if name == "SCORE_TOTAL_CHECK":
        return {"family": "condition", "template": "score total check", "value_role": "threshold"}
    if name == "MAIN_PHASE":
        return {"family": "condition", "template": "main phase", "value_role": "none"}
    if name == "SUCCESS_PILE_COUNT":
        return {"family": "condition", "template": "success pile count", "value_role": "threshold"}
    if name == "IS_SELF_MOVE":
        return {"family": "condition", "template": "is self move", "value_role": "none"}
    if name == "DISCARDED_CARDS":
        return {"family": "condition", "template": "discarded cards", "value_role": "threshold"}
    if name == "SYNC_COST":
        return {"family": "condition", "template": "sync cost", "value_role": "none"}
    if name == "SUM_VALUE":
        return {"family": "condition", "template": "sum value", "value_role": "math"}
    if name == "TARGET_MEMBER_HAS_NO_HEARTS":
        return {"family": "condition", "template": "target member has no hearts", "value_role": "none"}
    if name == "COUNT_LIVE_HEARTS":
        return {"family": "condition", "template": "count live hearts {comparison} {value}", "value_role": "threshold"}
    if name == "COUNT_SUCCESS_LIVE_SCORE":
        return {"family": "condition", "template": "count success live score {comparison} {value}", "value_role": "threshold"}
    if name == "CHECK_ALL_MEMBERS":
        return {"family": "condition", "template": "check all members", "value_role": "none"}
    if name == "COUNT_SUCCESS":
        return {"family": "condition", "template": "count success {comparison} {value}", "value_role": "threshold"}

    return {
        "family": kind or "misc",
        "template": name.lower().replace("_", " "),
        "value_role": "value",
    }


def build_dictionary(opcode_dictionary: dict[str, Any]) -> dict[str, Any]:
    opcodes = opcode_dictionary.get("opcodes", [])
    entries: list[dict[str, Any]] = []
    families: dict[str, list[str]] = defaultdict(list)

    for opcode in opcodes:
        if not isinstance(opcode, dict):
            continue
        phrase = phrase_for_opcode(opcode)
        family = phrase["family"]
        name = str(opcode.get("name", "")).upper()
        families[family].append(name)

        entry = {
            "name": name,
            "code": opcode.get("code"),
            "kind": opcode.get("kind"),
            "count": opcode.get("count", 0),
            "family": family,
            "value_role": phrase["value_role"],
            "template": phrase["template"],
            "triggers": opcode.get("triggers", []),
            "value_options": opcode.get("value_options", [])[:5],
            "attr_keys": opcode.get("attr_keys", []),
            "slot_keys": opcode.get("slot_keys", []),
            "params_keys": opcode.get("params_keys", []),
            "common_attr_values": top_values(opcode.get("common_attr_values")),
            "common_slot_values": top_values(opcode.get("common_slot_values")),
            "common_params_values": top_values(opcode.get("common_params_values")),
            "examples": opcode.get("examples", [])[:2],
            "common_windows": opcode.get("common_windows", [])[:3],
            "notes": [],
        }

        if name in COMPARISON_TO_SYMBOL:
            entry["comparison_symbol"] = COMPARISON_TO_SYMBOL[name]
        entries.append(entry)

    entries.sort(key=lambda item: (-int(item.get("count", 0)), str(item.get("name", ""))))
    for family, names in families.items():
        families[family] = sorted(names)

    quick_reference = [
        {"pattern": "draw {value}", "examples": ["DRAW"]},
        {"pattern": "count(stage) >= {value}", "examples": ["COUNT_STAGE"]},
        {"pattern": "count(energy) >= {value}", "examples": ["COUNT_ENERGY"]},
        {"pattern": "select mode {option_names}", "examples": ["SELECT_MODE"]},
        {"pattern": "look {value}, choose {choose_count}", "examples": ["LOOK_AND_CHOOSE"]},
        {"pattern": "move {value} from {source_zone} to discard", "examples": ["MOVE_TO_DISCARD"]},
        {"pattern": "recover live {value}", "examples": ["RECOVER_LIVE"]},
        {"pattern": "activate member {value}", "examples": ["ACTIVATE_MEMBER"]},
        {"pattern": "activate energy {value}", "examples": ["ACTIVATE_ENERGY"]},
        {"pattern": "boost score {value}", "examples": ["BOOST_SCORE"]},
        {"pattern": "add hearts {value}", "examples": ["ADD_HEARTS"]},
        {"pattern": "add blades {value}", "examples": ["ADD_BLADES"]},
    ]

    return {
        "schema": "ability_dictionary.v1",
        "generated_from": {
            "opcode_dictionary": "data/opcode_dictionary.json",
        },
        "comparison_symbols": COMPARISON_TO_SYMBOL,
        "comparison_codes": SYMBOL_TO_COMPARISON,
        "quick_reference": quick_reference,
        "families": dict(sorted(families.items(), key=lambda item: item[0])),
        "opcodes": entries,
    }


def render_markdown(dictionary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Ability Dictionary")
    lines.append("")
    lines.append("Comparison symbols:")
    lines.append("")
    for code, symbol in dictionary["comparison_symbols"].items():
        lines.append(f"- `{code}` -> `{symbol}`")
    lines.append("")

    families = dictionary.get("families", {})
    lines.append("Families:")
    for family, names in families.items():
        lines.append(f"- `{family}`: {len(names)} opcodes")
    lines.append("")

    lines.append("Common forms:")
    for item in dictionary.get("quick_reference", []):
        examples = ", ".join(f"`{example}`" for example in item.get("examples", []))
        lines.append(f"- `{item['pattern']}` -> {examples}")
    lines.append("")

    for family in sorted(families.keys()):
        lines.append(f"## {family.title()}")
        lines.append("")
        for entry in [item for item in dictionary["opcodes"] if item["family"] == family]:
            lines.append(f"- `{entry['name']}`")
            lines.append(f"  - template: `{entry['template']}`")
            lines.append(f"  - value role: `{entry['value_role']}`")
            lines.append(f"  - kind: `{entry['kind']}`")
            lines.append(f"  - count: `{entry['count']}`")
            if entry.get("triggers"):
                lines.append(f"  - triggers: {', '.join(f'`{t}`' for t in entry['triggers'][:5])}")
            if entry.get("attr_keys"):
                lines.append(f"  - attr keys: {', '.join(f'`{k}`' for k in entry['attr_keys'][:8])}")
            if entry.get("slot_keys"):
                lines.append(f"  - slot keys: {', '.join(f'`{k}`' for k in entry['slot_keys'][:8])}")
            if entry.get("params_keys"):
                lines.append(f"  - params keys: {', '.join(f'`{k}`' for k in entry['params_keys'][:8])}")
            if entry.get("examples"):
                sample = entry["examples"][0]
                frame = sample.get("frame", {})
                if isinstance(frame, dict):
                    lines.append(
                        "  - example: "
                        f"ability {sample.get('ability_index')}, "
                        f"trigger {sample.get('trigger')}, "
                        f"frame {frame.get('op')}"
                    )
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a useful ability dictionary from opcode metadata.")
    parser.add_argument(
        "--opcode-dictionary",
        default="data/opcode_dictionary.json",
        help="Path to opcode_dictionary.json",
    )
    parser.add_argument(
        "--output-json",
        default="data/ability_dictionary.json",
        help="Path for the rendered dictionary JSON",
    )
    parser.add_argument(
        "--output-md",
        default="data/ability_dictionary.md",
        help="Path for the human-readable markdown dictionary",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the rendered outputs differ from what is on disk",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    opcode_path = Path(args.opcode_dictionary)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)

    opcode_dictionary = load_json(opcode_path)
    dictionary = build_dictionary(opcode_dictionary)
    md = render_markdown(dictionary)
    json_text = json.dumps(dictionary, ensure_ascii=False, indent=2) + "\n"

    if args.check:
        if output_json.exists() and output_json.read_text(encoding="utf-8") != json_text:
            print(f"{output_json} is out of date")
            return 1
        if output_md.exists() and output_md.read_text(encoding="utf-8") != md:
            print(f"{output_md} is out of date")
            return 1
        return 0

    output_json.write_text(json_text, encoding="utf-8")
    output_md.write_text(md, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
