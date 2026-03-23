from __future__ import annotations

"""Sync the runtime ability frame index from authored ability frame data."""

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
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the runtime ability frame index from authored frame data")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Authored ability frame JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Runtime ability frame index JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = codec.load_json(args.input)
    metadata = codec.load_json(args.metadata)
    runtime_payload = codec.build_runtime_ability_index(payload, metadata)
    codec.dump_json(args.output, runtime_payload)
    print(f"Wrote runtime ability frame index to {args.output}")
    print(f"Unique abilities: {runtime_payload.get('summary', {}).get('unique_ability_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
