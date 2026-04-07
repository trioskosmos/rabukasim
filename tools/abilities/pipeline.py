"""Minimal ability pipeline - compile runtime card data and mirror live copies."""
from __future__ import annotations

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
METADATA_PATH = ROOT_DIR / "data" / "metadata.json"


@dataclass(slots=True)
class PrepareResult:
    cards_changed: bool = False
    ability_source_changed: bool = False
    launcher_assets_changed: bool = False


def _log(message: str, quiet: bool) -> None:
    if not quiet:
        print(f"[build] {message}")


def prepare_cards(*, quiet: bool = False) -> bool:
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


def prepare_ability_source(*, quiet: bool = False) -> bool:
    """Refresh the authored ability source."""
    _log("Refreshing authored ability source", quiet)
    payload = frame_codec.load_authored_payload(FRAME_SOURCE_PATH)
    metadata = frame_codec.load_json(METADATA_PATH)
    card_db = None
    if CARDS_OUTPUT_PATH.exists():
        card_db = frame_codec.load_json(CARDS_OUTPUT_PATH)
    normalized_payload = frame_codec.normalize_authored_ability_index(payload, metadata, card_db)
    source_payload = dict(normalized_payload)
    source_payload["schema"] = "ability_frame_source.flat.v2"
    source_payload["_comment"] = "Authored sparse ability source. Edit this file directly."

    changed = False
    current_payload = frame_codec.load_authored_payload(FRAME_SOURCE_PATH) if FRAME_SOURCE_PATH.exists() else None
    if current_payload != source_payload:
        frame_codec.dump_json(FRAME_SOURCE_PATH, source_payload)
        changed = True
    encoded = FRAME_SOURCE_PATH.read_text(encoding="utf-8")
    if not encoded.endswith("\n"):
        FRAME_SOURCE_PATH.write_text(encoded + "\n", encoding="utf-8")
        changed = True
    return changed


def prepare_server_assets(*, quiet: bool = False) -> bool:
    """Sync launcher/runtime assets from the freshly compiled root data."""
    return sync_assets(quiet=quiet)


def prepare_runtime(
    *,
    quiet: bool = False,
    sync_assets: bool = False,
) -> PrepareResult:
    """Main entry point for the build pipeline."""
    result = PrepareResult()
    result.cards_changed = prepare_cards(quiet=quiet)
    result.ability_source_changed = prepare_ability_source(quiet=quiet)
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
