from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CARDS_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_JSON_PATH = ROOT_DIR / "reports" / "ability_manifest.json"
DEFAULT_MD_PATH = ROOT_DIR / "reports" / "ability_manifest.md"

CONTROL_OPS = {"RETURN", "JUMP", "JUMP_IF_FALSE"}
PROMPT_OPS = {
    "SELECT_MODE",
    "SELECT_MEMBER",
    "SELECT_CARDS",
    "LOOK_AND_CHOOSE",
    "SELECT_PLAYER",
    "SELECT_LIVE",
    "OPPONENT_CHOOSE",
}
COST_OPS = {
    "PAY_ENERGY",
    "PAY_ENERGY_DYNAMIC",
    "MOVE_TO_DISCARD",
    "SET_TAPPED",
    "TAP_MEMBER",
    "ACTIVATE_ENERGY",
    "REDUCE_COST",
    "INCREASE_COST",
    "INCREASE_HEART_COST",
    "REDUCE_HEART_REQ",
    "REDUCE_LIVE_SET_LIMIT",
    "PREVENT_PLAY_TO_SLOT",
    "PREVENT_ACTIVATE",
    "PREVENT_BATON_TOUCH",
    "PREVENT_SET_TO_SUCCESS_PILE",
}
EFFECT_OPS = {
    "DRAW",
    "ADD_BLADES",
    "ADD_HEARTS",
    "REDUCE_COST",
    "LOOK_DECK",
    "RECOVER_LIVE",
    "BOOST_SCORE",
    "RECOVER_MEMBER",
    "BUFF_POWER",
    "IMMUNITY",
    "MOVE_MEMBER",
    "SWAP_CARDS",
    "SEARCH_DECK",
    "ENERGY_CHARGE",
    "SET_BLADES",
    "SET_HEARTS",
    "FORMATION_CHANGE",
    "NEGATE_EFFECT",
    "ORDER_DECK",
    "META_RULE",
    "MOVE_TO_DECK",
    "TAP_OPPONENT",
    "PLACE_UNDER",
    "FLAVOR_ACTION",
    "RESTRICTION",
    "BATON_TOUCH_MOD",
    "SET_SCORE",
    "SWAP_ZONE",
    "TRANSFORM_COLOR",
    "REVEAL_CARDS",
    "CHEER_REVEAL",
    "ACTIVATE_MEMBER",
    "ADD_TO_HAND",
    "COLOR_SELECT",
    "TRIGGER_REMOTE",
    "REDUCE_HEART_REQ",
    "MODIFY_SCORE_RULE",
    "ADD_STAGE_ENERGY",
    "TAP_MEMBER",
    "PLAY_MEMBER_FROM_HAND",
    "GRANT_ABILITY",
    "REDUCE_YELL_COUNT",
    "PLAY_MEMBER_FROM_DISCARD",
    "DRAW_UNTIL",
    "REVEAL_UNTIL",
    "PLAY_LIVE_FROM_DISCARD",
    "SET_TARGET_SELF",
    "SET_TARGET_OPPONENT",
    "ACTIVATE_ENERGY",
    "SET_HEART_COST",
    "LOOK_DECK_DYNAMIC",
    "REDUCE_SCORE",
    "REPEAT_ABILITY",
    "LOSE_EXCESS_HEARTS",
    "PLACE_ENERGY_UNDER_MEMBER",
    "CALC_SUM_COST",
    "LOOK_REORDER_DISCARD",
    "DIV_VALUE",
    "TRANSFORM_BLADES",
}

ZONE_NAMES = {
    "HAND": "hand",
    "DISCARD": "discard",
    "STAGE": "stage",
    "DECK": "deck",
    "DECK_TOP": "top of deck",
    "DECK_BOTTOM": "bottom of deck",
    "ENERGY": "energy",
    "LIVE": "success pile",
    "SUCCESS_PILE": "success pile",
}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def trigger_name(trigger_id: int, metadata: Dict[str, Any]) -> str:
    triggers = metadata.get("triggers", {})
    for name, value in triggers.items():
        if int(value) == int(trigger_id):
            return name
    return f"TRIGGER_{trigger_id}"


