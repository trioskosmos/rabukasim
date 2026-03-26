from __future__ import annotations

import argparse
import datetime
import json
import multiprocessing
import os
import re
import sys
import unicodedata
import hashlib
from pathlib import Path

# Add project root to path to allow imports if running as script
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Any

import numpy as np
from pydantic import TypeAdapter

# from compiler.parser import AbilityParser
from engine.models.ability import (
    Ability,
    AbilityCostType,
    Condition,
    ConditionType,
    Cost,
    Effect,
    EffectType,
    TargetType,
    TriggerType,
)
from engine.models.ability_ir import SEMANTIC_FORM_VERSION, VersionGate
from engine.models.card import EnergyCard, LiveCard, MemberCard
from engine.models.enums import CHAR_MAP, Unit
from engine.models.opcodes import Opcode
from tools import frame_codec

# O(total_abilities) -> O(unique_abilities)
_ABILITY_COMPILATION_CACHE: dict[str, dict[str, Any]] = {}
_bytecode_compile_errors: list[str] = []

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


def _coerce_bool(v: Any) -> bool:
    return bool(v)


def _coerce_enum(enum_cls: Any, v: Any, default: Any) -> Any:
    try:
        return enum_cls(int(v or 0))
    except (ValueError, TypeError, KeyError):
        return default


