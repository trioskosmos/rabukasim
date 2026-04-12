"""Card Compiler - Simplified Semantic Version

DATA FLOW:
---------
1. INPUT: data/cards.json (raw card data)
2. INPUT: data/ability_frame_source.json (authored sparse semantic source)
3. PROCESS: compile_cards() parses each card, resolves abilities from the authored sparse source
4. OUTPUT: data/cards_compiled.json (compiled card database)
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import re
import sys
import unicodedata
from pathlib import Path

# Add project root to path to allow imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from typing import Any

import numpy as np
from pydantic import TypeAdapter

from ..models.ability import (
    Ability,
    AbilityCostType,
    ConditionType,
    EffectType,
    TriggerType,
)
from ..models.card import EnergyCard, LiveCard, MemberCard
from ..models.enums import CHAR_MAP
from .semantic_processor import (
    build_ability_from_text,
    semantic_form_to_frame_program,
    select_ability_raw_text as _select_ability_raw_text,
)

# Worker-local adapters (initialized once per process)
_MEMBER_ADAPTER: TypeAdapter[MemberCard] | None = None
_LIVE_ADAPTER: TypeAdapter[LiveCard] | None = None
_ENERGY_ADAPTER: TypeAdapter[EnergyCard] | None = None


def _coerce_int(v: Any) -> int:
    try:
        if isinstance(v, str) and v.startswith("0x"):
            return int(v, 16)
        return int(v or 0)
    except (ValueError, TypeError):
        return 0


def _init_worker(
    sparse_mapping: dict,
    manual_translations: dict,
    source_path: str,
):
    """Initializer for multiprocessing pool to set up expensive adapters."""
    global _MEMBER_ADAPTER, _LIVE_ADAPTER, _ENERGY_ADAPTER, _manual_translations_en, _sparse_manager
    _MEMBER_ADAPTER = TypeAdapter(MemberCard)
    _LIVE_ADAPTER = TypeAdapter(LiveCard)
    _ENERGY_ADAPTER = TypeAdapter(EnergyCard)
    _manual_translations_en = manual_translations
    
    # We provide a pre-loaded "mapping" to avoid re-parsing YAML in each worker
    _sparse_manager = SparseSourceManager(source_path)
    _sparse_manager.mapping = sparse_mapping
    # Mark it as "loaded" to prevent get_ability() from calling load() again
    _sparse_manager._last_loaded_mtime = float("inf")


def _build_export_excludes(export_profile: str) -> tuple[dict, dict]:
    # Runtime exports retain authored frame_program and raw_text while also
    # carrying derived effects, conditions, and costs.
    exclude_ability_fields = {
        "bytecode": True,
        "filters": True,
        "option_names": True,
        "semantic_form": True,  # Exclude from default export
        "_semantic_source": True,  # Internal tracking field
    }
    exclude_card_fields = {"faq": True, "abilities": {"__all__": exclude_ability_fields}}

    if export_profile == "runtime":
        exclude_ability_fields.update(
            {
                "modal_options": True,
            }
        )

    return exclude_ability_fields, exclude_card_fields


def _card_has_ability_source(data: dict[str, Any]) -> bool:
    return any(str(data.get(key, "")).strip() for key in ("ability", "original_text")) or bool(
        data.get("abilities")
    ) or bool(
        isinstance(data.get("frame_program"), dict)
        and data["frame_program"].get("frames")
    )


def _process_card_worker(args):
    """Worker function for parallel card compilation."""
    key, item, export_profile, existing_id, logical_id, variant_idx = args
    
    ctype = item.get("type", "")
    card_no = key
    packed_id = existing_id if existing_id is not None else ((variant_idx << 12) | logical_id)
    
    # Define fields to exclude from compiled output to reduce bloat.
    _, exclude_card_fields = _build_export_excludes(export_profile)

    try:
        if ctype == "メンバー":
            card = parse_member(packed_id, card_no, item)
            dumped = _MEMBER_ADAPTER.dump_python(card, mode="json", exclude=exclude_card_fields)
            return ("member", str(packed_id), dumped, None)
        elif ctype == "ライブ":
            card = parse_live(packed_id, card_no, item)
            dumped = _LIVE_ADAPTER.dump_python(card, mode="json", exclude=exclude_card_fields)
            return ("live", str(packed_id), dumped, None)
        else:
            card = parse_energy(packed_id, card_no, item)
            dumped = _ENERGY_ADAPTER.dump_python(card, mode="json")
            return ("energy", str(packed_id), dumped, None)
    except Exception as e:
        import traceback
        return (None, card_no, None, f"[CARD PARSE] {card_no}: {e}\n{traceback.format_exc()}")


# =============================================================================
# COMPILATION PIPELINE - Top Level Entry Point
# =============================================================================

def compile_cards(
    input_path: str,
    output_path: str,
    quiet: bool = False,
    export_profile: str = "runtime",
    ability_source_path: str | None = None,
) -> bool:
    """
    Main compilation pipeline.
    
    FLOW:
    1. Load raw card JSON
    2. Resolve semantic/runtime data for each card
    3. Parallel worker compilation of cards
    4. Write compiled JSON output only when content changed
    
    Args:
        input_path: Path to raw cards.json
        output_path: Path for compiled output
        quiet: Minimize output logging
        export_profile: "runtime" (production) or "full" (with inspection fields)
    """
    if ability_source_path:
        _set_sparse_source_path(ability_source_path)

    if not quiet:
        print(f"Loading raw cards from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    compiled_data = {
        "member_db": {},
        "live_db": {},
        "energy_db": {},
        "meta": {
            "version": "1.0",
            "source": input_path,
            "ability_source": SPARSE_INDEX_PATH,
            "ability_source_mode": (
                "semantic_dump" if str(SPARSE_INDEX_PATH).endswith("ability_semantic_dump.json") else "frame_source"
            ),
            "execution_model": "semantic_runtime_export",
        },
    }

    # Load existing card_id mapping if available (for ID stability)
    existing_id_mapping = {}
    mapping_path = "data/card_id_mapping.json"
    if os.path.exists(mapping_path):
        if not quiet:
            print(f"Loading existing ID mapping from {mapping_path}...")
        with open(mapping_path, "r", encoding="utf-8") as f:
            raw_mapping = json.load(f)
            # Normalize keys to ensure stability across character variants (+ vs ＋)
            for k, v in raw_mapping.items():
                norm_k = SparseSourceManager._normalize_card_no(k)
                existing_id_mapping[norm_k] = v
        if not quiet:
            print(f"Loaded {len(existing_id_mapping)} existing ID mappings (normalized)")

    sorted_keys = sorted(raw_data.keys())
    # Logic for bit-packed IDs
    # Bits 0-11: Logical ID (0-4095)
    # Bits 12-15: Variant Index (0-15)
    logical_id_map = {}  # (name, ability_text) -> logic_id
    logic_id_to_variant_count = {}  # logic_id -> next_variant_index
    next_logic_id = 0

    # Initialize from existing mapping
    if existing_id_mapping:
        for card_no, card_id in existing_id_mapping.items():
            logic_id = card_id & 0xFFF  # Lower 12 bits
            variant_idx = (card_id >> 12) & 0xF  # Upper 4 bits
            if logic_id >= next_logic_id:
                next_logic_id = logic_id + 1
            if logic_id not in logic_id_to_variant_count:
                logic_id_to_variant_count[logic_id] = 0
            if variant_idx >= logic_id_to_variant_count[logic_id]:
                logic_id_to_variant_count[logic_id] = variant_idx + 1

    success_count = 0
    errors = []

    # Prepare worker arguments
    worker_args = []
    # We must determine IDs in the main process to ensure consistency
    # (especially since next_logic_id/variant_idx tracking is stateful)
    for key in sorted_keys:
        item = raw_data[key]
        v_key = key
        v_data = item

        # Use normalized key for lookup to match character variants
        norm_v_key = SparseSourceManager._normalize_card_no(v_key)
        existing_id = existing_id_mapping.get(norm_v_key)
        logical_id = 0
        v_idx = 0

        if existing_id is None:
            v_name = str(v_data.get("name", "Unknown"))
            v_ability = str(v_data.get("ability", ""))
            logic_key = (v_name, v_ability)

            if logic_key not in logical_id_map:
                logical_id_map[logic_key] = next_logic_id
                logic_id_to_variant_count[next_logic_id] = 0
                next_logic_id += 1

            logical_id = logical_id_map[logic_key]
            v_idx = logic_id_to_variant_count[logical_id]
            logic_id_to_variant_count[logical_id] += 1

        worker_args.append((v_key, v_data, export_profile, existing_id, logical_id, v_idx))

    # Execute in parallel
    try:
        worker_count = int(os.environ.get("LOVECA_COMPILER_WORKERS", multiprocessing.cpu_count()))
    except (TypeError, ValueError):
        worker_count = multiprocessing.cpu_count()
    worker_count = max(1, worker_count)

    init_args = (
        _sparse_manager.mapping,
        _manual_translations_en,
        SPARSE_INDEX_PATH,
    )
    
    # Default to single worker for speed (multiprocessing has overhead for small datasets)
    if worker_count == 1 or len(worker_args) < 100:
        if not quiet:
            print(f"Compiling {len(worker_args)} cards...")
        _init_worker(*init_args)
        results = [_process_card_worker(args) for args in worker_args]
    else:
        if not quiet:
            print(f"Compiling {len(worker_args)} cards using {worker_count} workers...")
        try:
            with multiprocessing.Pool(
                processes=worker_count, initializer=_init_worker, initargs=init_args
            ) as pool:
                results = pool.map(_process_card_worker, worker_args)
        except (OSError, PermissionError, RuntimeError) as exc:
            if not quiet:
                print(f"Warning: multiprocessing unavailable ({exc}); using single worker.")
            _init_worker(*init_args)
            results = [_process_card_worker(args) for args in worker_args]
        
    for res_type, pk, data, err in results:
        if err:
            errors.append(err)
        else:
            if res_type == "member":
                compiled_data["member_db"][pk] = data
            elif res_type == "live":
                compiled_data["live_db"][pk] = data
            elif res_type == "energy":
                compiled_data["energy_db"][pk] = data
            success_count += 1

    encoded_output = json.dumps(compiled_data, ensure_ascii=False, indent=2) + "\n"
    existing_output = None
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing_output = f.read()

    changed = encoded_output != existing_output
    if changed:
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(encoded_output)

    if not quiet:
        if errors:
            print(f"\nCompiled {success_count} cards with {len(errors)} errors:")
            for error in errors[:20]:  # Show first 20 errors
                print(f"  {error}")
            if len(errors) > 20:
                print(f"  ... and {len(errors) - 20} more errors")
        else:
            print(f"\nCompiled {success_count} cards successfully")
        print("Done.")

    return changed


def _resolve_img_path(data: dict) -> str:
    # Use cards_webp as the flattened source
    img_path = str(data.get("_img", ""))
    if img_path:
        filename = os.path.basename(img_path)
        if filename.lower().endswith(".png"):
            filename = filename[:-4] + ".webp"
        return f"cards_webp/{filename}"

    raw_url = str(data.get("img", ""))
    if raw_url:
        filename = os.path.basename(raw_url)
        if filename.lower().endswith(".png"):
            filename = filename[:-4] + ".webp"
        return f"cards_webp/{filename}"

    return raw_url


# Flag Constants (Matching Rust engine)
FLAG_DRAW = 1 << 0
FLAG_SEARCH = 1 << 1
FLAG_RECOVER = 1 << 2
FLAG_BUFF = 1 << 3
FLAG_CHARGE = 1 << 4
FLAG_TEMPO = 1 << 5
FLAG_REDUCE = 1 << 6
FLAG_BOOST = 1 << 7
FLAG_TRANSFORM = 1 << 8
FLAG_WIN_COND = 1 << 9
FLAG_MOVE = 1 << 10
FLAG_TAP = 1 << 11

CHOICE_FLAG_LOOK = 1
CHOICE_FLAG_DISCARD = 2
CHOICE_FLAG_MODE = 4
CHOICE_FLAG_COLOR = 8
CHOICE_FLAG_ORDER = 16

SYN_FLAG_GROUP = 1 << 0
SYN_FLAG_COLOR = 1 << 1
SYN_FLAG_BATON = 1 << 2
SYN_FLAG_CENTER = 1 << 3
SYN_FLAG_LIFE_LEAD = 1 << 4

COST_FLAG_DISCARD = 0x01

_TRIGGER_SEMANTIC_FLAGS = {
    TriggerType.ON_PLAY: 0x01,
    TriggerType.ACTIVATED: 0x02,
}

_EFFECT_FLAG_MAP = {
    EffectType.DRAW: FLAG_DRAW,
    EffectType.SEARCH_DECK: FLAG_SEARCH,
    EffectType.RECOVER_MEMBER: FLAG_RECOVER,
    EffectType.RECOVER_LIVE: FLAG_RECOVER,
    EffectType.ADD_BLADES: FLAG_BUFF,
    EffectType.ADD_HEARTS: FLAG_BUFF,
    EffectType.BUFF_POWER: FLAG_BUFF,
    EffectType.ENERGY_CHARGE: FLAG_CHARGE,
    EffectType.MOVE_MEMBER: FLAG_MOVE,
    EffectType.SWAP_CARDS: FLAG_MOVE,
    EffectType.TAP_MEMBER: FLAG_TAP,
    EffectType.TAP_OPPONENT: FLAG_TAP,
    EffectType.REDUCE_COST: FLAG_REDUCE,
    EffectType.BOOST_SCORE: FLAG_BOOST,
    EffectType.TRANSFORM_COLOR: FLAG_TRANSFORM,
    EffectType.REDUCE_HEART_REQ: FLAG_WIN_COND,
}

_SYNERGY_FLAG_MAP = {
    ConditionType.COUNT_GROUP: SYN_FLAG_GROUP,
    ConditionType.SELF_IS_GROUP: SYN_FLAG_GROUP,
    ConditionType.HAS_COLOR: SYN_FLAG_COLOR,
    ConditionType.BATON: SYN_FLAG_BATON,
    ConditionType.IS_CENTER: SYN_FLAG_CENTER,
    ConditionType.LIFE_LEAD: SYN_FLAG_LIFE_LEAD,
}

_COST_FLAG_MAP = {
    AbilityCostType.DISCARD_HAND: COST_FLAG_DISCARD,
    AbilityCostType.DISCARD_MEMBER: COST_FLAG_DISCARD,
    AbilityCostType.TAP_SELF: 0x02,
    AbilityCostType.TAP_MEMBER: 0x02,
}

# Load manual translations
MANUAL_TRANSLATIONS_EN_PATH = "data/manual_translations_en.json"
_manual_translations_en = {}


class SparseSourceManager:
    """Manages loading and looking up abilities from the canonical authored ability source."""

    _CARD_REF_RE = re.compile(
        r"^(?P<card_no>[^|]+?)\s*\|.*?\(ab#(?P<idx>\d+)(?:[\s\u3000)]|$)"
    )

    def __init__(self, source_path: str):
        self.yaml_path = source_path
        # (card_no, ab_idx) -> sparse entry payload
        self.mapping = {}
        self._last_loaded_mtime: float | None = None
        self._debug = os.environ.get("LOVECA_SPARSE_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
        self.load(force=True)

    @staticmethod
    def _normalize_card_no(card_no: str) -> str:
        if not card_no:
            return ""

        normalized = unicodedata.normalize("NFKC", str(card_no)).strip()
        translation = str.maketrans(
            {
                "\u2212": "-",
                "\u2010": "-",
                "\u2011": "-",
                "\u2012": "-",
                "\u2013": "-",
                "\u2014": "-",
                "\uff0b": "+",
                "\ufe62": "+",
                "\u207a": "+",
                "\u3000": "",
                " ": "",
            }
        )
        return normalized.translate(translation).upper()

    def _log(self, message: str) -> None:
        if self._debug:
            print(message)

    @classmethod
    def _extract_card_ref(cls, card_ref: Any) -> tuple[str, int] | None:
        if isinstance(card_ref, dict):
            card_no = cls._normalize_card_no(str(card_ref.get("card_no", "")))
            raw_idx = card_ref.get("ability_index", card_ref.get("ab_idx", card_ref.get("index")))
            if card_no and raw_idx is not None:
                try:
                    return card_no, int(raw_idx)
                except (TypeError, ValueError):
                    return None
            return None

        card_str = str(card_ref).strip()
        if not card_str:
            return None

        match = cls._CARD_REF_RE.match(card_str)
        if not match:
            return None

        return cls._normalize_card_no(match.group("card_no")), int(match.group("idx"))

    def load(self, force: bool = False):
        if not os.path.exists(self.yaml_path):
            self.mapping = {}
            self._last_loaded_mtime = None
            return

        try:
            current_mtime = os.path.getmtime(self.yaml_path)
        except OSError:
            self.mapping = {}
            self._last_loaded_mtime = None
            return

        if not force and self._last_loaded_mtime == current_mtime and self.mapping:
            return

        try:
            self._log(f"Loading sparse ability index from {self.yaml_path}")
            if str(self.yaml_path).endswith(".yaml"):
                import yaml
                with open(self.yaml_path, "r", encoding="utf-8-sig") as f:
                    data = yaml.safe_load(f)
            else:
                with open(self.yaml_path, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
            if not data:
                self.mapping = {}
                self._last_loaded_mtime = current_mtime
                return

            next_mapping = {}
            abilities_list = data.get("abilities")
            if not isinstance(abilities_list, list):
                abilities_list = []
            self._log(f"SparseSourceManager.load() found {len(abilities_list)} authored entries")

            for entry in abilities_list:
                trigger_id = _coerce_int(entry.get("trigger_id", 0))
                frames = list(entry.get("frames", []) or [])
                if not frames:
                    semantic_form = entry.get("semantic_form", {})
                    if isinstance(semantic_form, dict):
                        frames = list(semantic_form_to_frame_program(semantic_form).get("frames", []) or [])
                semantic_form = entry.get("semantic_form", {})
                if not isinstance(semantic_form, dict):
                    semantic_form = {}
                card_refs = entry.get("card_refs", [])
                if not isinstance(card_refs, list):
                    continue
                for card_ref in card_refs:
                    extracted = self._extract_card_ref(card_ref)
                    if extracted is None:
                        continue
                    card_no, ab_idx = extracted
                    next_mapping[(card_no, ab_idx)] = {
                        "trigger_id": trigger_id,
                        "frames": frames,
                        "semantic_form": semantic_form,
                        "raw_text": str(
                            entry.get("primary_text_jp", "")
                            or entry.get("primary_text_en", "")
                            or semantic_form.get("source_text", "")
                            or entry.get("raw_text", "")
                            or ""
                        ),
                        "is_once_per_turn": bool(entry.get("is_once_per_turn", False)),
                        "requires_selection": bool(entry.get("requires_selection", False)),
                        "choice_flags": _coerce_int(entry.get("choice_flags", 0)),
                        "choice_count": _coerce_int(entry.get("choice_count", 0)),
                        "source_words": entry.get("source_words", []),
                    }

            self.mapping = next_mapping
            self._last_loaded_mtime = current_mtime
            self._log(f"Loaded {len(self.mapping)} sparse mappings into memory")
        except Exception as e:
            print(f"Warning: Failed to load sparse ability index: {e}")
            self.mapping = {}
            self._last_loaded_mtime = None

    def get_ability(self, card_no: str, ab_idx: int) -> dict[str, Any] | None:
        # Skip load() if mapping is already populated (optimization for workers)
        if not self.mapping:
            self.load()
        return self.mapping.get((self._normalize_card_no(card_no), ab_idx))


# Global sparse manager for the authored ability source.
ABILITY_FRAME_SOURCE_PATH = "data/ability_frame_source.json"
ABILITY_SEMANTIC_DUMP_PATH = "data/ability_semantic_dump.json"
SPARSE_INDEX_PATH = ABILITY_FRAME_SOURCE_PATH
_sparse_manager = SparseSourceManager(SPARSE_INDEX_PATH)


def _set_sparse_source_path(source_path: str) -> None:
    """Rebuild the sparse source manager from a different authored source."""
    global SPARSE_INDEX_PATH, _sparse_manager
    SPARSE_INDEX_PATH = source_path
    _sparse_manager = SparseSourceManager(SPARSE_INDEX_PATH)


def _post_process_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Post-process frames to insert JUMP_IF_FALSE after SELECT_MEMBER when followed by target-dependent effects."""
    i = 0
    while i < len(frames) - 1:
        frame = frames[i]
        next_frame = frames[i + 1]
        op = str(frame.get("op", frame.get("opcode", ""))).upper()
        next_op = str(next_frame.get("op", next_frame.get("opcode", ""))).upper()
        
        # If SELECT_MEMBER is followed by an effect that needs a target (ADD_BLADES, ADD_HEARTS, ACTIVATE_MEMBER)
        # insert JUMP_IF_FALSE to skip the effect if selection failed
        if op == "SELECT_MEMBER" and next_op in {"ADD_BLADES", "ADD_HEARTS", "ACTIVATE_MEMBER"}:
            jump_frame = {
                "op": "JUMP_IF_FALSE",
                "value": 1,  # Skip 1 frame (the next effect)
                "frame_index": i + 1,
            }
            frames.insert(i + 1, jump_frame)
            i += 1  # Skip the jump frame we just inserted
        i += 1
    
    return frames


