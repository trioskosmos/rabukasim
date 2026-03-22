import datetime
import os
import re
import sys
from pathlib import Path

# Add project root to path to allow imports if running as script
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json
from typing import Any

import numpy as np
from pydantic import TypeAdapter

# from compiler.parser import AbilityParser
from compiler.pseudocode_pipeline import PseudocodeResolver
from engine.models.ability import (
    Ability,
    AbilityCostType,
    ConditionType,
    EffectType,
    TriggerType,
)
from engine.models.ability_ir import BYTECODE_LAYOUT_NAME, BYTECODE_LAYOUT_VERSION, SEMANTIC_FORM_VERSION, VersionGate
from engine.models.bytecode_readable import decode_bytecode
from engine.models.card import EnergyCard, LiveCard, MemberCard
from engine.models.enums import CHAR_MAP, Unit
from engine.models.generated_metadata import CONDITIONS, COSTS, OPCODES
from engine.models.opcodes import Opcode
from tools import bytecode_codec as ability_codec

# --- Compile-time Bytecode Validation ---
# Combined: all valid base opcodes derived from source metadata
_ALL_VALID_OPS = (
    set(OPCODES.values()) | set(CONDITIONS.values()) | set(COSTS.values()) | {0, 1}
)  # Ensure basic ops are included


def validate_bytecode(bytecode: list, card_no: str, ab_idx: int) -> list:
    """Validate a compiled bytecode array for structural integrity.

    Returns a list of warning/error strings. Empty = valid.
    """
    issues = []

    if not bytecode:
        return issues

    # Check 1: Length must be a multiple of 5
    if len(bytecode) % 5 != 0:
        issues.append(f"[{card_no}] ab#{ab_idx}: Bytecode length {len(bytecode)} not a multiple of 5")
        return issues  # Can't safely check further

    # Check 2: Scan all opcodes
    for i in range(0, len(bytecode), 5):
        op = bytecode[i]
        v = bytecode[i + 1]

        # Handle negated opcodes (1000+)
        real_op = op - 1000 if op >= 1000 else op

        if real_op not in _ALL_VALID_OPS:
            issues.append(f"[{card_no}] ab#{ab_idx}: Unknown opcode {real_op} at position {i}")

        # Check 3: JUMP targets in-bounds
        if real_op == 2 or real_op == 3:  # O_JUMP or O_JUMP_IF_FALSE
            target = i + 5 + (v * 5)
            if target < 0 or target > len(bytecode):
                issues.append(
                    f"[{card_no}] ab#{ab_idx}: JUMP at {i} targets position {target}, "
                    f"but bytecode length is {len(bytecode)}"
                )

    # Check 4: Should end with O_RETURN (opcode 1)
    if len(bytecode) >= 5:
        last_op = bytecode[-5]
        real_last = last_op - 1000 if last_op >= 1000 else last_op
        if real_last != 1:  # O_RETURN
            # Not necessarily an error — some bytecodes end with O_JUMP
            # back to the start or fall through. Warn only.
            issues.append(f"[{card_no}] ab#{ab_idx}: Does not end with O_RETURN (last opcode: {real_last})")

    return issues


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


