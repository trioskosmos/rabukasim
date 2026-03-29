from __future__ import annotations

"""Repair stale summary text in data/consolidated_abilities.json.

This normalizes a small set of known representation bugs:
- LOOK_AND_CHOOSE summaries/pseudocode that were written with 0/0 placeholders.
- Missing frame metadata fields on a small number of legacy frames.
"""

import json
import re
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT_DIR / "data" / "consolidated_abilities.json"


LOOK_SUMMARY_RE = re.compile(r"^Look at \d+ card\(s\) and choose \d+\.")
LOOK_DECoded_RE = re.compile(r"look=(\d+)")
LOOK_UP_TO_RE = re.compile(r"up to\s+(\d+)", re.IGNORECASE)
LOOK_EXPLICIT_RE = re.compile(r"\b(?:reveal|add|choose)\s+(?:up to\s+)?(\d+)\b", re.IGNORECASE)
ANY_NUMBER_RE = re.compile(r"any number", re.IGNORECASE)


def _infer_look_count(frame: dict[str, Any]) -> int:
    decoded = str(frame.get("decoded", ""))
    match = LOOK_DECoded_RE.search(decoded)
    if match:
        return int(match.group(1))
    return int(frame.get("value", 0) or 0)


def _infer_choose_text(entry: dict[str, Any], frame: dict[str, Any], look_count: int) -> str:
    """Return either a numeric count or a generic phrase."""
    source_text_en = str(entry.get("source_text_en", "") or "")
    source_text = str(entry.get("source_text", "") or "")
    text = f"{source_text_en} {source_text}".strip()

    if ANY_NUMBER_RE.search(text):
        return "from them"

    match = LOOK_UP_TO_RE.search(text)
    if match:
        return match.group(1)

    match = LOOK_EXPLICIT_RE.search(text)
    if match:
        return match.group(1)

    # If the source text explicitly says one card/member/live, the safe default is 1.
    if re.search(r"\b1\s+(?:card|member|live)\b", text, re.IGNORECASE):
        return "1"

    # Fall back to a generic phrase instead of guessing wrong.
    return "from them"


def _format_look_and_choose_summary(entry: dict[str, Any], frame: dict[str, Any]) -> str:
    look_count = _infer_look_count(frame)
    choose_text = _infer_choose_text(entry, frame, look_count)
    if choose_text == "from them":
        return f"Look at {look_count} card(s) and choose from them."
    return f"Look at {look_count} card(s) and choose {choose_text}."


def _format_move_to_discard_summary(frame: dict[str, Any]) -> str:
    decoded = str(frame.get("decoded", ""))
    value_match = re.search(r"count=(\d+)", decoded)
    value = value_match.group(1) if value_match else str(frame.get("value", 1) or 1)
    slot = frame.get("slot") if isinstance(frame.get("slot"), dict) else {}
    source_zone = str(slot.get("source_zone", "hand")).lower().replace("_", " ")
    dest_zone = str(slot.get("dest_zone", "discard")).lower().replace("_", " ")
    return f"Move {value} matching card(s) from {source_zone} to {dest_zone}."


def _normalize_frame_metadata(entry: dict[str, Any], frame: dict[str, Any], index: int) -> bool:
    changed = False
    if "index" not in frame:
        frame["index"] = index
        changed = True
    if "negated" not in frame:
        frame["negated"] = False
        changed = True
    if "optional" not in frame:
        frame["optional"] = bool(frame.get("attr", {}).get("is_optional", False))
        changed = True
    if "role" not in frame:
        opcode = str(frame.get("opcode", "")).upper()
        if opcode in {"RETURN", "JUMP", "JUMP_IF_FALSE"}:
            frame["role"] = "control"
        elif opcode in {"LOOK_AND_CHOOSE", "SELECT_MODE", "COLOR_SELECT", "ORDER_DECK", "SELECT_MEMBER", "SELECT_CARDS"}:
            frame["role"] = "prompt"
        elif opcode in {"PAY_ENERGY", "SET_TAPPED", "TAP_MEMBER", "MOVE_TO_DISCARD"}:
            frame["role"] = "cost"
        else:
            frame["role"] = "effect"
        changed = True

    opcode = str(frame.get("opcode", "")).upper()
    if opcode == "LOOK_AND_CHOOSE":
        new_summary = _format_look_and_choose_summary(entry, frame)
        if frame.get("summary") != new_summary:
            frame["summary"] = new_summary
            changed = True
    elif opcode == "MOVE_TO_DISCARD" and "summary" not in frame:
        frame["summary"] = _format_move_to_discard_summary(frame)
        changed = True

    return changed


def _replace_leading_summary(text: str, new_summary: str) -> str:
    if not text:
        return text
    return re.sub(
        r"^Look at \d+ card\(s\) and choose \d+\.",
        new_summary,
        text,
        count=1,
    )


def main() -> int:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    changed = False
    repaired_frames = 0
    repaired_entries = 0

    for key, entry in data.items():
        if key == "_metadata" or not isinstance(entry, dict):
            continue

        entry_changed = False
        frames = entry.get("frames", [])
        if isinstance(frames, list):
            for index, frame in enumerate(frames):
                if not isinstance(frame, dict):
                    continue
                if _normalize_frame_metadata(entry, frame, index):
                    entry_changed = True
                    repaired_frames += 1

        for field in ("summary", "pseudocode"):
            value = str(entry.get(field, "") or "")
            if value.startswith("Look at 0 card(s) and choose 0."):
                look_frame = next(
                    (frame for frame in frames if isinstance(frame, dict) and str(frame.get("opcode", "")).upper() == "LOOK_AND_CHOOSE"),
                    None,
                )
                if look_frame is not None:
                    new_summary = _format_look_and_choose_summary(entry, look_frame)
                    updated = _replace_leading_summary(value, new_summary)
                    if updated != value:
                        entry[field] = updated
                        entry_changed = True
                continue

        if entry_changed:
            repaired_entries += 1
            changed = True

    if changed:
        with open(DATA_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"repaired_entries={repaired_entries}")
    print(f"repaired_frames={repaired_frames}")
    print(f"changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