def _build_ability_from_sparse_entry(
    entry: dict[str, Any],
    raw_text: str,
    ability_index: int,
) -> Ability:
    """
    Build an Ability object from a sparse authored entry.
    
    FLOW:
    1. Extract trigger_id, frames, flags from sparse entry
    2. _post_process_frames() - insert JUMP_IF_FALSE where needed
    3. _select_ability_raw_text() - get appropriate raw text for this ability
    4. Return Ability with trigger, empty effects/conditions/costs (filled later by semantic processor)
    
    Args:
        entry: Sparse index entry with trigger_id, frames, flags
    raw_text: Full ability text from cards.json
    ability_index: Index of this ability on the card (0, 1, 2...)
    
    Returns:
        Ability object ready for semantic population
    """
    trigger_id = _coerce_int(entry.get("trigger_id", 0))
    semantic_form = entry.get("semantic_form", {})
    if not isinstance(semantic_form, dict):
        semantic_form = {}
    
    frames = list(entry.get("frames", []) or [])
    if not frames:
        frames = list(semantic_form_to_frame_program(semantic_form).get("frames", []) or [])
    frames = _post_process_frames(frames)
    
    ability_raw_text = str(entry.get("raw_text", "") or "").strip() or _select_ability_raw_text(raw_text, ability_index, entry)
    return Ability(
        raw_text=ability_raw_text,
        trigger=TriggerType(trigger_id),
        effects=[],
        frame_program={"frames": frames},
        semantic_form=semantic_form,
        costs=[],
        conditions=[],
        is_once_per_turn=bool(entry.get("is_once_per_turn", False)),
        requires_selection=bool(entry.get("requires_selection", False)),
        card_no="",
    )