def opcode_name(opcode_id: Any, frame: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    if isinstance(opcode_id, str) and opcode_id:
        return opcode_id.upper()
    if isinstance(opcode_id, int):
        opcodes = metadata.get("opcodes", {})
        for name, value in opcodes.items():
            if int(value) == opcode_id:
                return name
        return f"OP_{opcode_id}"

    for key in ("opcode_name", "opcode", "op", "kind"):
        value = frame.get(key)
        if isinstance(value, str) and value:
            return value.upper()
    return "UNKNOWN"


def get_frame_dict(frame: Dict[str, Any]) -> Dict[str, Any]:
    semantic = frame.get("semantic")
    if isinstance(semantic, dict) and semantic:
        merged = dict(frame)
        merged.setdefault("semantic", semantic)
        return merged
    return frame


def frame_attr(frame: Dict[str, Any]) -> Dict[str, Any]:
    attr = frame.get("attr")
    if isinstance(attr, dict):
        return attr
    semantic = frame.get("semantic")
    if isinstance(semantic, dict):
        inner = semantic.get("attr")
        if isinstance(inner, dict):
            return inner
    return {}


def frame_slot(frame: Dict[str, Any]) -> Dict[str, Any]:
    slot = frame.get("slot")
    if isinstance(slot, dict):
        return slot
    semantic = frame.get("semantic")
    if isinstance(semantic, dict):
        inner = semantic.get("slot")
        if isinstance(inner, dict):
            return inner
    return {}


def is_optional_frame(frame: Dict[str, Any]) -> bool:
    attr = frame_attr(frame)
    if attr.get("is_optional"):
        return True
    semantic = frame.get("semantic")
    if isinstance(semantic, dict):
        decoded = semantic.get("decoded")
        if isinstance(decoded, str) and "optional" in decoded.lower():
            return True
    return False


def is_negated_frame(frame: Dict[str, Any]) -> bool:
    if bool(frame.get("is_negated")) or bool(frame.get("negated")):
        return True
    semantic = frame.get("semantic")
    return bool(isinstance(semantic, dict) and semantic.get("negated"))


def friendly_zone(zone: Any) -> str:
    if not isinstance(zone, str) or not zone:
        return ""
    return ZONE_NAMES.get(zone.upper(), zone.lower().replace("_", " "))


def friendly_slot(slot: Dict[str, Any]) -> str:
    if not slot:
        return ""
    parts: List[str] = []
    if "source_zone" in slot:
        parts.append(f"source={friendly_zone(slot['source_zone'])}")
    if "dest_zone" in slot:
        parts.append(f"dest={friendly_zone(slot['dest_zone'])}")
    if "target_slot" in slot:
        parts.append(f"target={slot['target_slot']}")
    if "area_idx" in slot:
        parts.append(f"area={slot['area_idx']}")
    if slot.get("is_opponent"):
        parts.append("opponent")
    if slot.get("is_reveal_until_live"):
        parts.append("reveal_until_live")
    if slot.get("is_baton_slot"):
        parts.append("baton")
    if slot.get("is_wait"):
        parts.append("wait")
    if slot.get("is_dynamic"):
        parts.append("dynamic")
    return ", ".join(parts)


def compact_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: compact_json(v) for k, v in value.items() if v not in (None, "", [], {}, False)}
    if isinstance(value, list):
        return [compact_json(v) for v in value if v not in (None, "", [], {}, False)]
    return value


def frame_role(op: str, optional: bool) -> str:
    if op in CONTROL_OPS:
        return "control"
    if op in PROMPT_OPS:
        return "prompt"
    if op in COST_OPS or optional:
        return "cost"
    return "effect"


def count_text(value: Any) -> str:
    if isinstance(value, int):
        return str(value)
    return str(value) if value not in (None, "") else "0"


