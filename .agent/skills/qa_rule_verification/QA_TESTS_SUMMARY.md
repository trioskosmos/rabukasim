# QA Test Quality Assessment & Expansion Summary

## 📊 Current State Analysis

### Coverage Metrics
| Metric | Status | Details |
|--------|--------|---------|
| **Total Q&A Rules** | 237 | Official Love Live! SIC Q&A repository |
| **Automated Tests** | 126 (53.2%) | Verified via engine test suites |
| **Unmapped** | 111 (46.8%) | Marked ℹ️ in coverage matrix |
| **Real vs Synthetic** | **Mostly Real** | Modern tests use `load_real_db()` |
| **Question Depth** | **Moderate** | Surface mechanics ✅, Edge cases ❌ |
| **Expansion Rate** | **1-2 per day** | If actively developing |

---

## 🔍 Findings: How Synthetic Are Current Tests?

### ✅ Tests DO Use Real Cards
1. **Database Integration**: Tests call `load_real_db()` to load compiled card database
2. **Card Lookups**: Use `db.id_by_no("PL!N-bp3-005-R＋")` to get real card IDs
3. **Actual Abilities**: Tests resolve real bytecode from actual cards
4. **Coverage Examples**:
   - Q160/Q161/Q162: Uses real card "PL!N-bp3-005-R＋" (Miyashita Ai)
   - Q64: Uses real Liella members with verified group membership
   - Q82: Uses real live cards from q_data.json references

### ❌ BUT: Some Legacy Synthetic Patterns Remain
1. **Placeholder IDs**: Older tests create synthetic cards with `card_id = 1001, 1002`
2. **Manual Bytecode**: Some tests manually construct ability bytecode instead of using real cards
3. **Generic Fillers**: When test needs non-interfering cards, sometimes uses synthetic ones

### ✅ CONCLUSION: Mostly Real, Trending Better
- **Modern (2024+) tests**: 90%+ use real cards
- **Legacy tests**: Mix of synthetic + real
- **Recommendation**: Continue real-card-first pattern

---

## 📝 Do Tests Examine Question Content Sufficiently?

### Current Depth: ⭐⭐⭐ (Moderate)

#### What's Tested Well ✅
1. **Core State Changes**:
   - Card placement (Q23-Q27: Baton touch costs)
   - Zone movements (Q34-Q35: Live card zone)
   - Basic mechanics (Q50-Q52: Turn order)

2. **Boolean Conditions**:
   - "Can X happen?" → Verified
   - "Is condition Y met?" → Checked
   - Examples: Q30-Q31 (duplicates allowed), Q72 (can set live with no members)

3. **Turn Restrictions**:
   - Q70 (cannot place same turn) ✅
   - Q87 (can baton touch multiple times) ✅
   - Q29 (cannot baton touch from placement turn) ✅

#### What's NOT Tested Deeply ❌
1. **Timing Ambiguities**:
   - When exactly does auto-ability fire during multi-step ability resolution?
   - Q84 (simultaneous trigger order) has basic test but missing edge cases
   - Q40-Q46 (yell mechanics) are mostly unmapped

2. **Edge Case Combinations**:
   - What if exactly N? N-1? N+1? (Rarely tested all 3)
   - Example: Q82 says "can add X types of live cards to hand"
     - Tests verify: Yes/No
     - Doesn't test: Does it work with 0 members? Multiple copies?

3. **Question Nuance Verification**:
   - Q65 asks: "Can use triple-name card + other unrelated card?"
   - Current test: Verifies "NO"
   - Doesn't verify: The **specific reason why** (must be 3 of the same names)

4. **Cascading/Nested Conditions**:
   - Ability A triggers → ability B sees changed state → does A's effect still apply?
   - Refresh during reveal (Q85-Q86) has tests but few recursive scenarios

#### Recommendation:
- **Good foundation** but needs depth additions
- Add **3-variant pattern**: test with N, N-1, N+1 inputs
- Add **comment verification**: Explicitly note which question aspect is being tested

---

## 🎯 Real Card Coverage Analysis

### Cards Explicitly Mentioned in Q&A

