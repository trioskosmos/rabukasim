import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.compiler.main import SparseSourceManager
from tools.abilities.pipeline import prepare_runtime


class AbilitySourceModeTests(unittest.TestCase):
    def test_semantic_dump_loads_through_sparse_manager(self) -> None:
        dump_path = Path(project_root) / "data" / "ability_semantic_dump.json"
        payload = json.loads(dump_path.read_text(encoding="utf-8"))

        target_entry = None
        target_ref = None
        for entry in payload.get("abilities", []):
            semantic_form = entry.get("semantic_form", {})
            if not isinstance(semantic_form, dict):
                continue
            if not semantic_form.get("operations"):
                continue
            card_refs = entry.get("card_refs", [])
            if not card_refs:
                continue
            target_entry = entry
            target_ref = card_refs[0]
            break

        self.assertIsNotNone(target_entry)
        self.assertIsNotNone(target_ref)

        card_no = str(target_ref["card_no"])
        ability_index = int(target_ref["ability_index"])
        manager = SparseSourceManager(str(dump_path))
        loaded = manager.get_ability(card_no, ability_index)

        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertTrue(loaded["frames"])
        self.assertEqual(loaded["raw_text"], target_entry["primary_text_jp"])
        self.assertEqual(loaded["semantic_form"]["schema"], "ability_semantic_form.v1")

    def test_prepare_runtime_passes_selected_source_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            calls: list[tuple] = []

            def fake_compile_cards(*args, **kwargs):
                calls.append((args, kwargs))
                output_path = Path(kwargs.get("output_path", "") or "data/cards_compiled.json")
                output_path = Path(tmpdir) / "cards_compiled.json"
                output_path.write_text(
                    json.dumps({"member_db": {}, "live_db": {}, "energy_db": {}}),
                    encoding="utf-8",
                )
                return True

            with patch("tools.abilities.pipeline.compiler_runtime.compile_cards", side_effect=fake_compile_cards):
                prepare_runtime(quiet=True, ability_source_mode="semantic")

            self.assertTrue(calls)
            _, kwargs = calls[0]
            self.assertIn("ability_source_path", kwargs)
            self.assertTrue(str(kwargs["ability_source_path"]).endswith("ability_semantic_dump.json"))


if __name__ == "__main__":
    unittest.main()
