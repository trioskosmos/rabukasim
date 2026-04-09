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


@dataclass(slots=True)
class PrepareResult:
    cards_changed: bool = False
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
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