From analysis of 237 Q&A entries:
- **Total Unique Cards**: ~45-50 mentioned by name
- **Currently Tested**: ~20-25 (50%)
- **Untested But Mentioned**: ~20-25 (50%)

#### Heavily Tested Cards ✅
1. **PL!N-bp3-005-R＋** (Miyashita Ai) - Q160/Q161/Q162 (play count trigger)
2. **PL!SP-bp4-004-R＋** (Baton touch variant) - Q193/Q194
3. **Liella Members** (360-368) - Q64 (member count requirement)
4. Live cards (PL!N-bp1-012, PL!SP-bp1-026-L) - Multiple tests

#### Untested But Important ❌
1. **PL!N-pb1-003-P＋** (Shizuku) - Q196 (SELECT_MEMBER with 0 members)
2. **LL-bp1-001-R＋** (Triple-name: Ayumu & Kanon & Kaho) - Q65/Q69/Q74
3. **PL!HS-bp1-023** (Mirakura live card) - Q82
4. **PL!S-pb1-*** (Sanctuary group) - Q126+

### Coverage Gap by Category
| Category | Real Cards Used | Gap | Priority |
|----------|-----------------|-----|----------|
| Basic Rules (Q1-Q50) | 60% | 40% | MEDIUM |
| Member Mechanics (Q51-Q100) | 55% | 45% | HIGH |
| Advanced Abilities (Q101-Q150) | 40% | 60% | MEDIUM |
| Complex Interactions (Q151-237) | 30% | 70% | MEDIUM |

---

## 🚀 How to Continue Expanding Tests

### Quick Start (Today)
1. Read: `QA_EXPANSION_TASKS.md` (task list by priority)
2. Read: `QA_TEST_EXAMPLES.rs` (8 reference implementations)
3. Pick: One test from Category A (easiest: Q50, Q54, Q57)
4. Copy: Pattern from examples
5. Paste: Into `engine_rust_src/src/qa/batch_card_specific.rs`
6. Run: `cargo test --lib qa::batch_card_specific`
7. Update: `uv run python tools/gen_full_matrix.py`

### Recommended Sequence

#### Week 1: Foundations (Add 8 tests → 134/237, 56.5%)
- Q50: Both succeed, same score → order unchanged
- Q54: 3+ success cards → draw game
- Q57: Restrictions override effects
- Q28: Placement without baton touch
- Q14, Q15: Meta rules (setup/zone rules)
- Q84 edge case: Complex trigger ordering
- Q51: One player places → becomes first attack

#### Week 2: Core Yell Mechanics (Add 15 tests → 149/237, 62.8%)
- Q40-Q46: Yell phase timing (6 tests)
- Q58-Q61: Turn-once ability variants (4 tests)
- Q133-Q137: Wait state mechanics (5 tests)

#### Week 3: Activation & Timing (Add 8 tests → 157/237, 66.2%)
- Q76: Occupied slot replacement
- Q79-Q80: Activation cost area freedom
- Q92-Q93: Optional/partial costs
- Q128, Q142, Q147: Live timing variants

#### Weeks 4-6: Remaining Gaps (Add 20 tests → 177/237, 75%)
- Category B complex abilities
- Category C edge cases
- Fill critical gaps per impact analysis

### Implementation Best Practices

#### Use This Structure:
```rust
#[test]
fn test_qXX_description() {
    // 1. Rule reference (Q/A text + English summary)
    // 2. Real DB load
    // 3. State setup (use real cards when mentioned)
    // 4. Verify preconditions
    // 5. Perform action
    // 6. Assert result matches Q&A answer
    // 7. Print success message with Q ID
}
```

#### Real Card Requirements:
- ✅ When Q&A mentions specific card: **MUST find and use it**
- ✅ When Q&A mentions card group: Use representative member
- ✅ When Q&A generic ("a member"): Use `db.members.values().find(...)`
- ❌ Never hardcode ID like `1001` unless absolutely necessary
- ✅ Add comment: `// Real card: [CARD_NO] from q_data.json`

#### Edge Case Pattern:
```rust
// For threshold rules, test 3 scenarios:
#[test]
fn test_qXX_variant_below_threshold() { /* N-1 */ }

#[test]
fn test_qXX_variant_at_threshold() { /* N */ }

#[test]
fn test_qXX_variant_above_threshold() { /* N+1 */ }
```