def _override_trigger_for_known_choice_cards(card_no: str, ability: Ability) -> None:
    """Apply narrow trigger overrides for authored cards that still carry legacy markers."""
    if card_no.startswith("PL!S-bp5-004"):
        ability.trigger = TriggerType.ACTIVATED


def _resolve_abilities(card_no: str, data: dict) -> list[Ability]:
    """
    Resolve abilities for a card from the sparse YAML index.
    
    FLOW:
    1. Check if card has ability source data
    2. For ab_idx in 0..9: look up (card_no, ab_idx) in sparse index
    3. If found: _build_ability_from_sparse_entry() creates Ability
    4. Return list of abilities (empty list if card has no abilities)
    
    Args:
        card_no: Card number like "LL-PR-001-PR"
        data: Raw card dict from cards.json
    
    Returns:
        List of Ability objects (may be empty)
    """
    if not (
        any(str(data.get(key, "")).strip() for key in ("ability", "original_text"))
        or bool(data.get("abilities"))
        or bool(isinstance(data.get("frame_program"), dict) and data["frame_program"].get("frames"))
    ):
        return []

    abilities: list[Ability] = []
    used_sparse = False
    raw_text = str(data.get("ability", data.get("original_text", "")))

    for ab_idx in range(10):
        selected_entry = _sparse_manager.get_ability(card_no, ab_idx)

        if selected_entry is None:
            if used_sparse:
                break
            ability_text = _select_ability_raw_text(raw_text, ab_idx, data)
            if ability_text.strip():
                ability = build_ability_from_text(card_no, raw_text, ab_idx)
                _override_trigger_for_known_choice_cards(card_no, ability)
                abilities.append(ability)
                used_sparse = True
                continue
            continue

        ability = _build_ability_from_sparse_entry(
            selected_entry,
            raw_text,
            ab_idx,
        )
        _override_trigger_for_known_choice_cards(card_no, ability)
        abilities.append(ability)
        used_sparse = True

    if used_sparse:
        return abilities
    raise ValueError(f"[{card_no}] Missing frame entry and no semantic data was available")


