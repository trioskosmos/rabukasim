from __future__ import annotations

"""Two-way bytecode codec backed by metadata.json.

This module keeps the current 5-word bytecode layout, but names the fields using
the project metadata and the existing pack/unpack helpers. The goal is to make
the conversion round-trip reliably:

    bytecode -> annotated frames -> bytecode

The decoder is intentionally conservative. For unknown or complex frames it
preserves the raw word values so the encoder can reconstruct the original
sequence exactly.
"""

import argparse
import json
from hashlib import sha1
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.models import bytecode_readable as readable
from engine.models.generated_packer import (
    pack_a_heart_cost,
    pack_a_standard,
    pack_v_heart_counts,
    pack_v_look_choose,
    pack_v_scalar_dynamic,
    unpack_a_heart_cost,
    unpack_a_standard,
    unpack_s_standard,
    unpack_v_heart_counts,
    unpack_v_look_choose,
    unpack_v_scalar_dynamic,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "reports" / "bytecode_codec.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def reverse_map(mapping: dict[str, Any]) -> dict[int, str]:
    return {int(value): key for key, value in mapping.items()}


@dataclass(slots=True)
class MetadataLookups:
    metadata: dict[str, Any]
    opcodes_by_id: dict[int, str]
    triggers_by_id: dict[int, str]
    targets_by_id: dict[int, str]
    conditions_by_id: dict[int, str]
    costs_by_id: dict[int, str]
    slot_indices_by_id: dict[int, str]
    target_players_by_id: dict[int, str]


def load_lookups(metadata: dict[str, Any]) -> MetadataLookups:
    return MetadataLookups(
        metadata=metadata,
        opcodes_by_id=reverse_map(metadata.get("opcodes", {})),
        triggers_by_id=reverse_map(metadata.get("triggers", {})),
        targets_by_id=reverse_map(metadata.get("targets", {})),
        conditions_by_id=reverse_map(metadata.get("conditions", {})),
        costs_by_id=reverse_map(metadata.get("costs", {})),
        slot_indices_by_id=reverse_map(metadata.get("slot_indices", {})),
        target_players_by_id=reverse_map(metadata.get("target_players", {})),
    )


def _name_for_id(value: int, table: dict[int, str], prefix: str) -> str:
    return table.get(int(value), f"{prefix}_{value}")


def _slot_label(slot_value: int, lookups: MetadataLookups) -> str | None:
    if slot_value in lookups.target_players_by_id:
        return f"target_players.{lookups.target_players_by_id[slot_value]}"
    if slot_value in lookups.slot_indices_by_id:
        return f"slot_indices.{lookups.slot_indices_by_id[slot_value]}"
    return None


def _decode_payload(op_name: str, words: list[int]) -> dict[str, Any]:
    _, v, a, s, _ = words

    if op_name == "LOOK_AND_CHOOSE":
        return {
            "raw": {"opcode": words[0], "value": v, "attr": a, "slot": s},
            "v": unpack_v_look_choose(v),
            "a": unpack_a_standard(a),
            "s": unpack_s_standard(s),
        }
    if op_name == "SET_HEART_COST":
        return {
            "raw": {"opcode": words[0], "value": v, "attr": a, "slot": s},
            "v": unpack_v_heart_counts(v),
            "a": unpack_a_heart_cost(a),
            "s": unpack_s_standard(s),
        }
    if op_name == "CALC_SUM_COST":
        return {
            "raw": {"opcode": words[0], "value": v, "attr": a, "slot": s},
            "v": unpack_v_scalar_dynamic(v),
            "a": unpack_a_standard(a),
            "s": unpack_s_standard(s),
        }

    return {
        "raw": {"opcode": words[0], "value": v, "attr": a, "slot": s},
        "v": v,
        "a": unpack_a_standard(a),
        "s": unpack_s_standard(s),
    }


def decode_frame(words: list[int], lookups: MetadataLookups) -> dict[str, Any]:
    padded = list(words[:5])
    if len(padded) < 5:
        padded.extend([0] * (5 - len(padded)))

    opcode = int(padded[0])
    opcode_name = _name_for_id(opcode, lookups.opcodes_by_id, "OP")
    metadata_refs = [f"opcodes.{opcode_name}"] if opcode_name in lookups.metadata.get("opcodes", {}) else []
    slot_ref = _slot_label(int(padded[4]), lookups)
    if slot_ref:
        metadata_refs.append(slot_ref)

    return {
        "words": padded,
        "opcode": opcode,
        "opcode_name": opcode_name,
        "metadata_refs": metadata_refs,
        "payload": _decode_payload(opcode_name, padded),
        "decoded": readable.decode_chunk(padded),
    }


def encode_frame(frame: dict[str, Any]) -> list[int]:
    if "words" in frame and frame["words"]:
        words = list(frame["words"][:5])
        if len(words) < 5:
            words.extend([0] * (5 - len(words)))
        return [int(word) for word in words]

    opcode = int(frame.get("opcode", 0))
    opcode_name = str(frame.get("opcode_name", ""))
    payload = frame.get("payload", {}) or {}
    raw = payload.get("raw", {}) if isinstance(payload, dict) else {}

    if raw:
        return [
            int(raw.get("opcode", opcode)),
            int(raw.get("value", 0)),
            int(raw.get("attr", 0)),
            int(raw.get("slot", 0)),
            0,
        ]

    if opcode_name == "LOOK_AND_CHOOSE":
        v = pack_v_look_choose(**(payload.get("v", {}) if isinstance(payload, dict) else {}))
        a = pack_a_standard(**(payload.get("a", {}) if isinstance(payload, dict) else {}))
        s = 0
        if isinstance(payload, dict) and isinstance(payload.get("s"), dict):
            s = payload["s"].get("raw", 0) or 0
        return [opcode, int(v), int(a), int(s), 0]

    if opcode_name == "SET_HEART_COST":
        v = pack_v_heart_counts(**(payload.get("v", {}) if isinstance(payload, dict) else {}))
        a = pack_a_heart_cost(**(payload.get("a", {}) if isinstance(payload, dict) else {}))
        s = 0
        if isinstance(payload, dict) and isinstance(payload.get("s"), dict):
            s = payload["s"].get("raw", 0) or 0
        return [opcode, int(v), int(a), int(s), 0]

    if opcode_name == "CALC_SUM_COST":
        v = pack_v_scalar_dynamic(**(payload.get("v", {}) if isinstance(payload, dict) else {}))
        a = pack_a_standard(**(payload.get("a", {}) if isinstance(payload, dict) else {}))
        s = 0
        if isinstance(payload, dict) and isinstance(payload.get("s"), dict):
            s = payload["s"].get("raw", 0) or 0
        return [opcode, int(v), int(a), int(s), 0]

    v = int(payload.get("v", 0)) if isinstance(payload, dict) else 0
    a = int(payload.get("raw", {}).get("attr", 0)) if isinstance(payload, dict) and isinstance(payload.get("raw"), dict) else 0
    s = int(payload.get("raw", {}).get("slot", 0)) if isinstance(payload, dict) and isinstance(payload.get("raw"), dict) else 0
    return [opcode, v, a, s, 0]


def bytecode_to_model(bytecode: list[int], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    lookups = load_lookups(metadata or load_json(DEFAULT_METADATA_PATH))
    frames = [decode_frame(bytecode[i : i + 5], lookups) for i in range(0, len(bytecode), 5)]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "words_per_frame": 5,
            "frame_order": ["opcode", "value", "attr_low", "attr_high", "slot"],
        },
        "frames": frames,
        "bytecode": [int(word) for word in bytecode],
    }