def describe_frame(frame: Dict[str, Any], metadata: Dict[str, Any]) -> str:
    frame = get_frame_dict(frame)
    op = opcode_name(frame.get("opcode_id", frame.get("opcode")), frame, metadata)
    value = frame.get("value", 0)
    attr = frame_attr(frame)
    slot = frame_slot(frame)
    optional = is_optional_frame(frame)
    prefix = "May " if optional and op not in CONTROL_OPS else ""

    if op == "RETURN":
        return "Done."
    if op == "JUMP":
        return f"Jump ahead {count_text(value)} frame(s)."
    if op == "JUMP_IF_FALSE":
        return f"Skip ahead {count_text(value)} frame(s) if the preceding condition fails."
    if op == "DRAW":
        return f"{prefix}Draw {count_text(value)} card(s)."
    if op == "BOOST_SCORE":
        return f"{prefix}Gain +{count_text(value)} score."
    if op == "RECOVER_MEMBER":
        source = friendly_zone(slot.get("source_zone")) or "discard"
        target = friendly_zone(slot.get("dest_zone")) or "hand"
        return f"{prefix}Recover {count_text(value)} member(s) from {source} to {target}."
    if op == "RECOVER_LIVE":
        target = friendly_zone(slot.get("dest_zone")) or "success pile"
        return f"{prefix}Recover {count_text(value)} live card(s) to {target}."
    if op == "MOVE_TO_DISCARD":
        source = friendly_zone(slot.get("source_zone")) or "hand"
        return f"{prefix}Move {count_text(value)} matching card(s) from {source} to discard."
    if op == "PAY_ENERGY":
        return f"Pay {count_text(value)} energy."
    if op == "PAY_ENERGY_DYNAMIC":
        return f"Pay dynamic energy cost ({count_text(value)})."
    if op == "SET_TAPPED":
        return "Tap the selected member."
    if op == "TAP_MEMBER":
        return "Tap a member."
    if op == "ACTIVATE_MEMBER":
        return "Untap the selected member."
    if op == "SELECT_MEMBER":
        return f"Choose {count_text(value)} member(s)."
    if op == "SELECT_CARDS":
        return f"Choose {count_text(value)} card(s)."
    if op == "LOOK_AND_CHOOSE":
        choose_count = attr.get("choose_count", value)
        look_count = attr.get("look_count", value)
        return f"Look at {count_text(look_count)} card(s) and choose {count_text(choose_count)}."
    if op == "SELECT_MODE":
        return f"Choose one of {count_text(value)} mode(s)."
    if op == "SELECT_PLAYER":
        return "Choose a player."
    if op == "SELECT_LIVE":
        return "Choose a live card."
    if op == "OPPONENT_CHOOSE":
        return "Opponent chooses."
    if op == "PLAY_MEMBER_FROM_HAND":
        return "Play a member from hand."
    if op == "PLAY_MEMBER_FROM_DISCARD":
        return "Play a member from discard."
    if op == "PLAY_LIVE_FROM_DISCARD":
        return "Play a live card from discard."
    if op == "ADD_TO_HAND":
        return f"Add {count_text(value)} card(s) to hand."
    if op == "ADD_STAGE_ENERGY":
        return f"Add {count_text(value)} energy to stage."
    if op == "ENERGY_CHARGE":
        return f"Charge {count_text(value)} energy card(s)."
    if op == "SET_SCORE":
        return f"Set score to {count_text(value)}."
    if op == "REDUCE_SCORE":
        return f"Reduce score by {count_text(value)}."
    if op == "SET_HEART_COST":
        return f"Set heart cost to {count_text(value)}."
    if op == "SET_HEARTS":
        return f"Set hearts to {count_text(value)}."
    if op == "SET_BLADES":
        return f"Set blades to {count_text(value)}."
    if op == "ADD_BLADES":
        return f"Gain {count_text(value)} blade(s)."
    if op == "ADD_HEARTS":
        return f"Gain {count_text(value)} heart(s)."
    if op == "REDUCE_COST":
        return f"Reduce cost by {count_text(value)}."
    if op == "INCREASE_COST":
        return f"Increase cost by {count_text(value)}."
    if op == "INCREASE_HEART_COST":
        return f"Increase heart cost by {count_text(value)}."
    if op == "REDUCE_HEART_REQ":
        return f"Reduce heart requirement by {count_text(value)}."
    if op == "REDUCE_LIVE_SET_LIMIT":
        return f"Reduce live set limit by {count_text(value)}."
    if op == "PREVENT_PLAY_TO_SLOT":
        return "Prevent play to the selected slot."
    if op == "PREVENT_ACTIVATE":
        return "Prevent activation."
    if op == "PREVENT_BATON_TOUCH":
        return "Prevent baton touch."
    if op == "PREVENT_SET_TO_SUCCESS_PILE":
        return "Prevent setting a card to the success pile."
    if op == "LOOSE_EXCESS_HEARTS":
        return f"Lose excess hearts ({count_text(value)})."
    if op == "REPEAT_ABILITY":
        return "Repeat the ability."
    if op == "CALC_SUM_COST":
        return "Calculate the summed cost."
    if op == "TRANSFORM_COLOR":
        return "Transform color."
    if op == "TRANSFORM_HEART":
        return "Transform heart."
    if op == "TRANSFORM_BLADES":
        return "Transform blades."
    if op == "LOOK_DECK":
        return f"Look at {count_text(value)} card(s) from the deck."
    if op == "LOOK_DECK_DYNAMIC":
        return "Look at a dynamic number of cards from the deck."
    if op == "LOOK_REORDER_DISCARD":
        return "Look and reorder discard."
    if op == "REVEAL_CARDS":
        return f"Reveal {count_text(value)} card(s)."
    if op == "REVEAL_UNTIL":
        return "Reveal cards until the target is found."
    if op == "SEARCH_DECK":
        return "Search the deck."
    if op == "DRAW_UNTIL":
        return "Draw until a condition is met."

    semantic = frame.get("semantic")
    if isinstance(semantic, dict):
        decoded = semantic.get("decoded")
        if isinstance(decoded, str) and decoded:
            if "|" in decoded:
                decoded = decoded.split("|", 1)[1].strip()
            return decoded[:240]

    fallback = {
        "value": value,
        "attr": compact_json(attr),
        "slot": compact_json(slot),
    }
    return f"{op} {json.dumps(fallback, ensure_ascii=False, sort_keys=True)}"


