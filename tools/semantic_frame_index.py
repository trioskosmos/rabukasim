from __future__ import annotations

"""Build the runtime semantic ability index from authored ability frames."""

import hashlib
import json
import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = os.path.abspath(str(ROOT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from tools import frame_codec as codec

DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "ability_frames.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"
def build_semantic_ability_index(payload: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    index = codec.build_runtime_ability_index(payload, metadata)
    index["schema"] = "ability_frame_index.semantic.v1"
    return index


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the semantic ability index from authored frame data")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Authored ability frame JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compiled_data = codec.load_json(args.input)
    metadata = codec.load_json(args.metadata)
    payload = build_semantic_ability_index(compiled_data, metadata)
    codec.dump_json(args.output, payload)
    print(f"Wrote semantic ability index to {args.output}")
    print(f"Unique abilities: {payload['summary']['unique_ability_count']}")
    print(f"Abilities processed: {payload['summary']['ability_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
