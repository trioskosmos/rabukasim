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

with open('data/cards_compiled.json', 'r') as f:
    db = json.load(f)

cards_db = list(db.get('member_db', {}).values()) + list(db.get('live_db', {}).values()) + list(db.get('energy_db', {}).values())
card_lookup = {c['card_no']: c for c in cards_db}

def generate_board_and_action(qa, related_cards):
    q_text = qa['question']
    a_text = qa['answer']

    setup_steps = []
    action_steps = []
    assertions = []

    # Analyze cards
    main_card = related_cards[0] if related_cards else None

    if main_card:
        card_no = main_card['card_no']
        card_data = card_lookup.get(card_no, {})
        c_type = card_data.get('card_type', 'Member')

        setup_steps.append(f"Initialize engine with players P1 and P2.")

        # Determine based on text
        if 'ライブ' in q_text and '開始' in q_text:
            setup_steps.append(f"Place {card_no} in P1's Live Area (if Live card) or Stage (if Member).")
            setup_steps.append("Ensure any conditions for the ON_LIVE_START trigger are met (or intentionally not met, based on question).")
            action_steps.append("Execute Action: Start Live.")
            action_steps.append("Process event queue for ON_LIVE_START triggers.")
            if 'はい' in a_text or '満たします' in a_text:
                assertions.append("Assert that the trigger condition evaluates to TRUE.")
                assertions.append("Assert that the effect is applied (e.g., buff, heart reduction).")
            else:
                assertions.append("Assert that the trigger condition evaluates to FALSE or the effect is NOT applied.")

        elif '登場' in q_text:
            setup_steps.append(f"Add {card_no} to P1's Hand.")
            setup_steps.append(f"Set P1 Energy to match {card_no} cost (if applicable).")

            # Extract other specific cards mentioned in the question
            mentioned_cards = re.findall(r'「(.*?)」', q_text)
            for mc in mentioned_cards:
                if '登場' in q_text and mc != card_no:
                    setup_steps.append(f"Add {mc} to relevant zone (Hand or Deck) for the effect to target.")

            action_steps.append(f"Execute Action: Play Member ({card_no}) to Stage.")
            action_steps.append("Process event queue for ON_PLAY triggers.")
            if 'できる' in a_text or 'はい' in a_text:
                assertions.append("Assert that the ON_PLAY interaction is created and presented to the player.")
            else:
                assertions.append("Assert that the ON_PLAY interaction is NOT created or fails to execute.")

        elif 'バトンタッチ' in q_text:
            setup_steps.append(f"Add {card_no} to P1's Hand.")
            setup_steps.append(f"Place another target member on P1's Stage (to be baton touched).")
            if 'ターン' in q_text:
                setup_steps.append("Advance turn to satisfy 'previous turn' baton touch requirements, or keep on same turn to test restrictions.")
            action_steps.append(f"Execute Action: Play Member ({card_no}) via Baton Touch with the target member.")
            if 'できない' in a_text or 'いいえ' in a_text:
                assertions.append("Assert that Baton Touch action is INVALID or rejected by the engine.")
            else:
                assertions.append("Assert that Baton Touch action is VALID and succeeds.")
                assertions.append("Assert that the old member goes to Discard and the new member is on Stage.")

        elif 'スコア' in q_text:
            setup_steps.append(f"Place {card_no} in relevant zone.")
            action_steps.append("Calculate Live Score.")
            assertions.append(f"Assert Score calculation aligns with answer: {a_text.strip()}")

        elif 'エール' in q_text or 'ハート' in q_text:
            setup_steps.append(f"Set up Yell Deck with specific blade/heart types mentioned in question.")
            action_steps.append("Perform Yell or check Heart Requirements.")
            assertions.append(f"Assert Heart evaluation matches answer: {a_text.strip()}")

        else:
            setup_steps.append(f"Setup board with {card_no} in its standard starting zone (Hand/Stage).")
            action_steps.append("Trigger the relevant game phase or action.")
            assertions.append(f"Assert outcome: {a_text.strip()}")

    else:
        # Generic QA
        setup_steps.append("Initialize generic game state.")
        setup_steps.append(f"Set up board to match scenario: {q_text[:50]}...")
        action_steps.append("Perform the action described in the question.")
        assertions.append(f"Assert outcome aligns with answer: {a_text.strip()}")

    return setup_steps, action_steps, assertions

with open('detailed_qa_test_plans.md', 'w') as f:
    f.write("# Comprehensive QA Test Plans\n\n")
    f.write("> This document contains highly detailed, step-by-step test plans for all missing QA items, formatted for direct translation into Rust integration tests.\n\n")

    # Sort for better reading: specific cards first, descending ID
    untested.sort(key=lambda x: (0 if x.get('related_cards') else 1, -int(x['id'][1:])))

    for qa in untested:
        f.write(f"## {qa['id']}\n")
        f.write(f"**Question:** {qa['question'].strip()}\n\n")
        f.write(f"**Answer:** {qa['answer'].strip()}\n\n")

        cards = qa.get('related_cards', [])
        if cards:
            f.write("### Related Cards\n")
            for c in cards:
                card_data = card_lookup.get(c['card_no'], {})
                name = card_data.get('name', c['name'])
                f.write(f"- **{c['card_no']} ({name})**\n")
                if 'ability_text' in card_data:
                    ability = ''.join(card_data['ability_text']).strip().replace('\n', ' ')
                    f.write(f"  - *Ability:* `{ability}`\n")
            f.write("\n")

        setup_steps, action_steps, assertions = generate_board_and_action(qa, cards)

        f.write("### Test Setup (Board State)\n")
        for i, step in enumerate(setup_steps, 1):
            f.write(f"{i}. {step}\n")
        f.write("\n")

        f.write("### Execution (Action Sequence)\n")
        for i, step in enumerate(action_steps, 1):
            f.write(f"{i}. {step}\n")
        f.write("\n")

        f.write("### Expected Outcome (Assertions)\n")
        for i, step in enumerate(assertions, 1):
            f.write(f"- [ ] {step}\n")
        f.write("\n")
        f.write("---\n\n")

print(f"Generated highly detailed plans for {len(untested)} untested QAs in detailed_qa_test_plans.md")