def normalize_source_text(card: Dict[str, Any]) -> str:
    for key in ("original_text", "ability_text", "raw_text"):
        value = card.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def summarize_frames(frames: List[Dict[str, Any]], metadata: Dict[str, Any]) -> Tuple[str, str]:
    meaningful = [frame for frame in frames if opcode_name(frame.get("opcode_id", frame.get("opcode")), frame, metadata) != "RETURN"]
    if not meaningful:
        return "passive", "No executable frames."

    roles = [frame_role(opcode_name(frame.get("opcode_id", frame.get("opcode")), frame, metadata), is_optional_frame(frame)) for frame in meaningful]
    ops = [opcode_name(frame.get("opcode_id", frame.get("opcode")), frame, metadata) for frame in meaningful]
    has_prompt = any(role == "prompt" for role in roles)
    has_control = any(role == "control" for role in roles)
    has_optional = any(is_optional_frame(frame) for frame in meaningful)

    if has_prompt and has_control:
        pattern = "prompted_branching"
    elif has_prompt:
        pattern = "prompted"
    elif has_control and has_optional:
        pattern = "optional_branching"
    elif has_control:
        pattern = "branching"
    elif has_optional:
        pattern = "optional_effect"
    else:
        pattern = "linear"

    step_descriptions = [describe_frame(frame, metadata) for frame in meaningful]

    if pattern == "optional_branching":
        cost_summary = next((desc for desc, role in zip(step_descriptions, roles) if role == "cost"), step_descriptions[0])
        effect_summary = next((desc for desc, role in zip(step_descriptions, roles) if role == "effect"), step_descriptions[-1])
        summary = f"Optional cost: {cost_summary.rstrip('.')}. If paid, {effect_summary[0].lower() + effect_summary[1:] if effect_summary else 'continue.'}"
    elif pattern.startswith("prompted"):
        prompt_summary = next((desc for desc, role in zip(step_descriptions, roles) if role == "prompt"), step_descriptions[0])
        tail = next((desc for desc, role in zip(step_descriptions, roles) if role == "effect"), "")
        if tail and tail != prompt_summary:
            summary = f"{prompt_summary.rstrip('.')}. Then {tail[0].lower() + tail[1:]}"
        else:
            summary = prompt_summary
    elif pattern == "branching":
        summary = " ".join(step_descriptions)
    elif pattern == "optional_effect":
        summary = step_descriptions[0]
    else:
        summary = " ".join(step_descriptions)

    return pattern, summary.strip()


