"""Render `data/ability_frame_source.json` as a human-readable rules view."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.ability_frame_source_converter import load_json


COUNT_OP_LABELS = {
    "COUNT_STAGE": "stage",
    "COUNT_HAND": "hand",
    "COUNT_DISCARD": "discard",
    "COUNT_ENERGY": "energy",
    "COUNT_HEARTS": "hearts",
    "COUNT_BLADES": "blades",
    "COUNT_LIVE_ZONE": "live",
    "COUNT_SUCCESS_LIVE": "success_live",
    "COUNT_SUCCESS_LIVE_SCORE": "success_live_score",
    "COUNT_GROUP": "group",
    "COUNT_LIVE_HEARTS": "live_hearts",
}

COMPARISON_TO_SYMBOL = {
    "GE": ">=",
    "GT": ">",
    "LE": "<=",
    "LT": "<",
    "EQ": "==",
    "NE": "!=",
}

SYMBOL_TO_COMPARISON = {symbol: code for code, symbol in COMPARISON_TO_SYMBOL.items()}


def describe_zone(zone: Any) -> str:
    if zone is None:
        return ""
    text = str(zone).replace("_", " ").strip().lower()
    return text


def describe_slot(slot: dict[str, Any] | None) -> str:
    if not slot:
        return ""

    parts: list[str] = []
    source_zone = slot.get("source_zone")
    dest_zone = slot.get("dest_zone")
    target_slot = slot.get("target_slot")
    remainder_zone = slot.get("remainder_zone")
    comparison = slot.get("comparison")

    if source_zone:
        parts.append(f"from {describe_zone(source_zone)}")
    if dest_zone:
        parts.append(f"to {describe_zone(dest_zone)}")
    if remainder_zone:
        parts.append(f"remainder {describe_zone(remainder_zone)}")
    if target_slot:
        parts.append(f"target {describe_zone(target_slot)}")
    if comparison:
        parts.append(f"cmp {describe_zone(comparison)}")

    return " ".join(parts)


def describe_count_expr(frame: dict[str, Any]) -> str:
    op = frame.get("op", "")
    zone = COUNT_OP_LABELS.get(op, op.removeprefix("COUNT_").lower())
    value = frame.get("value")
    slot = frame.get("slot") if isinstance(frame.get("slot"), dict) else {}
    comparison_code = str(slot.get("comparison") or "").upper() if slot else ""
    comparator = COMPARISON_TO_SYMBOL.get(comparison_code, ">=")
    threshold = value if value is not None else slot.get("value_threshold", 0) if slot else 0
    return f"count({zone}) {comparator} {threshold}"


def describe_select_mode(frame: dict[str, Any]) -> str:
    options = frame.get("option_names") or []
    if options:
        return "choose_mode [" + ", ".join(f'"{opt}"' for opt in options) + "]"
    value = frame.get("value")
    return f"choose_mode x{value or 0}"


def describe_frame(frame: dict[str, Any]) -> str:
    op = str(frame.get("op", "UNKNOWN")).upper()
    value = frame.get("value")
    slot = frame.get("slot") if isinstance(frame.get("slot"), dict) else {}
    attr = frame.get("attr") if isinstance(frame.get("attr"), dict) else {}
    params = frame.get("params") if isinstance(frame.get("params"), dict) else {}
    parts: list[str] = []

    if op == "RETURN":
        return "end"
    if op == "JUMP":
        return f"jump +{value or 0}"
    if op == "JUMP_IF_FALSE":
        return f"if previous check fails -> jump +{value or 0}"
    if op == "SELECT_MODE":
        return describe_select_mode(frame)
    if op in COUNT_OP_LABELS or op.startswith("COUNT_"):
        return describe_count_expr(frame)
    if op == "DRAW":
        return f"draw {value or 1}"
    if op == "MOVE_TO_DISCARD":
        src = describe_zone(slot.get("source_zone"))
        dst = describe_zone(slot.get("dest_zone"))
        tail = f" from {src}" if src else ""
        if dst:
            tail += f" to {dst}"
        return f"discard {value or 1}{tail}".strip()
    if op == "MOVE_MEMBER":
        return f"move member {value or 1} {describe_slot(slot)}".strip()
    if op == "RECOVER_LIVE":
        return f"recover live {value or 1} {describe_slot(slot)}".strip()
    if op == "RECOVER_MEMBER":
        return f"recover member {value or 1} {describe_slot(slot)}".strip()
    if op == "ACTIVATE_MEMBER":
        return f"activate member {value or 1} {describe_slot(slot)}".strip()
    if op == "ACTIVATE_ENERGY":
        return f"activate energy {value or 1} {describe_slot(slot)}".strip()
    if op == "ADD_HEARTS":
        return f"add hearts {value or 1} {describe_slot(slot)}".strip()
    if op == "ADD_BLADES":
        return f"add blades {value or 1} {describe_slot(slot)}".strip()
    if op == "BOOST_SCORE":
        return f"boost score {value or 1} {describe_slot(slot)}".strip()
    if op == "PAY_ENERGY":
        return f"pay energy {value or 0}".strip()
    if op == "LOOK_AND_CHOOSE":
        count = value if isinstance(value, int) else (value or {}).get("count", 0) if isinstance(value, dict) else 0
        return f"look and choose {count or 0} {describe_slot(slot)}".strip()
    if op == "LOOK_DECK":
        return f"look deck {value or 0} {describe_slot(slot)}".strip()
    if op == "SELECT_MEMBER":
        return f"select member {value or 1} {describe_slot(slot)}".strip()
    if op == "SELECT_LIVE":
        return f"select live {value or 1} {describe_slot(slot)}".strip()
    if op == "SELECT_CARDS":
        return f"select cards {value or 1} {describe_slot(slot)}".strip()
    if op == "SELECT_PLAYER":
        return f"select player {value or 1}".strip()

    if attr:
        parts.extend(f"{key}={value}" for key, value in attr.items())
    if slot:
        parts.append(describe_slot(slot))
    if params:
        parts.extend(f"{key}={value}" for key, value in params.items())
    if value is not None:
        parts.append(f"x{value}")
    suffix = f" ({', '.join(parts)})" if parts else ""
    return f"{op.lower()}{suffix}"


def _render_block(frames: list[dict[str, Any]], indent: int = 0) -> list[str]:
    lines: list[str] = []
    pad = "  " * indent
    i = 0
    while i < len(frames):
        frame = frames[i]
        op = str(frame.get("op", "")).upper()

        if op == "RETURN":
            lines.append(f"{pad}end")
            i += 1
            continue

        if op.startswith("COUNT_") and i + 1 < len(frames) and str(frames[i + 1].get("op", "")).upper() == "JUMP_IF_FALSE":
            lines.append(f"{pad}if {describe_count_expr(frame)}:")
            j = i + 2
            body: list[dict[str, Any]] = []
            while j < len(frames):
                next_op = str(frames[j].get("op", "")).upper()
                if next_op == "RETURN":
                    break
                if next_op == "JUMP":
                    break
                body.append(frames[j])
                j += 1
            lines.extend(_render_block(body, indent + 1))
            i = j
            continue

        if op == "SELECT_MODE":
            option_names = frame.get("option_names") or []
            branch_count = int(frame.get("value") or len(option_names) or 0)
            lines.append(f"{pad}{describe_select_mode(frame)}:")
            j = i + 1
            # Skip the branch table JUMPs.
            while j < len(frames) and str(frames[j].get("op", "")).upper() == "JUMP":
                j += 1
            for branch_idx in range(branch_count):
                lines.append(f"{pad}  option {branch_idx + 1}:")
                body: list[dict[str, Any]] = []
                while j < len(frames):
                    next_op = str(frames[j].get("op", "")).upper()
                    if next_op in {"JUMP", "RETURN"}:
                        break
                    body.append(frames[j])
                    j += 1
                lines.extend(_render_block(body, indent + 2))
                if j < len(frames) and str(frames[j].get("op", "")).upper() == "JUMP":
                    j += 1
            i = j
            continue

        lines.append(f"{pad}- {describe_frame(frame)}")
        i += 1

    return lines


def render_simple_view(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"schema: {payload.get('schema', 'ability_frame_source.flat.v2')}")
    lines.append("")
    abilities = payload.get("abilities", [])
    for idx, ability in enumerate(abilities, start=1):
        if not isinstance(ability, dict):
            continue
        trigger = str(ability.get("trigger", "UNKNOWN")).lower()
        refs = ability.get("card_refs") or []
        card_label = ""
        if refs and isinstance(refs[0], dict):
            ref = refs[0]
            card_label = str(ref.get("card_no") or ref.get("card_id") or "")
        title = f"{idx:04d}. {trigger}"
        if card_label:
            title += f" [{card_label}]"
        lines.append(title)

        text = str(ability.get("primary_text_jp", "")).strip()
        if text:
            lines.append(f"  text: {text}")

        lines.append(f"  meta: {json.dumps(ability, ensure_ascii=False)}")

        frames = ability.get("frames") or []
        if isinstance(frames, list) and frames:
            lines.extend(_render_block([f for f in frames if isinstance(f, dict)], indent=1))
        else:
            lines.append("  - no frames")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


_ABILITY_HEADER_RE = re.compile(r"^(?P<idx>\d+)\.\s+(?P<trigger>[a-z_]+)(?:\s+\[(?P<label>.+)\])?$")


def parse_simple_view(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    schema = "ability_frame_source.flat.v2"
    abilities: list[dict[str, Any]] = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("schema:"):
            schema = stripped.split(":", 1)[1].strip() or schema
            i += 1
            continue

        header_match = _ABILITY_HEADER_RE.match(stripped)
        if not header_match:
            i += 1
            continue

        block_start = i + 1
        block_end = block_start
        while block_end < len(lines):
            next_line = lines[block_end].rstrip()
            next_stripped = next_line.strip()
            if next_stripped and _ABILITY_HEADER_RE.match(next_stripped):
                break
            block_end += 1

        block_lines = lines[block_start:block_end]
        meta_obj: dict[str, Any] | None = None
        for block_line in block_lines:
            if block_line.strip().startswith("meta:"):
                raw_meta = block_line.strip().split(":", 1)[1].strip()
                if raw_meta:
                    meta_obj = json.loads(raw_meta)
                break

        if meta_obj is None:
            raise ValueError(f"Missing meta block for ability at line {i + 1}")

        abilities.append(meta_obj)
        i = block_end

    return {"schema": schema, "abilities": abilities}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Authored ability source JSON")
    parser.add_argument("output", type=Path, help="Markdown/text output path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = load_json(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_simple_view(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
