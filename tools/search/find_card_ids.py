import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from engine.game.data_loader import CardDataLoader

target_numbers = ["PL!SP-bp1-010-R", "PL!S-pb1-001-R", "PL!N-bp1-012-R＋", "PL!HS-bp1-007-P"]

loader = CardDataLoader("engine/data/cards.json")
member_db, live_db, _ = loader.load()

found = {}
# Scan member_db
for cid, card in member_db.items():
    if card.card_no in target_numbers:
        found[card.card_no] = cid

# Scan live_db
for cid, card in live_db.items():
    if card.card_no in target_numbers:
        found[card.card_no] = cid

for num in target_numbers:
    if num in found:
        print(f"{num}: {found[num]}")
    else:
        print(f"{num}: NOT FOUND")