def normalize_frame(frame: Dict[str, Any], metadata: Dict[str, Any], index: int) -> Dict[str, Any]:
    frame = get_frame_dict(frame)
    op = opcode_name(frame.get("opcode_id", frame.get("opcode")), frame, metadata)
    role = frame_role(op, is_optional_frame(frame))
    semantic = frame.get("semantic") if isinstance(frame.get("semantic"), dict) else {}
    summary = describe_frame(frame, metadata)
    normalized = {
        "index": index,
        "opcode_id": frame.get("opcode_id"),
        "opcode": op,
        "role": role,
        "summary": summary,
        "optional": is_optional_frame(frame),
        "negated": is_negated_frame(frame),
    }

    if "value" in frame:
        normalized["value"] = frame.get("value")

    attr = frame_attr(frame)
    if attr:
        normalized["attr"] = compact_json(attr)

    slot = frame_slot(frame)
    if slot:
        normalized["slot"] = compact_json(slot)

    if isinstance(semantic, dict) and semantic.get("decoded"):
        normalized["decoded"] = semantic["decoded"]

    return normalized


def iter_cards(payload: Dict[str, Any]) -> Iterable[Tuple[str, Dict[str, Any]]]:
    for db_name, db in payload.items():
        if not isinstance(db, dict) or not db_name.endswith("_db"):
            continue
        for _card_key, card in db.items():
            if isinstance(card, dict) and card.get("abilities"):
                yield db_name, card


