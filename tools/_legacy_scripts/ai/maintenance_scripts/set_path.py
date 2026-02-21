import os
import sys


def setup_paths():
    """Add project root to sys.path to ensure imports work correctly."""
    # Assume this file is in <root>/ai/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)


if __name__ == "__main__":
    setup_paths()
    print(f"Added {sys.path[0]} to sys.path")
