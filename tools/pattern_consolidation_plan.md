# Pattern Consolidation Plan

## Current State Analysis
- **Total patterns:** 282
- **Patterns with matches:** 162 (57.4%)
- **Patterns without matches:** 120 (42.6%)
- **Coverage:** 100% of abilities

## Immediate Actions

### 1. Remove Unused Patterns (120 patterns)
**Priority: HIGH** - These patterns have zero matches and add no value.

**Examples to remove:**
- select_member_and_cost_modification
- parenthesized_formation_change_restriction
- cost_and_blade_count_comparison
- ability_resolution_trigger
- optional_energy_placement_from_member
- effect_opponent_state_change_trigger
- baton_touch_specific_card_recovery
- phase_based_trigger_on_card_discard
- placed_card_trigger_ability_activation
- original_heart_count_comparison_condition
- phase_limit_reduction
- dual_zone_card_count_condition
- distinct_cost_member_count_condition_resource_gain
- multi_condition_zone_card_presence
- specific_card_cost_reduce
- conditional_live_card_discard_draw
- zone_cost_member_condition_draw
- move_members_to_preferred_areas_optional
- member_cost_total_comparison_condition
- heart_color_comparison
- ... (100 more patterns)

**Expected impact:** Reduce pattern count from 282 to 162 patterns (42.6% reduction)

### 2. Consolidate Low-Match Patterns
**Priority: MEDIUM** - Patterns with 1-3 matches that could be merged.

**Consolidation candidates:**
- Single-match literal patterns that could use regex instead
- Similar structure patterns with minor variations
- Patterns with overlapping functionality

**Examples:**
- Multiple "live_start_*_gain" patterns could be consolidated
- Similar "trigger_energy_*" patterns could be merged
- "toujyou_deck_top_three_discard_heart_gain" variants could be unified

### 3. Atomic Variable Enhancement
**Priority: HIGH** - Variables must separate core mechanics from parameters for clause recombination.

**Purpose of Atomic Decomposition:**
- "draw member card" and "draw live card" should be recognized as same core ability
- Core mechanic: "draw card" (atomic)
- Parameters: card type (member/live), zone, player, etc. (combinable)
- Enables combining abilities with different clauses

**Current Problem:**
Patterns capture specific combinations as separate patterns:
- "draw member card" → one pattern
- "draw live card" → another pattern
- Result: seen as radically different abilities when they're the same core mechanic

**Atomic Variable Rules (Core Mechanics vs Parameters):**
- **Core mechanics (atomic):**
  - Actions: "draw", "place", "gain", "lose", "reveal"
  - Conditions: "if", "when", "while"
  - Operators: "add", "subtract", "multiply"

- **Parameters (combinable):**
  - Card types: "member", "live", "energy"
  - Zones: "stage", "waiting room", "hand", "energy zone"
  - Players: "self", "opponent"
  - Numbers: quantities
  - Conditions: cost, group, state

**Implementation approach:**
- Consolidate patterns by core mechanic
- Make card types, zones, players into parameter variables
- Create unified patterns like "draw [CARD_TYPE] from [ZONE]"
- Enable clause recombination through atomic parameter separation

## Implementation Order

1. **Remove 120 unused patterns** (immediate - safe removal)
2. **Test coverage remains 100%** after removal
3. **Consolidate low-match patterns** (requires careful testing)
4. **Implement atomic variable filtering** (add post-processing)
5. **Re-run full analysis** to verify improvements

## Expected Results

**Pattern Count Reduction:**
- Initial: 282 patterns
- After removing unused: 162 patterns (42.6% reduction)
- After consolidation: ~120-140 patterns (50-57% total reduction)

**Variable Quality:**
- Current: Mixed atomic/non-atomic variables
- Target: 100% atomic game mechanic words only

**Coverage:**
- Maintain 100% ability coverage throughout consolidation