def build_manifest(cards_payload: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
    cards: List[Dict[str, Any]] = []
    trigger_counts: Counter[str] = Counter()
    flow_counts: Counter[str] = Counter()
    opcode_counts: Counter[str] = Counter()

    for db_name, card in iter_cards(cards_payload):
        card_no = str(card.get("card_no", "")).strip()
        card_id = card.get("card_id")
        name = card.get("name", "")
        source_text = normalize_source_text(card)
        abilities = card.get("abilities", [])
        normalized_abilities: List[Dict[str, Any]] = []

        for ability_index, ability in enumerate(abilities):
            if not isinstance(ability, dict):
                continue

            trigger_id = int(ability.get("trigger", 0) or 0)
            trigger = trigger_name(trigger_id, metadata)
            frames = []
            frame_program = ability.get("frame_program")
            if isinstance(frame_program, dict):
                frames = frame_program.get("frames", [])
            elif isinstance(ability.get("bytecode"), list):
                frames = []

            normalized_frames = [normalize_frame(frame, metadata, idx) for idx, frame in enumerate(frames) if isinstance(frame, dict)]
            flow_pattern, summary = summarize_frames(frames, metadata)
            opcode_sequence = [frame.get("opcode") for frame in normalized_frames if frame.get("opcode")]
            trigger_counts[trigger] += 1
            flow_counts[flow_pattern] += 1
            for opcode in opcode_sequence:
                opcode_counts[str(opcode)] += 1

            normalized_abilities.append(
                {
                    "ability_index": ability_index,
                    "trigger_id": trigger_id,
                    "trigger": trigger,
                    "flow_pattern": flow_pattern,
                    "summary": summary,
                    "frame_count": len(normalized_frames),
                    "opcode_sequence": opcode_sequence,
                    "source_text": source_text,
                    "source_text_en": str(card.get("original_text_en", "") or "").strip(),
                    "frames": normalized_frames,
                    "choice_flags": int(ability.get("choice_flags", 0) or 0),
                    "choice_count": int(ability.get("choice_count", 0) or 0),
                    "requires_selection": bool(ability.get("requires_selection", False)),
                    "is_once_per_turn": bool(ability.get("is_once_per_turn", False)),
                    "card_no": card_no,
                    "card_id": card_id,
                    "name": name,
                    "db": db_name,
                }
            )

        if normalized_abilities:
            cards.append(
                {
                    "card_id": card_id,
                    "card_no": card_no,
                    "name": name,
                    "db": db_name,
                    "ability_count": len(normalized_abilities),
                    "source_text": source_text,
                    "source_text_en": str(card.get("original_text_en", "") or "").strip(),
                    "abilities": normalized_abilities,
                }
            )

    cards.sort(key=lambda entry: (str(entry.get("card_no", "")), int(entry.get("card_id", 0) or 0)))

    total_abilities = sum(card["ability_count"] for card in cards)
    summary = {
        "card_count": len(cards),
        "ability_count": total_abilities,
        "trigger_counts": dict(sorted(trigger_counts.items())),
        "flow_counts": dict(sorted(flow_counts.items())),
        "opcode_counts": dict(sorted(opcode_counts.items())),
    }

    return {
        "generated_at": utc_now(),
        "source_cards": str(DEFAULT_CARDS_PATH),
        "source_metadata": str(DEFAULT_METADATA_PATH),
        "schema": "ability_manifest.v1",
        "summary": summary,
        "cards": cards,
    }


def render_markdown(manifest: Dict[str, Any]) -> str:
    summary = manifest["summary"]
    lines: List[str] = []
    lines.append("# Ability System Manifest\n")
    lines.append(
        f"Generated: {manifest['generated_at']}  "
        f"Cards with abilities: {summary['card_count']}  "
        f"Total abilities: {summary['ability_count']}\n"
    )
    lines.append("## Summary\n")
    lines.append("| Metric | Value |\n")
    lines.append("| :-- | --: |\n")
    lines.append(f"| Cards | {summary['card_count']} |\n")
    lines.append(f"| Abilities | {summary['ability_count']} |\n")
    lines.append("\n### Trigger Counts\n")
    for name, count in summary["trigger_counts"].items():
        lines.append(f"- `{name}`: {count}\n")
    lines.append("\n### Flow Counts\n")
    for name, count in summary["flow_counts"].items():
        lines.append(f"- `{name}`: {count}\n")
    lines.append("\n## Cards\n")

    for card in manifest["cards"]:
        lines.append(f"### {card['card_no']} - {card['name']}\n")
        lines.append(f"- `card_id`: {card['card_id']}\n")
        lines.append(f"- `db`: `{card['db']}`\n")
        if card["source_text"]:
            lines.append(f"- `source_text`:\n\n```text\n{card['source_text']}\n```\n")
        for ability in card["abilities"]:
            lines.append(f"#### Ability {ability['ability_index'] + 1}\n")
            lines.append(f"- `trigger`: `{ability['trigger']}`\n")
            lines.append(f"- `flow_pattern`: `{ability['flow_pattern']}`\n")
            lines.append(f"- `summary`: {ability['summary']}\n")
            lines.append(f"- `opcode_sequence`: `{', '.join(ability['opcode_sequence'])}`\n")
            if ability["source_text_en"]:
                lines.append(f"- `source_text_en`: {ability['source_text_en']}\n")
            lines.append("\n| # | Role | Opcode | Summary |\n")
            lines.append("| :-- | :-- | :-- | :-- |\n")
            for frame in ability["frames"]:
                lines.append(
                    f"| {frame['index']} | {frame['role']} | `{frame['opcode']}` | {frame['summary'].replace('|', '\\|')} |\n"
                )
            lines.append("\n")

    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a normalized ability manifest for every compiled ability.")
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS_PATH, help="Path to cards_compiled.json")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Path to metadata.json")
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON_PATH, help="Output path for manifest JSON")
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_PATH, help="Output path for manifest Markdown")
    args = parser.parse_args()

    cards_payload = load_json(args.cards)
    metadata = load_json(args.metadata)
    manifest = build_manifest(cards_payload, metadata)

    dump_json(args.json_out, manifest)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.md_out, "w", encoding="utf-8") as handle:
        handle.write(render_markdown(manifest))

    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.md_out}")


if __name__ == "__main__":
    main()