def _compute_ability_flags(ab: Ability) -> dict[str, int]:
    """Calculate flags for a single ability based on its effects - simplified version."""
    ability_flags = 0
    choice_flags = int(getattr(ab, "choice_flags", 0) or 0)
    choice_count = int(getattr(ab, "choice_count", 0) or 0)

    for eff in ab.effects:
        et = eff.effect_type
        ability_flags |= _EFFECT_FLAG_MAP.get(et, 0)

        if et == EffectType.LOOK_AND_CHOOSE:
            choice_flags |= CHOICE_FLAG_LOOK
            choice_count = max(choice_count, int(eff.params.get("choose_count", 0) or 0))
        elif et == EffectType.SELECT_MODE:
            choice_flags |= CHOICE_FLAG_MODE
            choice_count = max(choice_count, int(eff.params.get("num_options", 2) or 0))
        elif et == EffectType.COLOR_SELECT:
            choice_flags |= CHOICE_FLAG_COLOR
            choice_count = max(choice_count, len(eff.params.get("choices", [])) or 6)
        elif et == EffectType.ORDER_DECK:
            choice_flags |= CHOICE_FLAG_ORDER
            choice_count = max(choice_count, 3)
    
    res = {
        "ability_flags": ability_flags,
        "choice_flags": choice_flags,
        "choice_count": choice_count,
        "unflagged_logic": False,
    }
    
    return res


