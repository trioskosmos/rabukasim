import json
import re

with open('data/qa_data.json', 'r') as f:
    qas = json.load(f)

with open('engine_rust_src/src/qa_verification_tests.rs', 'r') as f:
    text = f.read()

func_names = re.findall(r'fn\s+test_([a-zA-Z0-9_]+)', text)
tested_qas = set()
for name in func_names:
    q_matches = re.findall(r'q(\d+)', name, re.IGNORECASE)
    for q in q_matches:
        tested_qas.add(f'Q{q}')

untested = [qa for qa in qas if qa['id'] not in tested_qas]

# Sort so specific cards are first
untested_specific = [qa for qa in untested if qa.get('related_cards')]
untested_generic = [qa for qa in untested if not qa.get('related_cards')]

untested_sorted = untested_specific + untested_generic

with open('data/cards_compiled.json', 'r') as f:
    db = json.load(f)

cards_db = list(db.get('member_db', {}).values()) + list(db.get('live_db', {}).values()) + list(db.get('energy_db', {}).values())
card_lookup = {c['card_no']: c for c in cards_db}

with open('qa_test_plans.md', 'w') as f:
    f.write("# QA Test Plans\n\n")
    for qa in untested_sorted:
        f.write(f"## {qa['id']}\n")
        f.write(f"**Question:** {qa['question'].strip()}\n\n")
        f.write(f"**Answer:** {qa['answer'].strip()}\n\n")

        cards = qa.get('related_cards', [])
        if cards:
            f.write("**Related Cards:**\n")
            for c in cards:
                card_data = card_lookup.get(c['card_no'], {})
                name = card_data.get('name', c['name'])
                f.write(f"- {c['card_no']} ({name})\n")
            f.write("\n")

        # Very basic heuristic for Board/Action
        q_text = qa['question']

        board_elements = []
        action_elements = []

        if 'ライブ' in q_text:
            board_elements.append("Live card(s) set up.")
            action_elements.append("Start live and verify outcome matches answer.")
        if '登場' in q_text:
            board_elements.append("Member in hand ready to play.")
            action_elements.append("Play member and check effects.")
        if 'バトンタッチ' in q_text:
            board_elements.append("Member(s) on stage to baton touch.")
            action_elements.append("Perform baton touch and verify outcome.")
        if 'エール' in q_text or 'ハート' in q_text:
            board_elements.append("Yell deck prepared or required hearts checked.")
        if 'スコア' in q_text:
            action_elements.append("Check score calculation.")

        if not board_elements:
            board_elements.append("Setup board according to question context.")
        if not action_elements:
            action_elements.append("Execute action described in question and verify answer.")

        if cards:
            board_elements.append(f"Include related cards in relevant zones (hand/stage/live).")

        f.write("**Planned Board:**\n")
        for b in board_elements:
            f.write(f"- {b}\n")
        f.write("\n")

        f.write("**Planned Action:**\n")
        for a in action_elements:
            f.write(f"- {a}\n")
        f.write("\n")
        f.write("---\n\n")

print(f"Generated plans for {len(untested_sorted)} untested QAs in qa_test_plans.md")
