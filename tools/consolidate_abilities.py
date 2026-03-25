from __future__ import annotations

"""Generate consolidated ability JSON from authored frame data.

This script now keeps its JSON output away from `data/ability_frames.json`
so the authored source file is never overwritten by a generator.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = os.path.abspath(str(ROOT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from tools import frame_codec as codec

DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "ability_frames.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "consolidated_abilities.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build or normalize consolidated ability JSON")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Authored frame JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compiled_data = codec.load_json(args.input)
    metadata = codec.load_json(args.metadata)
    payload = codec.build_compact_ability_index(compiled_data, metadata)
    codec.dump_json(args.output, payload)
    print(f"Wrote consolidated ability JSON to {args.output}")
    print(f"Unique abilities: {payload['summary']['unique_ability_count']}")
    print(f"Abilities processed: {payload['summary']['ability_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
