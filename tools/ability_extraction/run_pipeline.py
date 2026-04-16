#!/usr/bin/env python3
"""
Main pipeline script that runs ability extraction and semantic extraction in order.
"""

import subprocess
import sys
from pathlib import Path


def run_script(script_path: str, description: str) -> bool:
    """Run a Python script and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Script: {script_path}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr, file=sys.stderr)
        print(f"\n✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr, file=sys.stderr)
        return False


def main():
    print("=== Ability Extraction and Semantic Analysis Pipeline ===\n")
    
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Define the scripts to run in order
    scripts = [
        (script_dir / "extract_card_abilities.py", "Ability Extraction from Cards"),
        (script_dir / "extract_costs.py", "Cost Extraction from Abilities"),
        (script_dir / "pattern_based_semantic_extractor.py", "Pattern-based Semantic Extraction"),
        (script_dir / "integrate_semantic.py", "Semantic Integration"),
    ]
    
    # Run each script
    all_success = True
    for script_path, description in scripts:
        if not run_script(str(script_path), description):
            all_success = False
            print(f"\n⚠ Pipeline stopped due to failure in {description}")
            break
    
    if all_success:
        print(f"\n{'='*60}")
        print("✓ Pipeline completed successfully!")
        print(f"{'='*60}\n")
        print("Output files:")
        print("  - data/abilities_extracted_from_cards.json (with integrated semantics)")
        print("  - data/pattern_based_semantic_abilities.json")
        sys.exit(0)
    else:
        print(f"\n{'='*60}")
        print("✗ Pipeline failed")
        print(f"{'='*60}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
