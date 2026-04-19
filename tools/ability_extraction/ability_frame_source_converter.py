"""Compact, reversible converter for `data/ability_frame_source.json`."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


IGNORE_FRAME_KEYS = {"op", "opcode", "opcode_name", "kind", "frame_index"}
VALUE_KEYS = ("value",)

COMPARISON_TO_SYMBOL = {
    "GE": ">=",
    "GT": ">",
    "LE": "<=",
    "LT": "<",
    "EQ": "==",
    "NE": "!=",
}

SYMBOL_TO_COMPARISON = {symbol: code for code, symbol in COMPARISON_TO_SYMBOL.items()}


def load_json(path: Path | str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _normalize_op(frame: Any) -> str:
    if isinstance(frame, str):
        return frame.strip().upper()

    if isinstance(frame, dict):
        op = frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind")
        if op is not None:
            return str(op).strip().upper()

        if len(frame) == 1:
            key = next(iter(frame))
            return str(key).strip().upper()

    raise ValueError(f"Unable to determine opcode from frame: {frame!r}")


def frame_to_compact(frame: Any) -> Any:
    """Convert one canonical frame into a shorter reversible representation."""

    if isinstance(frame, str):
        return [_normalize_op(frame)]

    if not isinstance(frame, dict):
        return deepcopy(frame)

    op = _normalize_op(frame)
    frame_index = frame.get("frame_index")
    value_present = any(key in frame for key in VALUE_KEYS)
    value = frame.get("value") if value_present else None

    extras = {
        key: deepcopy(value)
        for key, value in frame.items()
        if key not in IGNORE_FRAME_KEYS and key not in VALUE_KEYS
    }
    if frame_index is not None:
        extras["frame_index"] = deepcopy(frame_index)

    if not extras and not value_present:
        return [op]

    if not extras:
        return [op, deepcopy(value)]

    if value_present:
        return [op, deepcopy(value), extras]

    return [op, None, extras]


def frame_from_compact(frame: Any, frame_index: int) -> dict[str, Any]:
    """Expand a compact frame back into the canonical runtime-friendly object."""

    if isinstance(frame, str):
        return {"op": frame.strip().upper(), "frame_index": frame_index}

    if not isinstance(frame, list) or not frame:
        raise ValueError(f"Compact frame must be a non-empty list or string: {frame!r}")

    op = _normalize_op(frame[0])
    canonical: dict[str, Any] = {"op": op, "frame_index": frame_index}

    if len(frame) == 2:
        canonical["value"] = deepcopy(frame[1])
        return canonical

    if len(frame) >= 3:
        value = frame[1]
        if value is not None:
            canonical["value"] = deepcopy(value)

        extras = frame[2] if isinstance(frame[2], dict) else {}
        if "frame_index" in extras:
            canonical["frame_index"] = deepcopy(extras["frame_index"])
        else:
            canonical["frame_index"] = frame_index
        for key, value in extras.items():
            if key == "frame_index":
                continue
            canonical[key] = deepcopy(value)
        return canonical

    return canonical


def canonical_to_compact_payload(payload: dict[str, Any]) -> dict[str, Any]:
    compact = deepcopy(payload)
    compact["schema"] = "ability_frame_source.compact.v1"

    abilities = []
    for ability in payload.get("abilities", []):
        if not isinstance(ability, dict):
            abilities.append(deepcopy(ability))
            continue
        compact_ability = deepcopy(ability)
        frames = ability.get("frames", [])
        compact_ability["frames"] = [frame_to_compact(frame) for frame in frames]
        abilities.append(compact_ability)
    compact["abilities"] = abilities
    return compact


def compact_to_canonical_payload(payload: dict[str, Any]) -> dict[str, Any]:
    canonical = deepcopy(payload)
    canonical["schema"] = "ability_frame_source.flat.v2"

    abilities = []
    for ability in payload.get("abilities", []):
        if not isinstance(ability, dict):
            abilities.append(deepcopy(ability))
            continue
        canonical_ability = deepcopy(ability)
        frames = ability.get("frames", [])
        canonical_ability["frames"] = [frame_from_compact(frame, idx) for idx, frame in enumerate(frames)]
        abilities.append(canonical_ability)
    canonical["abilities"] = abilities
    return canonical


def convert_file(input_path: Path | str, output_path: Path | str, *, expand: bool = False) -> dict[str, Any]:
    payload = load_json(input_path)
    converted = compact_to_canonical_payload(payload) if expand else canonical_to_compact_payload(payload)
    dump_json(output_path, converted)
    return converted


def comparison_code_to_symbol(code: str) -> str:
    return COMPARISON_TO_SYMBOL.get(str(code).upper(), str(code))


def comparison_symbol_to_code(symbol: str) -> str:
    return SYMBOL_TO_COMPARISON.get(str(symbol).strip(), str(symbol).upper())


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input JSON file")
    parser.add_argument("output", type=Path, help="Output JSON file")
    parser.add_argument("--expand", action="store_true", help="Expand compact source back to canonical JSON")
    parser.add_argument("--check-roundtrip", action="store_true", help="Convert there and back and verify equality")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    if args.check_roundtrip:
        original = load_json(args.input)
        compact = canonical_to_compact_payload(original)
        restored = compact_to_canonical_payload(compact)
        if restored != original:
            raise SystemExit("Round-trip check failed: compact conversion did not preserve the canonical payload")
        dump_json(args.output, compact)
        return 0

    convert_file(args.input, args.output, expand=args.expand)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
