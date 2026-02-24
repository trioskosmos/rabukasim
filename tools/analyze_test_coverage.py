#!/usr/bin/env python3
"""
Analyze test coverage for semantic truth data.
Generates a report showing test count and types for each card.
"""

import json
from collections import defaultdict
from pathlib import Path


def load_truth_data():
    """Load semantic truth v3 JSON."""
    truth_path = Path(__file__).parent.parent / "reports" / "semantic_truth_v3.json"
    with open(truth_path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_card(card_id, card_data):
    """Analyze a single card's test coverage."""
    abilities = card_data.get("abilities", [])
    
    analysis = {
        "card_id": card_id,
        "ability_count": len(abilities),
        "triggers": [],
        "total_sequences": 0,
        "total_deltas": 0,
        "complexity": "単純",
        "needs_additional_tests": False,
        "additional_test_reason": [],
        "ability_details": []
    }
    
    for i, ability in enumerate(abilities):
        trigger = ability.get("trigger", "UNKNOWN")
        sequence = ability.get("sequence", [])
        
        analysis["triggers"].append(trigger)
        analysis["total_sequences"] += len(sequence)
        
        ability_detail = {
            "index": i,
            "trigger": trigger,
            "sequence_count": len(sequence),
            "delta_count": 0,
            "has_empty_sequence": len(sequence) == 0,
            "has_modal": False
        }
        
        for seg in sequence:
            deltas = seg.get("deltas", [])
            ability_detail["delta_count"] += len(deltas)
            analysis["total_deltas"] += len(deltas)
            
            # Check for modal options
            text = seg.get("text", "")
            if "OPTION" in text or "SELECT_MODE" in text or "modal" in text.lower():
                ability_detail["has_modal"] = True
                analysis["needs_additional_tests"] = True
                analysis["additional_test_reason"].append(f"Ab{i}: モーダル選択あり")
        
        analysis["ability_details"].append(ability_detail)
    
    # Determine complexity
    if analysis["ability_count"] >= 3:
        analysis["complexity"] = "複雑"
    elif analysis["ability_count"] >= 2 or analysis["total_sequences"] >= 3:
        analysis["complexity"] = "普通"
    elif any(d["has_modal"] for d in analysis["ability_details"]):
        analysis["complexity"] = "モーダル"
    
    # Check for empty sequences (untested abilities)
    for detail in analysis["ability_details"]:
        if detail["has_empty_sequence"]:
            analysis["needs_additional_tests"] = True
            analysis["additional_test_reason"].append(f"Ab{detail['index']}: 空のシーケンス（テスト未実装）")
    
    return analysis


def generate_report(truth_data):
    """Generate test coverage report."""
    analyses = []
    trigger_stats = defaultdict(lambda: {"count": 0, "cards": []})
    complexity_stats = defaultdict(int)
    
    for card_id, card_data in truth_data.items():
        analysis = analyze_card(card_id, card_data)
        analyses.append(analysis)
        
        for trigger in analysis["triggers"]:
            trigger_stats[trigger]["count"] += 1
            trigger_stats[trigger]["cards"].append(card_id)
        
        complexity_stats[analysis["complexity"]] += 1
    
    # Sort by ability count (descending)
    analyses.sort(key=lambda x: x["ability_count"], reverse=True)
    
    # Generate markdown report
    report = []
    report.append("# テストカバレッジレポート")
    report.append("")
    report.append("## サマリー")
    report.append("")
    report.append(f"- 総カード数: {len(truth_data)}")
    report.append(f"- 総アビリティ数: {sum(a['ability_count'] for a in analyses)}")
    report.append(f"- 平均アビリティ数/カード: {sum(a['ability_count'] for a in analyses) / len(analyses):.2f}")
    report.append(f"- 追加テスト必要なカード: {sum(1 for a in analyses if a['needs_additional_tests'])}")
    report.append("")
    
    report.append("## 複雑さ別統計")
    report.append("")
    report.append("| 複雑さ | カード数 |")
    report.append("|--------|----------|")
    for complexity, count in sorted(complexity_stats.items()):
        report.append(f"| {complexity} | {count} |")
    report.append("")
    
    report.append("## トリガー別統計")
    report.append("")
    report.append("| トリガー | アビリティ数 |")
    report.append("|----------|-------------|")
    for trigger, data in sorted(trigger_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        report.append(f"| {trigger} | {data['count']} |")
    report.append("")
    
    report.append("## カード別統計（アビリティ数順）")
    report.append("")
    report.append("| カードID | アビリティ数 | トリガー | 複雑さ | 追加テスト |")
    report.append("|----------|------------|----------|--------|----------|")
    
    for a in analyses[:50]:  # Top 50
        triggers_str = ", ".join(a["triggers"])
        additional = "はい" if a["needs_additional_tests"] else "いいえ"
        report.append(f"| {a['card_id']} | {a['ability_count']} | {triggers_str} | {a['complexity']} | {additional} |")
    
    report.append("")
    report.append("## 追加テストが必要なカード")
    report.append("")
    
    cards_needing_tests = [a for a in analyses if a["needs_additional_tests"]]
    for a in cards_needing_tests[:30]:  # Top 30
        report.append(f"### {a['card_id']}")
        report.append("")
        report.append(f"- アビリティ数: {a['ability_count']}")
        report.append(f"- 理由: {', '.join(a['additional_test_reason'])}")
        report.append("")
        
        for detail in a["ability_details"]:
            status = "✅" if not detail["has_empty_sequence"] else "❌"
            report.append(f"  - {status} Ab{detail['index']} ({detail['trigger']}): {detail['sequence_count']}シーケンス, {detail['delta_count']}デルタ")
        report.append("")
    
    return "\n".join(report)


def main():
    truth_data = load_truth_data()
    report = generate_report(truth_data)
    
    # Write report
    report_path = Path(__file__).parent.parent / "reports" / "TEST_COVERAGE_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"Report written to: {report_path}")
    print(f"\nTotal cards: {len(truth_data)}")
    print(f"Total abilities: {sum(len(c.get('abilities', [])) for c in truth_data.values())}")


if __name__ == "__main__":
    main()
