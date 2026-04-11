"""Minimal ability pipeline - compile runtime card data and mirror live copies."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from engine.compiler import runtime_cards as compiler_runtime
from tools.sync_launcher_assets import sync_assets

CARDS_INPUT_PATH = ROOT_DIR / "data" / "cards.json"
CARDS_OUTPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
FRAME_SOURCE_PATH = ROOT_DIR / "data" / "ability_frame_source.json"
SEMANTIC_DUMP_PATH = ROOT_DIR / "data" / "ability_semantic_dump.json"


@dataclass(slots=True)
class PrepareResult:
    cards_changed: bool = False
    launcher_assets_changed: bool = False


def _log(message: str, quiet: bool) -> None:
    if not quiet:
        print(f"[build] {message}")


def _resolve_ability_source_path(
    ability_source_mode: str = "frame",
    ability_source_path: str | None = None,
) -> Path:
    if ability_source_path:
        return Path(ability_source_path)
    if ability_source_mode == "semantic":
        return SEMANTIC_DUMP_PATH
    return FRAME_SOURCE_PATH


def prepare_cards(
    *,
    quiet: bool = False,
    ability_source_mode: str = "frame",
    ability_source_path: str | None = None,
) -> bool:
    """Compile cards."""
    resolved_source_path = _resolve_ability_source_path(ability_source_mode, ability_source_path)
    _log(f"Compiling cards from authored sources ({resolved_source_path.name})", quiet)
    try:
        return compiler_runtime.compile_cards(
            str(CARDS_INPUT_PATH),
            str(CARDS_OUTPUT_PATH),
            quiet=quiet,
            export_profile="runtime",
            ability_source_path=str(resolved_source_path),
        )
    except Exception as e:
        _log(f"Compilation error: {e}", quiet)
        return False


def prepare_server_assets(*, quiet: bool = False) -> bool:
    """Sync launcher/runtime assets from the freshly compiled root data."""
    return sync_assets(quiet=quiet)


def prepare_runtime(
    *,
    quiet: bool = False,
    sync_assets: bool = False,
    ability_source_mode: str = "frame",
    ability_source_path: str | None = None,
) -> PrepareResult:
    """Main entry point for the build pipeline."""
    result = PrepareResult()
    result.cards_changed = prepare_cards(
        quiet=quiet,
        ability_source_mode=ability_source_mode,
        ability_source_path=ability_source_path,
    )
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
