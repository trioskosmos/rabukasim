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


def _rust_opcode_name(opcode_section: str, opcode_name: str) -> str:
    prefix_by_section = {
        "opcodes": "O",
        "conditions": "C",
        "costs": "COST",
        "action_bases": "ACTION_BASE",
    }
    prefix = prefix_by_section.get(opcode_section, "O")
    return f"{prefix}_{opcode_name}"


def _rust_handler_path(opcode_name: str) -> str:
    handler_groups = {
        "SELECT_MODE": "engine_rust_src/src/core/logic/interpreter/handlers/select_mode.rs::handle_select_mode",
        "DRAW": "engine_rust_src/src/core/logic/interpreter/handlers/movement_draw.rs::handle_draw",
        "DRAW_UNTIL": "engine_rust_src/src/core/logic/interpreter/handlers/movement_draw.rs::handle_draw",
        "ADD_TO_HAND": "engine_rust_src/src/core/logic/interpreter/handlers/movement_draw.rs::handle_draw",
        "ACTIVATE_MEMBER": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "SET_TAPPED": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "TAP_MEMBER": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "TAP_OPPONENT": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "MOVE_MEMBER": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "FORMATION_CHANGE": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "PLACE_UNDER": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "ADD_STAGE_ENERGY": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "GRANT_ABILITY": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "PLAY_MEMBER_FROM_HAND": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "PLAY_MEMBER_FROM_DISCARD": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "INCREASE_COST": "engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs::handle_member_state",
        "ENERGY_CHARGE": "engine_rust_src/src/core/logic/interpreter/handlers/state_energy.rs::handle_energy",
        "PAY_ENERGY": "engine_rust_src/src/core/logic/interpreter/handlers/state_energy.rs::handle_energy",
        "ACTIVATE_ENERGY": "engine_rust_src/src/core/logic/interpreter/handlers/state_energy.rs::handle_energy",
        "PAY_ENERGY_DYNAMIC": "engine_rust_src/src/core/logic/interpreter/handlers/state_energy.rs::handle_energy",
        "PLACE_ENERGY_UNDER_MEMBER": "engine_rust_src/src/core/logic/interpreter/handlers/state_energy.rs::handle_energy",
        "SEARCH_DECK": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "ORDER_DECK": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "MOVE_TO_DECK": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "SWAP_CARDS": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "REVEAL_UNTIL": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "LOOK_DECK": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "REVEAL_CARDS": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "CHEER_REVEAL": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "LOOK_DECK_DYNAMIC": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "MOVE_TO_DISCARD": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "LOOK_AND_CHOOSE": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "RECOVER_LIVE": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "RECOVER_MEMBER": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "PLAY_LIVE_FROM_DISCARD": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "SELECT_CARDS": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "LOOK_REORDER_DISCARD": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "SWAP_ZONE": "engine_rust_src/src/core/logic/interpreter/handlers/movement_deck_zones.rs::handle_deck_zones",
        "BOOST_SCORE": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "REDUCE_COST": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "SET_SCORE": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "ADD_BLADES": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "BUFF_POWER": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "SET_BLADES": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "ADD_HEARTS": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "SET_HEARTS": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "TRANSFORM_COLOR": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "REDUCE_HEART_REQ": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "TRANSFORM_HEART": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "INCREASE_HEART_COST": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "SET_HEART_COST": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "REDUCE_SCORE": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "LOSE_EXCESS_HEARTS": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "TRANSFORM_BLADES": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "SKIP_ACTIVATE_PHASE": "engine_rust_src/src/core/logic/interpreter/handlers/state_score_hearts.rs::handle_score_hearts",
        "NEGATE_EFFECT": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "REDUCE_YELL_COUNT": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "RESTRICTION": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "SELECT_MEMBER": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "SELECT_LIVE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "SELECT_PLAYER": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "OPPONENT_CHOOSE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "PREVENT_ACTIVATE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "PREVENT_BATON_TOUCH": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "PREVENT_SET_TO_SUCCESS_PILE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "PREVENT_PLAY_TO_SLOT": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "TRIGGER_REMOTE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "REDUCE_LIVE_SET_LIMIT": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "META_RULE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "BATON_TOUCH_MOD": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "IMMUNITY": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "COLOR_SELECT": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "SWAP_AREA": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "REPEAT_ABILITY": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "SET_TARGET_SELF": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "SET_TARGET_OPPONENT": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "CALC_SUM_COST": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
        "DIV_VALUE": "engine_rust_src/src/core/logic/interpreter/handlers/flow.rs::handle_meta_control",
    }
    return handler_groups.get(opcode_name, "engine_rust_src/src/core/logic/interpreter/handlers/mod.rs::HandlerRegistry::dispatch")


