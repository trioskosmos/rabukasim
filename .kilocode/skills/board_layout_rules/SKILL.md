---
name: board_layout_rules
description: Use when editing board positions, slot layout, orientation, or placement semantics.
---
# Board Layout Rules
## Do
- Treat zone orientation and slot indexing as authoritative.
- Keep stage, hand, deck, discard, energy, and success areas consistent.
- Update UI and engine rules together when placement changes.
## Do not
- Do not hardcode visuals that contradict zone semantics.
- Do not change rotation rules without checking every affected area.
## Verify
- Run a placement test or visual check on the changed zone.