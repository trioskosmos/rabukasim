"""Tiny JSON/YAML helpers for authored and compiled ability data."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import yaml


def load_authored_payload(path: Path | str) -> dict[str, Any]:
    """Load the canonical authored ability source from JSON or legacy YAML."""
    path = Path(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return load_yaml(path)
    return load_json(path)


def load_yaml(path: Path | str) -> dict[str, Any]:
    """Load YAML file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8-sig") as f:
        return yaml.safe_load(f)


def load_json(path: Path | str) -> dict[str, Any]:
    """Load JSON file with UTF-8 encoding."""
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def dump_json(path: Path | str, payload: dict[str, Any]) -> None:
    """Write JSON file with UTF-8 encoding and pretty printing."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