def _format_frame_trace(frame: dict[str, Any]) -> str:
    opcode_name = str(frame.get("opcode_name", frame.get("opcode", "")) or "")
    rust_opcode = str(frame.get("rust_opcode", "") or "")
    handler_path = _rust_handler_path(opcode_name)

    parts = [rust_opcode or opcode_name or "OP_0", f"[{handler_path}]"]

    value = frame.get("value")
    if value not in (None, 0):
        parts.append(f"value={value}")

    attr = frame.get("attr") or frame.get("filter")
    if isinstance(attr, dict) and attr:
        parts.append(f"attr={attr}")

    slot = frame.get("slot")
    if isinstance(slot, dict) and slot:
        parts.append(f"slot={slot}")

    params = frame.get("params")
    if params not in (None, {}, []):
        parts.append(f"params={params}")

    return " | ".join(parts)


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


_BOOL_FILTER_FIELDS = {
    "group_enabled",
    "is_tapped",
    "has_blade_heart",
    "not_has_blade_heart",
    "unique_names",
    "unit_enabled",
    "value_enabled",
    "is_le",
    "is_cost_type",
    "is_setsuna",
    "compare_accumulated",
    "is_optional",
    "keyword_energy",
    "keyword_member",
}

_BOOL_SLOT_FIELDS = {
    "is_opponent",
    "is_reveal_until_live",
    "is_baton_slot",
    "is_empty_slot",
    "is_wait",
    "is_dynamic",
}


def _label_filter_dict(filter_dict: dict[str, Any]) -> dict[str, Any]:
    labeled = dict(filter_dict)
    for key in _BOOL_FILTER_FIELDS:
        if key in labeled:
            labeled[key] = bool(labeled[key])
    if labeled.get("special_id") and labeled["special_id"] in SPECIAL_ID_LABELS:
        labeled["special_id"] = SPECIAL_ID_LABELS[labeled["special_id"]]
    if labeled.get("zone_mask") and labeled["zone_mask"] in ZONE_MASK_LABELS:
        labeled["zone_mask"] = ZONE_MASK_LABELS[labeled["zone_mask"]]
    return labeled


def _label_slot_dict(slot_dict: dict[str, Any]) -> dict[str, Any]:
    labeled = dict(slot_dict)
    for key in _BOOL_SLOT_FIELDS:
        if key in labeled:
            labeled[key] = bool(labeled[key])
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


def _is_sparse_value(value: Any) -> bool:
    """Helper to check if a value is 'non-zero' or non-default for sparse pruning."""
    return value not in (None, 0, False, "", [], {})


def _prune_sparse(value: Any) -> Any:
    """Recursively prune zero/empty/False values from a structure, keeping 'raw' keys."""
    if isinstance(value, dict):
        pruned: dict[str, Any] = {}
        for key, item in value.items():
            if key == "raw":
                pruned[key] = item
                continue
            pruned_item = _prune_sparse(item)
            if _is_sparse_value(pruned_item):
                pruned[key] = pruned_item
        return pruned
    if isinstance(value, list):
        pruned_list = [_prune_sparse(item) for item in value]
        return [item for item in pruned_list if _is_sparse_value(item)]
    return value


