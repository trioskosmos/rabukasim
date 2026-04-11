import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

try:
    from tools.abilities.pipeline import prepare_runtime
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def _compiled_output_is_populated(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return any(payload.get(section) for section in ("member_db", "live_db", "energy_db"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare compiled card data and optionally sync the launcher/engine live mirrors"
    )
    parser.add_argument("--quiet", action="store_true", help="Reduce build output")
    parser.add_argument(
        "--ability-source-mode",
        choices=["frame", "semantic"],
        default="frame",
        help="Choose the authored ability source used by the compiler",
    )
    parser.add_argument(
        "--ability-source-path",
        default=None,
        help="Override the authored ability source path directly",
    )
    parser.add_argument(
        "--sync-launcher-assets",
        action="store_true",
        help="Also sync launcher/frontend assets and mirror cards_compiled.json into live copies",
    )
    return parser.parse_args()

def print_status(message, is_done=False):
    """Prints an updating status line."""
    if is_done:
        print(f"\r[build] {message:<60}")
    else:
        sys.stdout.write(f"\r[build] {message}...")
        sys.stdout.flush()

def main():
    args = parse_args()

    output_path = ROOT_DIR / "data" / "cards_compiled.json"
    result = prepare_runtime(
        quiet=args.quiet,
        sync_assets=args.sync_launcher_assets,
        ability_source_mode=args.ability_source_mode,
        ability_source_path=args.ability_source_path,
    )

    if not _compiled_output_is_populated(output_path):
        print(f"Error: {output_path} was not populated by the compiler.")
        sys.exit(1)

    if args.quiet:
        return

    if result.cards_changed or result.launcher_assets_changed:
        print_status("Build complete.", is_done=True)
    else:
        print_status("Card artifacts are up to date.", is_done=True)

if __name__ == "__main__":
    main()
