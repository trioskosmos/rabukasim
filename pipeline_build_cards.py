"""Pipeline script: extract abilities, convert to frames, build cards."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]

def run_command(cmd, cwd=None):
    """Run a command and return success status."""
    print(f"\n{'='*80}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*80}")
    result = subprocess.run(cmd, cwd=cwd or ROOT)
    if result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        return False
    print("SUCCESS")
    return True

def main():
    """Run the full pipeline."""
    print("Starting card build pipeline...")
    
    # Step 1: Extract abilities from cards.json
    print("\n" + "="*80)
    print("STEP 1: Extract abilities from cards.json")
    print("="*80)
    if not run_command([sys.executable, "tools/ability_extraction/extract_card_abilities.py"]):
        print("ERROR: Ability extraction failed")
        return 1
    
    # Step 2: Convert abilities to frame format
    print("\n" + "="*80)
    print("STEP 2: Convert abilities to frame format")
    print("="*80)
    if not run_command([sys.executable, "tools/semantic_to_frame_converter.py"]):
        print("ERROR: Frame conversion failed")
        return 1
    
    # Step 3: Build cards
    print("\n" + "="*80)
    print("STEP 3: Build cards")
    print("="*80)
    if not run_command([sys.executable, "tools/build_cards.py"]):
        print("ERROR: Card build failed")
        return 1
    
    print("\n" + "="*80)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("="*80)
    return 0

if __name__ == "__main__":
    sys.exit(main())
