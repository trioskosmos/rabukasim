# Card 654 Fix Summary

## Issue
Card 654 test was failing because the place_card action with energy_card was generating wrong frames:
- Before: MOVE_TO_DISCARD with empty source_zone and dest_zone: DISCARD
- After: DRAW_ENERGY with source_zone: ENERGY, target_slot: ENERGY

## Fix Applied
1. Added logic to infer source/destination for energy_card when not specified in semantic data:
   - If card_type is "energy_card" and source is not specified, default to "energy_deck"
   - If card_type is "energy_card" and destination is not specified, default to "energy_zone"

2. Added specific opcode case for drawing energy card from energy_deck to energy_zone:
   - When source_zone is ENERGY/ENERGY_DECK, card_type is energy_card, and state is "active"
   - Use DRAW_ENERGY opcode with source_zone: ENERGY, target_slot: ENERGY

## Generated Frames After Fix
```
Frame 0: SCORE_TOTAL_CHECK, value=6
Frame 1: JUMP_IF_FALSE, value=1
Frame 2: DRAW_ENERGY, value=1, source_zone: ENERGY, target_slot: ENERGY
Frame 3: RETURN
```

## Test Result
Test still fails with "left: 3 right: 4". The DRAW_ENERGY frame is now generated correctly, but the Rust engine may not be executing it properly. This could be:
- Rust interpreter bug with DRAW_ENERGY opcode
- Incorrect slot/attr parameters for DRAW_ENERGY
- Engine needs additional configuration for DRAW_ENERGY

## Next Steps
Need to examine Rust engine's DRAW_ENERGY handler to see what parameters it expects and why it's not adding the energy card to the energy zone.
