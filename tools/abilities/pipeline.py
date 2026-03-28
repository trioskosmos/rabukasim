"""Minimal ability pipeline - just runs the compiler."""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from engine.compiler import main as compiler_main

CARDS_INPUT_PATH = ROOT_DIR / "data" / "cards.json"
CARDS_OUTPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"


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
    compiled_data = compiler_main.load_json(str(CARDS_OUTPUT_PATH))
    if not compiled_data:
        return False
    return True


def prepare_cards(*, force: bool = False, quiet: bool = False) -> bool:
    """Compile cards."""
    # Always compile to ensure fresh data with current compiler
    _log("Compiling cards from authored sources", quiet)
    try:
        compiler_main.compile_cards(
            str(CARDS_INPUT_PATH),
            str(CARDS_OUTPUT_PATH),
            quiet=quiet,
            export_profile="runtime",
        )
        return True
    except Exception as e:
        _log(f"Compilation error: {e}", quiet)
        return False


def prepare_rust_codegen(*, quiet: bool = False) -> bool:
    """Generate Rust code - simplified, no-op for now."""
    _log("Rust codegen skipped (simplified pipeline)", quiet)
    return False


def prepare_server_assets(*, quiet: bool = False) -> bool:
    """Sync server assets - simplified, no-op for now."""
    return False


def prepare_runtime(
    *,
    force: bool = False,
    quiet: bool = False,
    sync_assets: bool = False,
) -> PrepareResult:
    """Main entry point for the build pipeline."""
    result = PrepareResult()
    result.cards_changed = prepare_cards(force=force, quiet=quiet)
    result.frame_index_changed = False  # Simplified - no separate frame index
    result.rust_codegen_changed = prepare_rust_codegen(quiet=quiet)
    if sync_assets:
        result.launcher_assets_changed = prepare_server_assets(quiet=quiet)
    return result