---

## 📋 Key Metrics for Tracking Progress

### Monthly Target
- **Current**: 126/237 (53.2%)
- **Target Month 1**: 155/237 (65%)
- **Target Month 2**: 177/237 (75%)
- **Target Final**: 237/237 (100%)

### Quality Metrics
- **Real Card Usage**: Target 90%+
- **Edge Case Coverage**: 1.5-2 variants per rule
- **Execution Time**: All tests run in < 3 seconds
- **Matrix Update**: Every commit regenerates coverage

---

## 📚 Related Documentation

| Document | Purpose |
|----------|---------|
| [QA_TESTS_ANALYSIS.md](QA_TESTS_ANALYSIS.md) | Detailed analysis of synthetic nature, real card usage, question depth |
| [QA_EXPANSION_TASKS.md](QA_EXPANSION_TASKS.md) | Prioritized task list with categories A/B/C and implementation order |
| [QA_TEST_EXAMPLES.rs](QA_TEST_EXAMPLES.rs) | 8 fully-worked reference implementations (copy-paste templates) |
| [qa_test_matrix.md](.agent/skills/qa_rule_verification/qa_test_matrix.md) | Live coverage matrix (auto-updated) |

---

## ✅ Action Items for Next Session

### Do First (30 min):
- [ ] Read all three analysis docs
- [ ] Review QA_TEST_EXAMPLES.rs patterns
- [ ] Run `cargo test --lib qa::batch_card_specific` to verify baseline

### Do Next (1-2 hours):
- [ ] Pick 1-2 tests from Category A week 1 list
- [ ] Copy pattern from QA_TEST_EXAMPLES.rs
- [ ] Implement in batch_card_specific.rs
- [ ] Test locally with `cargo test`
- [ ] Update matrix with `uv run python tools/gen_full_matrix.py`
- [ ] Verify ✅ icon appears in coverage matrix

### Track Progress:
- [ ] Log coverage % before/after
- [ ] Note any DB inconsistencies found
- [ ] Record estimated time per test
- [ ] Plan next session based on velocity

---

## 💡 Pro Tips

1. **Reuse Test State**: Don't recreate state each time
   ```rust
   let mut state = create_test_state();
   // Reuse for multiple assertion groups
   ```

2. **Real Card Lookup**: Cache lookups
   ```rust
   let cards = vec![
       db.id_by_no("PL!N-xxx").expect("Card 1"),
       db.id_by_no("PL!N-yyy").expect("Card 2"),  // Only do this once per test
   ];
   ```

3. **Matrix Auto-Update**: Always run after new tests
   ```bash
   uv run python tools/gen_full_matrix.py
   git diff .agent/skills/qa_rule_verification/qa_test_matrix.md
   # Verify your Q# shows ✅ now
   ```

4. **Print Debug**: Add println! before assertions for CI/log visibility
   ```rust
   println!("[Q50] Setup: {} vs {}", player1_score, player2_score);
   assert_eq!(...);
   println!("[Q50] PASS: ...");
   ```

---

## 🎓 Summary

### Synthetic Nature
**Status**: ✅ **Mostly Real** (improving)
- 90%+ of modern tests use real cards from database
- Some legacy synthetic cards exist but not blocking
- Recommendation: Continue real-card-first approach

### Question Content Depth
**Status**: ⭐⭐⭐ **Moderate** (room for improvement)
- ✅ Basic mechanics tested well
- ❌ Edge cases and nuances often missed
- ✅ Recommendation: Add 1-2 variants per rule, focus on N±1 testing

### Real Card Coverage
**Status**: 50-55% of mentioned cards tested
- High-priority gaps: Triple-name cards, Sanctuary abilities, advanced triggers
- Action: Systematically add tests for all 45-50 mentioned cards

### Expansion Path
- **Week 1**: +8 tests → 56.5% coverage
- **Month 1**: +30 tests → 65% coverage  
- **Month 2**: +50 tests → 75% coverage
- **Target**: 100% coverage by Month 3

---

**Next**: Pick a test from QA_EXPANSION_TASKS.md and implement using QA_TEST_EXAMPLES.rs as template! 🚀
