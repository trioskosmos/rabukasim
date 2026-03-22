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
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any

from engine.models import bytecode_readable as readable
from engine.models.ability_filter import SPECIAL_ID_LABELS, ZONE_MASK_LABELS
from engine.models.bytecode_readable import ZONE_NAMES
from engine.models.generated_packer import (
    pack_a_heart_cost,
    pack_a_standard,
    pack_s_standard,
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
DEFAULT_OUTPUT_PATH = ROOT_DIR / "reports" / "bytecode_codec.yaml"


def load_data(path: Path | str) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() in (".yml", ".yaml"):
            import yaml
            return yaml.safe_load(handle)
        return json.load(handle)


def load_json(path: Path | str) -> dict[str, Any]:
    # Deprecated fallback
    return load_data(path)


def dump_data(path: Path | str, payload: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        if path.suffix.lower() in (".yml", ".yaml"):
            import yaml
            # Use sort_keys=False to preserve the ordered keys we carefully constructed
            yaml.dump(payload, handle, allow_unicode=True, sort_keys=False, default_flow_style=False)
        else:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    # Deprecated fallback
    dump_data(path, payload)


def reverse_map(mapping: dict[str, Any]) -> dict[int, str]:
    return {int(value): key for key, value in mapping.items()}


@dataclass(slots=True)
class MetadataLookups:
    metadata: dict[str, Any]
    opcodes_by_id: dict[int, str]
    action_bases_by_id: dict[int, str]
    triggers_by_id: dict[int, str]
    targets_by_id: dict[int, str]
    conditions_by_id: dict[int, str]
    costs_by_id: dict[int, str]
    slot_indices_by_id: dict[int, str]
    target_players_by_id: dict[int, str]
    opcode_sections_by_id: dict[int, tuple[str, str]]
    ids_by_opcode: dict[str, int]
    ids_by_slot: dict[str, int]
    ids_by_special: dict[str, int]
    ids_by_zone_mask: dict[str, int]
    ids_by_zone: dict[str, int]


def load_lookups(metadata: dict[str, Any]) -> MetadataLookups:
    opcode_sections_by_id: dict[int, tuple[str, str]] = {}
    for section_name in ("opcodes", "conditions", "costs"):
        section = metadata.get(section_name, {})
        if isinstance(section, dict):
            for name, value in section.items():
                try:
                    opcode_sections_by_id[int(value)] = (section_name, str(name))
                except (TypeError, ValueError):
                    continue
    return MetadataLookups(
        metadata=metadata,
        opcodes_by_id=reverse_map(metadata.get("opcodes", {})),
        action_bases_by_id=reverse_map(metadata.get("action_bases", {})),
        triggers_by_id=reverse_map(metadata.get("triggers", {})),
        targets_by_id=reverse_map(metadata.get("targets", {})),
        conditions_by_id=reverse_map(metadata.get("conditions", {})),
        costs_by_id=reverse_map(metadata.get("costs", {})),
        slot_indices_by_id=reverse_map(metadata.get("slot_indices", {})),
        target_players_by_id=reverse_map(metadata.get("target_players", {})),
        opcode_sections_by_id=opcode_sections_by_id,
        ids_by_opcode={**metadata.get("opcodes", {}), **metadata.get("conditions", {}), **metadata.get("costs", {})},
        ids_by_slot=metadata.get("slot_indices", {}),
        ids_by_special={v: k for k, v in SPECIAL_ID_LABELS.items()},
        ids_by_zone_mask={v: k for k, v in ZONE_MASK_LABELS.items()},
        ids_by_zone={v: k for k, v in ZONE_NAMES.items()},
    )


def _name_for_id(value: int, table: dict[int, str], prefix: str) -> str:
    return table.get(int(value), f"{prefix}_{value}")


def _opcode_name(value: int, lookups: MetadataLookups) -> tuple[str, str]:
    if 1000 <= value < 2000:
        base_value = value - 1000
        if base_value in lookups.conditions_by_id:
            return "conditions", lookups.conditions_by_id[base_value]
        if base_value in lookups.opcodes_by_id:
            return "opcodes", lookups.opcodes_by_id[base_value]
    if value in lookups.opcodes_by_id:
        return "opcodes", lookups.opcodes_by_id[value]
    if value in lookups.action_bases_by_id:
        return "action_bases", lookups.action_bases_by_id[value]
    if value in lookups.conditions_by_id:
        return "conditions", lookups.conditions_by_id[value]
    if value in lookups.costs_by_id:
        return "costs", lookups.costs_by_id[value]
    return "opcodes", f"OP_{value}"


def _slot_name(slot_id: int, lookups: MetadataLookups) -> str:
    # Mask out FILTER_IS_OPTIONAL (bit 61)
    clean_id = slot_id & 0x1FFFFFFFFFFFFFFF
    if clean_id in lookups.slot_indices_by_id:
        return lookups.slot_indices_by_id[clean_id]
    if clean_id in lookups.target_players_by_id:
        return lookups.target_players_by_id[clean_id].title()
    return f"Slot_{clean_id}"


def _slot_label(slot_value: int, lookups: MetadataLookups) -> str | None:
    # Mask out FILTER_IS_OPTIONAL (bit 61)
    clean_value = slot_value & 0x1FFFFFFFFFFFFFFF
    if clean_value in lookups.target_players_by_id:
        return f"target_players.{lookups.target_players_by_id[clean_value]}"
    if clean_value in lookups.slot_indices_by_id:
        return lookups.slot_indices_by_id[clean_value]
    return None


def _opcode_label(value: int, lookups: MetadataLookups) -> str:
    if value in lookups.opcodes_by_id:
        return lookups.opcodes_by_id[value]
    if value in lookups.conditions_by_id:
        return lookups.conditions_by_id[value]
    if value in lookups.costs_by_id:
        return lookups.costs_by_id[value]
    return f"OP_{value}"


def _label_filter_dict(filter_dict: dict[str, Any]) -> dict[str, Any]:
    labeled = dict(filter_dict)
    if labeled.get("special_id") and labeled["special_id"] in SPECIAL_ID_LABELS:
        labeled["special_id"] = SPECIAL_ID_LABELS[labeled["special_id"]]
    if labeled.get("zone_mask") and labeled["zone_mask"] in ZONE_MASK_LABELS:
        labeled["zone_mask"] = ZONE_MASK_LABELS[labeled["zone_mask"]]
    return labeled


def _label_slot_dict(slot_dict: dict[str, Any]) -> dict[str, Any]:
    labeled = dict(slot_dict)
    for key in ("source_zone", "dest_zone", "remainder_zone"):
        if labeled.get(key) and labeled[key] in ZONE_NAMES:
            labeled[key] = ZONE_NAMES[labeled[key]]
    return labeled


def _unlabel_filter_dict(filter_dict: dict[str, Any], lookups: MetadataLookups) -> dict[str, Any]:
    unlabeled = dict(filter_dict)
    if isinstance(unlabeled.get("special_id"), str):
        unlabeled["special_id"] = lookups.ids_by_special.get(unlabeled["special_id"], 0)
    if isinstance(unlabeled.get("zone_mask"), str):
        unlabeled["zone_mask"] = lookups.ids_by_zone_mask.get(unlabeled["zone_mask"], 0)
    return unlabeled


def _unlabel_slot_dict(slot_dict: dict[str, Any], lookups: MetadataLookups) -> dict[str, Any]:
    unlabeled = dict(slot_dict)
    for key in ("source_zone", "dest_zone", "remainder_zone"):
        if isinstance(unlabeled.get(key), str):
            unlabeled[key] = lookups.ids_by_zone.get(unlabeled[key], 0)
    return unlabeled


def _decode_payload(op_name: str, words: list[int], lookups: MetadataLookups) -> dict[str, Any]:
    op, v, a_low, a_high, s = words
    a_low_u = a_low & 0xFFFFFFFF
    a_high_u = a_high & 0xFFFFFFFF
    a = (a_high_u << 32) | a_low_u
    if a_low > 0xFFFFFFFF or a_low < -0x80000000:
        a = a_low

    raw = {
        "opcode": _opcode_label(words[0], lookups),
        "value": v,
        "attr": a,
        "slot": _slot_label(s, lookups) or s,
    }

    if op_name == "LOOK_AND_CHOOSE":
        return {
            "raw": raw,
            "v": unpack_v_look_choose(v),
            "a": _label_filter_dict(unpack_a_standard(a)),
            "s": _label_slot_dict(unpack_s_standard(s)),
        }
    if op_name == "SET_HEART_COST":
        return {
            "raw": raw,
            "v": unpack_v_heart_counts(v),
            "a": unpack_a_heart_cost(a),
            "s": _label_slot_dict(unpack_s_standard(s)),
        }
    if op_name == "CALC_SUM_COST":
        return {
            "raw": raw,
            "v": unpack_v_scalar_dynamic(v),
            "a": _label_filter_dict(unpack_a_standard(a)),
            "s": _label_slot_dict(unpack_s_standard(s)),
        }

    return {
        "raw": raw,
        "v": v,
        "a": _label_filter_dict(unpack_a_standard(a)),
        "s": _label_slot_dict(unpack_s_standard(s)),
    }


def decode_frame(words: list[int], lookups: MetadataLookups) -> dict[str, Any]:
    padded = list(words[:5])
    if len(padded) < 5:
        padded.extend([0] * (5 - len(padded)))

    opcode = int(padded[0])
    opcode_section, opcode_name = _opcode_name(opcode, lookups)
    metadata_refs = [f"{opcode_section}.{opcode_name}"]
    slot_ref = _slot_label(int(padded[4]), lookups)
    if slot_ref:
        metadata_refs.append(f"slot_indices.{slot_ref}")
    negated = 1000 <= opcode < 2000
    payload = _decode_payload(opcode_name, padded, lookups)
    semantic = {
        "opcode_id": opcode,
        "opcode_name": opcode_name,
        "opcode_section": opcode_section,
        "negated": bool(negated),
        "decoded": readable.decode_chunk(padded),
        "value": payload.get("v"),
        "attr": payload.get("a"),
        "slot": payload.get("s"),
        "raw": payload.get("raw", {}),
        "metadata_refs": metadata_refs,
    }

    return {
        "words": padded,
        "opcode": opcode,
        "opcode_name": opcode_name,
        "opcode_section": opcode_section,
        "negated": negated or None,
        "metadata_refs": metadata_refs,
        "payload": payload,
        "semantic": semantic,
        "decoded": semantic["decoded"],
    }


def _choice_blocks(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    i = 0
    while i < len(frames):
        frame = frames[i]
        if frame.get("opcode_name") == "SELECT_MODE":
            payload = frame.get("payload", {}) if isinstance(frame.get("payload", {}), dict) else {}
            option_count = int(payload.get("v", payload.get("raw", {}).get("value", 0)) or 0)
            if option_count > 0 and i + 1 + option_count <= len(frames):
                jump_table = frames[i + 1 : i + 1 + option_count]
                if all(j.get("opcode_name") == "JUMP" for j in jump_table):
                    targets: list[int] = []
                    for jump_index, jump in enumerate(jump_table):
                        jump_payload = jump.get("payload", {}) if isinstance(jump.get("payload", {}), dict) else {}
                        jump_value = int(jump_payload.get("v", jump_payload.get("raw", {}).get("value", 0)) or 0)
                        targets.append(max(0, i + 1 + jump_index + jump_value))

                    end_index = len(frames)
                    for idx in range(i + 1 + option_count, len(frames)):
                        if frames[idx].get("opcode_name") == "RETURN":
                            end_index = idx + 1
                            break

                    options: list[dict[str, Any]] = []
                    for option_index, target_index in enumerate(targets):
                        next_target = end_index
                        for future_target in targets[option_index + 1 :]:
                            if future_target > target_index:
                                next_target = future_target
                                break
                        body_frames = [deepcopy(f) for f in frames[target_index:min(next_target, len(frames))]]
                        options.append(
                            {
                                "index": option_index,
                                "jump_target": target_index,
                                "frames": body_frames,
                            }
                        )

                    blocks.append(
                        {
                            "selector_frame_index": i,
                            "option_count": option_count,
                            "jump_table": [deepcopy(f) for f in jump_table],
                            "options": options,
                        }
                    )
                    i += 1 + option_count
                    continue
        i += 1
    return blocks


def encode_frame(frame: dict[str, Any], lookups: MetadataLookups) -> list[int]:
    if "words" in frame and frame["words"]:
        words = list(frame["words"][:5])
        if len(words) < 5:
            words.extend([0] * (5 - len(words)))
        return [int(word) for word in words]

    semantic = frame.get("semantic") if isinstance(frame, dict) else None
    
    # If no payload exists, try to synthesize it from top-level properties or semantic
    if isinstance(frame, dict) and "payload" not in frame:
        merged: dict[str, Any] = dict(frame)
        merged_payload: dict[str, Any] = {}
        
        if isinstance(semantic, dict):
            merged.pop("semantic", None)
            if "opcode" not in merged or isinstance(merged.get("opcode"), str):
                merged["opcode"] = int(semantic.get("opcode_id", merged.get("opcode_id", 0)) or 0)
            if "opcode_name" not in merged and semantic.get("opcode_name"):
                merged["opcode_name"] = semantic.get("opcode_name")
            
            # Favor semantics over raw, but keep raw for obscure opcodes
            if isinstance(semantic.get("raw"), dict) and semantic.get("opcode_name") not in {"LOOK_AND_CHOOSE", "SET_HEART_COST", "CALC_SUM_COST"}:
                merged_payload["raw"] = dict(semantic["raw"])
            if semantic.get("value") is not None:
                merged_payload["v"] = semantic.get("value")
            if semantic.get("attr") is not None:
                merged_payload["a"] = _unlabel_filter_dict(semantic["attr"], lookups) if isinstance(semantic["attr"], dict) else semantic["attr"]
            if semantic.get("slot") is not None:
                merged_payload["s"] = _unlabel_slot_dict(semantic["slot"], lookups) if isinstance(semantic["slot"], dict) else semantic["slot"]
        else:
            # Fall back to top-level properties (what the user actually wrote recursively)
            if "raw" in merged:
                merged_payload["raw"] = merged.get("raw")
            if "value" in merged:
                merged_payload["v"] = merged.get("value")
            if "attr" in merged:
                merged_payload["a"] = _unlabel_filter_dict(merged["attr"], lookups) if isinstance(merged["attr"], dict) else merged["attr"]
            if "slot" in merged:
                merged_payload["s"] = _unlabel_slot_dict(merged["slot"], lookups) if isinstance(merged["slot"], dict) else merged["slot"]
                
        if merged_payload:
            merged["payload"] = merged_payload
            return encode_frame(merged, lookups)

    source_words = frame.get("source_words") if isinstance(frame, dict) else None
    if isinstance(source_words, list) and source_words:
        words = [int(word) for word in source_words[:5]]
        if len(words) < 5:
            words.extend([0] * (5 - len(words)))
        return words

    opcode = int(frame.get("opcode_id", frame.get("opcode", 0)) or 0)  # prefer numeric opcode_id
    opcode_name = str(frame.get("opcode_name", frame.get("opcode", "")) or "")
    payload = frame.get("payload", {}) or {}
    raw = payload.get("raw", {}) if isinstance(payload, dict) else {}

    if raw:
        raw_opcode = raw.get("opcode", opcode)
        if isinstance(raw_opcode, str) and raw_opcode in lookups.ids_by_opcode:
            raw_opcode = lookups.ids_by_opcode[raw_opcode]
        
        raw_slot = raw.get("slot", 0)
        if isinstance(raw_slot, str) and raw_slot in lookups.ids_by_slot:
            raw_slot = lookups.ids_by_slot[raw_slot]
            
        a = int(raw.get("attr", 0))
        return [
            int(raw_opcode),
            int(raw.get("value", 0)),
            a & 0xFFFFFFFF,
            (a >> 32) & 0xFFFFFFFF,
            int(raw_slot),
        ]

    if opcode_name == "LOOK_AND_CHOOSE":
        v = pack_v_look_choose(**(payload.get("v", {}) if isinstance(payload, dict) else {}))
        a = pack_a_standard(**(payload.get("a", {}) if isinstance(payload, dict) else {}))
        s = 0
        if isinstance(payload, dict) and isinstance(payload.get("s"), dict):
            s = payload["s"].get("raw", 0) or 0
        return [opcode, int(v), int(a) & 0xFFFFFFFF, (int(a) >> 32) & 0xFFFFFFFF, int(s)]

    if opcode_name == "SET_HEART_COST":
        v = pack_v_heart_counts(**(payload.get("v", {}) if isinstance(payload, dict) else {}))
        a = pack_a_heart_cost(**(payload.get("a", {}) if isinstance(payload, dict) else {}))
        s = 0
        if isinstance(payload, dict) and isinstance(payload.get("s"), dict):
            s = payload["s"].get("raw", 0) or 0
        return [opcode, int(v), int(a) & 0xFFFFFFFF, (int(a) >> 32) & 0xFFFFFFFF, int(s)]

    if opcode_name == "CALC_SUM_COST":
        v = pack_v_scalar_dynamic(**(payload.get("v", {}) if isinstance(payload, dict) else {}))
        a = pack_a_standard(**(payload.get("a", {}) if isinstance(payload, dict) else {}))
        s = 0
        if isinstance(payload, dict) and isinstance(payload.get("s"), dict):
            s = payload["s"].get("raw", 0) or 0
        return [opcode, int(v), int(a) & 0xFFFFFFFF, (int(a) >> 32) & 0xFFFFFFFF, int(s)]

    v = int(payload.get("v", 0)) if isinstance(payload, dict) else 0
    a_data = payload.get("a", {}) if isinstance(payload, dict) else {}
    s_data = payload.get("s", {}) if isinstance(payload, dict) else {}
    
    # Resolve semantic labels in a_data
    if isinstance(a_data, dict):
        a_data = a_data.copy()
        if "special_id" in a_data and isinstance(a_data["special_id"], str):
            a_data["special_id"] = lookups.ids_by_special.get(a_data["special_id"], 0)
        if "zone_mask" in a_data and isinstance(a_data["zone_mask"], str):
            a_data["zone_mask"] = lookups.ids_by_zone_mask.get(a_data["zone_mask"], 0)
        # Ensure all values are int/bool for the packer
        for k, val in a_data.items():
            if isinstance(val, (int, bool)):
                continue
            # Try to resolve other known labels if needed, but these are the main ones
            
    if isinstance(a_data, dict) and a_data:
        a = pack_a_standard(**a_data)
    else:
        a = int(payload.get("raw", {}).get("attr", 0)) if isinstance(payload, dict) and isinstance(payload.get("raw"), dict) else 0
        
    # Resolve semantic labels in s_data
    if isinstance(s_data, dict):
        s_data = s_data.copy()
        if "source_zone" in s_data and isinstance(s_data["source_zone"], str):
            s_data["source_zone"] = lookups.ids_by_zone.get(s_data["source_zone"], 0)
        if "dest_zone" in s_data and isinstance(s_data["dest_zone"], str):
            s_data["dest_zone"] = lookups.ids_by_zone.get(s_data["dest_zone"], 0)
        if "remainder_zone" in s_data and isinstance(s_data["remainder_zone"], str):
            s_data["remainder_zone"] = lookups.ids_by_zone.get(s_data["remainder_zone"], 0)

    if isinstance(s_data, dict) and s_data:
        s = pack_s_standard(**s_data)
    else:
        s = int(payload.get("raw", {}).get("slot", 0)) if isinstance(payload, dict) and isinstance(payload.get("raw"), dict) else 0

    return [opcode, v, int(a) & 0xFFFFFFFF, (int(a) >> 32) & 0xFFFFFFFF, int(s)]


def bytecode_to_model(bytecode: list[int], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    lookups = load_lookups(metadata or load_data(DEFAULT_METADATA_PATH))
    frames = [
        dict(
            decode_frame(bytecode[i : i + 5], lookups),
            ability_frame_index=(i // 5),
            _frame_index=(i // 5),
        )
        for i in range(0, len(bytecode), 5)
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layout": {
            "words_per_frame": 5,
            "frame_order": ["opcode", "value", "attr_low", "attr_high", "slot"],
        },
        "frames": frames,
        "choices": _choice_blocks(frames),
        "bytecode": [int(word) for word in bytecode],
    }


def _to_i32(val: int) -> int:
    val = val & 0xFFFFFFFF
    return val if val < 0x80000000 else val - 0x100000000


def model_to_bytecode(model: dict[str, Any], metadata: dict[str, Any] | None = None) -> list[int]:
    lookups = load_lookups(metadata or load_data(DEFAULT_METADATA_PATH))
    frames = model.get("frames", [])
    bytecode: list[int] = []
    for frame in frames:
        bytecode.extend(_to_i32(w) for w in encode_frame(frame, lookups))
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
    opcode_id = int(frame.get("opcode", 0))
    payload = frame.get("payload", {}) if isinstance(frame, dict) else {}
    sparse: dict[str, Any] = {"opcode_id": opcode_id, "opcode": opcode_name}

    frame_index = frame.get("ability_frame_index", frame.get("_frame_index")) if isinstance(frame, dict) else None
    if isinstance(frame_index, int) and frame_index >= 0:
        sparse["ability_frame_index"] = frame_index

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

    return sparse


def model_to_sparse_model(model: dict[str, Any], include_raw_words: bool = False) -> dict[str, Any]:
    sparse_frames: list[dict[str, Any]] = []
    for frame in model.get("frames", []):
        sparse_frame = frame_to_sparse(frame)
        # Include the rich semantic dict so callers can edit named fields and re-encode.
        if isinstance(frame.get("semantic"), dict):
            sparse_frame["semantic"] = frame["semantic"]
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
                    "source_words": list(bytecode),
                    "cards": [],
                },
            )
            ab_trigger_name = _name_for_id(int(ability.get("trigger", 0)), lookups.triggers_by_id, "TRIGGER")
            entry["cards"].append(
                f"{card_no} | {card_name} [{db_name}:{card_id}] (ab#{ab_idx} {ab_trigger_name})"
            )

    ordered_entries = sorted(
        groups.values(),
        key=lambda entry: (
            entry["trigger"],
            -len(entry["cards"]),
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
        entry.pop("bytecode", None)
        entry.pop("model", None)
        entry.pop("round_trip_bytecode", None)
        entry.pop("signature_source", None)
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
    metadata = load_data(args.metadata)
    if args.mode == "report":
        compiled_data = load_data(args.input)
        dump_data(args.output, build_report(compiled_data, metadata))
        print(f"Wrote codec report to {args.output}")
        return 0

    if args.mode == "decode":
        payload = load_data(args.input)
        bytecode = payload.get("bytecode", [])
        model = bytecode_to_model(bytecode, metadata)
        dump_data(args.output, model)
        print(f"Wrote decoded model to {args.output}")
        return 0

    if args.mode == "encode":
        payload = load_data(args.input)
        bytecode = model_to_bytecode(payload)
        dump_data(args.output, {"bytecode": bytecode})
        print(f"Wrote encoded bytecode to {args.output}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