def compute_flags(card):
    """Replicates Rust flag calculation logic in the Python compiler."""

    ability_flags = 0
    semantic_flags = 0
    synergy_flags = 0
    cost_flags = 0

    for ab in card.abilities:
        semantic_flags |= _TRIGGER_SEMANTIC_FLAGS.get(ab.trigger, 0)
        if ab.trigger in (TriggerType.TURN_START, TriggerType.TURN_END):
            semantic_flags |= 0x04
        if ab.is_once_per_turn:
            semantic_flags |= 0x08

        res = _compute_ability_flags(ab)
        ability_flags |= res["ability_flags"]
        ab.choice_flags = res["choice_flags"]
        ab.choice_count = res["choice_count"]

        if res.get("unflagged_logic", False):
            semantic_flags |= 0x10

        for c in ab.conditions:
            synergy_flags |= _SYNERGY_FLAG_MAP.get(c.type, 0)

        for cost in ab.costs:
            cost_flags |= _COST_FLAG_MAP.get(cost.type, 0)

    card.ability_flags = ability_flags
    card.semantic_flags = semantic_flags
    card.synergy_flags = synergy_flags
    if hasattr(card, "cost_flags"):
        card.cost_flags = cost_flags


def _hydrate_card_abilities(card_no: str, data: dict) -> tuple[str, list[Ability], dict]:
    translation_en = _manual_translations_en.get(card_no)
    abilities = _resolve_abilities(card_no, data)
    for ab in abilities:
        ab.card_no = card_no
    return translation_en, abilities, data.get("special_heart", {})


