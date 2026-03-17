"""
Master Ability Verification & Dashboard Tool (PR#4 Validation Variant)

Adapts the master validator to use:
- compiler.parser.AbilityParser
- engine.models.ability.*

Outputs report: docs/pr4_ability_report.md
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List

# Ensure we can import from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- CHANGED IMPORTS FOR PR #4 ---
from compiler.parser import AbilityParser
from engine.models.ability import Ability, ConditionType, EffectType

# ---------------------------------


class MasterValidator:
    def __init__(self, cards_path: str):
        self.cards_path = cards_path
        with open(cards_path, encoding="utf-8") as f:
            self.cards = json.load(f)

        self.stats = {
            "total_cards": len(self.cards),
            "with_abilities": 0,
            "parsed_ok": 0,
            "parse_failed": 0,
            "with_faq": 0,
            "semantic_gaps": 0,
            "heuristic_issues": 0,
        }

        self.effect_counts = Counter()
        self.trigger_counts = Counter()
        self.gap_counts = Counter()
        self.issue_counts = Counter()
        self.reports_by_card = {}
        self.passed_cards = set()

        # Load behavioral results
        if os.path.exists("tests/behavioral_results.json"):
            with open("tests/behavioral_results.json", encoding="utf-8") as f:
                res = json.load(f)
                self.passed_cards = set(res.get("passed_cards", []))

        # Complexity Tiers
        self.card_scores = self._load_tiers("docs/card_complexity_tiers.md")
        self.tier_stats = defaultdict(lambda: {"total": 0, "passed": 0})

    def _load_tiers(self, path: str) -> Dict[str, int]:
        scores = {}
        if not os.path.exists(path):
            return scores
        with open(path, encoding="utf-8") as f:
            for line in f:
                # Match ID and score in markdown table row
                match = re.search(r"\|\s*([^\|\s]+?)\s*\|\s*(\d+)\s*\|", line)
                if match:
                    scores[match.group(1).strip()] = int(match.group(2))
        return scores

    def _calculate_score(self, text: str, abilities: List[Ability], faq_count: int = 0) -> int:
        score = 0
        if not text:
            return 0

        # FAQ Complexity (New Factor)
        score += faq_count * 5

        # Base components
        for ab in abilities:
            score += 10  # Each ability block
            score += len(ab.effects) * 8
            score += len(ab.conditions) * 6
            score += len(ab.costs) * 5
            if ab.is_once_per_turn:
                score += 5
            if ab.modal_options:
                score += 15  # Select Mode

        # Keyword complexity
        keywords = {
            "選ぶ|選んだ": 12,  # Choice
            "見る": 8,  # Look
            "代わりに": 20,  # Replacement
            "枚につき|人につき": 15,  # Multiplier
            "相手": 10,  # Opponent interaction
            "控え室": 5,  # Discard interaction
            "エネルギー": 5,  # Energy interaction
            "デッキ|山札": 5,  # Deck interaction
            "シャッフル": 10,  # Randomness
            "ならない|できない": 15,  # Logic restrictions
            "。その後、": 10,  # Sequential effects
        }
        for pattern, points in keywords.items():
            if re.search(pattern, text):
                score += points

        return score

    def reconstruct_ability(self, ability: Ability) -> str:
        return ability.reconstruct_text()

    def find_semantic_gaps(self, text: str, reconstructed: str) -> List[str]:
        gaps = []
        # Pattern in Japanese text -> concept that should appear in reconstructed output -> label if missing
        checks = [
            ("引く|ドロー", "Draw", "drawing"),
            ("控え室", "discard", "discard interaction"),
            ("ハート", "Heart", "hearts"),
            ("ブレード", "Blade", "blades"),
            ("エネルギー|チャージ", "Energy", "energy"),
            ("デッキ|山札", "deck", "deck interaction"),
            ("相手", "opponent|TAP_OPPONENT|Opponent", "opponent interaction"),
            ("スコア", "score|Score", "score interaction"),
            ("ライブ", "live|Live", "live interaction"),
            ("公開", "Reveal", "reveal"),
            ("選ぶ|選択|以下から", "Choose|Pick|Select|Modal|MODE|Choice", "choice"),
        ]
        for pattern, concept_en, label in checks:
            if re.search(pattern, text) and not re.search(concept_en, reconstructed, re.IGNORECASE):
                gaps.append(f"Missing '{label}'")
        return gaps

    def validate_heuristics(self, card, abilities) -> List[str]:
        text = card.get("ability", "")
        issues = []

        # Collect all effects including those in modal options
        all_effects = []
        for a in abilities:
            all_effects.extend([e.effect_type for e in a.effects])
            for modal_opt in a.modal_options:
                all_effects.extend([e.effect_type for e in modal_opt])

        all_conditions = [c.type for a in abilities for c in a.conditions]

        if "引く" in text and EffectType.DRAW not in all_effects:
            issues.append("MISSING_DRAW")

        # Score check: either BOOST_SCORE, SET_SCORE, META_RULE, SCORE_COMPARE condition, or score filter
        # Score filters like "スコア3以下のライブカード" should not trigger MISSING_SCORE
        has_score_filter = bool(re.search(r"スコア\d+以[下上]の", text))
        if (
            "スコア" in text
            and not has_score_filter
            and (
                EffectType.BOOST_SCORE not in all_effects
                and EffectType.SET_SCORE not in all_effects
                and EffectType.META_RULE not in all_effects
                and ConditionType.SCORE_COMPARE not in all_conditions
            )
        ):
            issues.append("MISSING_SCORE")

        # Hearts check: only flag if "ハート" + "得る" exists AND no ADD_HEARTS effect AND no count condition
        # Also exclude cards where ハート is just referencing heart colors (e.g., heart_01.png)
        if "ハート" in text and "得る" in text:
            # Must actually gain hearts, not just a condition about them
            is_heart_condition_only = "ハートの総数" in text or re.search(r"ハート.*\d+個以上", text)
            if not is_heart_condition_only and EffectType.ADD_HEARTS not in all_effects:
                if ConditionType.COUNT_HEARTS not in all_conditions:
                    issues.append("MISSING_HEARTS")

        # Blades check: similar logic
        if "ブレード" in text and "得る" in text:
            # Check for condition patterns like "ブレードの数", "ブレード...以上", "ブレード...合計"
            # Use regex to handle {{icon_blade.png|ブレード}} formatting
            is_blade_condition_only = (
                bool(re.search(r"ブレード.*?の(?:総)?数", text))
                or bool(re.search(r"ブレード.*?合計", text))
                or bool(re.search(r"ブレード.*?\d+(つ|個)以上", text))
            )

            if not is_blade_condition_only and EffectType.ADD_BLADES not in all_effects:
                if ConditionType.COUNT_BLADES not in all_conditions:
                    issues.append("MISSING_BLADES")

        return issues

    def run(self):
        for card_no, card in self.cards.items():
            text = card.get("ability", "")
            faq = card.get("faq", [])

            if not text:
                continue

            self.stats["with_abilities"] += 1
            if faq:
                self.stats["with_faq"] += 1

            try:
                abilities = AbilityParser.parse_ability_text(text)
                self.stats["parsed_ok"] += 1

                # Tier stats (Prefer manual score if exists, else automated)
                score = self.card_scores.get(card_no)
                if score is None:
                    score = self._calculate_score(text, abilities, len(faq))

                # Store score for later statistical analysis (Tiering deferred)
                self.reports_by_card[card_no] = {
                    "name": card.get("name", "Unknown"),
                    "text": text,
                    "reports": [],  # Placeholder
                    "score": score,
                    "faq": faq,
                    # Other fields added below
                }

                reconstructions = [self.reconstruct_ability(ab) for ab in abilities]
                full_recon = " | ".join(reconstructions)

                # Update counts
                for ab in abilities:
                    self.trigger_counts[ab.trigger.name] += 1
                    for eff in ab.effects:
                        self.effect_counts[eff.effect_type.name] += 1

                # Analysis
                gaps = self.find_semantic_gaps(text, full_recon)
                issues = self.validate_heuristics(card, abilities)

                if gaps:
                    self.stats["semantic_gaps"] += 1
                    for g in gaps:
                        self.gap_counts[g] += 1
                if issues:
                    self.stats["heuristic_issues"] += 1
                    for iss in issues:
                        self.issue_counts[iss] += 1

                self.reports_by_card[card_no] = {
                    "name": card.get("name", "Unknown"),
                    "text": text,
                    "recon": full_recon,
                    "gaps": gaps,
                    "issues": issues,
                    "faq": faq,
                    "score": score,
                }

            except Exception as e:
                import traceback

                traceback.print_exc()
                self.stats["parse_failed"] += 1
                self.reports_by_card[card_no] = {
                    "name": card.get("name", "Unknown"),
                    "text": text,
                    "error": str(e),
                    "faq": faq,
                }

    def write_report(self, output_path: str):
        with open(output_path, "w", encoding="utf-8-sig") as f:
            f.write("# Master Ability Verification Dashboard (PR #4 Architecture)\n\n")

            # Calculate Statistics
            all_scores = []
            for cno, r in self.reports_by_card.items():
                if "score" in r:
                    all_scores.append(r["score"])
                elif "error" in r:
                    print(f"Warning: Card {cno} failed to parse: {r['error']}")

            if all_scores:
                mean = sum(all_scores) / len(all_scores)
                variance = sum((x - mean) ** 2 for x in all_scores) / len(all_scores)
                std_dev = variance**0.5
            else:
                mean, std_dev = 0, 0

            # Summary
            f.write("## 1. System Summary\n\n")
            f.write("| Metric | Count | Status |\n")
            f.write("|--------|-------|--------|\n")
            f.write(f"| Total Cards | {self.stats['total_cards']} | - |\n")
            f.write(f"| Cards with Abilities | {self.stats['with_abilities']} | - |\n")
            f.write(
                f"| Successful Parse | {self.stats['parsed_ok']} | {'✅' if self.stats['parse_failed'] == 0 else '⚠️'} |\n"
            )
            f.write(
                f"| Behaviorally Verified | {len(self.passed_cards)} | {'✅' if len(self.passed_cards) == self.stats['with_abilities'] else '⚠️'} |\n"
            )
            f.write(
                f"| Semantic Gaps found | {self.stats['semantic_gaps']} | {'✅' if self.stats['semantic_gaps'] == 0 else '⚠️'} |\n"
            )
            f.write(
                f"| Heuristic Issues found | {self.stats['heuristic_issues']} | {'✅' if self.stats['heuristic_issues'] == 0 else '❌'} |\n"
            )
            f.write(f"| Cards with FAQ | {self.stats['with_faq']} | - |\n\n")

            f.write(f"### Complexity Statistics (Based on {len(all_scores)} cards)\n")

            thresholds = {
                "SSS": mean + 2.5 * std_dev,
                "SS": mean + 2.0 * std_dev,
                "S": mean + 1.0 * std_dev,
                "A": mean,
                "B": mean - 0.5 * std_dev,
                "C": mean - 1.0 * std_dev,
                "D": mean - 1.5 * std_dev,
                "E": mean - 2.0 * std_dev,
            }

            # Recalculate tier stats
            self.tier_stats = defaultdict(lambda: {"total": 0, "passed": 0})
            self.faq_tier_stats = defaultdict(lambda: {"total": 0, "passed": 0})

            for card_no, r in self.reports_by_card.items():
                if "score" not in r:
                    continue
                s = r["score"]
                if s >= thresholds["SSS"]:
                    t = "SSS"
                elif s >= thresholds["SS"]:
                    t = "SS"
                elif s >= thresholds["S"]:
                    t = "S"
                elif s >= thresholds["A"]:
                    t = "A"
                elif s >= thresholds["B"]:
                    t = "B"
                elif s >= thresholds["C"]:
                    t = "C"
                elif s >= thresholds["D"]:
                    t = "D"
                elif s >= thresholds["E"]:
                    t = "E"
                else:
                    t = "F"

                self.reports_by_card[card_no]["tier"] = t
                self.tier_stats[t]["total"] += 1
                if card_no in self.passed_cards:
                    self.tier_stats[t]["passed"] += 1

                if r.get("faq"):
                    self.faq_tier_stats[t]["total"] += 1
                    if card_no in self.passed_cards:
                        self.faq_tier_stats[t]["passed"] += 1

            # Tier Table
            f.write("## 2. Verification by Complexity Tier (Statistical)\n\n")
            f.write("| Tier | Score Range | Threshold | Total Cards | Verified | % |\n")
            f.write("|------|-------------|-----------|-------------|----------|---|\n")

            tier_order = ["SSS", "SS", "S", "A", "B", "C", "D", "E", "F"]
            tier_labels = {
                "SSS": "Universe (> +2.5σ)",
                "SS": "God (> +2.0σ)",
                "S": "Final Boss (> +1.0σ)",
                "A": "Complex (> Mean)",
                "B": "Advanced (> -0.5σ)",
                "C": "Standard (> -1.0σ)",
                "D": "Basic (> -1.5σ)",
                "E": "Simple (> -2.0σ)",
                "F": "Trivial (< -2.0σ)",
            }

            for t in tier_order:
                ts = self.tier_stats[t]
                perc = (ts["passed"] / ts["total"] * 100) if ts["total"] > 0 else 0
                emoji = "🏆" if perc == 100 else "💪" if perc > 50 else "🚧"
                thresh_val = thresholds.get(t, 0) if t != "F" else thresholds["E"]
                operator = "≥" if t != "F" else "<"
                f.write(
                    f"| {t} | {tier_labels[t]} | {operator} {thresh_val:.1f} | {ts['total']} | {ts['passed']} | {perc:.1f}% {emoji} |\n"
                )
            f.write("\n")

            # FAQ Table
            f.write("## 3. FAQ Verification by Complexity\n\n")
            f.write("| Tier | Total FAQ Cards | Verified | % |\n")
            f.write("|------|-----------------|----------|---|\n")

            for t in tier_order:
                ts = self.faq_tier_stats[t]
                perc = (ts["passed"] / ts["total"] * 100) if ts["total"] > 0 else 0
                emoji = "🏆" if perc == 100 else "💪" if perc > 50 else "🚧"
                f.write(f"| {t} | {ts['total']} | {ts['passed']} | {perc:.1f}% {emoji} |\n")
            f.write("\n")

            # Effect Coverage
            f.write("## 4. Effect Coverage\n\n")
            f.write("| Effect Type | Count |\n")
            f.write("|-------------|-------|\n")
            for et, count in self.effect_counts.most_common(15):
                f.write(f"| {et} | {count} |\n")
            f.write("\n")

            # Detailed Analysis
            f.write("## 5. Analysis Breakdown\n\n")
            f.write("### Semantic Gaps (Keyword Mismatch)\n")
            for gap, count in self.gap_counts.most_common():
                f.write(f"- {gap}: {count} cards\n")
            f.write("\n### Heuristic Issues (Logic Gaps)\n")
            for iss, count in self.issue_counts.most_common():
                f.write(f"- {iss}: {count} cards\n")
            f.write("\n")

            # Samples with Gaps/Issues
            f.write("## 6. Problematic Cards (Sample)\n\n")
            count = 0
            for card_no, r in self.reports_by_card.items():
                if (r.get("gaps") or r.get("issues")) and count < 100:
                    status = "✅ (Verified) " if card_no in self.passed_cards else ""
                    f.write(f"### {card_no}: {r['name']} {status}\n")
                    f.write(f"**Text:**\n```\n{r['text']}\n```\n")
                    f.write(f"**Parsed:** {r['recon']}\n")
                    if r.get("gaps"):
                        f.write(f"⚠️ **Gaps:** {', '.join(r['gaps'])}\n")
                    if r.get("issues"):
                        f.write(f"❌ **Issues:** {', '.join(r['issues'])}\n")
                    score = r.get("score", 0)
                    tier = r.get("tier", "D")
                    f.write(f"📈 **Tier:** {tier} (Score: {score})\n")
                    if r.get("faq"):
                        f.write(f"📚 **FAQ:** {len(r['faq'])} entries\n")
                    f.write("\n---\n\n")
                    count += 1


if __name__ == "__main__":
    validator = MasterValidator("data/cards.json")
    validator.run()
    validator.write_report("docs/pr4_ability_report.md")
    print("Master report updated at docs/pr4_ability_report.md")