def _decode_payload(op_name: str, words: list[int], lookups: MetadataLookups, strict: bool = False) -> dict[str, Any]:
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

    if strict:
        a_dict = unpack_a_standard(a)
        # Type casting for Rust engine (Serde bool requirements)
        for key in _BOOL_FILTER_FIELDS:
            if key in a_dict:
                a_dict[key] = bool(a_dict[key])

        # Virtual field for Rust (DecodedFilterAttr::char_id_3)
        unit_enabled = a_dict.get("unit_enabled", False)
        unit_id = a_dict.get("unit_id", 0)
        a_dict["char_id_3"] = unit_id if not unit_enabled else 0
        
        s_dict = unpack_s_standard(s)
        for key in _BOOL_SLOT_FIELDS:
            if key in s_dict:
                s_dict[key] = bool(s_dict[key])
            
        return {
            "raw": raw,
            "v": v,
            "a": a_dict,
            "s": s_dict,
        }

    if op_name == "LOOK_AND_CHOOSE":
        look_choose = unpack_v_look_choose(v)
        look_choose["reveal"] = bool(look_choose.get("reveal"))
        look_choose["dest_discard"] = bool(look_choose.get("dest_discard"))
        return {
            "raw": raw,
            "v": look_choose,
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


def decode_frame(words: list[int], lookups: MetadataLookups, strict: bool = False) -> dict[str, Any]:
    padded = list(words[:5])
    if len(padded) < 5:
        padded.extend([0] * (5 - len(padded)))

    opcode = int(padded[0])
    opcode_section, opcode_name = _opcode_name(opcode, lookups)
    rust_opcode = _rust_opcode_name(opcode_section, opcode_name)
    metadata_refs = [f"{opcode_section}.{opcode_name}"]
    slot_ref = _slot_label(int(padded[4]), lookups)
    if slot_ref:
        metadata_refs.append(f"slot_indices.{slot_ref}")
    negated = 1000 <= opcode < 2000
    payload = _decode_payload(opcode_name, padded, lookups, strict=strict)
    
    # Prune attr and slot for cleaner semantic model
    pruned_attr = payload.get("a") if strict else _prune_sparse(payload.get("a"))
    pruned_slot = payload.get("s") if strict else _prune_sparse(payload.get("s"))

    semantic = {
        "opcode_id": opcode,
        "opcode_name": opcode_name,
        "opcode_section": opcode_section,
        "rust_opcode": rust_opcode,
        "negated": bool(negated),
        "decoded": readable.decode_chunk(padded),
        "value": payload.get("v"),
        "attr": pruned_attr if strict or _is_sparse_value(pruned_attr) else None,
        "slot": pruned_slot if strict or _is_sparse_value(pruned_slot) else None,
        "raw": payload.get("raw", {}),
        "metadata_refs": metadata_refs,
    }
    
    # Prune semantic to remove the None values we just added if they were sparse
    # This ensures those keys are omitted entirely in the JSON/YAML output.
    if not strict:
        semantic = _prune_sparse(semantic)

    return {
        "words": padded,
        "opcode": opcode,
        "opcode_name": opcode_name,
        "opcode_section": opcode_section,
        "rust_opcode": rust_opcode,
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
    opcode_alias = frame.get("op") if isinstance(frame, dict) else None
    if isinstance(opcode_alias, str) and opcode_alias and "opcode_name" not in frame:
        frame = dict(frame)
        frame["opcode_name"] = opcode_alias
    
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
            if "params" in merged and "v" not in merged_payload:
                merged_payload["v"] = merged.get("params")

        if merged_payload:
            merged["payload"] = merged_payload
            return encode_frame(merged, lookups)

    source_words = frame.get("source_words") if isinstance(frame, dict) else None
    if isinstance(source_words, list) and source_words:
        words = [int(word) for word in source_words[:5]]
        if len(words) < 5:
            words.extend([0] * (5 - len(words)))
        return words

    opcode_value = frame.get("opcode_id", None)
    if opcode_value is None:
        opcode_value = frame.get("opcode", 0)
    try:
        opcode = int(opcode_value or 0)  # prefer numeric opcode_id
    except (TypeError, ValueError):
        opcode = 0
    opcode_name = str(frame.get("opcode_name", frame.get("opcode", "")) or "")
    if opcode == 0 and opcode_name in lookups.ids_by_opcode:
        opcode = int(lookups.ids_by_opcode[opcode_name])
    payload = frame.get("payload", {}) or {}
    negated = bool(
        frame.get("negated")
        or frame.get("is_negated")
        or (isinstance(payload, dict) and (payload.get("negated") or payload.get("is_negated")))
    )
    if negated and opcode < 1000:
        opcode += 1000
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


def bytecode_to_model(bytecode: list[int], metadata: dict[str, Any] | None = None, strict: bool = False) -> dict[str, Any]:
    lookups = load_lookups(metadata or load_data(DEFAULT_METADATA_PATH))
    frames = [
        dict(
            decode_frame(bytecode[i : i + 5], lookups, strict=strict),
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


def frame_program_to_model(frame_program: Any) -> dict[str, Any]:
    """Normalize an Ability.frame_program payload into codec model form.

    The runtime and semantic index both store frame programs as a small set of
    human-readable frame variants. This helper converts that shape into the
    flat model structure understood by ``model_to_bytecode``.
    """

    if isinstance(frame_program, dict):
        frames = frame_program.get("frames", [])
    else:
        frames = frame_program

    normalized_frames: list[dict[str, Any]] = []
    for frame in frames or []:
        if frame == "Return":
            normalized_frames.append(
                {
                    "opcode": "RETURN",
                    "opcode_name": "RETURN",
                    "opcode_id": 1,
                    "value": 0,
                    "filter": {},
                    "slot": {},
                    "is_negated": False,
                    "params": None,
                }
            )
            continue

        if not isinstance(frame, dict):
            continue

        if "opcode" in frame or "opcode_id" in frame or "payload" in frame or "semantic" in frame:
            normalized_frames.append(dict(frame))
            continue

        if len(frame) == 1:
            kind, payload = next(iter(frame.items()))
            if kind == "Semantic" and isinstance(payload, dict):
                normalized_frames.append(dict(payload))
                continue

            if kind in {"Draw", "RecoverLive", "RecoverMember", "LookAndChoose", "SelectMember", "MoveMember", "MetaRule"}:
                opcode_name = {
                    "Draw": "DRAW",
                    "RecoverLive": "RECOVER_LIVE",
                    "RecoverMember": "RECOVER_MEMBER",
                    "LookAndChoose": "LOOK_AND_CHOOSE",
                    "SelectMember": "SELECT_MEMBER",
                    "MoveMember": "MOVE_MEMBER",
                    "MetaRule": "META_RULE",
                }[kind]
                payload = payload if isinstance(payload, dict) else {}
                value_key = "count" if kind != "MetaRule" else "rule_type"
                normalized_frames.append(
                    {
                        "opcode": opcode_name,
                        "opcode_name": opcode_name,
                        "opcode_id": 0,
                        "value": int(payload.get(value_key, 0) or 0),
                        "filter": dict(payload.get("filter", {})) if isinstance(payload.get("filter", {}), dict) else {},
                        "slot": dict(payload.get("slot", {})) if isinstance(payload.get("slot", {}), dict) else {},
                        "is_negated": bool(payload.get("is_negated", False)),
                        "params": payload.get("params"),
                    }
                )
                continue

        normalized_frames.append(dict(frame))

    return {
        "frames": normalized_frames,
    }


def _iter_cards(compiled_data: dict[str, Any]):
    for db_name in ("member_db", "live_db", "energy_db"):
        for card_id, card in compiled_data.get(db_name, {}).items():
            yield db_name, card_id, card


def render_model_pseudocode(model: dict[str, Any]) -> str:
    lines: list[str] = []
    for frame in model.get("frames", []):
        lines.append(_format_frame_trace(frame))
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
    semantic = frame.get("semantic") if isinstance(frame, dict) and isinstance(frame.get("semantic"), dict) else {}
    opcode_name = str(
        frame.get("opcode_name")
        or frame.get("op")
        or semantic.get("opcode_name")
        or "OP_0"
    )
    opcode_id = int(
        frame.get("opcode")
        or frame.get("opcode_id")
        or semantic.get("opcode_id", 0)
        or 0
    )
    payload = frame.get("payload", {}) if isinstance(frame, dict) else {}
    sparse: dict[str, Any] = {"opcode_id": opcode_id, "opcode": opcode_name}
    rust_opcode = (
        frame.get("rust_opcode")
        or frame.get("rust_opcode_name")
        or semantic.get("rust_opcode")
        or semantic.get("rust_opcode_name")
    )
    if isinstance(rust_opcode, str) and rust_opcode:
        sparse["rust_opcode"] = rust_opcode

    frame_index = frame.get("ability_frame_index", frame.get("_frame_index")) if isinstance(frame, dict) else None
    if isinstance(frame_index, int) and frame_index >= 0:
        sparse["ability_frame_index"] = frame_index

    if not isinstance(payload, dict) or not payload:
        payload = frame if isinstance(frame, dict) else {}

    v_value = payload.get("v", payload.get("value"))
    a_value = payload.get("a", payload.get("attr"))
    s_value = payload.get("s", payload.get("slot"))
    neg_value = payload.get("negated", payload.get("is_negated"))
    params_value = payload.get("params")

    if _is_sparse_value(_prune_sparse(v_value)):
        sparse["value"] = _prune_sparse(v_value)
    if _is_sparse_value(_prune_sparse(a_value)):
        sparse["attr"] = _prune_sparse(a_value)
    if _is_sparse_value(_prune_sparse(s_value)):
        sparse["slot"] = _prune_sparse(s_value)
    if bool(neg_value):
        sparse["negated"] = True
    if params_value not in (None, {}, []):
        sparse["params"] = params_value

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


def frame_to_compact(frame: dict[str, Any]) -> dict[str, Any]:
    sparse = frame_to_sparse(frame)
    compact: dict[str, Any] = {
        "op": sparse["opcode"],
        "opcode_id": sparse["opcode_id"],
    }
    if isinstance(sparse.get("rust_opcode"), str) and sparse["rust_opcode"]:
        compact["rust_opcode"] = sparse["rust_opcode"]

    if isinstance(sparse.get("value"), dict):
        compact["value"] = sparse["value"]
    elif sparse.get("value") not in (None, 0):
        compact["value"] = sparse["value"]

    if isinstance(sparse.get("attr"), dict) and sparse["attr"]:
        compact["attr"] = sparse["attr"]
    if isinstance(sparse.get("slot"), dict) and sparse["slot"]:
        compact["slot"] = sparse["slot"]
    if sparse.get("is_negated"):
        compact["negated"] = True
    if sparse.get("negated"):
        compact["negated"] = True
    if sparse.get("params") not in (None, {}, []):
        compact["params"] = sparse["params"]
    if isinstance(sparse.get("ability_frame_index"), int):
        compact["frame_index"] = sparse["ability_frame_index"]
    if isinstance(frame.get("source_words"), list) and frame.get("source_words"):
        compact["source_words"] = [int(word) for word in frame["source_words"]]

    return compact


def model_to_compact_model(model: dict[str, Any], include_raw_words: bool = False) -> dict[str, Any]:
    compact_frames: list[dict[str, Any]] = []
    for frame in model.get("frames", []):
        compact_frame = frame_to_compact(frame)
        if include_raw_words and "words" in frame:
            compact_frame["source_words"] = [int(word) for word in frame.get("words", [])]
        compact_frames.append(compact_frame)

    return {
        "generated_at": model.get("generated_at"),
        "layout": model.get("layout", {}),
        "frames": compact_frames,
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
    opcode_sequence = []
    opcode_ids = []
    rust_opcode_sequence = []
    for frame in model.get("frames", []):
        opcode_name = frame.get("opcode_name")
        opcode_id = frame.get("opcode_id")
        rust_opcode = frame.get("rust_opcode")
        if opcode_name:
            opcode_sequence.append(str(opcode_name))
            if opcode_name not in opcode_names:
                opcode_names.append(str(opcode_name))
        if opcode_id is not None:
            opcode_ids.append(int(opcode_id))
        if isinstance(rust_opcode, str) and rust_opcode:
            rust_opcode_sequence.append(rust_opcode)

    return {
        "signature": f"{trigger_name}|{signature_hash}",
        "signature_hash": signature_hash,
        "signature_source": signature_source,
        "trigger_id": trigger_id,
        "trigger": trigger_name,
        "bytecode": bytecode,
        "bytecode_words": len(bytecode),
        "frame_count": len(model.get("frames", [])),
        "opcode_sequence": opcode_sequence,
        "opcode_ids": opcode_ids,
        "opcode_names": opcode_names,
        "rust_opcode_sequence": rust_opcode_sequence,
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
                    "opcode_sequence": sig["opcode_sequence"],
                    "opcode_ids": sig["opcode_ids"],
                    "opcode_names": sig["opcode_names"],
                    "rust_opcode_sequence": sig["rust_opcode_sequence"],
                    "pseudocode": sig["pseudocode"],
                    "model": sig["model"],
                    "sparse_model": sig["sparse_model"],
                    "round_trip_matches": sig["round_trip_matches"],
                    "source_words": list(bytecode),
                    "cards": [],
                    "card_refs": [],
                },
            )
            ab_trigger_name = _name_for_id(int(ability.get("trigger", 0)), lookups.triggers_by_id, "TRIGGER")
            entry["cards"].append(
                f"{card_no} | {card_name} [{db_name}:{card_id}] (ab#{ab_idx} {ab_trigger_name})"
            )
            entry["card_refs"].append(
                {
                    "db": db_name,
                    "card_id": int(card_id) if str(card_id).isdigit() else card_id,
                    "card_no": card_no,
                    "name": card_name,
                    "ability_index": ab_idx,
                    "trigger": ab_trigger_name,
                }
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


def build_compact_ability_index(compiled_data: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    """Build a human-editable ability index from compiled cards."""

    payload = build_ability_index(compiled_data, metadata)
    payload["schema"] = "ability_frames.flat.v1"
    for entry in payload.get("abilities", []):
        model = entry.pop("model", {})
        entry["frames"] = [frame_to_compact(frame) for frame in model.get("frames", [])]
        entry.pop("sparse_model", None)
        entry.pop("bytecode", None)
        entry.pop("round_trip_bytecode", None)
        entry.pop("signature_source", None)
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
