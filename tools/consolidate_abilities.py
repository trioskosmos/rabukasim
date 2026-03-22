from __future__ import annotations

"""Generate a unique-ability index grouped by bytecode signature.

This is a companion to the bytecode codec. It takes compiled cards, groups
abilities by stable trigger + bytecode signature, and writes a JSON index that
lists every card using each unique ability.
"""

import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = os.path.abspath(str(ROOT_DIR))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from tools import bytecode_codec as codec

DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "cards_compiled.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a unique ability index from compiled cards")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Compiled card JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output JSON path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    compiled_data = codec.load_json(args.input)
    metadata = codec.load_json(args.metadata)
    payload = codec.build_sparse_ability_index(compiled_data, metadata)
    codec.dump_json(args.output, payload)
    print(f"Wrote sparse ability index to {args.output}")
    print(f"Unique abilities: {payload['summary']['unique_ability_count']}")
    print(f"Abilities processed: {payload['summary']['ability_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
