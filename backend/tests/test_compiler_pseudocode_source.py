import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.compiler import main as compiler_main


ROOT = Path(project_root)


class CompilerPseudocodeSourceTests(unittest.TestCase):
    def test_pseudocode_counts_as_ability_source(self) -> None:
        self.assertTrue(compiler_main._card_has_ability_source({"pseudocode": "TRIGGER: ON_PLAY; EFFECT: DRAW(1)"}))


if __name__ == "__main__":
    unittest.main()