def model_to_bytecode(model: dict[str, Any]) -> list[int]:
    frames = model.get("frames", [])
    bytecode: list[int] = []
    for frame in frames:
        bytecode.extend(encode_frame(frame))
    return bytecode


def _iter_cards(compiled_data: dict[str, Any]):
    for db_name in ("member_db", "live_db", "energy_db"):
        for card_id, card in compiled_data.get(db_name, {}).items():
            yield db_name, card_id, card


def render_model_pseudocode(model: dict[str, Any]) -> str:
    lines: list[str] = []
    for frame in model.get("frames", []):
        decoded = frame.get("decoded")
        if decoded:
            lines.append(str(decoded))
    return "\n".join(lines).strip()


def _is_sparse_value(value: Any) -> bool:
    return value not in (None, 0, False, "", [], {})


def _prune_sparse(value: Any) -> Any:
    if isinstance(value, dict):
        pruned: dict[str, Any] = {}
        for key, item in value.items():
            if key == "raw":
                continue
            pruned_item = _prune_sparse(item)
            if _is_sparse_value(pruned_item):
                pruned[key] = pruned_item
        return pruned
    if isinstance(value, list):
        pruned_list = [_prune_sparse(item) for item in value]
        return [item for item in pruned_list if _is_sparse_value(item)]
    return value


