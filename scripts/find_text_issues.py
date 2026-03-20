import json
import re

def analyze_text_issues():
    with open('qa/interactions_analysis.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = []
    
    for item in data:
        card_info = f"{item['card_no']} ({item['card_name']})"
        
        # Check choice_text
        choice_text = item['choice_text']
        if '_' in choice_text:
            issues.append({
                "card": card_info,
                "type": "UNDERSCORE_IN_PROMPT",
                "text": choice_text
            })
        if '[[' in choice_text or ']]' in choice_text:
            issues.append({
                "card": card_info,
                "type": "PLACEHOLDER_IN_PROMPT",
                "text": choice_text
            })
            
        # Check action labels
        for label_obj in item['action_labels']:
            label = label_obj['label']
            if '_' in label:
                # Filter out intentional underscores like [LL01-001]
                # but keep things like rps_rock or e_ 2
                if not re.search(r'\[[A-Z0-9-]+_[A-Z0-9-]+\]', label):
                    issues.append({
                        "card": card_info,
                        "type": "UNDERSCORE_IN_LABEL",
                        "text": label,
                        "action_id": label_obj['action_id']
                    })
            if '[[' in label or ']]' in label:
                issues.append({
                    "card": card_info,
                    "type": "PLACEHOLDER_IN_LABEL",
                    "text": label,
                    "action_id": label_obj['action_id']
                })

    # Deduplicate and count
    summary = {}
    for issue in issues:
        key = (issue['type'], issue['text'])
        if key not in summary:
            summary[key] = []
        summary[key].append(issue['card'])
    
    report = []
    for (itype, text), cards in summary.items():
        report.append({
            "type": itype,
            "text": text,
            "count": len(cards),
            "example_cards": list(set(cards))[:5]
        })
    
    report.sort(key=lambda x: x['count'], reverse=True)
    
    with open('qa/text_issues_categorized.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Analysis complete. Found {len(report)} unique text issues.")
    for item in report[:10]:
        print(f"[{item['type']}] ({item['count']} occurrences) \"{item['text']}\"")

if __name__ == "__main__":
    analyze_text_issues()