def _dict_or_empty(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _init_worker(ability_cache: dict[str, dict[str, Any]], sparse_mapping: dict, manual_translations: dict):
    """Initializer for multiprocessing pool to set up expensive adapters and shared ability cache."""
    global _MEMBER_ADAPTER, _LIVE_ADAPTER, _ENERGY_ADAPTER, _ABILITY_COMPILATION_CACHE, _manual_translations_en, _sparse_manager
    _MEMBER_ADAPTER = TypeAdapter(MemberCard)
    _LIVE_ADAPTER = TypeAdapter(LiveCard)
    _ENERGY_ADAPTER = TypeAdapter(EnergyCard)
    _ABILITY_COMPILATION_CACHE = ability_cache
    _manual_translations_en = manual_translations
    
    # We provide a pre-loaded "mapping" to avoid re-parsing YAML in each worker
    _sparse_manager = SparseSourceManager(SPARSE_INDEX_PATH)
    _sparse_manager.mapping = sparse_mapping
    # Mark it as "loaded" to prevent get_ability() from calling load() again
    _sparse_manager._last_loaded_mtime = float("inf")


def _build_export_excludes(export_profile: str) -> tuple[dict, dict]:
    exclude_ability_fields = {
        "instructions": True,
        "raw_text": True,
        "pseudocode": True,
        "filters": True,
        "option_names": True,
        "semantic_form": True,
    }
    exclude_card_fields = {"faq": True, "abilities": {"__all__": exclude_ability_fields}}

    if export_profile == "runtime":
        exclude_ability_fields.update(
            {
                "modal_options": True,
            }
        )

    return exclude_ability_fields, exclude_card_fields


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
            card = parse_member(packed_id, card_no, item, export_profile=export_profile)
            dumped = _MEMBER_ADAPTER.dump_python(card, mode="json", exclude=exclude_card_fields)
            return ("member", str(packed_id), dumped, None)
        elif ctype == "ライブ":
            card = parse_live(packed_id, card_no, item, export_profile=export_profile)
            dumped = _LIVE_ADAPTER.dump_python(card, mode="json", exclude=exclude_card_fields)
            return ("live", str(packed_id), dumped, None)
        else:
            card = parse_energy(packed_id, card_no, item)
            dumped = _ENERGY_ADAPTER.dump_python(card, mode="json")
            return ("energy", str(packed_id), dumped, None)
    except Exception as e:
        import traceback
        return (None, card_no, None, f"[CARD PARSE] {card_no}: {e}\n{traceback.format_exc()}")


def compile_cards(input_path: str, output_path: str, quiet: bool = False, export_profile: str = "full"):
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
            "semantic_form_version": SEMANTIC_FORM_VERSION,
            "semantic_form_enabled": export_profile != "runtime",
            "export_profile": export_profile,
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
    validation_issues = []  # Bytecode validation

    # Pre-create adapters
    member_adapter = TypeAdapter(MemberCard)
    live_adapter = TypeAdapter(LiveCard)
    energy_adapter = TypeAdapter(EnergyCard)

    # Prepare worker arguments
    worker_args = []
    processed_keys = set()
    
    # We must determine IDs in the main process to ensure consistency
    # (especially since next_logic_id/variant_idx tracking is stateful)
    for key in sorted_keys:
        if key in processed_keys:
            continue
            
        item = raw_data[key]
        processed_keys.add(key)
        
        # Collect variants from rare_list
        variants = [{"card_no": key, "data": item}]
        if "rare_list" in item and isinstance(item["rare_list"], list):
            for r in item["rare_list"]:
                v_no = r.get("card_no")
                if v_no and v_no != key:
                    if v_no in sorted_keys:
                        processed_keys.add(v_no)
                    v_item = item.copy()
                    v_item.update(r)
                    variants.append({"card_no": v_no, "data": v_item})
                    
        for v in variants:
            v_key = v["card_no"]
            v_data = v["data"]
            
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
    # --- Pre-compile Unique Abilities (Big O Optimization: O(total) -> O(unique)) ---
    # We identify all unique ability signatures across the entire game and compile them ONCE
    # in the main process, then share the result with all worker processes.
    if not quiet:
        print("Pre-compiling unique abilities...")
    
    _sparse_manager.load()
    unique_ability_cache: dict[str, dict[str, Any]] = {}
    
    # Track unique signatures to avoid redundant compilation during pre-pass
    unique_sigs = set()
    for (card_no, ab_idx), entry in _sparse_manager.mapping.items():
        trigger_id = int(entry.get("trigger_id", 0))
        frames = entry.get("frames", [])
        
        # Build signature for memoization
        sig = hashlib.sha1(json.dumps([frames, trigger_id], sort_keys=True).encode()).hexdigest()
        if sig in unique_sigs:
            continue
            
        unique_sigs.add(sig)
        
        # Compile a dummy ability to populate the cache entry
        ab = Ability(
            raw_text="",
            trigger=TriggerType(trigger_id),
            effects=[], conditions=[], costs=[],
            frame_program={"frames": frames}
        )
        
        try:
            # Build Semantic Form
            ab.build_semantic_form()
            
            # 3. Calculate Flags (Updates ab.choice_flags etc.)
            res = _compute_ability_flags(ab)
            
            # 4. Store in shared cache
            unique_ability_cache[sig] = {
                "semantic_form": dict(ab.semantic_form),
                "ability_flags": res["ability_flags"],
                "choice_flags": res["choice_flags"],
                "choice_count": res["choice_count"],
                "unflagged_logic": res.get("unflagged_logic", False),
            }
        except Exception as e:
            if not quiet:
                print(f"Warning: Failed to pre-compile ability for {card_no}#{ab_idx}: {e}")

    if not quiet:
        print(f"Pre-compiled {len(unique_ability_cache)} unique abilities.")

    if not quiet:
        print(f"Compiling {len(worker_args)} cards using {multiprocessing.cpu_count()} cores...")
    
    # Pass pre-loaded data to workers to minimize I/O contention
    init_args = (unique_ability_cache, _sparse_manager.mapping, _manual_translations_en)
    with multiprocessing.Pool(initializer=_init_worker, initargs=init_args) as pool:
        results = pool.map(_process_card_worker, worker_args)
        
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

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(compiled_data, f, ensure_ascii=False, indent=2)

    if export_profile != "runtime":
        metadata = frame_codec.load_json(Path("data/metadata.json"))

        # --- Consume the authored frame source without rewriting it ---
        ability_frames_path = Path(ABILITY_FRAME_SOURCE_PATH)
        if ability_frames_path.exists():
            if str(ability_frames_path).endswith(".yaml"):
                ability_frames = frame_codec.load_yaml(ability_frames_path)
            else:
                ability_frames = frame_codec.load_json(ability_frames_path)
            if not quiet:
                print(f"Using authored ability frames from {ability_frames_path}...")
        else:
            ability_frames = {
                "source": str(ability_frames_path),
                "metadata_source": "data/metadata.json",
                "summary": {"card_count": 0, "ability_count": 0, "unique_ability_count": 0},
                "abilities": [],
            }
            print(f"[FRAME WARNING] Authored frame source not found: {ability_frames_path}")

        normalized_ability_frames = frame_codec.normalize_authored_ability_index(ability_frames, metadata)

        # --- Generate Semantic Ability Index (canonical JSON) ---
        sparse_index_path = "data/ability_frame_index.json"
        from tools import semantic_frame_index as semantic_index

        sparse_index = semantic_index.build_semantic_ability_index(
            normalized_ability_frames,
            metadata,
        )
        frame_codec.dump_json(Path(sparse_index_path), sparse_index)
        if not quiet:
            print(f"Generating {sparse_index_path}...")
        # Migration guard: warn if the legacy YAML artifact still exists
        legacy_yaml_path = "data/ability_frame_index.yaml"
        if os.path.exists(legacy_yaml_path):
            print(f"[MIGRATION WARNING] Legacy artifact exists: {legacy_yaml_path}. "
                  f"It is superseded by {sparse_index_path} and can be deleted.")

        # --- Generate Frame Decode Export ---
        if not quiet:
            print("Generating frame decode export...")

    # ============================================================
    #  COMPILATION SUMMARY
    # ============================================================
    total_errors = len(errors) + len(_bytecode_compile_errors) + len(validation_issues)
    sep_thick = "=" * 60
    sep_thin = "-" * 60
    if not quiet or total_errors > 0:
        print(f"\n{sep_thick}")
        print("  COMPILATION SUMMARY")
        print(sep_thick)
        print(f"  Cards compiled: {success_count}")
        print(f"  Total issues:   {total_errors}")

    def _print_grouped_errors(title: str, error_list: list[str]):
        """Group errors by root cause and print a compact summary."""
        if not error_list:
            return
        # Extract first line (the summary) as key, collect card identifiers
        from collections import defaultdict

        groups: dict[str, list[str]] = defaultdict(list)
        for entry in error_list:
            first_line = entry.split("\n")[0].strip()
            # Extract card identifier from "[TYPE] CARD_NO ab#N: error_msg"
            # or "[CARD PARSE] CARD_NO: error_msg"
            parts = first_line.split(": ", 1)
            card_tag = parts[0] if len(parts) > 1 else first_line
            error_msg = parts[1] if len(parts) > 1 else "Unknown"
            groups[error_msg].append(card_tag)

        print(f"\n{sep_thin}")
        print(f"  {title} ({len(error_list)} total, {len(groups)} unique)")
        print(sep_thin)
        for error_msg, cards in groups.items():
            print(f"  [{len(cards)}x] {error_msg}")
            # Show card list compactly (strip [TYPE] prefix for readability)
            card_names = [c.split("] ", 1)[-1] if "] " in c else c for c in cards]
            line = "       Cards: " + ", ".join(card_names)
            if len(line) > 200:
                line = line[:197] + "..."
            print(line)

    if not quiet or (total_errors > 0 and (errors or _bytecode_compile_errors)):
        _print_grouped_errors("CARD PARSE ERRORS", errors)
        _print_grouped_errors("BYTECODE COMPILE ERRORS", _bytecode_compile_errors)

        print(f"\n{sep_thin}")
        print("  FRAME PIPELINE")
        print(sep_thin)
        print(f"  Frame source path:    {ABILITY_FRAME_SOURCE_PATH}")
        print(f"  Frame entries loaded: {len(_sparse_manager.mapping)}")

        if total_errors == 0:
            print("\n  All cards compiled from frames and validated successfully!")
        print(sep_thick)

    # Write detailed log for reference (with full tracebacks)
        print("  Full log: compiler_errors.log")

    if not quiet:
        print("Done.")


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


COST_FLAG_TAP = 0x02

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


# Global compilation version gate (can be overridden per compilation run)
_COMPILATION_VERSION_GATE: VersionGate = VersionGate(
    semantic_version=SEMANTIC_FORM_VERSION
)

_COMPILED_CARD_DB_CACHE: dict[str, Any] | None = None


# Removed _build_frame_program and _frame_program_frame_from_model helpers
# as they are replaced by Ability.to_frame_program() for direct emission.


def _iter_ability_frames(ability):
    frame_program = getattr(ability, "frame_program", None)
    frames = frame_program.get("frames") if isinstance(frame_program, dict) else None
    if isinstance(frames, list) and frames:
        for frame in frames:
            if isinstance(frame, dict):
                op_name = str(frame.get("op") or frame.get("opcode") or frame.get("opcode_name") or frame.get("kind") or "").upper()
                if op_name:
                    yield op_name, frame
        return

    return


def _compile_abilities_for_export(
    abilities: list,
    card_no: str,
    scope: str,
    version_gate: VersionGate = None,
    export_profile: str = "full",
) -> None:
    """
    Compile abilities for export with optional version gating.
    
    Args:
        abilities: List of Ability objects to compile
        card_no: Card number for error reporting
        scope: Scope string ("MEMBER" or "LIVE") for error reporting
        version_gate: Optional VersionGate for controlling compilation version
    """
    
    for idx, ab in enumerate(abilities):
        ab.card_no = card_no
        
        # Use signature-based memoization to avoid redundant compilation of identical abilities.
        # Signature is derived from the frame_program structure and trigger.
        frame_program = getattr(ab, "frame_program", None)
        frames_list = frame_program.get("frames", []) if isinstance(frame_program, dict) else []
        sig = hashlib.sha1(json.dumps([frames_list, int(ab.trigger)], sort_keys=True).encode()).hexdigest()
        
        if sig in _ABILITY_COMPILATION_CACHE:
            cached = _ABILITY_COMPILATION_CACHE[sig]
            ab.semantic_form = dict(cached["semantic_form"])
            ab.ability_flags = int(cached.get("ability_flags", 0))
            ab.choice_flags = int(cached.get("choice_flags", 0))
            ab.choice_count = int(cached.get("choice_count", 0))
            continue

        try:
            if not frames_list:
                frames_list = ab.to_frame_program()
                ab.frame_program = {"frames": frames_list}
            # Bytecode generation removed in favor of direct frame emission.
        except Exception as e:
            import traceback

            tb_str = traceback.format_exc()
            _bytecode_compile_errors.append(f"[{scope}] {card_no} ab#{idx}: {e}\n{tb_str}")
            continue

        try:
            ab.build_semantic_form()
            # Store in cache after successful compilation
            # Note: compute_flags (which updates ab.ability_flags etc.) is called LATER in parse_member/parse_live.
            # We will finalize this cache entry AFTER compute_flags if we want to cache everything.
            # For now, just cache the heavy bytecode/semantic parts.
            _ABILITY_COMPILATION_CACHE[sig] = {
                "semantic_form": dict(ab.semantic_form),
            }
        except Exception as e:
            import traceback

            tb_str = traceback.format_exc()
            _bytecode_compile_errors.append(f"[{scope} SEMANTIC] {card_no} ab#{idx}: {e}\n{tb_str}")

# Load manual translations
MANUAL_TRANSLATIONS_EN_PATH = "data/manual_translations_en.json"
_manual_translations_en = {}


def _load_translations_if_present(quiet: bool = False):
    """Load manual translations from JSON file."""
    global _manual_translations_en
    if os.path.exists(MANUAL_TRANSLATIONS_EN_PATH):
        if not quiet:
            print(f"Loading manual English translations from {MANUAL_TRANSLATIONS_EN_PATH}")
        with open(MANUAL_TRANSLATIONS_EN_PATH, "r", encoding="utf-8") as f:
            _manual_translations_en = json.load(f)


class SparseSourceManager:
    """Manages loading and looking up abilities from the sparse frame index."""

    _CARD_REF_RE = re.compile(
        r"^(?P<card_no>[^|]+?)\s*\|.*?\(ab#(?P<idx>\d+)(?:[\s\u3000)]|$)"
    )

    def __init__(self, yaml_path: str):
        self.yaml_path = yaml_path
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
                data = frame_codec.load_yaml(self.yaml_path)
            else:
                data = frame_codec.load_json(self.yaml_path)
            if not data:
                self.mapping = {}
                self._last_loaded_mtime = current_mtime
                return

            next_mapping = {}
            abilities_list = data.get("abilities", [])
            self._log(f"SparseSourceManager.load() found {len(abilities_list)} abilities in YAML")

            for entry in abilities_list:
                trigger_id = _coerce_int(entry.get("trigger_id", 0))
                frames = list(entry.get("frames", []) or [])
                card_refs = entry.get("card_refs", [])
                cards_list = card_refs if isinstance(card_refs, list) and card_refs else entry.get("cards", [])
                for card_ref in cards_list:
                    extracted = self._extract_card_ref(card_ref)
                    if extracted is None:
                        continue
                    card_no, ab_idx = extracted
                    next_mapping[(card_no, ab_idx)] = {
                        "trigger_id": trigger_id,
                        "frames": frames,
                        "is_once_per_turn": _coerce_bool(entry.get("is_once_per_turn", False)),
                        "requires_selection": _coerce_bool(entry.get("requires_selection", False)),
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
        self.load()
        return self.mapping.get((self._normalize_card_no(card_no), ab_idx))


# Global sparse manager. This is the editable semantic source of truth used by the compiler.
# Ability Frame Path should now point to the YAML source of truth.
ABILITY_FRAME_SOURCE_PATH = "data/ability_frame_index.yaml"
SPARSE_INDEX_PATH = ABILITY_FRAME_SOURCE_PATH
_sparse_manager = SparseSourceManager(SPARSE_INDEX_PATH)


def _build_ability_from_sparse_entry(entry: dict[str, Any], raw_text: str) -> Ability:
    trigger_id = _coerce_int(entry.get("trigger_id", 0))
    frames = list(entry.get("frames", []) or [])
    ability = Ability(
        raw_text=raw_text,
        trigger=TriggerType(trigger_id),
        effects=[],
        conditions=[],
        costs=[],
        is_once_per_turn=_coerce_bool(entry.get("is_once_per_turn", False)),
        requires_selection=_coerce_bool(entry.get("requires_selection", False)),
        choice_flags=_coerce_int(entry.get("choice_flags", 0)),
        choice_count=_coerce_int(entry.get("choice_count", 0)),
    )
    ability.frame_program = {"frames": frames}
    try:
        ability.build_semantic_form()
    except Exception:
        pass
    return ability


def _card_has_ability_source(data: dict[str, Any]) -> bool:
    return any(str(data.get(key, "")).strip() for key in ("ability", "original_text")) or bool(
        data.get("abilities")
    ) or bool(isinstance(data.get("frame_program"), dict) and data["frame_program"].get("frames"))

def _ability_from_dict(payload: dict[str, Any]) -> Ability:
    effects: list[Effect] = []
    for eff in payload.get("effects", []) if isinstance(payload.get("effects"), list) else []:
        if not isinstance(eff, dict):
            continue
        effect_type = _coerce_enum(EffectType, eff.get("effect_type", eff.get("type", 0)), EffectType.NONE)
        target = _coerce_enum(TargetType, eff.get("target", eff.get("target_type", 0)), TargetType.SELF)

        modal_options = []
        for option in eff.get("modal_options", []) if isinstance(eff.get("modal_options"), list) else []:
            option_items = []
            for item in option if isinstance(option, list) else []:
                if isinstance(item, dict):
                    option_items.append(_effect_from_dict(item))
            if option_items:
                modal_options.append(option_items)

        effects.append(
            Effect(
                effect_type=effect_type,
                value=_coerce_int(eff.get("value", 0)),
                value_cond=_coerce_enum(ConditionType, eff.get("value_cond", 0), ConditionType.NONE)
                if str(eff.get("value_cond", 0)).isdigit()
                else ConditionType.NONE,
                target=target,
                params=_dict_or_empty(eff.get("params", {})),
                is_optional=_coerce_bool(eff.get("is_optional", eff.get("optional", False))),
                modal_options=modal_options,
                runtime_opcode=_coerce_int(eff.get("runtime_opcode", 0)),
                runtime_value=_coerce_int(eff.get("runtime_value", 0)),
                runtime_attr=_coerce_int(eff.get("runtime_attr", 0)),
                runtime_slot=_coerce_int(eff.get("runtime_slot", 0)),
                runtime_filter=_dict_or_empty(eff.get("runtime_filter", {})),
                runtime_slot_params=_dict_or_empty(eff.get("runtime_slot_params", {})),
            )
        )

    conditions: list[Condition] = []
    for cond in payload.get("conditions", []) if isinstance(payload.get("conditions"), list) else []:
        if not isinstance(cond, dict):
            continue
        cond_type = _coerce_enum(ConditionType, cond.get("type", cond.get("condition_type", 0)), ConditionType.NONE)
        conditions.append(
            Condition(
                type=cond_type,
                params=_dict_or_empty(cond.get("params", {})),
                is_negated=_coerce_bool(cond.get("is_negated", cond.get("negated", False))),
                value=_coerce_int(cond.get("value", 0)),
                attr=_coerce_int(cond.get("attr", 0)),
                runtime_opcode=_coerce_int(cond.get("runtime_opcode", 0)),
                runtime_filter=_dict_or_empty(cond.get("runtime_filter", {})),
                runtime_slot=_dict_or_empty(cond.get("runtime_slot", {})),
            )
        )

    costs: list[Cost] = []
    for cost in payload.get("costs", []) if isinstance(payload.get("costs"), list) else []:
        if not isinstance(cost, dict):
            continue
        cost_type = _coerce_enum(AbilityCostType, cost.get("type", cost.get("cost_type", 0)), AbilityCostType.NONE)
        costs.append(
            Cost(
                type=cost_type,
                value=_coerce_int(cost.get("value", 0)),
                params=_dict_or_empty(cost.get("params", {})),
                runtime_opcode=_coerce_int(cost.get("runtime_opcode", 0)),
                is_optional=_coerce_bool(cost.get("is_optional", cost.get("optional", False))),
                runtime_filter=_dict_or_empty(cost.get("runtime_filter", {})),
                runtime_slot=_dict_or_empty(cost.get("runtime_slot", {})),
            )
        )

    frame_program = _frame_program_from_payload(payload)
    frame_program = _frame_program_from_payload(payload)
    ability = Ability(
        raw_text=str(payload.get("raw_text", payload.get("original_text", ""))),
        trigger=TriggerType(int(payload.get("trigger", 0))),
        effects=effects,
        conditions=conditions,
        costs=costs,
        modal_options=[list(option) for option in payload.get("modal_options", [])] if isinstance(payload.get("modal_options"), list) else [],
        is_once_per_turn=bool(payload.get("is_once_per_turn", False)),
        frame_program=frame_program,
        instructions=[],
        card_no=str(payload.get("card_no", "")),
        requires_selection=bool(payload.get("requires_selection", False)),
        choice_flags=int(payload.get("choice_flags", 0)),
        choice_count=int(payload.get("choice_count", 0)),
        filters=list(payload.get("filters", [])) if isinstance(payload.get("filters"), list) else [],
        option_names=list(payload.get("option_names", [])) if isinstance(payload.get("option_names"), list) else [],
    )
    try:
        ability.build_semantic_form()
    except Exception:
        pass
    return ability


def _effect_from_dict(payload: dict[str, Any]) -> Effect:
    effect_type = _coerce_enum(EffectType, payload.get("effect_type", payload.get("type", 0)), EffectType.NONE)
    target = _coerce_enum(TargetType, payload.get("target", payload.get("target_type", 0)), TargetType.SELF)
    return Effect(
        effect_type=effect_type,
        value=_coerce_int(payload.get("value", 0)),
        value_cond=_coerce_enum(ConditionType, payload.get("value_cond", 0), ConditionType.NONE)
        if str(payload.get("value_cond", 0)).isdigit()
        else ConditionType.NONE,
        target=target,
        params=_dict_or_empty(payload.get("params", {})),
        is_optional=_coerce_bool(payload.get("is_optional", payload.get("optional", False))),
        modal_options=[],
        runtime_opcode=_coerce_int(payload.get("runtime_opcode", 0)),
        runtime_value=_coerce_int(payload.get("runtime_value", 0)),
        runtime_attr=_coerce_int(payload.get("runtime_attr", 0)),
        runtime_slot=_coerce_int(payload.get("runtime_slot", 0)),
        runtime_filter=_dict_or_empty(payload.get("runtime_filter", {})),
        runtime_slot_params=_dict_or_empty(payload.get("runtime_slot_params", {})),
    )


def _resolve_abilities(card_kind: str, card_no: str, data: dict) -> list[Ability]:
    if not _card_has_ability_source(data):
        return []

    abilities: list[Ability] = []
    used_sparse = False
    raw_text = str(data.get("ability", data.get("original_text", "")))

    for ab_idx in range(10):
        entry = _sparse_manager.get_ability(card_no, ab_idx)
        if entry is None:
            if used_sparse:
                break
            continue

        abilities.append(_build_ability_from_sparse_entry(entry, raw_text))
        used_sparse = True

    if used_sparse:
        return abilities
    raise ValueError(f"[{card_no}] Missing frame entry and no frame data was available")


def _compute_ability_flags(ab: Ability) -> dict[str, int]:
    """Calculate flags for a single ability, using memoization."""
    # Build signature
    frame_program = getattr(ab, "frame_program", None)
    frames_list = frame_program.get("frames", []) if isinstance(frame_program, dict) else []
    sig = hashlib.sha1(json.dumps([frames_list, int(ab.trigger)], sort_keys=True).encode()).hexdigest()

    # If we already have flags in the compilation cache, return them
    if sig in _ABILITY_COMPILATION_CACHE:
        cached = _ABILITY_COMPILATION_CACHE[sig]
        if "ability_flags" in cached:
            return {
                "ability_flags": cached["ability_flags"],
                "choice_flags": cached["choice_flags"],
                "choice_count": cached["choice_count"],
            }

    ability_flags = 0
    choice_flags = 0
    choice_count = 0

    flagged_ops = {
        int(Opcode.DRAW): FLAG_DRAW,
        int(Opcode.LOOK_AND_CHOOSE): FLAG_DRAW,
        int(Opcode.RETURN): FLAG_DRAW,
        int(Opcode.SEARCH_DECK): FLAG_SEARCH,
        int(Opcode.RECOVER_LIVE): FLAG_RECOVER,
        int(Opcode.RECOVER_MEMBER): FLAG_RECOVER,
        int(Opcode.ADD_BLADES): FLAG_BUFF,
        int(Opcode.ADD_HEARTS): FLAG_BUFF,
        int(Opcode.MOVE_MEMBER): FLAG_MOVE,
        int(Opcode.SWAP_CARDS): FLAG_MOVE,
        int(Opcode.TAP_OPPONENT): FLAG_TAP,
        int(Opcode.TAP_MEMBER): FLAG_TAP,
        int(Opcode.ENERGY_CHARGE): FLAG_CHARGE,
        int(Opcode.ACTIVATE_MEMBER): FLAG_TEMPO,
        int(Opcode.SET_TAPPED): FLAG_TEMPO,
        int(Opcode.REDUCE_COST): FLAG_REDUCE,
        int(Opcode.BOOST_SCORE): FLAG_BOOST,
        int(Opcode.TRANSFORM_COLOR): FLAG_TRANSFORM,
        int(Opcode.REDUCE_HEART_REQ): FLAG_WIN_COND,
    }

    core_ops = {
        "DRAW", "RECOVER_MEMBER", "RECOVER_LIVE", "ADD_BLADES", "ADD_HEARTS",
        "SEARCH_DECK", "BOOST_SCORE", "ENERGY_CHARGE", "MOVE_MEMBER",
        "SWAP_CARDS", "TAP_OPPONENT", "MODIFY_SCORE_RULE", "REDUCE_COST",
        "REDUCE_HEART_REQ", "RETURN", "LOOK_AND_CHOOSE", "TAP_MEMBER",
        "ACTIVATE_MEMBER", "SET_TAPPED", "TRANSFORM_COLOR", "NOP",
        "JUMP", "JUMP_IF_FALSE", "META_RULE", "SELECT_MODE", "COLOR_SELECT",
        "ORDER_DECK", "MOVE_TO_DECK", "MOVE_TO_DISCARD", "PLAY_MEMBER_FROM_HAND",
        "SET_TARGET_SELF", "SET_TARGET_OPPONENT", "SUM_VALUE", "HAS_KEYWORD",
        "COUNT_STAGE", "COUNT_CARDS", "GROUP_FILTER", "DISCARDED_CARDS",
    }

    unflagged_logic = False
    for op_name, frame in _iter_ability_frames(ab):
        op_name = str(op_name).upper()
        op_id = int(Opcode[op_name]) if op_name in Opcode.__members__ else None

        if op_id is not None and op_id in flagged_ops:
            ability_flags |= flagged_ops[op_id]

        if op_name not in core_ops and not op_name.startswith("C_"):
            unflagged_logic = True

        # Choice Flags Logic
        if op_name == "LOOK_AND_CHOOSE":
            choice_flags |= CHOICE_FLAG_LOOK
            if choice_count == 0:
                raw_choice = frame.get("value", 0)
                pick_count = 0
                if isinstance(raw_choice, int):
                    pick_count = (raw_choice >> 8) & 0xFF
                if pick_count > 0:
                    choice_count = pick_count
                else:
                    effect_choice_count = 0
                    for eff in ab.effects:
                        if eff.runtime_opcode == int(Opcode.LOOK_AND_CHOOSE) or eff.effect_type == EffectType.LOOK_AND_CHOOSE:
                            raw_choice_count = eff.params.get("choose_count")
                            if raw_choice_count is not None:
                                try:
                                    effect_choice_count = int(raw_choice_count)
                                except (TypeError, ValueError):
                                    effect_choice_count = 0
                            if effect_choice_count > 0:
                                break
                    choice_count = effect_choice_count if effect_choice_count > 0 else 3
        elif op_name == "SELECT_MODE":
            choice_flags |= CHOICE_FLAG_MODE
            if choice_count == 0:
                raw_choice = frame.get("value", 0)
                choice_count = int(raw_choice) if isinstance(raw_choice, int) and raw_choice > 0 else 2
        elif op_name == "COLOR_SELECT":
            choice_flags |= CHOICE_FLAG_COLOR
            if choice_count == 0:
                choice_count_from_effect = None
                params = frame.get("params", {}) if isinstance(frame.get("params"), dict) else {}
                choices = params.get("choices")
                if isinstance(choices, list) and choices:
                    choice_count_from_effect = len(choices)
                choice_count = choice_count_from_effect if choice_count_from_effect else 6
        elif op_name == "ORDER_DECK":
            choice_flags |= CHOICE_FLAG_ORDER
            if choice_count == 0:
                choice_count = 3
            params = frame.get("params", {}) if isinstance(frame.get("params"), dict) else {}
            attr = frame.get("attr", {}) if isinstance(frame.get("attr"), dict) else {}
            if (
                params.get("remainder") == "discard"
                or params.get("destination") == "discard"
                or params.get("raw_val") == "REMAINDER"
                or attr.get("remainder") == "discard"
                or attr.get("destination") == "discard"
            ):
                choice_flags |= CHOICE_FLAG_DISCARD

    res = {
        "ability_flags": ability_flags,
        "choice_flags": choice_flags,
        "choice_count": choice_count,
        "unflagged_logic": unflagged_logic,
    }

    # Store back in cache if compilation result already exists
    if sig in _ABILITY_COMPILATION_CACHE:
        _ABILITY_COMPILATION_CACHE[sig].update(res)

    return res


def compute_flags(card):
    """Replicates Rust flag calculation logic in the Python compiler."""

    ability_flags = 0
    semantic_flags = 0
    synergy_flags = 0
    cost_flags = 0

    for ab in card.abilities:
        # Semantic Flags
        if ab.trigger == TriggerType.ON_PLAY:
            semantic_flags |= 0x01
        if ab.trigger == TriggerType.ACTIVATED:
            semantic_flags |= 0x02
        if ab.trigger in [TriggerType.TURN_START, TriggerType.TURN_END]:
            semantic_flags |= 0x04
        if ab.is_once_per_turn:
            semantic_flags |= 0x08

        # Frame/opcode loop for Ability & Choice Flags
        res = _compute_ability_flags(ab)
        ability_flags |= res["ability_flags"]
        ab.choice_flags = res["choice_flags"]
        ab.choice_count = res["choice_count"]
        
        if res.get("unflagged_logic", False):
            semantic_flags |= 0x10

        # Synergy Flags
        for c in ab.conditions:
            if c.type in [ConditionType.COUNT_GROUP, ConditionType.SELF_IS_GROUP]:
                synergy_flags |= SYN_FLAG_GROUP
            if c.type == ConditionType.HAS_COLOR:
                synergy_flags |= SYN_FLAG_COLOR
            if c.type == ConditionType.BATON:
                synergy_flags |= SYN_FLAG_BATON
            if c.type == ConditionType.IS_CENTER:
                synergy_flags |= SYN_FLAG_CENTER
            if c.type == ConditionType.LIFE_LEAD:
                synergy_flags |= SYN_FLAG_LIFE_LEAD

        # Cost Flags
        for cost in ab.costs:
            if cost.type in [AbilityCostType.DISCARD_HAND, AbilityCostType.DISCARD_MEMBER]:
                cost_flags |= COST_FLAG_DISCARD
            if cost.type in [AbilityCostType.TAP_SELF, AbilityCostType.TAP_MEMBER]:
                cost_flags |= COST_FLAG_TAP

    card.ability_flags = ability_flags
    card.semantic_flags = semantic_flags
    card.synergy_flags = synergy_flags
    if hasattr(card, "cost_flags"):
        card.cost_flags = cost_flags


def _extract_units_from_add_tag(abilities):
    """Extract unit IDs from CONSTANT trigger + ADD_TAG (META_RULE) abilities.

    Returns a set of Unit enum values to merge with card.units.
    """
    units_set = set()
    # Mapping token names to Unit enum values
    name_map = {
        "UNIT_CERISE": Unit.CERISE_BOUQUET,
        "UNIT_DOLL": Unit.DOLLCHESTRA,
        "UNIT_MIRAKURA": Unit.MIRA_CRA_PARK,
    }

    for ab_idx, ab in enumerate(abilities):
        if getattr(ab, "trigger", None) != TriggerType.CONSTANT:
            continue
        for _eff_idx, eff in enumerate(getattr(ab, "effects", [])):
            if getattr(eff, "effect_type", None) != EffectType.META_RULE:
                continue
            tag_str = eff.params.get("tag", "") if hasattr(eff, "params") else ""
            if not tag_str:
                continue
            # Normalize tag string: remove surrounding quotes and whitespace
            raw = str(tag_str).strip()
            if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
                raw = raw[1:-1]
            parts_found = []
            for part in raw.split("/"):
                key = part.strip().strip('"').strip("'")
                if key in name_map:
                    units_set.add(name_map[key])
                    parts_found.append((key, name_map[key]))
            # if parts_found:
            #     print(f"[DEBUG _extract] Found META_RULE ADD_TAG in ability #{ab_idx}: raw='{raw}', matched parts: {parts_found}")
    return units_set


def _normalize_unit_values(values):
    """Coerce any stored unit values back into Unit enums."""
    normalized = []
    seen = set()
    for value in values:
        if isinstance(value, Unit):
            unit = value
        elif isinstance(value, int) or (isinstance(value, str) and str(value).isdigit()):
            unit = Unit(int(value))
        else:
            unit = Unit.from_japanese_name(str(value))
        if unit not in seen:
            normalized.append(unit)
            seen.add(unit)
    return normalized


def parse_member(card_id: int, card_no: str, data: dict, export_profile: str = "full") -> MemberCard:
    spec = data.get("special_heart", {})
    translation_en = _manual_translations_en.get(card_no)

    # --- Ability Source Resolution ---
    # Resolve directly from authored frame data.
    abilities = _resolve_abilities("MEMBER", card_no, data)


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
        char_id=int(CHAR_MAP.get(str(data.get("name", "")), 0)),
        faq=data.get("faq", []),
    )

    _compile_abilities_for_export(card.abilities, card_no, "MEMBER", export_profile=export_profile)

    # Extract units from CONSTANT ADD_TAG effects and merge with existing units.
    add_tag_units = _extract_units_from_add_tag(card.abilities)
    if add_tag_units:
        existing_units = set(card.units) if isinstance(card.units, list) else set()
        card.units = _normalize_unit_values(existing_units | add_tag_units)

    compute_flags(card)
    return card


def parse_live(card_id: int, card_no: str, data: dict, export_profile: str = "full") -> LiveCard:
    spec = data.get("special_heart", {})
    translation_en = _manual_translations_en.get(card_no)

    # --- Ability Source Resolution ---
    # Resolve directly from authored frame data.
    abilities = _resolve_abilities("LIVE", card_no, data)

    card = LiveCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Unknown")),
        score=int(data.get("score", 0)),
        required_hearts=parse_live_reqs(data.get("need_heart", {})),
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

    _compile_abilities_for_export(card.abilities, card_no, "LIVE", export_profile=export_profile)

    # Extract units from CONSTANT ADD_TAG effects and merge with existing units.
    add_tag_units = _extract_units_from_add_tag(card.abilities)
    if add_tag_units:
        existing_units = set(card.units) if isinstance(card.units, list) else set()
        card.units = _normalize_unit_values(existing_units | add_tag_units)

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


def parse_live_reqs(req_dict: dict) -> np.ndarray:
    # Use parse_hearts directly as it now handles 7 elements correctly
    return parse_hearts(req_dict)


def calculate_hash(path):
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_json(path):
    """Safely load a JSON file with UTF-8 encoding."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def check_parity(input_path, output_path):
    print(f"Checking parity between {input_path} and {output_path}...")
    compiled_data = load_json(output_path)
    if not compiled_data:
        print("Error: Compiled data not found.")
        return False

    meta = compiled_data.get("meta", {})
    stored_hash = meta.get("source_hash")
    current_hash = calculate_hash(input_path)
    stored_ability_hash = meta.get("ability_source_hash")
    current_ability_hash = calculate_hash(SPARSE_INDEX_PATH)

    if stored_hash == current_hash and stored_ability_hash == current_ability_hash:
        print("SUCCESS: Parity check passed. Compiled data is up to date.")
        return True

    print("WARNING: Parity check FAILED. Source file has changed since last compilation.")
    print(f"Stored cards:   {stored_hash}")
    print(f"Current cards:   {current_hash}")
    print(f"Stored frames:   {stored_ability_hash}")
    print(f"Current frames:  {current_ability_hash}")
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compile raw card data into frame-first card JSON with optional version gating"
    )
    parser.add_argument("--input", default="data/cards.json", help="Path to raw cards.json")
    parser.add_argument("--output", default="data/cards_compiled.json", help="Output path")
    parser.add_argument(
        "--check", action="store_true", help="Only check parity and exit"
    )
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Minimize output"
    )
    parser.add_argument(
        "--export-profile",
        choices=["full", "runtime"],
        default="full",
        help="Export schema profile: 'full' keeps inspection fields, 'runtime' prunes inspection-only fields",
    )
    args = parser.parse_args()

    # Version gating for bytecode is deprecated. Frame format is now the primary unit.

    if args.check:
        if check_parity(args.input, args.output):
            sys.exit(0)
        else:
            sys.exit(1)

    _load_translations_if_present(quiet=args.quiet)
    compile_cards(args.input, args.output, quiet=args.quiet, export_profile=args.export_profile)

    # Update hash in the output file
    if not args.quiet:
        print("Updating source hash in compiled file...")
    compiled_data = load_json(args.output)
    if compiled_data:
        if "meta" not in compiled_data:
            compiled_data["meta"] = {}
        compiled_data["meta"]["source_hash"] = calculate_hash(args.input)
        compiled_data["meta"]["ability_source_hash"] = calculate_hash(SPARSE_INDEX_PATH)
        compiled_data["meta"]["generated_by"] = "compiler/main.py"
        compiled_data["meta"]["generated_at"] = datetime.datetime.now().isoformat()
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            json.dump(compiled_data, f, ensure_ascii=False, indent=2)

    # Copy to both data/ and engine/data/ for compatibility with all scripts
    import shutil

    root_data_path = os.path.join(os.getcwd(), "data", "cards_compiled.json")
    engine_data_path = os.path.join(os.getcwd(), "engine", "data", "cards_compiled.json")

    # Sync to root data/
    if os.path.abspath(args.output) != os.path.abspath(root_data_path):
        try:
            shutil.copy(args.output, root_data_path)
            if not args.quiet:
                print(f"Copied compiled data to {root_data_path}")
        except Exception as e:
            if not args.quiet:
                print(f"Warning: Failed to copy to root data directory: {e}")

    # Sync to engine/data/ to keep paths consistent
    try:
        os.makedirs(os.path.dirname(engine_data_path), exist_ok=True)
        shutil.copy(root_data_path, engine_data_path)
        if not args.quiet:
            print(f"Synced compiled data to {engine_data_path}")
    except Exception as e:
        if not args.quiet:
            print(f"Warning: Failed to sync to engine/data directory: {e}")
