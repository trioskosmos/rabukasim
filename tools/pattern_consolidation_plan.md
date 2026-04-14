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
**Priority: HIGH** - Variables must capture atomic components based on clause structure.

**Proper Understanding of Non-Atomic Variables:**
The issue is NOT about filtering "filler words" - demonstratives and player references serve important purposes:
- "このメンバー" (this member) - specifies which entity, not filler
- "自分のステージ" (my stage) - necessary for targeting
- "ライブ終了時まで" (until end of live) - timing condition

**Real Problem:** Patterns capture multi-component phrases in single variables:
- "{{toujyou.png|登場}}自分" mixes trigger + player reference
- "センターにいるメンバー" mixes location + state + entity
- "コスト11以上のカード" mixes condition + entity type

**Atomic Variable Rules (Clause-Based Decomposition):**
- **Separate components by clause structure:**
  - Demonstratives: "この" + "メンバー" (separate specifier from entity)
  - Player refs: "自分" + "ステージ" (separate player from location)
  - Timing: "ライブ終了時" + "まで" (separate timing from duration marker)
  - Conditions: "コスト11以上" + "カード" (separate condition from entity)

- **Capture atomic game mechanic components:**
  - Entity types: "メンバー", "カード", "ハート", "ブレード"
  - Zones: "ステージ", "控え室", "手札", "エネルギー"
  - States: "アクティブ", "ウェイト", "表", "裏"
  - Actions: "置く", "得る", "引く", "公開する"
  - Numbers: pure numeric values

**Implementation approach:**
- Redesign pattern regex to capture atomic components separately
- Update templates to recombine components in proper clause structure
- Ensure each variable represents a single atomic game mechanic component

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