def frame_to_sparse(frame: dict[str, Any]) -> dict[str, Any]:
    opcode_name = str(frame.get("opcode_name", "OP_0"))
    payload = frame.get("payload", {}) if isinstance(frame, dict) else {}
    sparse: dict[str, Any] = {"opcode": opcode_name}

    if not isinstance(payload, dict):
        return sparse

    v_value = payload.get("v")
    a_value = payload.get("a")
    s_value = payload.get("s")

    if _is_sparse_value(_prune_sparse(v_value)):
        sparse["value"] = _prune_sparse(v_value)
    if _is_sparse_value(_prune_sparse(a_value)):
        sparse["attr"] = _prune_sparse(a_value)
    if _is_sparse_value(_prune_sparse(s_value)):
        sparse["slot"] = _prune_sparse(s_value)

    if _is_sparse_value(payload.get("decoded")):
        sparse["decoded"] = payload.get("decoded")

    return sparse


def model_to_sparse_model(model: dict[str, Any], include_raw_words: bool = True) -> dict[str, Any]:
    sparse_frames: list[dict[str, Any]] = []
    for frame in model.get("frames", []):
        sparse_frame = frame_to_sparse(frame)
        if include_raw_words and "words" in frame:
            sparse_frame["source_words"] = [int(word) for word in frame.get("words", [])]
        sparse_frames.append(sparse_frame)

    return {
        "generated_at": model.get("generated_at"),
        "layout": model.get("layout", {}),
        "frames": sparse_frames,
        "bytecode": [int(word) for word in model.get("bytecode", [])],
    }