def compile_cards(input_path: str, output_path: str, quiet: bool = False, export_profile: str = "full"):
    if not quiet:
        print(f"Loading raw cards from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    _pseudocode_resolver.reset()

    compiled_data = {
        "member_db": {},
        "live_db": {},
        "energy_db": {},
        "meta": {
            "version": "1.0",
            "source": input_path,
            "bytecode_layout_version": BYTECODE_LAYOUT_VERSION,
            "bytecode_layout_name": BYTECODE_LAYOUT_NAME,
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
            existing_id_mapping = json.load(f)
        if not quiet:
            print(f"Loaded {len(existing_id_mapping)} existing ID mappings")

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

    processed_keys = set()

    for key in sorted_keys:
        if key in processed_keys:
            continue

        item = raw_data[key]
        ctype = item.get("type", "")

        # Collect variants from rare_list
        variants = [{"card_no": key, "name": item.get("name", ""), "data": item}]
        processed_keys.add(key)

        if "rare_list" in item and isinstance(item["rare_list"], list):
            for r in item["rare_list"]:
                v_no = r.get("card_no")
                if v_no and v_no != key:
                    # Create a variant that inherits base data but overrides metadata
                    if v_no in sorted_keys:
                        processed_keys.add(v_no)  # Mark variant as processed so main loop skips it

                    v_item = item.copy()
                    v_item.update(r)
                    variants.append({"card_no": v_no, "name": r.get("name", item.get("name", "")), "data": v_item})

        for v in variants:
            v_key = v["card_no"]
            v_data = v["data"]

            # Check if this card already has an ID in the existing mapping
            if v_key in existing_id_mapping:
                packed_id = existing_id_mapping[v_key]
                # print(f"DEBUG: Using existing ID for card_no={v_key}, packed_id={packed_id}")
            else:
                # Determine Logical Identity for new cards
                # We use Name + Original Text (Ability) as the unique logical key
                v_name = str(v_data.get("name", "Unknown"))
                v_ability = str(v_data.get("ability", ""))
                logic_key = (v_name, v_ability)

                if logic_key not in logical_id_map:
                    logical_id_map[logic_key] = next_logic_id
                    logic_id_to_variant_count[next_logic_id] = 0
                    next_logic_id += 1

                logic_id = logical_id_map[logic_key]
                variant_idx = logic_id_to_variant_count[logic_id]
                logic_id_to_variant_count[logic_id] += 1

                # Pack ID: (variant << 12) | logic
                # Bits 0-11: Logical ID (0-4095)
                # Bits 12-15: Variant Index (0-15)

                if logic_id >= 4096:
                    print(f"WARNING: Logic ID {logic_id} exceeds 12-bit limit (4096). Card: {v_key}")
                if variant_idx >= 16:
                    print(f"WARNING: Variant Index {variant_idx} exceeds 4-bit limit (16). Card: {v_key}")
                    variant_idx = 15  # Cap at maximum to prevent overflow

                packed_id = (variant_idx << 12) | logic_id
                # print(f"DEBUG: Assigned new ID for card_no={v_key}, packed_id={packed_id}")
            # Define fields to exclude from compiled output to reduce bloat.
            # The runtime profile keeps the schema needed by the Rust engine and launcher,
            # while dropping inspection-only fields that are redundant with source data.
            _, exclude_card_fields = _build_export_excludes(export_profile)

            try:
                if ctype == "メンバー":
                    m_card = parse_member(packed_id, v_key, v_data)
                    compiled_data["member_db"][str(packed_id)] = member_adapter.dump_python(
                        m_card, mode="json", exclude=exclude_card_fields
                    )
                elif ctype == "ライブ":
                    l_card = parse_live(packed_id, v_key, v_data)
                    compiled_data["live_db"][str(packed_id)] = live_adapter.dump_python(
                        l_card, mode="json", exclude=exclude_card_fields
                    )
                else:
                    e_card = parse_energy(packed_id, v_key, v_data)
                    compiled_data["energy_db"][str(packed_id)] = energy_adapter.dump_python(
                        e_card, mode="json"
                    )
                success_count += 1
            except Exception as e:
                import traceback

                tb_str = traceback.format_exc()
                errors.append(f"[CARD PARSE] {v_key}: {e}\n{tb_str}")

    # Collect bytecode compile errors from parse_member/parse_live
    global _bytecode_compile_errors
    bc_errors = list(_bytecode_compile_errors)
    _bytecode_compile_errors.clear()

    # --- Bytecode Validation Pass ---
    for db_key in ["member_db", "live_db"]:
        for cid_str, card_data in compiled_data[db_key].items():
            card_no = card_data.get("card_no", cid_str)
            for ab_idx, ab in enumerate(card_data.get("abilities", [])):
                bc = ab.get("bytecode", [])
                issues = validate_bytecode(bc, card_no, ab_idx)
                validation_issues.extend(issues)

    # Output Automatic Documentation
    from compiler.doc_generator import generate_opcode_docs

    generate_opcode_docs(compiled_data, "reports/opcode_reference.md")

    # Note: Units extraction is now handled in parse_live() and parse_member()
    # via consolidated_abilities metadata and ADD_TAG extraction helpers

    # Write output (always write, even with errors)
    if not quiet:
        print(f"Writing compiled data to {output_path}...")
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(compiled_data, f, ensure_ascii=False, indent=2)

    # --- Generate Sparse Ability Index (canonical JSON) ---
    sparse_index_path = "data/ability_frame_index.json"
    sparse_index = ability_codec.build_sparse_ability_index(compiled_data, ability_codec.load_data("data/metadata.json"))
    ability_codec.dump_data(Path(sparse_index_path), sparse_index)
    if not quiet:
        print(f"Generating {sparse_index_path}...")
    # Migration guard: warn if the legacy YAML artifact still exists
    legacy_yaml_path = "data/ability_frame_index.yaml"
    if os.path.exists(legacy_yaml_path):
        print(f"[MIGRATION WARNING] Legacy artifact exists: {legacy_yaml_path}. "
              f"It is superseded by {sparse_index_path} and can be deleted.")

    # --- Generate Decoded Consolidated Abilities ---
    if not quiet:
        print("Generating consolidated_abilities_decoded.json...")
    
    decoded_output_path = "data/consolidated_abilities_decoded.json"
    consolidated_decoded = {
        "_metadata": {
            "generated_by": "compiler/main.py",
            "generated_at": datetime.datetime.now().isoformat()
        }
    }
    decoded_by_card_no = {}
    
    # We'll use the original consolidated_abilities structure as a template
    # but only for the keys that were actually compiled
    for db_name in ["member_db", "live_db"]:
        for cid_str, card_data in compiled_data[db_name].items():
            card_no = str(card_data.get("card_no", "")).strip()
            raw_jp = card_data.get("original_text", "")
            decoded_abs = []
            for ab in card_data.get("abilities", []):
                bc = ab.get("bytecode", [])
                if bc:
                    # Use the authoritative decoder from bytecode_readable
                    decoded_str = decode_bytecode(bc)
                    # Split into lines and remove the legend if present
                    lines = decoded_str.split("\n")
                    if "--- BYTECODE LEGEND ---" in lines:
                        legend_idx = lines.index("--- BYTECODE LEGEND ---")
                        lines = lines[:legend_idx]
                    
                    # Also strip "  00: " prefixes if we want it cleaner, but the user asked for "like in the debug menu"
                    # The debug menu shows the prefixes.
                    decoded_abs.append([line.strip() for line in lines if line.strip()])

            if not decoded_abs:
                continue

            if card_no:
                decoded_by_card_no[card_no] = decoded_abs

            if not raw_jp or raw_jp in consolidated_decoded:
                continue

            # Find the original entry from consolidated_abilities to get metadata (like card lists)
            original_entry = _pseudocode_resolver.consolidated.get(raw_jp)
            if not original_entry:
                continue

            # Copy the original entry and add decoded_bytecode
            new_entry = dict(original_entry) if isinstance(original_entry, dict) else {"pseudocode": original_entry}
            new_entry["decoded_bytecode"] = decoded_abs
            consolidated_decoded[raw_jp] = new_entry

    # Some consolidated keys are intentionally preserved "constant" JP strings that
    # no longer exactly match the compiled card text. Backfill those entries by card id
    # so the decoded export still covers every in-use consolidated ability constant.
    for raw_jp, original_entry in _pseudocode_resolver.consolidated.items():
        if raw_jp in consolidated_decoded or not isinstance(original_entry, dict):
            continue

        candidate_card_nos = []
        for key in ("cards", "ids"):
            values = original_entry.get(key, [])
            if isinstance(values, list):
                candidate_card_nos.extend(str(value).strip() for value in values if str(value).strip())

        decoded_abs = next((decoded_by_card_no.get(card_no) for card_no in candidate_card_nos if card_no in decoded_by_card_no), None)
        if not decoded_abs:
            continue

        new_entry = dict(original_entry)
        new_entry["decoded_bytecode"] = decoded_abs
        consolidated_decoded[raw_jp] = new_entry

    with open(decoded_output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(consolidated_decoded, f, ensure_ascii=False, indent=2)

    # ============================================================
    #  COMPILATION SUMMARY
    # ============================================================
    total_errors = len(errors) + len(bc_errors) + len(validation_issues)
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

    if not quiet or (total_errors > 0 and (errors or bc_errors)):
        _print_grouped_errors("CARD PARSE ERRORS", errors)
        _print_grouped_errors("BYTECODE COMPILE ERRORS", bc_errors)

    if not quiet or total_errors > 0:
        if validation_issues:
            print(f"\n{sep_thin}")
            print(f"  BYTECODE VALIDATION ISSUES ({len(validation_issues)})")
            print(sep_thin)
            for issue in validation_issues:
                print(f"  {issue}")

        pipeline_summary = _pseudocode_resolver.summary()

        print(f"\n{sep_thin}")
        print("  PSEUDOCODE PIPELINE")
        print(sep_thin)
        print(f"  Consolidated entries: {pipeline_summary.consolidated_total}")
        print(f"  Consolidated used:    {pipeline_summary.consolidated_used}")
        print(f"  Consolidated unused:  {pipeline_summary.consolidated_unused}")
        print(f"  Inline fallbacks:     {pipeline_summary.inline_used}")
        print(f"  Missing pseudocode:   {len(pipeline_summary.missing)}")
        print(f"  Empty pseudocode:     {len(pipeline_summary.empty)}")

        if pipeline_summary.missing:
            preview = pipeline_summary.preview(pipeline_summary.missing)
            print(f"  Missing cards:        {preview}")

        if pipeline_summary.empty:
            preview = pipeline_summary.preview(pipeline_summary.empty)
            print(f"  Empty-entry cards:    {preview}")

        if total_errors == 0:
            print("\n  All cards compiled and validated successfully!")
        print(sep_thick)

    # Write detailed log for reference (with full tracebacks)
    if errors or bc_errors or validation_issues:
        with open("compiler_errors.log", "w", encoding="utf-8") as f_err:
            if errors:
                f_err.write("=== CARD PARSE ERRORS ===\n")
                for err_msg in errors:
                    f_err.write(f"{err_msg}\n\n")
            if bc_errors:
                f_err.write("=== BYTECODE COMPILE ERRORS ===\n")
                for err_msg in bc_errors:
                    f_err.write(f"{err_msg}\n\n")
            if validation_issues:
                f_err.write("=== BYTECODE VALIDATION ISSUES ===\n")
                for issue in validation_issues:
                    f_err.write(f"{issue}\n")
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


from compiler.parser_v2 import AbilityParserV2

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


# Initialize parser globally
_v2_parser = AbilityParserV2()

# Module-level error collector for bytecode compilation errors in parse_member/parse_live
_bytecode_compile_errors: list[str] = []

# Global compilation version gate (can be overridden per compilation run)
_COMPILATION_VERSION_GATE: VersionGate = VersionGate(
    bytecode_version=BYTECODE_LAYOUT_VERSION,
    semantic_version=SEMANTIC_FORM_VERSION
)


def _compile_abilities_for_export(abilities: list, card_no: str, scope: str, version_gate: VersionGate = None) -> None:
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
        try:
            # Only compile if bytecode is not already present (e.g. from sparse source)
            if not ab.bytecode:
                ab.bytecode = ab.compile()
        except Exception as e:
            import traceback

            tb_str = traceback.format_exc()
            _bytecode_compile_errors.append(f"[{scope}] {card_no} ab#{idx}: {e}\n{tb_str}")
            continue

        try:
            ab.build_semantic_form()
        except Exception as e:
            import traceback

            tb_str = traceback.format_exc()
            _bytecode_compile_errors.append(f"[{scope} SEMANTIC] {card_no} ab#{idx}: {e}\n{tb_str}")

# Load consolidated ability mappings
CONSOLIDATED_ABILITIES_PATH = "data/consolidated_abilities.json"
_pseudocode_resolver = PseudocodeResolver.from_file(CONSOLIDATED_ABILITIES_PATH)

# Load manual translations
MANUAL_TRANSLATIONS_EN_PATH = "data/manual_translations_en.json"
_manual_translations_en = {}
if os.path.exists(MANUAL_TRANSLATIONS_EN_PATH):
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

    def _log(self, message: str) -> None:
        if self._debug:
            print(message)

    @classmethod
    def _extract_card_ref(cls, card_ref: Any) -> tuple[str, int] | None:
        if isinstance(card_ref, dict):
            card_no = str(card_ref.get("card_no", "")).strip()
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

        return match.group("card_no").strip(), int(match.group("idx"))

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
            data = ability_codec.load_data(self.yaml_path)
            if not data:
                self.mapping = {}
                self._last_loaded_mtime = current_mtime
                return

            next_mapping = {}
            abilities_list = data.get("abilities", [])
            self._log(f"SparseSourceManager.load() found {len(abilities_list)} abilities in YAML")

            for entry in abilities_list:
                trigger_id = int(entry.get("trigger_id", 0))
                frames = entry.get("frames", [])
                cards_list = entry.get("cards", [])
                for card_ref in cards_list:
                    extracted = self._extract_card_ref(card_ref)
                    if extracted is None:
                        continue
                    card_no, ab_idx = extracted
                    next_mapping[(card_no, ab_idx)] = {
                        "trigger_id": trigger_id,
                        "frames": frames,
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
        return self.mapping.get((card_no.strip(), ab_idx))


# Global sparse manager — JSON is the canonical format
SPARSE_INDEX_PATH = "data/ability_frame_index.json"
_sparse_manager = SparseSourceManager(SPARSE_INDEX_PATH)


def _build_ability_from_sparse_entry(entry: dict[str, Any], raw_text: str) -> Ability:
    trigger_id = int(entry.get("trigger_id", 0))
    frames = entry.get("frames", []) or []
    # Rebuild bytecode from frames (canonical). Fall back to source_words only if
    # frames are absent (migration-only shim — safe to remove once suite is green).
    bytecode = ability_codec.model_to_bytecode({"frames": frames})
    if not bytecode:
        source_words = [int(word) for word in entry.get("source_words", []) or []]
        bytecode = source_words

    ability = Ability(
        raw_text=raw_text,
        trigger=TriggerType(trigger_id),
        effects=[],
        conditions=[],
        costs=[],
        pseudocode="[RECONSTRUCTED FROM SPARSE INDEX]",
        bytecode=bytecode,
    )
    try:
        ability.build_semantic_form()
    except Exception:
        pass
    return ability


def _resolve_abilities(card_kind: str, card_no: str, data: dict) -> list[Ability]:
    raw_text = str(data.get("ability", ""))
    abilities: list[Ability] = []
    used_sparse = False

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

    raw_ability = _pseudocode_resolver.resolve(card_kind, card_no, data, _bytecode_compile_errors)
    if not raw_ability:
        return []

    print(f"[{card_no}] Loaded from pseudocode source")
    return _v2_parser.parse(raw_ability)


def compute_flags(card):
    """Replicates Rust flag calculation logic in the Python compiler."""

    ability_flags = 0
    semantic_flags = 0
    synergy_flags = 0
    cost_flags = 0

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
        int(Opcode.DRAW),
        int(Opcode.RECOVER_MEMBER),
        int(Opcode.RECOVER_LIVE),
        int(Opcode.ADD_BLADES),
        int(Opcode.ADD_HEARTS),
        int(Opcode.SEARCH_DECK),
        int(Opcode.BOOST_SCORE),
        int(Opcode.ENERGY_CHARGE),
        int(Opcode.MOVE_MEMBER),
        int(Opcode.SWAP_CARDS),
        int(Opcode.TAP_OPPONENT),
        int(Opcode.MODIFY_SCORE_RULE),
        int(Opcode.REDUCE_COST),
        int(Opcode.REDUCE_HEART_REQ),
        int(Opcode.RETURN),
        int(Opcode.LOOK_AND_CHOOSE),
        int(Opcode.TAP_MEMBER),
        int(Opcode.ACTIVATE_MEMBER),
        int(Opcode.SET_TAPPED),
        int(Opcode.TRANSFORM_COLOR),
        int(Opcode.NOP),
        int(Opcode.RETURN),
        int(Opcode.JUMP),
        int(Opcode.JUMP_IF_FALSE),
        int(Opcode.META_RULE),
        int(Opcode.SELECT_MODE),
        int(Opcode.COLOR_SELECT),
        int(Opcode.ORDER_DECK),
        int(Opcode.MOVE_TO_DECK),
        int(Opcode.MOVE_TO_DISCARD),
        int(Opcode.PLAY_MEMBER_FROM_HAND),
        int(Opcode.SET_TARGET_SELF),
        int(Opcode.SET_TARGET_OPPONENT),
    }

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

        # Bytecode loop for Ability & Choice Flags
        unflagged_logic = False
        for i in range(0, len(ab.bytecode), 5):
            op = ab.bytecode[i]
            if op in flagged_ops:
                ability_flags |= flagged_ops[op]

            if op not in core_ops and op < 100:  # Opcode < 100 are effect opcodes
                unflagged_logic = True

            # Choice Flags
            if op == int(Opcode.LOOK_AND_CHOOSE):
                ab.choice_flags |= CHOICE_FLAG_LOOK
                if ab.choice_count == 0:
                    v = ab.bytecode[i + 1] if i + 1 < len(ab.bytecode) else 3
                    # Extract the high byte (pick count) as the choice count
                    pick_count = (v >> 8) & 0xFF
                    if pick_count > 0:
                        ab.choice_count = pick_count
                    else:
                        effect_choice_count = 0
                        for eff in ab.effects:
                            if eff.runtime_opcode == int(Opcode.LOOK_AND_CHOOSE) or eff.effect_type == EffectType.LOOK_AND_CHOOSE:
                                raw_choice_count = eff.params.get("choose_count")
                                if raw_choice_count is None:
                                    continue
                                try:
                                    effect_choice_count = int(raw_choice_count)
                                except (TypeError, ValueError):
                                    effect_choice_count = 0
                                if effect_choice_count > 0:
                                    break
                        ab.choice_count = effect_choice_count if effect_choice_count > 0 else 3
            elif op == int(Opcode.SELECT_MODE):
                ab.choice_flags |= CHOICE_FLAG_MODE
                if ab.choice_count == 0:
                    ab.choice_count = ab.bytecode[i + 1] if i + 1 < len(ab.bytecode) else 2
            elif op == int(Opcode.COLOR_SELECT):
                ab.choice_flags |= CHOICE_FLAG_COLOR
                if ab.choice_count == 0:
                    # Try to get the actual choice count from the effect's params
                    choice_count_from_effect = None
                    color_select_effect_type = int(Opcode.COLOR_SELECT)
                    for eff in ab.effects:
                        if eff.effect_type == color_select_effect_type:
                            if "choices" in eff.params:
                                choice_count_from_effect = len(eff.params["choices"])
                            break
                    ab.choice_count = choice_count_from_effect if choice_count_from_effect else 6
            elif op == int(Opcode.ORDER_DECK):
                ab.choice_flags |= CHOICE_FLAG_ORDER
                if ab.choice_count == 0:
                    ab.choice_count = 3
                # Check if this ability also has a REMAINDER discard instruction
                for eff in ab.effects:
                    if eff.params.get("remainder") == "discard" or eff.params.get("destination") == "discard" or eff.params.get("raw_val") == "REMAINDER":
                        ab.choice_flags |= CHOICE_FLAG_DISCARD

        if unflagged_logic:
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
            # Debug output for PL!HS-bp2-020-L
            if parts_found:
                print(f"[DEBUG _extract] Found META_RULE ADD_TAG in ability #{ab_idx}: raw='{raw}', matched parts: {parts_found}")
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


def parse_member(card_id: int, card_no: str, data: dict) -> MemberCard:
    spec = data.get("special_heart", {})
    translation_en = _manual_translations_en.get(card_no)

    # --- Ability Source Resolution ---
    # Try sparse index first, fall back to pseudocode.
    abilities = _resolve_abilities("MEMBER", card_no, data)

    # --- GRANT_ABILITY FLATTENING ---
    extra_abilities = []
    for ab in abilities:
        for eff in ab.effects:
            if eff.effect_type == EffectType.GRANT_ABILITY:
                granted_text = None
                for key in ("granted_ability_text", "ability", "ABILITY"):
                    if key in eff.params:
                        granted_text = str(eff.params.pop(key))
                        break

                if granted_text:
                    inner_text = granted_text
                    for section_name in ("TRIGGER:", "COST:", "CONDITION:", "EFFECT:"):
                        inner_text = inner_text.replace(f", {section_name}", f"\n{section_name}")
                    granted_abs = _v2_parser.parse(inner_text)
                    if granted_abs:
                        start_idx = len(abilities) + len(extra_abilities)
                        eff.value = start_idx
                        if "target_str" in eff.params:
                            del eff.params["target_str"]
                        extra_abilities.extend(granted_abs)
    abilities.extend(extra_abilities)
    # --------------------------------

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

    _compile_abilities_for_export(card.abilities, card_no, "MEMBER")

    # Extract units from CONSTANT ADD_TAG effects and merge with existing units
    add_tag_units = _extract_units_from_add_tag(card.abilities)
    if add_tag_units:
        existing_units = set(card.units) if isinstance(card.units, list) else set()
        card.units = _normalize_unit_values(existing_units | add_tag_units)
    
    # Check consolidated_abilities for units metadata
    # If the original pseudocode entry has a "units" field, merge those units into card.units
    original_entry = _pseudocode_resolver.consolidated.get(card.original_text)
    if original_entry and isinstance(original_entry, dict) and "units" in original_entry:
        metadata_units = original_entry["units"]
        if metadata_units:
            # Map unit names (e.g., "CERISE_BOUQUET") to Unit enum values
            unit_name_map = {
                "CERISE_BOUQUET": Unit.CERISE_BOUQUET,
                "DOLLCHESTRA": Unit.DOLLCHESTRA,
                "MIRA_CRA_PARK": Unit.MIRA_CRA_PARK,
            }
            existing_units = set(card.units) if isinstance(card.units, list) else set()
            for unit_name in metadata_units:
                if unit_name in unit_name_map:
                    existing_units.add(unit_name_map[unit_name])
            card.units = _normalize_unit_values(existing_units)

    compute_flags(card)
    return card


def parse_live(card_id: int, card_no: str, data: dict) -> LiveCard:
    spec = data.get("special_heart", {})
    translation_en = _manual_translations_en.get(card_no)

    # --- Ability Source Resolution ---
    # Try sparse index first, fall back to pseudocode.
    abilities = _resolve_abilities("LIVE", card_no, data)

    # --- GRANT_ABILITY FLATTENING ---
    extra_abilities = []
    for ab in abilities:
        for eff in ab.effects:
            if eff.effect_type == EffectType.GRANT_ABILITY:
                if "granted_ability_text" in eff.params:
                    inner_text = str(eff.params.pop("granted_ability_text"))
                    granted_abs = _v2_parser.parse(inner_text)
                    if granted_abs:
                        start_idx = len(abilities) + len(extra_abilities)
                        eff.value = start_idx
                        if "target_str" in eff.params:
                            del eff.params["target_str"]
                        extra_abilities.extend(granted_abs)
    abilities.extend(extra_abilities)
    # --------------------------------
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

    _compile_abilities_for_export(card.abilities, card_no, "LIVE")

    # Extract units from CONSTANT ADD_TAG effects and merge with existing units
    add_tag_units = _extract_units_from_add_tag(card.abilities)
    if add_tag_units:
        existing_units = set(card.units) if isinstance(card.units, list) else set()
        card.units = _normalize_unit_values(existing_units | add_tag_units)
    
    # Check consolidated_abilities for units metadata
    # If the original pseudocode entry has a "units" field, merge those units into card.units
    original_entry = _pseudocode_resolver.consolidated.get(card.original_text)
    if original_entry and isinstance(original_entry, dict) and "units" in original_entry:
        metadata_units = original_entry["units"]
        if metadata_units:
            # Map unit names (e.g., "CERISE_BOUQUET") to Unit enum values
            unit_name_map = {
                "CERISE_BOUQUET": Unit.CERISE_BOUQUET,
                "DOLLCHESTRA": Unit.DOLLCHESTRA,
                "MIRA_CRA_PARK": Unit.MIRA_CRA_PARK,
            }
            existing_units = set(card.units) if isinstance(card.units, list) else set()
            for unit_name in metadata_units:
                if unit_name in unit_name_map:
                    existing_units.add(unit_name_map[unit_name])
            card.units = _normalize_unit_values(existing_units)

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


import hashlib


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

    # Check if meta contains the source hash
    stored_hash = compiled_data.get("meta", {}).get("source_hash")
    current_hash = calculate_hash(input_path)

    if stored_hash == current_hash:
        print("SUCCESS: Parity check passed. Compiled data is up to date.")
        return True
    else:
        print("WARNING: Parity check FAILED. Source file has changed since last compilation.")
        print(f"Stored:  {stored_hash}")
        print(f"Current: {current_hash}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compile raw card data to bytecode with optional version gating"
    )
    parser.add_argument("--input", default="data/cards.json", help="Path to raw cards.json")
    parser.add_argument("--output", default="data/cards_compiled.json", help="Output path")
    parser.add_argument(
        "--bytecode-version",
        type=int,
        default=BYTECODE_LAYOUT_VERSION,
        help=f"Bytecode layout version (default: {BYTECODE_LAYOUT_VERSION})"
    )
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

    # Set up version gate if non-default version requested
    if args.bytecode_version != BYTECODE_LAYOUT_VERSION:
        _COMPILATION_VERSION_GATE = VersionGate(
            bytecode_version=args.bytecode_version,
            semantic_version=SEMANTIC_FORM_VERSION
        )
        print(f"Using bytecode layout version {args.bytecode_version} "
              f"({_COMPILATION_VERSION_GATE.get_layout_name()})")

    if args.check:
        if check_parity(args.input, args.output):
            sys.exit(0)
        else:
            sys.exit(1)

    compile_cards(args.input, args.output, quiet=args.quiet, export_profile=args.export_profile)

    # Update hash in the output file
    if not args.quiet:
        print("Updating source hash in compiled file...")
    compiled_data = load_json(args.output)
    if compiled_data:
        if "meta" not in compiled_data:
            compiled_data["meta"] = {}
        compiled_data["meta"]["source_hash"] = calculate_hash(args.input)
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
