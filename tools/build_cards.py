import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

try:
    from tools.abilities.pipeline import prepare_runtime
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare compiled card data and optionally sync the launcher/engine live mirrors"
    )
    parser.add_argument("--force", action="store_true", help="Force rebuild of compiled artifacts")
    parser.add_argument("--quiet", action="store_true", help="Reduce build output")
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

    result = prepare_runtime(
        force=args.force,
        quiet=args.quiet,
        sync_assets=args.sync_launcher_assets,
    )
    if args.quiet:
        return

    if result.cards_changed or result.frame_index_changed or result.rust_codegen_changed:
        print_status("Build complete.", is_done=True)
    else:
        print_status("Card and ability artifacts are up to date.", is_done=True)

if __name__ == "__main__":
    main()
