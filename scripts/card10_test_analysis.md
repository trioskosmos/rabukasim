# Card 10 Test Analysis

## Tests
Multiple card_10 tests failing:
- test_card_10_cost_reduction_hand_size_variations
- test_card_10_counts_other_hand_cards_not_itself
- test_card_10_playability_uses_effective_hand_cost
- test_card_10_reduce_cost_opcode_per_card_filter
- test_card_10_baton_cost_does_not_double_count_hand_reduction
- test_card_10_baton_cost_ignores_stage_copy_hand_reduction_leak

## Error Messages
- "BUG: PER_CARD multiplier not applied correctly"
- "Cost reduction should be 4 (other cards * 1), but got 0"
- "card 10 baton cost should be 20 - 6 hand cards - 2 replaced cost = 12" but got 18

## Card 10 Ability Text (Japanese)
手札にあるこのメンバーカードのコストは、このカード以外の自分の手札1枚につき、1少なくなる。

## Translation
The cost of this member card in hand is reduced by 1 for each other card in your hand (excluding this card).

## Generated Frames
The frames include REDUCE_COST with PER_CARD multiplier, which is correct.

## Issue
**RUST INTERPRETER BUG**

The Rust interpreter is not correctly applying the PER_CARD multiplier for cost reduction. The frames are being generated correctly, but the engine is not executing them correctly.

The test expects:
- Hand with 4 other cards → cost reduction = 4
- Actual cost reduction = 0

This is a Rust interpreter bug in the cost calculation logic, not a frame generation bug.

## Root Cause
**RUST INTERPRETER BUG**

The Rust interpreter has a bug in how it handles the PER_CARD multiplier for REDUCE_COST opcodes. It's not correctly counting the number of cards in hand and applying the multiplier.

## Conclusion
This is NOT a frame generation bug. The frames are being generated correctly with the PER_CARD multiplier. The Rust interpreter needs to be fixed to correctly apply the PER_CARD multiplier.

## Action Required
Fix Rust interpreter cost calculation logic to correctly apply PER_CARD multiplier for REDUCE_COST opcodes.