def parse_member(card_id: int, card_no: str, data: dict) -> MemberCard:
    """
    Parse a member card from raw JSON data.
    
    FLOW:
    1. _resolve_abilities() - Get abilities from sparse index
    2. _populate_semantic_from_frames() - Fill effects/conditions/costs from frames
    3. Create MemberCard with all fields
    4. compute_flags() - Calculate card-level flags
    
    Args:
        card_id: Bit-packed card ID
        card_no: Card number string
        data: Raw card dict from cards.json
    Returns:
        MemberCard ready for JSON export
    """
    translation_en, abilities, spec = _hydrate_card_abilities(card_no, data)

    card = MemberCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Unknown")),
        cost=int(data.get("cost", 0)),
        hearts=parse_hearts(data.get("base_heart", {})),
        blade_hearts=parse_blade_hearts(data.get("blade_heart", {})),
        blades=int(data.get("blade", 0)),
        groups=data.get("series", ""),
        units=data.get("unit", ""),
        abilities=abilities,
        rare=str(data.get("rare", "N")),
        img_path=_resolve_img_path(data),
        ability_text="",
        original_text=str(data.get("ability", "")),
        original_text_en=str(translation_en) if translation_en else "",
        volume_icons=int(spec.get("score", data.get("volume", 0))),
        draw_icons=int(spec.get("draw", data.get("draw", 0))),
        faq=data.get("faq", []),
    )

    compute_flags(card)
    return card


