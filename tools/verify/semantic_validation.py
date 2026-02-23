"""
Comprehensive Semantic Validation Script
Parses every card and validates that the parsed output makes sense compared to raw text.
Uses heuristics to flag potentially incomplete or incorrect parses.
"""

import json
import re
import sys

sys.path.insert(0, ".")
from engine.models.ability import ConditionType, EffectType, TriggerType, TargetType
from compiler.parser_v2 import parse_ability_text


def load_cards():
    with open("data/cards.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.values()) if isinstance(data, dict) else data


def validate_card(card):
    """Validate that parsing output matches expected patterns in raw text."""
    text = card.get("ability", "")
    if not text:
        return None  # No ability to validate

    issues = []

    try:
        abilities = parse_ability_text(text)
    except Exception as e:
        return [f"PARSE_ERROR: {str(e)[:50]}"]

    # Flatten all effects and conditions
    all_effects = []
    all_conditions = []
    for ability in abilities:
        all_effects.extend(ability.effects)
        all_conditions.extend(ability.conditions)

    effect_types = {e.effect_type for e in all_effects}
    condition_types = {c.type for c in all_conditions}

    # --- HEURISTIC CHECKS ---

    # 1. Draw Check
    draw_match = re.search(r"(\d+)枚引", text) or "引く" in text
    if draw_match and EffectType.DRAW not in effect_types:
        issues.append("MISSING_DRAW: Text mentions drawing but no DRAW effect parsed")

    # 2. Score Boost Check
    if "スコア" in text and ("＋" in text or "+" in text):
        if EffectType.BOOST_SCORE not in effect_types:
            issues.append("MISSING_SCORE: Text mentions score boost but no BOOST_SCORE parsed")

    # 3. Blade/Heart Check
    if "ブレード" in text and "得る" in text:
        if EffectType.ADD_BLADES not in effect_types:
            issues.append("MISSING_BLADES: Text mentions gaining blades but no ADD_BLADES parsed")

    if "ハート" in text and "得る" in text:
        if EffectType.ADD_HEARTS not in effect_types:
            issues.append("MISSING_HEARTS: Text mentions gaining hearts but no ADD_HEARTS parsed")

    # 4. Numbered Condition Check (5人以上, 3枚以上, etc.)
    count_match = re.search(r"(\d+)(人|枚)以上", text)
    if count_match:
        expected_count = int(count_match.group(1))
        has_count_condition = any(
            c.params.get("count") == expected_count for c in all_conditions if hasattr(c, "params") and c.params
        )
        if not has_count_condition:
            issues.append(f"MISSING_COUNT: Text mentions '{count_match.group(0)}' but no matching count condition")

    # 5. Multi-Sentence Check (multiple 。 but few effects)
    sentence_count = text.count("。") + text.count("\n")
    if sentence_count > 2 and len(all_effects) < sentence_count - 1:
        issues.append(f"LOW_EFFECT_RATIO: {sentence_count} sentences but only {len(all_effects)} effects")

    # 6. Named Member Check
    names = re.findall(r"「(.*?)」", text)
    if names and "場合" in text:
        has_member_condition = any(c.type == ConditionType.HAS_MEMBER for c in all_conditions)
        if not has_member_condition:
            issues.append("MISSING_MEMBER_COND: Text mentions named members but no HAS_MEMBER condition")

    # 7. Opponent Targeting Check
    if "相手" in text and ("手札" in text or "メンバー" in text or "デッキ" in text):
        has_opponent_effect = any(
            e.params.get("opponent") or "opponent" in str(e.target).lower()
            for e in all_effects
            if hasattr(e, "params") and e.params
        )
        # Check target type too
        # TargetType already imported at top

        has_opponent_target = any(e.target in [TargetType.OPPONENT, TargetType.OPPONENT_HAND] for e in all_effects)
        if not has_opponent_effect and not has_opponent_target:
            issues.append("MISSING_OPPONENT: Text mentions opponent but no opponent target/effect")

    # 8. Trigger Detection
    if "登場時" in text or "{{toujyou" in text:
        has_on_play = any(a.trigger == TriggerType.ON_PLAY for a in abilities)
        if not has_on_play:
            issues.append("MISSING_TRIGGER: Text has 登場時 but no ON_PLAY trigger")

    if "ライブ成功" in text or "{{live_success" in text:
        has_live_success = any(a.trigger == TriggerType.ON_LIVE_SUCCESS for a in abilities)
        if not has_live_success:
            issues.append("MISSING_TRIGGER: Text has ライブ成功時 but no ON_LIVE_SUCCESS trigger")

    # 9. Cost Check
    if ("コスト" in text and ("減" in text or "-" in text)) or "{{icon_energy" in text:
        has_cost = any(a.costs for a in abilities) or EffectType.REDUCE_COST in effect_types
        if not has_cost and "{{icon_energy" in text:
            # Energy cost in conditions
            pass  # This might be an optional cost indicator, not a bug

    # 10. Zone Detection
    zone_keywords = ["控え室", "デッキ", "手札", "ステージ", "ライブカード置き場", "成功ライブ"]
    found_zones = [z for z in zone_keywords if z in text]
    if len(found_zones) > 1:
        # Text mentions multiple zones, check if conditions/effects reflect this
        has_zone_param = any(c.params.get("zone") for c in all_conditions if hasattr(c, "params") and c.params)
        if not has_zone_param:
            issues.append(f"MISSING_ZONE: Text mentions zones {found_zones} but no zone params in conditions")

    return issues if issues else None


def extract_keywords(text):
    """Extract all potential game-relevant keywords from text."""
    keywords = set()

    # Action verbs (stem forms) - these indicate effects
    verbs = re.findall(
        r"([ぁ-んァ-ン一-龥]+)(する|できる|させる|なる|置く|引く|見る|選ぶ|得る|失う|移動|戻す|加える|払う|消す|与える|受ける|持つ|使う|出す|入れる|送る|渡す|変える|増える|減る|残す|捨てる|探す|公開|確認|宣言|聞く)",
        text,
    )
    for v in verbs:
        keywords.add(v[0] + v[1])

    # Nouns with particles (indicates conditions/targets)
    nouns = re.findall(r"([ぁ-んァ-ン一-龥]+)(が|を|に|で|と|から|まで|より|の|は)", text)
    for n in nouns:
        if len(n[0]) >= 2:  # Filter out single-char noise
            keywords.add(n[0])

    # Bracketed terms [X] - often game-specific
    brackets = re.findall(r"\[(.*?)\]", text)
    keywords.update(brackets)

    # Template markers {{X.png|Y}} - icon references
    icons = re.findall(r"\{\{([^|]+)\|([^}]+)\}\}", text)
    for i in icons:
        keywords.add(i[1])  # The text label

    # Quoted names 「X」
    names = re.findall(r"「(.*?)」", text)
    keywords.update(names)

    # Group names 『X』
    groups = re.findall(r"『(.*?)』", text)
    keywords.update(groups)

    return keywords


def analyze_keyword_gaps(cards):
    """Find keywords that appear frequently but may not be handled by parser."""
    # Known handled keywords (mapped to parser logic)
    KNOWN_HANDLED = {
        # Effects
        "引く",
        "得る",
        "置く",
        "戻す",
        "加える",
        "移動",
        "探す",
        "見る",
        "選ぶ",
        "アクティブ",
        "ウェイト",
        "バトンタッチ",
        "スコア",
        "ブレード",
        "ハート",
        "エネルギー",
        "コスト",
        "デッキ",
        "手札",
        "控え室",
        "ステージ",
        "エリア",
        # Triggers
        "登場時",
        "ライブ成功時",
        "ライブ開始時",
        "ターン開始",
        "ターン終了",
        "常時",
        "起動",
        # Conditions
        "場合",
        "以上",
        "以下",
        "限り",
        "時",
        "のみ",
        # Targets
        "メンバー",
        "カード",
        "自分",
        "相手",
        "全員",
        # Modifiers
        "ターン1回",
        "ライブ終了時まで",
        "ターン終了時まで",
        # Groups/Characters (handled generically)
        "μ's",
        "Aqours",
        "Liella!",
        "虹ヶ咲",
        "蓮ノ空",
    }

    keyword_freq = {}
    keyword_cards = {}

    for card in cards:
        text = card.get("ability", "")
        if not text:
            continue

        card_id = card.get("card_no") or card.get("cardNumber") or "UNKNOWN"
        keywords = extract_keywords(text)

        for kw in keywords:
            if kw not in keyword_freq:
                keyword_freq[kw] = 0
                keyword_cards[kw] = []
            keyword_freq[kw] += 1
            if len(keyword_cards[kw]) < 3:  # Store up to 3 example cards
                keyword_cards[kw].append((card_id, text[:80]))

    # Find unhandled keywords (appear 5+ times but not in KNOWN_HANDLED)
    unhandled = {}
    for kw, freq in keyword_freq.items():
        if freq >= 5 and kw not in KNOWN_HANDLED:
            # Check if it's a subset of a known keyword
            is_subset = any(kw in known or known in kw for known in KNOWN_HANDLED)
            if not is_subset and len(kw) >= 2:
                unhandled[kw] = {"frequency": freq, "examples": keyword_cards[kw]}

    return unhandled


def main():
    print("Loading cards...")
    cards = load_cards()

    # --- PART 1: Heuristic Validation (existing logic) ---
    all_issues = {}
    severity_counts = {
        "PARSE_ERROR": 0,
        "MISSING_DRAW": 0,
        "MISSING_SCORE": 0,
        "MISSING_BLADES": 0,
        "MISSING_HEARTS": 0,
        "MISSING_COUNT": 0,
        "LOW_EFFECT_RATIO": 0,
        "MISSING_MEMBER_COND": 0,
        "MISSING_OPPONENT": 0,
        "MISSING_TRIGGER": 0,
        "MISSING_ZONE": 0,
    }

    for card in cards:
        card_id = card.get("card_no") or card.get("cardNumber") or card.get("id", "UNKNOWN")
        issues = validate_card(card)
        if issues:
            all_issues[card_id] = {
                "name": card.get("name", "Unknown"),
                "issues": issues,
                "text": card.get("ability", "")[:100] + "...",
            }
            for issue in issues:
                for key in severity_counts:
                    if key in issue:
                        severity_counts[key] += 1

    # --- PART 2: Keyword Gap Analysis (NEW) ---
    print("Analyzing keyword gaps...")
    unhandled = analyze_keyword_gaps(cards)

    # Write report
    with open("semantic_validation_report.txt", "w", encoding="utf-8") as out:
        out.write("=" * 70 + "\n")
        out.write("SEMANTIC VALIDATION REPORT\n")
        out.write(f"Total Cards: {len(cards)}\n")
        out.write(f"Cards with Heuristic Issues: {len(all_issues)}\n")
        out.write(f"Cards OK: {len(cards) - len(all_issues)}\n")
        out.write("=" * 70 + "\n\n")

        # Part 1: Known issues
        out.write("PART 1: HEURISTIC ISSUES (Known Patterns)\n")
        out.write("-" * 40 + "\n")
        for key, count in sorted(severity_counts.items(), key=lambda x: -x[1]):
            if count > 0:
                out.write(f"  {key}: {count}\n")
        out.write("\n")

        # Part 2: Keyword Gaps (NEW PATTERNS!)
        out.write("=" * 70 + "\n")
        out.write("PART 2: KEYWORD GAP ANALYSIS (Potential NEW Patterns)\n")
        out.write("-" * 40 + "\n")
        out.write(f"Found {len(unhandled)} potential unhandled keywords\n\n")

        # Sort by frequency
        sorted_unhandled = sorted(unhandled.items(), key=lambda x: -x[1]["frequency"])
        for kw, info in sorted_unhandled[:30]:  # Top 30
            out.write(f"'{kw}' (appears {info['frequency']} times)\n")
            for card_id, text in info["examples"][:2]:
                out.write(f"  - [{card_id}]: {text}...\n")
            out.write("\n")

        if len(sorted_unhandled) > 30:
            out.write(f"... and {len(sorted_unhandled) - 30} more unhandled keywords\n")

        out.write("\n" + "=" * 70 + "\n")
        out.write("DETAILED HEURISTIC ISSUES (First 30):\n\n")
        for card_id, info in list(all_issues.items())[:30]:
            out.write(f"[{card_id}] {info['name']}\n")
            out.write(f"  Text: {info['text']}\n")
            for issue in info["issues"]:
                out.write(f"  - {issue}\n")
            out.write("\n")

    print("Validation complete.")
    print(f"  - {len(all_issues)} cards with heuristic issues")
    print(f"  - {len(unhandled)} potential unhandled keywords discovered")
    print("Report written to: semantic_validation_report.txt")


if __name__ == "__main__":
    main()
