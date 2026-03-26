"""
test_debug.py - Frame-based engine debug test runner.

Runs cargo test against the Rust engine, targeting the qa_verification_tests
integration suite and any src-level frame tests. Uses --lib and --test flags
so we exercise AbilityFrame / FrameProgram execution paths, NOT raw bytecode.

Usage:
    uv run python tools/debug/scripts/test_debug.py
    uv run python tools/debug/scripts/test_debug.py --filter test_q103
    uv run python tools/debug/scripts/test_debug.py --nocapture
"""

import subprocess
import sys
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINE_DIR = REPO_ROOT / "engine_rust_src"


def run_cargo_test(filter_: str | None, nocapture: bool) -> int:
    cmd = ["cargo", "test"]

    if filter_:
        cmd.append(filter_)

    cmd += ["--"]
    if nocapture:
        cmd.append("--nocapture")

    print(f"[test_debug] cwd={ENGINE_DIR}")
    print(f"[test_debug] cmd={' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=str(ENGINE_DIR))
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Frame-based engine debug test runner")
    parser.add_argument(
        "--filter",
        default=None,
        help="Optional cargo test name filter (e.g. 'test_q103', 'frame', 'qa_verification')",
    )
    parser.add_argument(
        "--nocapture",
        action="store_true",
        help="Pass --nocapture to cargo test for verbose output",
    )
    args = parser.parse_args()

    rc = run_cargo_test(args.filter, args.nocapture)
    if rc != 0:
        print(f"\n[test_debug] FAILED (exit code {rc})")
        sys.exit(rc)
    else:
        print("\n[test_debug] All tests passed.")


if __name__ == "__main__":
    main()
