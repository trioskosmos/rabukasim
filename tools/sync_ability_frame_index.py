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

import hashlib

def calculate_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

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
    
    # --- Parity Check ---
    hash_file = ROOT_DIR / "data" / ".ability_frame_sync_hash"
    h1 = calculate_hash(args.input)
    h2 = calculate_hash(args.metadata)
    current_hash = f"{h1}|{h2}"
    
    if hash_file.exists() and args.output.exists():
        with open(hash_file, "r") as f:
            stored_hash = f.read().strip()
        if stored_hash == current_hash:
            print("Ability frame index is up to date (O(1) match). Skipping sync.")
            return 0

    payload = codec.load_json(args.input)
    metadata = codec.load_json(args.metadata)
    runtime_payload = codec.build_runtime_ability_index(payload, metadata)
    codec.dump_json(args.output, runtime_payload)
    print(f"Wrote runtime ability frame index to {args.output}")
    print(f"Unique abilities: {runtime_payload.get('summary', {}).get('unique_ability_count', 0)}")
    
    # Save hash for parity
    try:
        with open(hash_file, "w") as f:
            f.write(current_hash)
    except Exception as e:
        print(f"Warning: Could not save parity hash: {e}")
        
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
