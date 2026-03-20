from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_PATH = os.path.abspath(str(ROOT_DIR))
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from tools.bytecode_codec import *  # noqa: F401,F403
from tools.bytecode_codec import main as _main


if __name__ == "__main__":
    raise SystemExit(_main())
