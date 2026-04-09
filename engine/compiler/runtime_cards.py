"""Public runtime card compiler API.

This module is the supported import surface for generating
`data/cards_compiled.json`. The implementation still lives in `main.py`
today, but callers should depend on this module instead of importing the
CLI-oriented file directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .main import compile_cards


def _card_has_ability_source(data: dict[str, Any]) -> bool:
    return any(str(data.get(key, "")).strip() for key in ("ability", "original_text")) or bool(
        data.get("abilities")
    ) or bool(
        isinstance(data.get("frame_program"), dict)
        and data["frame_program"].get("frames")
    )


def load_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)

__all__ = ["compile_cards", "load_json", "_card_has_ability_source"]
