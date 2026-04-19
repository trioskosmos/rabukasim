# Frame Generation Debug Analysis

## Current Status
- Baseline: 598 passed; 95 failed
- Semantic extraction bugs identified for:
  - Card 777: semantic data doesn't match ability text (missing reveal, select, grant hearts actions)
  - Card 693: semantic data missing milling action, wrong trigger

## Frame Generation Issues to Investigate

### Variable Names (Source/Destination)
- `source_zone`: Where cards come FROM
- `dest_zone`: Where cards go TO
- Need to ensure these are consistently used across all frame generation

### Who Gets to Do the Effect (target_player)
- Need to verify `target_player` is set correctly in attr
- SELF vs OPPONENT vs BOTH
- Check if this is being set for all relevant opcodes

### Slot Generation
- `target_slot`: Where the effect applies
- `source_zone`: Where cards come from
- `dest_zone`: Where cards go to
- Need to ensure these are set correctly for each opcode

### Attr Generation
- `target_player`: Who performs the action
- `card_type`: Filter by card type
- `group_enabled`/`group_id`: Filter by group
- `zone_mask`: Filter by zone
- Need to ensure all relevant attributes are set

## Next Steps
1. Create debug output for frame generation process
2. Compare generated frames to authored frames for specific abilities
3. Identify cases where semantic data is correct but frame generation is wrong
4. Fix frame generation logic for those cases
