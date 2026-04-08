import os
import sys
import unittest
from pathlib import Path

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from tools.frame_codec import load_json
from tools.unique_ability_parser import load_unique_ability_report


ROOT = Path(project_root)


class UniqueAbilityParserTests(unittest.TestCase):
    def test_parser_finds_real_optional_and_choice_patterns(self) -> None:
        report = load_unique_ability_report(ROOT / "data" / "ability_frame_source.json")

        summary = report.summary()
        self.assertEqual(summary["unique_ability_count"], 544)
        self.assertEqual(summary["source_entry_count"], summary["unique_ability_count"])
        self.assertTrue(any(ability.has_optional_text for ability in report.abilities))
        self.assertTrue(any(ability.has_choice_text for ability in report.abilities))
        self.assertGreater(summary["optional_mismatch_count"], 0)

    def test_parser_uses_real_ability_text_entries(self) -> None:
        payload = load_json(ROOT / "data" / "ability_frame_source.json")
        abilities = payload.get("abilities", [])

        sample = next(
            entry
            for entry in abilities
            if isinstance(entry, dict) and "primary_text_jp" in entry and "もよい" in str(entry.get("primary_text_jp", ""))
        )

        report = load_unique_ability_report(ROOT / "data" / "ability_frame_source.json")
        parsed = next(
            ability
            for ability in report.abilities
            if ability.signature == sample.get("signature", "")
        )

        self.assertTrue(parsed.has_optional_text)
        self.assertTrue(parsed.clauses)
        self.assertTrue(any(clause.optional for clause in parsed.clauses))

    def test_parser_flags_missing_optional_frame_marker(self) -> None:
        report = load_unique_ability_report(ROOT / "data" / "ability_frame_source.json")
        self.assertTrue(any("optional_text_frame_mismatch" in issue for issue in report.issues))


if __name__ == "__main__":
    unittest.main()