def parse_live(card_id: int, card_no: str, data: dict) -> LiveCard:
    translation_en, abilities, spec = _hydrate_card_abilities(card_no, data)

    card = LiveCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Unknown")),
        score=int(data.get("score", 0)),
        required_hearts=parse_hearts(data.get("need_heart", {})),
        abilities=abilities,
        groups=data.get("series", ""),
        units=data.get("unit", ""),
        img_path=_resolve_img_path(data),
        rare=str(data.get("rare", "N")),
        ability_text="",
        original_text=str(data.get("ability", "")),
        original_text_en=str(translation_en) if translation_en else "",
        volume_icons=int(spec.get("score", data.get("volume", 0))),
        draw_icons=int(spec.get("draw", data.get("draw", 0))),
        blade_hearts=parse_blade_hearts(data.get("blade_heart", {})),
        faq=data.get("faq", []),
    )

    compute_flags(card)
    return card


def parse_energy(card_id: int, card_no: str, data: dict) -> EnergyCard:
    translation_en = _manual_translations_en.get(card_no)
    return EnergyCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Energy")),
        img_path=_resolve_img_path(data),
        ability_text=str(data.get("ability", "")),
        original_text=str(data.get("ability", "")),
        original_text_en=str(translation_en) if translation_en else "",
        rare=str(data.get("rare", "N")),
    )


