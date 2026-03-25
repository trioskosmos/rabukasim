from __future__ import annotations

"""Generate and archive a bytecode atlas for cards.

This remains intentionally closer to the existing 5-word bytecode layout than
to the authored semantic frame source. The goal is to make every word traceable
back to:

* the opcode / target / trigger metadata in ``data/metadata.json``
* the code paths that compile or decode that word

The output is a structured catalog that can be consumed as JSON or rendered as
markdown later if we want a human-friendly report.
"""

import argparse
import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.models import bytecode_readable as readable
from engine.models.generated_packer import (
    unpack_a_heart_cost,
    unpack_a_standard,
    unpack_s_standard,
    unpack_v_heart_counts,
    unpack_v_look_choose,
    unpack_v_scalar_dynamic,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_COMPILED_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "archive" / "reports" / "bytecode_catalog.json"
DEFAULT_MARKDOWN_PATH = ROOT_DIR / "archive" / "reports" / "bytecode_catalog.md"


COMMON_CODE_REFS = [
    "engine/models/bytecode_readable.py:decode_bytecode",
    "engine/models/bytecode_readable.py:decode_chunk",
]

WORD_CODE_REFS = {
    "opcode": [
        "engine/models/bytecode_readable.py:decode_chunk",
        "compiler/main.py:validate_bytecode",
    ],
    "value": [
        "compiler/ability_compiler.py:compile_to_bytecode",
        "engine/models/bytecode_readable.py:decode_chunk",
    ],
    "offset": [
        "compiler/ability_compiler.py:compile_to_bytecode",
        "compiler/main.py:validate_bytecode",
        "engine/models/bytecode_readable.py:decode_chunk",
    ],
    "packed_attr_low": [
        "compiler/ability_compiler.py:_pack_filter_attr",
        "engine/models/generated_packer.py:pack_a_standard",
        "engine/models/bytecode_readable.py:decode_filter",
    ],
    "packed_attr_high": [
        "compiler/ability_compiler.py:_pack_filter_attr",
        "engine/models/generated_packer.py:pack_a_standard",
        "engine/models/bytecode_readable.py:decode_filter",
    ],
    "slot": [
        "compiler/ability_compiler.py:_resolve_effect_target",
        "compiler/ability_compiler.py:_resolve_effect_source_zone",
        "engine/models/bytecode_readable.py:decode_standard_slot",
    ],
}

OPCODE_CODE_REFS = {
    "SELECT_MODE": [
        "compiler/ability_compiler.py:compile_to_bytecode",
        "compiler/ability_compiler.py:_compile_single_effect",
        "compiler/ability_compiler.py:SELECT_MODE jump-table branch",
    ],
    "LOOK_AND_CHOOSE": [
        "compiler/ability_compiler.py:_pack_effect_look_and_choose",
        "engine/models/generated_packer.py:pack_v_look_choose",
        "engine/models/bytecode_readable.py:_decode_look_and_choose",
    ],
    "SET_HEART_COST": [
        "compiler/ability_compiler.py:_pack_effect_heart_cost",
        "engine/models/generated_packer.py:pack_v_heart_counts",
        "engine/models/generated_packer.py:pack_a_heart_cost",
        "engine/models/bytecode_readable.py:_decode_set_heart_cost",
    ],
    "CALC_SUM_COST": [
        "compiler/ability_compiler.py:_resolve_effect_dynamic_multiplier",
        "engine/models/generated_packer.py:pack_v_scalar_dynamic",
    ],
    "JUMP": [
        "compiler/ability_compiler.py:compile_to_bytecode",
        "compiler/main.py:validate_bytecode",
    ],
    "JUMP_IF_FALSE": [
        "compiler/ability_compiler.py:compile_to_bytecode",
        "compiler/main.py:validate_bytecode",
    ],
    "RETURN": [
        "compiler/ability_compiler.py:compile_to_bytecode",
        "compiler/main.py:validate_bytecode",
    ],
}


@dataclass(slots=True)
class CatalogPaths:
    compiled_path: Path
    metadata_path: Path
    output_path: Path


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def dump_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(text)


def reverse_map(mapping: dict[str, Any]) -> dict[int, str]:
    return {int(value): key for key, value in mapping.items()}


def sorted_items(mapping: dict[str, Any]) -> Iterable[tuple[str, Any]]:
    def sort_key(item: tuple[str, Any]) -> tuple[int, str]:
        key, _ = item
        return (0, f"{int(key):08d}") if str(key).isdigit() else (1, str(key))

    return sorted(mapping.items(), key=sort_key)


def split_frames(bytecode: list[int]) -> list[list[int]]:
    frames = []
    for i in range(0, len(bytecode), 5):
        frame = list(bytecode[i : i + 5])
        if len(frame) < 5:
            frame.extend([0] * (5 - len(frame)))
        frames.append(frame)
    return frames


def opcode_name(opcode: int) -> str:
    return readable.OPCODE_NAMES.get(int(opcode), f"OP_{opcode}")


def trigger_name(trigger: int) -> str:
    return readable.TRIGGER_NAMES.get(int(trigger), f"TRIGGER_{trigger}")


def _metadata_slot_ref(slot_value: int, metadata: dict[str, Any]) -> str | None:
    slot_indices = reverse_map(metadata.get("slot_indices", {}))
    target_players = reverse_map(metadata.get("target_players", {}))

    if slot_value in target_players:
        return f"target_players.{target_players[slot_value]}"
    if slot_value in slot_indices:
        return f"slot_indices.{slot_indices[slot_value]}"
    return None


def metadata_refs_for_opcode(op_name: str, metadata: dict[str, Any], frame: list[int]) -> list[str]:
    refs = [f"opcodes.{op_name}"] if op_name in metadata.get("opcodes", {}) else []

    if op_name in metadata.get("triggers", {}):
        refs.append(f"triggers.{op_name}")

    if op_name in metadata.get("targets", {}):
        refs.append(f"targets.{op_name}")

    if op_name in metadata.get("conditions", {}):
        refs.append(f"conditions.{op_name}")

    if op_name in metadata.get("costs", {}):
        refs.append(f"costs.{op_name}")

    # Slot/target hints derived from the frame's last word.
    slot_ref = _metadata_slot_ref(int(frame[4]), metadata)
    if slot_ref:
        refs.append(slot_ref)

    return list(dict.fromkeys(refs))


def code_refs_for_opcode(op_name: str) -> list[str]:
    refs = list(COMMON_CODE_REFS)
    refs.extend(WORD_CODE_REFS.get("value", []))
    refs.extend(WORD_CODE_REFS.get("packed_attr_low", []))
    refs.extend(WORD_CODE_REFS.get("packed_attr_high", []))
    refs.extend(WORD_CODE_REFS.get("slot", []))
    refs.extend(OPCODE_CODE_REFS.get(op_name, []))
    return list(dict.fromkeys(refs))


def word_role(op_name: str, index: int) -> str:
    if index == 0:
        return "opcode"

    if op_name in {"JUMP", "JUMP_IF_FALSE"}:
        return ["offset", "padding", "padding", "padding"][index - 1] if index > 0 else "opcode"

    if op_name == "SELECT_MODE":
        if index == 1:
            return "option_count"
        if index == 4:
            return "choice_target"
        return ["padding", "padding", "padding"][index - 1]

    if op_name == "LOOK_AND_CHOOSE":
        if index == 1:
            return "look_value"
        if index == 2:
            return "packed_attr_low"
        if index == 3:
            return "packed_attr_high"
        if index == 4:
            return "slot"

    if op_name == "SET_HEART_COST":
        if index == 1:
            return "heart_value"
        if index == 2:
            return "packed_req_low"
        if index == 3:
            return "packed_req_high"
        if index == 4:
            return "slot"

    if op_name == "CALC_SUM_COST":
        if index == 1:
            return "value"
        if index == 2:
            return "packed_attr_low"
        if index == 3:
            return "packed_attr_high"
        if index == 4:
            return "slot"

    if op_name in {"RETURN", "NOP"}:
        return ["value", "padding", "padding", "padding"][index - 1] if index > 0 else "opcode"

    if index == 1:
        return "value"
    if index in (2, 3):
        return "packed_attr_low" if index == 2 else "packed_attr_high"
    if index == 4:
        return "slot"
    return f"word_{index}"


def unpack_word_payload(op_name: str, frame: list[int]) -> dict[str, Any]:
    op, v, a, s, _ = frame

    payload: dict[str, Any] = {
        "raw": {
            "opcode": int(op),
            "value": int(v),
            "attr": int(a),
            "slot": int(s),
        }
    }

    if op_name == "LOOK_AND_CHOOSE":
        payload["v"] = unpack_v_look_choose(v)
        payload["a"] = unpack_a_standard(a)
        payload["s"] = unpack_s_standard(s)
    elif op_name == "SET_HEART_COST":
        payload["v"] = unpack_v_heart_counts(v)
        payload["a"] = unpack_a_heart_cost(a)
        payload["s"] = unpack_s_standard(s)
    elif op_name == "CALC_SUM_COST":
        payload["v"] = unpack_v_scalar_dynamic(v)
        payload["a"] = unpack_a_standard(a)
        payload["s"] = unpack_s_standard(s)
    else:
        slot = unpack_s_standard(s)
        if slot.get("is_dynamic"):
            payload["v"] = unpack_v_scalar_dynamic(v)["base_value"]
        else:
            payload["v"] = int(v)
        payload["a"] = unpack_a_standard(a)
        payload["s"] = slot

    return payload


def annotate_frame(frame: list[int], metadata: dict[str, Any]) -> dict[str, Any]:
    padded = list(frame[:5])
    if len(padded) < 5:
        padded.extend([0] * (5 - len(padded)))

    op, v, a, s, _ = padded
    op_name = opcode_name(op)
    decoded = readable.decode_chunk(padded)

    words = []
    for index, value in enumerate(padded):
        role = word_role(op_name, index)
        metadata_refs: list[str] = []
        code_refs = list(WORD_CODE_REFS.get(role, []))
        if index == 0:
            if op_name in metadata.get("opcodes", {}):
                metadata_refs.append(f"metadata.opcodes.{op_name}")
        elif index == 4:
            slot_ref = _metadata_slot_ref(int(value), metadata)
            if slot_ref:
                metadata_refs.append(f"metadata.{slot_ref}")

        words.append(
            {
                "index": index,
                "raw": int(value),
                "role": role,
                "metadata_refs": list(dict.fromkeys(metadata_refs)),
                "code_refs": list(dict.fromkeys(code_refs + code_refs_for_opcode(op_name))),
            }
        )

    return {
        "opcode": int(op),
        "opcode_name": op_name,
        "opcode_metadata": f"opcodes.{op_name}" if op_name in metadata.get("opcodes", {}) else None,
        "decoded": decoded,
        "payload": unpack_word_payload(op_name, padded),
        "words": words,
        "metadata_refs": metadata_refs_for_opcode(op_name, metadata, padded),
        "code_refs": code_refs_for_opcode(op_name),
    }


def build_card_entry(db_name: str, card_id: str, card: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    abilities = []
    for ab_idx, ability in enumerate(card.get("abilities", [])):
        bytecode = list(ability.get("bytecode", []))
        if not bytecode:
            continue

        frames = [annotate_frame(frame, metadata) for frame in split_frames(bytecode)]
        abilities.append(
            {
                "ability_index": ab_idx,
                "trigger": trigger_name(int(ability.get("trigger", 0))),
                "raw_text": ability.get("raw_text", ""),
                "pseudocode": ability.get("pseudocode", ""),
                "bytecode": bytecode,
                "decoded_trace": readable.decode_bytecode(bytecode),
                "frames": frames,
                "summary": ability.get("semantic_form", {}).get("instructions_summary", ""),
                "metadata_refs": list(dict.fromkeys(ref for frame in frames for ref in frame["metadata_refs"])),
            }
        )

    return {
        "db": db_name,
        "card_id": int(card_id) if str(card_id).isdigit() else card_id,
        "card_no": card.get("card_no", ""),
        "name": card.get("name", ""),
        "ability_count": len(abilities),
        "abilities": abilities,
    }


def build_catalog(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    cards = []
    opcode_counts: Counter[str] = Counter()
    frame_counts: Counter[str] = Counter()
    for db_name in ("member_db", "live_db", "energy_db"):
        db = compiled_data.get(db_name, {})
        for card_id, card in sorted_items(db):
            entry = build_card_entry(db_name, card_id, card, metadata)
            if entry["ability_count"] > 0:
                for ability in entry["abilities"]:
                    for frame in ability["frames"]:
                        opcode_counts[frame["opcode_name"]] += 1
                        frame_counts[frame["words"][0]["role"]] += 1
                cards.append(entry)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(DEFAULT_COMPILED_PATH),
        "metadata_source": str(DEFAULT_METADATA_PATH),
        "layout": {
            "words_per_frame": 5,
            "frame_order": ["opcode", "value", "attr_low", "attr_high", "slot"],
        },
        "summary": {
            "card_count": len(cards),
            "ability_count": sum(card["ability_count"] for card in cards),
            "opcode_counts": dict(sorted(opcode_counts.items(), key=lambda item: (-item[1], item[0]))),
            "frame_roles": dict(sorted(frame_counts.items(), key=lambda item: (-item[1], item[0]))),
        },
        "cards": cards,
    }


def render_markdown(catalog: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Bytecode Catalog")
    lines.append("")
    lines.append(f"- Generated: `{catalog['generated_at']}`")
    lines.append(f"- Source: `{catalog['source']}`")
    lines.append(f"- Metadata: `{catalog['metadata_source']}`")
    lines.append(f"- Cards indexed: `{catalog['summary']['card_count']}`")
    lines.append(f"- Abilities indexed: `{catalog['summary']['ability_count']}`")
    lines.append("")
    lines.append("## Opcode Counts")
    lines.append("")
    for opcode_name, count in catalog["summary"]["opcode_counts"].items():
        lines.append(f"- `{opcode_name}`: {count}")
    lines.append("")
    lines.append("## Card Index")
    lines.append("")

    for card in catalog["cards"]:
        lines.append(f"### {card['name']} (`{card['card_no']}`)")
        lines.append(f"- DB: `{card['db']}`")
        lines.append(f"- Card ID: `{card['card_id']}`")
        lines.append(f"- Abilities: `{card['ability_count']}`")
        lines.append("")

        for ability in card["abilities"]:
            lines.append(f"#### Ability {ability['ability_index']}: `{ability['trigger']}`")
            if ability["summary"]:
                lines.append(f"- Summary: {ability['summary']}")
            if ability["pseudocode"]:
                lines.append("```text")
                lines.append(ability["pseudocode"])
                lines.append("```")
            lines.append("")
            for frame_index, frame in enumerate(ability["frames"]):
                lines.append(
                    f"- Frame {frame_index}: `{frame['opcode_name']}` "
                    f"words=({', '.join(str(word['raw']) for word in frame['words'])})"
                )
                if frame["metadata_refs"]:
                    lines.append(f"  - Metadata: {', '.join(f'`{ref}`' for ref in frame['metadata_refs'])}")
                if frame["code_refs"]:
                    preview = frame["code_refs"][:4]
                    suffix = " ..." if len(frame["code_refs"]) > 4 else ""
                    lines.append(f"  - Code: {', '.join(f'`{ref}`' for ref in preview)}{suffix}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a bytecode catalog for compiled cards")
    parser.add_argument("--compiled", type=Path, default=DEFAULT_COMPILED_PATH, help="Compiled card JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Catalog output path")
    parser.add_argument(
        "--format",
        choices=["json", "markdown"],
        default="json",
        help="Output format",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compiled_data = load_json(args.compiled)
    metadata = load_json(args.metadata)
    catalog = build_catalog(compiled_data, metadata)
    if args.format == "markdown":
        output_path = args.output if args.output.suffix else DEFAULT_MARKDOWN_PATH
        dump_text(output_path, render_markdown(catalog))
    else:
        dump_json(args.output, catalog)
        output_path = args.output
    print(f"Wrote bytecode catalog to {output_path}")
    print(f"Cards indexed: {len(catalog['cards'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