def ability_signature(ability: dict[str, Any], metadata: dict[str, Any] | MetadataLookups) -> dict[str, Any]:
    lookups = metadata if isinstance(metadata, MetadataLookups) else load_lookups(metadata)
    trigger_id = int(ability.get("trigger", 0))
    trigger_name = _name_for_id(trigger_id, lookups.triggers_by_id, "TRIGGER")
    bytecode = [int(word) for word in ability.get("bytecode", [])]
    model = bytecode_to_model(bytecode, lookups.metadata)
    round_trip_bytecode = model_to_bytecode(model)
    signature_payload = {
        "trigger": trigger_id,
        "bytecode": bytecode,
    }
    signature_source = json.dumps(signature_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    signature_hash = sha1(signature_source.encode("utf-8")).hexdigest()
    opcode_names = []
    for frame in model.get("frames", []):
        opcode_name = frame.get("opcode_name")
        if opcode_name and opcode_name not in opcode_names:
            opcode_names.append(str(opcode_name))

    return {
        "signature": f"{trigger_name}|{signature_hash}",
        "signature_hash": signature_hash,
        "signature_source": signature_source,
        "trigger_id": trigger_id,
        "trigger": trigger_name,
        "bytecode": bytecode,
        "bytecode_words": len(bytecode),
        "frame_count": len(model.get("frames", [])),
        "opcode_names": opcode_names,
        "pseudocode": render_model_pseudocode(model),
        "model": model,
        "sparse_model": model_to_sparse_model(model),
        "round_trip_bytecode": round_trip_bytecode,
        "round_trip_matches": round_trip_bytecode == bytecode,
    }


def build_ability_index(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    groups: dict[str, dict[str, Any]] = {}
    lookups = load_lookups(metadata)
    total_cards = 0
    total_abilities = 0

    for db_name, card_id, card in _iter_cards(compiled_data):
        total_cards += 1
        card_name = str(card.get("name", ""))
        card_no = str(card.get("card_no", ""))
        for ab_idx, ability in enumerate(card.get("abilities", [])):
            bytecode = [int(word) for word in ability.get("bytecode", [])]
            if not bytecode:
                continue

            total_abilities += 1
            sig = ability_signature(ability, lookups)
            entry = groups.setdefault(
                sig["signature"],
                {
                    "signature": sig["signature"],
                    "signature_hash": sig["signature_hash"],
                    "trigger_id": sig["trigger_id"],
                    "trigger": sig["trigger"],
                    "bytecode": sig["bytecode"],
                    "bytecode_words": sig["bytecode_words"],
                    "frame_count": sig["frame_count"],
                    "opcode_names": sig["opcode_names"],
                    "pseudocode": sig["pseudocode"],
                    "model": sig["model"],
                    "sparse_model": sig["sparse_model"],
                    "round_trip_matches": sig["round_trip_matches"],
                    "cards": [],
                },
            )
            entry["cards"].append(
                {
                    "db": db_name,
                    "card_id": card_id,
                    "card_no": card_no,
                    "name": card_name,
                    "ability_index": ab_idx,
                    "ability_trigger": _name_for_id(int(ability.get("trigger", 0)), lookups.triggers_by_id, "TRIGGER"),
                    "raw_text": ability.get("raw_text", ""),
                    "pseudocode": ability.get("pseudocode", ""),
                }
            )

    ordered_entries = sorted(
        groups.values(),
        key=lambda entry: (
            entry["trigger"],
            entry["signature_hash"],
        ),
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(DEFAULT_INPUT_PATH),
        "metadata_source": str(DEFAULT_METADATA_PATH),
        "summary": {
            "card_count": total_cards,
            "ability_count": total_abilities,
            "unique_ability_count": len(ordered_entries),
        },
        "abilities": ordered_entries,
    }


def build_sparse_ability_index(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    payload = build_ability_index(compiled_data, metadata)
    payload["schema"] = "ability_frame_index.v1"
    for entry in payload.get("abilities", []):
        entry["frames"] = entry.pop("sparse_model", {}).get("frames", [])
        entry["bytecode"] = entry.get("bytecode", [])
        entry["trigger"] = entry.get("trigger")
        entry["trigger_id"] = entry.get("trigger_id")
        entry["round_trip_matches"] = entry.get("round_trip_matches", False)
    return payload


def build_report(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    lookups = load_lookups(metadata)
    cards = []
    for db_name, card_id, card in _iter_cards(compiled_data):
        abilities = []
        for ab_idx, ability in enumerate(card.get("abilities", [])):
            bytecode = list(ability.get("bytecode", []))
            if not bytecode:
                continue
            model = bytecode_to_model(bytecode, metadata)
            abilities.append(
                {
                    "ability_index": ab_idx,
                    "trigger": _name_for_id(int(ability.get("trigger", 0)), lookups.triggers_by_id, "TRIGGER"),
                    "raw_text": ability.get("raw_text", ""),
                    "pseudocode": ability.get("pseudocode", ""),
                    "bytecode": bytecode,
                    "model": model,
                }
            )
        if abilities:
            cards.append(
                {
                    "db": db_name,
                    "card_id": card_id,
                    "card_no": card.get("card_no", ""),
                    "name": card.get("name", ""),
                    "ability_count": len(abilities),
                    "abilities": abilities,
                }
            )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(DEFAULT_INPUT_PATH),
        "metadata_source": str(DEFAULT_METADATA_PATH),
        "layout": {
            "words_per_frame": 5,
            "frame_order": ["opcode", "value", "attr_low", "attr_high", "slot"],
        },
        "cards": cards,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Two-way bytecode codec")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Compiled card JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output report path")
    parser.add_argument(
        "--mode",
        choices=["report", "decode", "encode"],
        default="report",
        help="Operation mode",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    metadata = load_json(args.metadata)
    if args.mode == "report":
        compiled_data = load_json(args.input)
        dump_json(args.output, build_report(compiled_data, metadata))
        print(f"Wrote codec report to {args.output}")
        return 0

    if args.mode == "decode":
        payload = load_json(args.input)
        bytecode = payload.get("bytecode", [])
        model = bytecode_to_model(bytecode, metadata)
        dump_json(args.output, model)
        print(f"Wrote decoded model to {args.output}")
        return 0

    if args.mode == "encode":
        payload = load_json(args.input)
        bytecode = model_to_bytecode(payload)
        dump_json(args.output, {"bytecode": bytecode})
        print(f"Wrote encoded bytecode to {args.output}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
