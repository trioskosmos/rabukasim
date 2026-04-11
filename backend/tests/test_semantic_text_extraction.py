import os
import sys
import unittest

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

from engine.compiler.semantic_processor import (
    abstract_authored_text,
    extract_semantic_form_from_text,
    populate_semantic_from_text,
    tokenize_authored_text,
)
from engine.models.ability import Ability
from engine.models.generated_enums import TriggerType


class SemanticTextExtractionTests(unittest.TestCase):
    def test_extracts_meaningful_clauses_from_japanese_text(self) -> None:
        text = (
            "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい："
            "自分のデッキの上からカードを7枚見る。"
            "その中から{{heart_02.png|heart02}}か{{heart_04.png|heart04}}か{{heart_05.png|heart05}}を持つ"
            "メンバーカードを3枚まで公開して手札に加えてもよい。"
            "残りを控え室に置く。"
        )

        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["schema"], "ability_semantic_form.v1")
        self.assertEqual(report["trigger_markers"], ["登場"])
        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(
            [operation["kind"] for operation in report["operations"]],
            ["cost", "look", "selection", "cleanup"],
        )
        selection = report["operations"][2]
        self.assertEqual(selection["notes"]["heart_colors"], [2, 4, 5])
        self.assertIn("choose_up_to=3", selection["code"])

    def test_reports_unmatched_clauses_explicitly(self) -> None:
        report = extract_semantic_form_from_text("自分のデッキの上からカードを7枚見る。謎の処理をする。")

        self.assertEqual(report["coverage"]["clause_count"], 2)
        self.assertEqual(report["coverage"]["matched_clause_count"], 1)
        self.assertEqual(report["coverage"]["unmatched_clause_count"], 1)
        self.assertEqual(report["unmatched_clauses"][0]["text"], "謎の処理をする")

    def test_populate_semantic_from_text_attaches_report_to_ability(self) -> None:
        ability = Ability(
            raw_text="手札を1枚控え室に置いてもよい。自分のデッキの上からカードを7枚見る。",
            trigger=TriggerType.ON_PLAY,
            effects=[],
        )

        populate_semantic_from_text([ability])

        self.assertEqual(ability.semantic_form["coverage"]["clause_count"], 2)
        self.assertEqual(ability.semantic_form["operations"][0]["kind"], "cost")

    def test_tokenization_preserves_templates_and_abstracts_numbers(self) -> None:
        text = "{{toujyou.png|登場}}手札を1枚控え室に置いてもよい。"
        tokens = tokenize_authored_text(text)

        self.assertEqual(tokens[0]["kind"], "template")
        self.assertEqual(tokens[0]["label"], "登場")
        self.assertIn("raw", tokens[0])
        self.assertEqual(abstract_authored_text(text), "登場手札を<NUM>枚控え室に置いてもよい。")

    def test_extracts_draw_cards_pattern(self) -> None:
        text = "カードを1枚引き"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "draw(1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "DRAW")
        self.assertEqual(report["operations"][0]["runtime"]["value"], 1)

    def test_extracts_add_to_hand_pattern(self) -> None:
        text = "その中から1枚を手札に加え"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "add_to_hand(1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "ADD_TO_HAND")
        self.assertEqual(report["operations"][0]["runtime"]["value"], 1)

    def test_extracts_compound_draw_and_discard_pattern(self) -> None:
        text = "カードを1枚引き、手札を1枚控え室に置く"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "compound")
        self.assertEqual(report["operations"][0]["code"], "draw_and_discard(draw=1, discard=1)")
        self.assertEqual(len(report["operations"][0]["runtime"]["operations"]), 2)
        self.assertEqual(report["operations"][0]["runtime"]["operations"][0]["op"], "DRAW")
        self.assertEqual(report["operations"][0]["runtime"]["operations"][1]["op"], "MOVE_TO_DISCARD")

    def test_extracts_optional_discard_with_limit_pattern(self) -> None:
        text = "手札を3枚まで控え室に置いてもよい"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "cost")
        self.assertEqual(report["operations"][0]["code"], "optional_discard_limit(hand, up_to=3)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "MOVE_TO_DISCARD")
        self.assertEqual(report["operations"][0]["notes"]["is_limit"], True)

    def test_extracts_dynamic_draw_pattern(self) -> None:
        text = "これにより置いた枚数分カードを引く"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "draw_dynamic(discard_count)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "DRAW")
        self.assertEqual(report["operations"][0]["notes"]["dynamic"], True)

    def test_extracts_energy_payment_pattern(self) -> None:
        text = "EE支払ってもよい"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "cost")
        self.assertEqual(report["operations"][0]["code"], "pay_energy(2)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "PAY_ENERGY")
        self.assertEqual(report["operations"][0]["notes"]["energy_count"], 2)

    def test_extracts_deck_to_discard_pattern(self) -> None:
        text = "自分のデッキの上からカードを3枚控え室に置く"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "deck_top_to_discard(3)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "MOVE_TO_DISCARD")

    def test_extracts_gain_hearts_pattern(self) -> None:
        text = "ブレードを得る"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "add_blades(1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "ADD_BLADES")

    def test_extracts_stage_member_pattern(self) -> None:
        text = "ステージに登場させる"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "play_member_from_hand(1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "PLAY_MEMBER_FROM_HAND")

    def test_extracts_place_energy_pattern(self) -> None:
        text = "自分のエネルギーデッキから、エネルギーカードを1枚ウェイト状態で置く"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "place_energy(1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "PLACE_ENERGY_UNDER_MEMBER")

    def test_extracts_choice_pattern(self) -> None:
        text = "以下から1つを選ぶ"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "selection")
        self.assertEqual(report["operations"][0]["code"], "select_mode(1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "SELECT_MODE")

    def test_extracts_add_to_hand_remainder_pattern(self) -> None:
        text = "その中から1枚を手札に加え、残りを控え室に置く"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "add_to_hand(1, discard_remainder=true)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "ADD_TO_HAND")

    def test_extracts_target_opponent_wait_pattern(self) -> None:
        text = "相手のステージにいるコスト4以下のメンバー1人をウェイトにする"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "tap_opponent(cost<=4, count=1)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "TAP_MEMBER")

    def test_extracts_conditional_effect_pattern(self) -> None:
        text = "それらがすべてメンバーカードの場合、ライブ終了時まで、ブレードを得る"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "conditional")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "CONDITIONAL")
        self.assertIn("condition", report["operations"][0]["notes"])

    def test_extracts_duration_pattern(self) -> None:
        text = "ライブ終了時まで、ブレードを得る"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        # This is matched by the specific gain hearts with duration pattern
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "ADD_BLADES")
        self.assertEqual(report["operations"][0]["notes"]["duration"], "LIVE_END")

    def test_extracts_boost_score_pattern(self) -> None:
        text = "このライブのスコアを2上げる"
        report = extract_semantic_form_from_text(text)

        self.assertEqual(report["coverage"]["unmatched_clause_count"], 0)
        self.assertEqual(len(report["operations"]), 1)
        self.assertEqual(report["operations"][0]["kind"], "effect")
        self.assertEqual(report["operations"][0]["code"], "boost_score(2)")
        self.assertEqual(report["operations"][0]["runtime"]["op"], "BOOST_SCORE")


if __name__ == "__main__":
    unittest.main()
