"""
FAQ Rule Extractor - Semantic analysis of FAQ Q&A text to extract testable rules.
Similar to AbilityParser, uses Japanese keyword patterns to identify rule types.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class FAQRule:
    """Structured rule extracted from FAQ answer."""

    faq_id: str
    rule_type: str  # refresh, replacement, restriction, cost, baton, etc.
    value: bool
    context: Dict[str, Any] = field(default_factory=dict)
    raw_question: str = ""
    raw_answer: str = ""


class FAQRuleExtractor:
    """Extract testable rules from FAQ Q&A text using semantic patterns."""

    # Pattern mappings: (regex or keyword, rule_type, value, context_extractor)
    ANSWER_PATTERNS = [
        # Refresh rules
        (r"リフレッシュは行いません", "refresh", False, None),
        (r"リフレッシュを行います", "refresh", True, None),
        # Replacement rules (member to discard)
        (r"控え室に置かれます", "replacement", True, None),
        (r"登場させることはできます", "can_play_to_slot", True, None),
        # Restriction rules
        (r"できません", "blocked", True, None),
        (r"バトンタッチはできません", "baton_blocked", True, None),
        (r"指定することはできません", "target_blocked", True, None),
        # Cost rules
        (r"支払いません", "cost_paid", False, None),
        (r"支払います", "cost_paid", True, None),
        # Affirmative rules
        (r"はい、できます", "allowed", True, None),
        (r"いいえ、できません", "allowed", False, None),
        # Turn restriction
        (r"登場したターン中は", "turn_restriction", True, None),
        (r"次のターン以降", "next_turn_ok", True, None),
    ]

    QUESTION_CONTEXT_PATTERNS = [
        # Deck/Look context
        (r"デッキ.*?(\d+)枚.*?見", "deck_look", lambda m: {"look_count": int(m.group(1))}),
        (r"メインデッキが(\d+)枚", "deck_size", lambda m: {"deck_size": int(m.group(1))}),
        # Slot/Area context
        (r"メンバーカードがあるエリア", "occupied_slot", lambda m: {"slot_occupied": True}),
        (r"このターンに登場しているメンバー", "played_this_turn", lambda m: {"played_this_turn": True}),
        # Baton touch context
        (r"バトンタッチ", "baton_touch", lambda m: {"involves_baton": True}),
        # Effect vs Normal play context
        (r"能力の効果で.*?登場", "effect_play", lambda m: {"via_effect": True}),
        (r"手札から登場させる場合と同様", "normal_play_comparison", lambda m: {"compare_to_normal": True}),
    ]

    @classmethod
    def extract_rules(cls, faq_id: str, question: str, answer: str) -> List[FAQRule]:
        """Extract all applicable rules from a single FAQ entry."""
        rules = []
        context = {}

        # Extract context from question
        for pattern, ctx_type, ctx_extractor in cls.QUESTION_CONTEXT_PATTERNS:
            match = re.search(pattern, question)
            if match:
                if ctx_extractor:
                    context.update(ctx_extractor(match))
                else:
                    context[ctx_type] = True

        # Extract rules from answer
        for pattern, rule_type, value, _ in cls.ANSWER_PATTERNS:
            if re.search(pattern, answer):
                rule = FAQRule(
                    faq_id=faq_id,
                    rule_type=rule_type,
                    value=value,
                    context=context.copy(),
                    raw_question=question[:100],  # Truncate for storage
                    raw_answer=answer[:100],
                )
                rules.append(rule)

        return rules

    @classmethod
    def extract_from_card_faqs(cls, card_data: dict) -> List[FAQRule]:
        """Extract rules from all FAQs of a card."""
        all_rules = []
        card_no = card_data.get("card_no", "UNKNOWN")

        for faq in card_data.get("faq", []):
            faq_id = f"{card_no}_{faq.get('title', 'FAQ')}"
            question = faq.get("question", "")
            answer = faq.get("answer", "")

            rules = cls.extract_rules(faq_id, question, answer)
            all_rules.extend(rules)

        return all_rules

    @classmethod
    def generate_test_data(cls, cards: dict) -> List[dict]:
        """Generate test data from all cards with FAQs."""
        test_data = []

        for card_id, card_data in cards.items():
            if card_data.get("faq"):
                rules = cls.extract_from_card_faqs(card_data)
                for rule in rules:
                    test_data.append(asdict(rule))

        return test_data


def main():
    """Run extractor on all cards and output extracted rules."""
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    with open("data/cards.json", encoding="utf-8") as f:
        cards = json.load(f)

    test_data = FAQRuleExtractor.generate_test_data(cards)

    # Output summary
    print(f"Extracted {len(test_data)} rules from FAQs")

    # Group by rule type
    by_type = {}
    for rule in test_data:
        rt = rule["rule_type"]
        by_type[rt] = by_type.get(rt, 0) + 1

    print("\nRule Type Distribution:")
    for rt, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {rt}: {count}")

    # Save to file
    with open("data/faq_rules_extracted.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    print("\nSaved extracted rules to data/faq_rules_extracted.json")


if __name__ == "__main__":
    main()
