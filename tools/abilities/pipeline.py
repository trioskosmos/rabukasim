"""Minimal ability pipeline - compile runtime card data and mirror live copies."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from engine.compiler import runtime_cards as compiler_runtime
from tools import frame_codec
from tools.sync_launcher_assets import sync_assets

CARDS_INPUT_PATH = ROOT_DIR / "data" / "cards.json"
CARDS_OUTPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
FRAME_SOURCE_PATH = ROOT_DIR / "data" / "ability_frame_source.json"
FRAME_RUNTIME_PATH = ROOT_DIR / "data" / "ability_runtime_index.json"
METADATA_PATH = ROOT_DIR / "data" / "metadata.json"


@dataclass(slots=True)
class PrepareResult:
    cards_changed: bool = False
    frame_index_changed: bool = False
    launcher_assets_changed: bool = False


def _log(message: str, quiet: bool) -> None:
    if not quiet:
        print(f"[build] {message}")


def prepare_cards(*, force: bool = False, quiet: bool = False) -> bool:
    """Compile cards."""
    _log("Compiling cards from authored sources", quiet)
    try:
        return compiler_runtime.compile_cards(
            str(CARDS_INPUT_PATH),
            str(CARDS_OUTPUT_PATH),
            quiet=quiet,
            export_profile="runtime",
        )
    except Exception as e:
        _log(f"Compilation error: {e}", quiet)
        return False


def prepare_frame_index(*, quiet: bool = False) -> bool:
    """Refresh authored source and runtime index."""
    _log("Refreshing authored source and runtime index", quiet)
    payload = frame_codec.load_authored_payload(FRAME_SOURCE_PATH)
    metadata = frame_codec.load_json(METADATA_PATH)
    card_db = None
    if CARDS_OUTPUT_PATH.exists():
        card_db = frame_codec.load_json(CARDS_OUTPUT_PATH)
    source_payload = frame_codec.strip_duplicate_instruction_entries(
        frame_codec.build_compact_ability_index(payload, metadata, card_db)
    )
    runtime_payload = frame_codec.strip_duplicate_instruction_entries(
        frame_codec.build_runtime_ability_index(source_payload, metadata, card_db)
    )

    changed = False
    for path, next_payload in (
        (FRAME_SOURCE_PATH, source_payload),
        (FRAME_RUNTIME_PATH, runtime_payload),
    ):
        current_payload = frame_codec.load_authored_payload(path) if path.exists() else None
        if current_payload != next_payload:
            frame_codec.dump_json(path, next_payload)
            changed = True
        encoded = path.read_text(encoding="utf-8")
        if not encoded.endswith("\n"):
            path.write_text(encoded + "\n", encoding="utf-8")
            changed = True
    return changed


def prepare_server_assets(*, quiet: bool = False) -> bool:
    """Sync launcher/runtime assets from the freshly compiled root data."""
    return sync_assets(quiet=quiet)


def prepare_runtime(
    *,
    force: bool = False,
    quiet: bool = False,
    sync_assets: bool = False,
) -> PrepareResult:
    """Main entry point for the build pipeline."""
    result = PrepareResult()
    result.cards_changed = prepare_cards(force=force, quiet=quiet)
    result.frame_index_changed = prepare_frame_index(quiet=quiet)
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
