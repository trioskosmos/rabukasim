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

from tools.abilities.pipeline import prepare_frame_index

DEFAULT_INPUT_PATH = ROOT_DIR / "data" / "ability_frames.json"
DEFAULT_METADATA_PATH = ROOT_DIR / "data" / "metadata.json"
DEFAULT_OUTPUT_PATH = ROOT_DIR / "data" / "ability_frame_index.json"
DEFAULT_CARDS_PATH = ROOT_DIR / "data" / "cards_compiled.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the runtime ability frame index from authored frame data")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH, help="Authored ability frame JSON")
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH, help="Metadata JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Runtime ability frame index JSON")
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS_PATH, help="Compiled card database JSON")
    parser.add_argument("--force", action="store_true", help="Force rebuilding the frame index")
    parser.add_argument("--quiet", action="store_true", help="Reduce build output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changed = prepare_frame_index(
        force=args.force,
        quiet=args.quiet,
        input_path=args.input,
        metadata_path=args.metadata,
        output_path=args.output,
        cards_path=args.cards,
    )
    if not args.quiet and not changed:
        print("Ability frame index is up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
