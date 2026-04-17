"""Compatibility wrapper for the legacy ability build pipeline.

The current build entrypoint still expects ``tools.abilities.pipeline`` to
expose a ``prepare_runtime`` function and a ``compiler_runtime`` namespace with
``compile_cards``.  This module restores that contract while delegating the
actual compilation work to ``engine.compiler.main``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from engine.compiler import main as compiler_runtime

from ..sync_launcher_assets import sync_assets as sync_launcher_assets


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
CARDS_PATH = DATA_DIR / "cards.json"
FRAME_SOURCE_PATH = DATA_DIR / "ability_frame_source.json"
SEMANTIC_DUMP_PATH = DATA_DIR / "ability_semantic_dump.json"
COMPILED_OUTPUT_PATH = DATA_DIR / "cards_compiled.json"


@dataclass(frozen=True)
class BuildResult:
    """Summary of a runtime build invocation."""

    cards_changed: bool
    launcher_assets_changed: bool


def _resolve_ability_source_path(
    ability_source_mode: str,
    ability_source_path: str | None,
) -> Path:
    if ability_source_path:
        return Path(ability_source_path)

    if ability_source_mode == "semantic":
        return SEMANTIC_DUMP_PATH

    return FRAME_SOURCE_PATH


def _compile_cards(*, quiet: bool, ability_source_path: Path) -> bool:
    return bool(
        compiler_runtime.compile_cards(
            input_path=str(CARDS_PATH),
            output_path=str(COMPILED_OUTPUT_PATH),
            quiet=quiet,
            export_profile="runtime",
            ability_source_path=str(ability_source_path),
        )
    )


def prepare_runtime(
    *,
    quiet: bool = False,
    sync_assets: bool = False,
    ability_source_mode: str = "frame",
    ability_source_path: str | None = None,
) -> BuildResult:
    """Compile runtime card data and optionally mirror launcher assets."""
    resolved_source = _resolve_ability_source_path(ability_source_mode, ability_source_path)

    cards_changed = _compile_cards(quiet=quiet, ability_source_path=resolved_source)
    launcher_assets_changed = False
    if sync_assets:
        launcher_assets_changed = bool(sync_launcher_assets(quiet=quiet))

    return BuildResult(
        cards_changed=cards_changed,
        launcher_assets_changed=launcher_assets_changed,
    )
