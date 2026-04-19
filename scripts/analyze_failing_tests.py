import json

# Load cards.json to get card names
with open('data/cards.json', 'r', encoding='utf-8') as f:
    cards = json.load(f)

# Mismatched cards and their names
mismatched_cards = {
    'PL!-bp3-025-L': 'タカラモノズ',
    'PL!N-bp5-010-R': '三船栞子',
    'PL!N-bp5-010-AR': '三船栞子',
    'PL!HS-bp1-003-R+': '乙宗 梢',
    'PL!HS-bp1-003-P': '乙宗 梢',
    'PL!HS-bp1-003-P+': '乙宗 梢',
    'PL!-PR-007-PR': '東條 希',
    'PL!-PR-009-PR': '矢澤にこ',
    'PL!S-bp3-012-N': '松浦果南',
    'PL!N-bp1-003-R+': '桜坂しずく',
    'PL!N-bp1-003-P': '桜坂しずく',
    'PL!N-bp1-003-P+': '桜坂しずく'
}

print("Mismatched cards from compare_frames_detailed.py:")
print("=" * 80)
for card_no, name in mismatched_cards.items():
    # Get card ID if available
    if card_no in cards:
        card_id = cards[card_no].get('id', 'N/A')
    else:
        card_id = 'N/A'
    print(f"{card_no}: ID={card_id}, Name={name}")

print("\n\nFailing tests that may relate to these cards:")
print("=" * 80)
print("Based on test names and card names:")
print("- test_q168_q169_q170_q181_q188_nico_exhaustive -> relates to 矢澤にこ (PL!-PR-009-PR)")
print("- Other failing tests need manual correlation based on card IDs in test code")

print("\n\nSummary of frame mismatches by pattern:")
print("=" * 80)
print("1. surplus_heart pattern:")
print("   - Cards: PL!-bp3-025-L, PL!N-bp5-010-R, PL!N-bp5-010-AR")
print("   - Issues: Frame count mismatch (7 vs 6), OP mismatches")
print("   - OP mismatches: COUNT_HEARTS vs HAS_EXCESS_HEART, BOOST_SCORE vs COUNT_HEARTS")
print("")
print("2. names_different pattern:")
print("   - Cards: PL!HS-bp1-003-R+, PL!HS-bp1-003-P, PL!HS-bp1-003-P+")
print("   - Issues: Frame count mismatch (4 vs 3), OP mismatches")
print("   - OP mismatches: COUNT_STAGE vs AREA_CHECK, SUM_VALUE vs PAY_ENERGY, etc.")
print("")
print("3. opponent_member_to_wait pattern:")
print("   - Cards: PL!-PR-007-PR, PL!-PR-009-PR, PL!S-bp3-012-N")
print("   - Issues: Count mismatches, OP mismatches")
print("   - OP mismatches: SELECT_MEMBER vs TAP_OPPONENT, MOVE_MEMBER vs RETURN")
print("")
print("4. waitroom_live_recovery pattern:")
print("   - Cards: PL!N-bp1-003-R+, PL!N-bp1-003-P, PL!N-bp1-003-P+")
print("   - Issues: Frame count mismatches (6 vs 4, 4 vs 5), OP mismatches")
print("   - OP mismatches: BATON vs MOVE_TO_DISCARD, COUNT_ENERGY vs RECOVER_LIVE, etc.")
