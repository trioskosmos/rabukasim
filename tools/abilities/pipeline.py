"""Minimal ability pipeline - compile runtime card data and mirror live copies."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
import json

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from engine.compiler import runtime_cards as compiler_runtime
from tools import frame_codec
from tools.sync_launcher_assets import sync_assets

CARDS_INPUT_PATH = ROOT_DIR / "data" / "cards.json"
CARDS_OUTPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
FRAME_SOURCE_PATH = ROOT_DIR / "data" / "ability_frame_index.yaml"
FRAME_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"
ENGINE_FRAME_OUTPUT_PATH = ROOT_DIR / "engine" / "data" / "ability_frame_index.json"
METADATA_PATH = ROOT_DIR / "data" / "metadata.json"


@dataclass(slots=True)
class PrepareResult:
    cards_changed: bool = False
    frame_index_changed: bool = False
    rust_codegen_changed: bool = False
    launcher_assets_changed: bool = False


def _log(message: str, quiet: bool) -> None:
    if not quiet:
        print(f"[build] {message}")


def _cards_are_current() -> bool:
    """Check if compiled cards are up to date."""
    if not CARDS_OUTPUT_PATH.exists():
        return False
    compiled_data = compiler_runtime.load_json(str(CARDS_OUTPUT_PATH))
    if not compiled_data:
        return False
    return True


def prepare_cards(*, force: bool = False, quiet: bool = False) -> bool:
    """Compile cards."""
    # Always compile to ensure fresh data with current compiler
    _log("Compiling cards from authored sources", quiet)
    try:
        compiler_runtime.compile_cards(
            str(CARDS_INPUT_PATH),
            str(CARDS_OUTPUT_PATH),
            quiet=quiet,
            export_profile="runtime",
        )
        return True
    except Exception as e:
        _log(f"Compilation error: {e}", quiet)
        return False


def prepare_frame_index(*, quiet: bool = False) -> bool:
    """Regenerate the derived frame index from the authored YAML source."""
    _log("Rebuilding derived ability frame index", quiet)
    payload = frame_codec.load_authored_payload(FRAME_SOURCE_PATH)
    metadata = frame_codec.load_json(METADATA_PATH)
    runtime_index = frame_codec.build_runtime_ability_index(payload, metadata)
    encoded = json.dumps(runtime_index, indent=2, ensure_ascii=False)

    changed = True
    if FRAME_OUTPUT_PATH.exists():
        changed = FRAME_OUTPUT_PATH.read_text(encoding="utf-8") != encoded

    FRAME_OUTPUT_PATH.write_text(encoded, encoding="utf-8")
    ENGINE_FRAME_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENGINE_FRAME_OUTPUT_PATH.write_text(encoded, encoding="utf-8")
    return changed


def prepare_rust_codegen(*, quiet: bool = False) -> bool:
    """Generate Rust code - simplified, no-op for now."""
    _log("Rust codegen skipped (simplified pipeline)", quiet)
    return False


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
    result.rust_codegen_changed = prepare_rust_codegen(quiet=quiet)
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