def parse_hearts(heart_dict: dict) -> np.ndarray:
    hearts = np.zeros(7, dtype=np.int32)
    if not heart_dict:
        return hearts
    for k, v in heart_dict.items():
        if k.startswith("heart"):
            try:
                num_str = k.replace("heart", "")
                if num_str == "0":  # Handle heart0 as ANY/STAR
                    hearts[6] = int(v)
                    continue
                idx = int(num_str) - 1
                if 0 <= idx < 6:
                    hearts[idx] = int(v)
            except ValueError:
                pass
        elif k in ["common", "any", "star"]:
            hearts[6] = int(v)
    return hearts


def parse_blade_hearts(heart_dict: dict) -> np.ndarray:
    hearts = np.zeros(7, dtype=np.int32)
    if not heart_dict:
        return hearts
    for k, v in heart_dict.items():
        if k == "b_all":
            hearts[6] = int(v)
        elif k.startswith("b_heart"):
            try:
                idx = int(k.replace("b_heart", "")) - 1
                if 0 <= idx < 6:
                    hearts[idx] = int(v)
            except ValueError:
                pass
    return hearts
def main():
    """Main entry point for the compiler."""
    parser = argparse.ArgumentParser(
        description="Compile raw card data into compiled card JSON"
    )
    parser.add_argument("--input", default="data/cards.json", help="Path to raw cards.json")
    parser.add_argument("--output", default="data/cards_compiled.json", help="Output path")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimize output"
    )
    parser.add_argument(
        "--export-profile",
        choices=["full", "runtime"],
        default="runtime",
        help="Export schema profile: 'full' keeps inspection fields, 'runtime' prunes inspection-only fields",
    )
    args = parser.parse_args()

    _load_translations_if_present(quiet=args.quiet)
    compile_cards(args.input, args.output, quiet=args.quiet, export_profile=args.export_profile)


if __name__ == "__main__":
    main()
