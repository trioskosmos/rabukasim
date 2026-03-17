import json

with open("data/cards.json", "r", encoding="utf-8") as f:
    cards = json.load(f)

fixes = {
    # Activate Energy Fixes (Many used ACTIVATE_MEMBER by mistake)
    "PL!N-bp1-004-R": "EFFECT: ACTIVATE_ENERGY(1) -> PLAYER",
    "PL!N-bp1-004-P": "EFFECT: ACTIVATE_ENERGY(1) -> PLAYER",
    "PL!HS-bp1-001-R": "EFFECT: ACTIVATE_ENERGY(2) -> PLAYER",
    "PL!HS-bp1-001-P": "EFFECT: ACTIVATE_ENERGY(2) -> PLAYER",
    "PL!HS-bp1-018-R": "EFFECT: ACTIVATE_ENERGY(1) -> PLAYER",  # Just in case
    "PL!N-sd1-008-SD": "TRIGGER: ON_PLAY\nEFFECT: ACTIVATE_ENERGY(2) -> PLAYER",  # Already correct, but making sure
    "PL!SP-pb1-007-R": "EFFECT: ACTIVATE_ENERGY(2) -> PLAYER",
    "PL!SP-pb1-007-P＋": "EFFECT: ACTIVATE_ENERGY(2) -> PLAYER",
    "PL!N-pb1-006-R": "COST: TAP_MEMBER(1)\nEFFECT: ACTIVATE_ENERGY(1) -> PLAYER",
    "PL!N-pb1-006-P＋": "COST: TAP_MEMBER(1)\nEFFECT: ACTIVATE_ENERGY(1) -> PLAYER",
    "PL!N-pb1-008-R": "EFFECT: REDUCE_COST(2) -> CARD_HAND\n\nEFFECT: SELECT_MODE(1) -> PLAYER; ACTIVATE_ENERGY(2) -> PLAYER",
    "PL!N-pb1-008-P＋": "EFFECT: REDUCE_COST(2) -> CARD_HAND\n\nEFFECT: SELECT_MODE(1) -> PLAYER; ACTIVATE_ENERGY(2) -> PLAYER",
    "PL!N-pb1-010-R": "CONDITION: HAS_CHOICE\nEFFECT: SELECT_MODE(1) -> PLAYER; ACTIVATE_ENERGY(1) -> PLAYER",
    "PL!N-pb1-010-P＋": "CONDITION: HAS_CHOICE\nEFFECT: SELECT_MODE(1) -> PLAYER; ACTIVATE_ENERGY(1) -> PLAYER",
    # Place Under Fixes (source=energy)
    "PL!N-bp3-001-R＋": "EFFECT: PLACE_UNDER(1) {source=energy} -> PLAYER; DRAW(1) -> PLAYER; ADD_BLADES(2) -> PLAYER",
    "PL!N-bp3-001-P": "EFFECT: PLACE_UNDER(1) {source=energy} -> PLAYER; DRAW(1) -> PLAYER; ADD_BLADES(2) -> PLAYER",
    "PL!N-bp3-001-P＋": "EFFECT: PLACE_UNDER(1) {source=energy} -> PLAYER; DRAW(1) -> PLAYER; ADD_BLADES(2) -> PLAYER",
    "PL!N-bp3-001-SEC": "EFFECT: PLACE_UNDER(1) {source=energy} -> PLAYER; DRAW(1) -> PLAYER; ADD_BLADES(2) -> PLAYER",
    "PL!N-bp3-007-R": 'COST: ACTIVATE_ENERGY(2); TAP_MEMBER(1)\nEFFECT: PLAY_MEMBER_FROM_HAND(1) {unit="Setsuna"} -> CARD_HAND; PLACE_UNDER(1) {source=energy} -> PLAYER',
    "PL!N-bp3-007-P": 'COST: ACTIVATE_ENERGY(2); TAP_MEMBER(1)\nEFFECT: PLAY_MEMBER_FROM_HAND(1) {unit="Setsuna"} -> CARD_HAND; PLACE_UNDER(1) {source=energy} -> PLAYER',
    "PL!N-bp3-013-N": "EFFECT: PLACE_UNDER(1) {source=energy} -> PLAYER; DRAW(2) -> PLAYER",
    "PL!N-pb1-002-R": "EFFECT: PLACE_UNDER(2) {source=energy} -> PLAYER\n\nCONDITION: COUNT_STAGE {MIN=2}\nEFFECT: BOOST_SCORE(1) -> PLAYER",
    "PL!N-pb1-002-P＋": "EFFECT: PLACE_UNDER(2) {source=energy} -> PLAYER\n\nCONDITION: COUNT_STAGE {MIN=2}\nEFFECT: BOOST_SCORE(1) -> PLAYER",
    "PL!N-pb1-011-R": "EFFECT: BUFF_POWER(1) -> PLAYER; ADD_BLADES(1) -> PLAYER\n\nCOST: PLACE_UNDER(1) {source=energy}\nEFFECT: RECOVER_LIVE(1) -> CARD_DISCARD",
    "PL!N-pb1-011-P＋": "EFFECT: BUFF_POWER(1) -> PLAYER; ADD_BLADES(1) -> PLAYER\n\nCOST: PLACE_UNDER(1) {source=energy}\nEFFECT: RECOVER_LIVE(1) -> CARD_DISCARD",
    # Active Energy Condition Fixes
    "PL!SP-bp4-028-L": "CONDITION: COUNT_ENERGY {MIN=1, attr=1}\nEFFECT: BOOST_SCORE(1) -> PLAYER",
}

count = 0
for k, p in fixes.items():
    if k in cards:
        cards[k]["pseudocode"] = p
        count += 1

with open("data/cards.json", "w", encoding="utf-8") as f:
    json.dump(cards, f, indent=4, ensure_ascii=False)

print(f"Applied {count} pseudocode fixes to data/cards.json")
