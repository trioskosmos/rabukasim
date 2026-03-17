import json

# Results data to be formatted into the walkthrough
results = {
    "Slash Trigger": {
        "text": "{{toujyou.png|登場}}/{{live_start.png|ライブ開始時}} カードを1枚引く。",
        "status": "PASSED (Found 2 abilities: ON_PLAY, ON_LIVE_START)",
    },
    "Parentheses": {
        "text": "{{toujyou.png|登場}} カードを1枚引く。（これは説明文です。）",
        "status": "PASSED (Correctly labeled effects vs reminder text)",
    },
    "Dash Bullets": {
        "text": "以下から1回を選ぶ。\\n- カードを1枚引く。\\n- スコア+1。",
        "status": "PASSED (Detected 2 modal options via '-' bullet)",
    },
    "Numerical Variants": {
        "text": "以下から2つを選ぶ。\\n・カードを1枚引く。\\n・スコア+1。\\n・エネチャージ。",
        "status": "PASSED (Detected SELECT_MODE value: 2, 3 options)",
    },
}

print(json.dumps(results, indent=2))
