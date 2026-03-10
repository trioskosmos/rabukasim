# QA Tests Analysis & Expansion Plan

## Current State Assessment

### 📊 Coverage Summary
- **Total Rulings**: 237 official Q&A questions
- **Automated Tests**: 126 (53.2%)
- **Unmapped**: 111 (46.8%) - marked with ℹ️

### 1. Synthetic vs Real Cards

#### Current Approach:
**MOSTLY REAL NOW** (improvement over baseline)
- ✅ Modern tests use `load_real_db()` 
- ✅ Real card IDs from database lookups: `db.id_by_no("PL!N-bp3-005-R＋")`
- ✅ Tests use actual ability bytecode from compiled cards
- ❌ Some legacy tests still contain synthetic cards (1001, 1002) as placeholders

#### Examples of Real Card Usage:
```rust
// ✅ GOOD: Real card with real bytecode
let target_card = db.id_by_no("PL!N-bp3-005-R＋").unwrap_or(4369);
// Gets actual card from database with compiled abilities

// ✅ GOOD: Real cards from Liella group
let liella_ids = vec![360, 361, 362, 363, 364];  // Actual Liella member IDs

// ❌ OLD: Synthetic test card
let mut member_a = MemberCard::default();
member_a.card_id = 1001;  // Placeholder ID
member_a.blades = 2;
// Manually construct ability bytecode
```

### 2. Question Content Examination

#### Current Quality: **MODERATE (Surface-level)**

Tests verify **basic mechanics** but miss **question nuances**:

##### ✅ What Tests Currently Check:
1. **State Changes**: 
   - Card placement, energy deduction, hand drawing  
   - Zone movements (discard, stage, hand, live zone)
   - Buffer tracking (blades, hearts)

2. **Boolean Conditions**:
   - "Can X happen?" → Test if X is allowed/blocked
   - "Does condition Y apply?" → Check condition resolution

3. **Simple Interactions**:
   - Baton touch cost calculations
   - Live card placement restrictions
   - Turn-based slot reuse blocking

##### ❌ What Tests DON'T Deeply Examine:

1. **Timing Ambiguities**:
   - "When exactly does this ability trigger?" - Tests barely probe timing sequences
   - Multi-card simultaneous trigger ordering (Q84 test is basic)
   - Interrupt/suspension mechanics during ability resolution

2. **Edge Cases**:
   - Partial cost resolution (Q55) - test exists but basic
   - Insufficient zones (deck refresh on view exceeding cards Q85) - tests exist
   - Boundary conditions: What if exactly N cards? What if N-1? What if N+1?

3. **Question Nuances**:
   - Multi-part questions (e.g., Q65: "Can use **this specific card** + other cards?")
     - Current test only verifies "cannot mix", not the **full requirement**
   - Contextual dependencies (e.g., "if 5+ members with **different names**")
     - Tests check count, not **name uniqueness enforcement**

4. **Complex Scenarios**:
   - Cascading effects (ability A triggers → ability B changes state → A's effect now invalid?)
   - Nested conditions with multiple filters
   - Zone interaction chains (e.g., refresh during refresh)

### 3. Depth of Real Card Selection

#### Current Limitations:

1. **Limited Card Type Coverage**:
   - Tests focus on a few frequently-mentioned cards
   - Example: "PL!N-bp3-005-R＋" appears in Q160, Q161, Q162 - good!
   - But many other cards in Q&A are ignored

2. **Ability Bytecode Under-Exploration**:
   - Tests don't verify bytecode **parsing** matches ability text
   - No comparison between: Card ability text → Bytecode → Test behavior
   - Missing: Does the compiled bytecode actually implement the card as described?

3. **Data Inconsistencies Not Tested**:
   - What if card database has wrong group membership?
   - What if bytecode encoding is wrong?
   - Tests assume DB accuracy, don't validate it

---

## 🎯 Recommendations for Continuation

### Phase 1: Deepen Existing Tests (Priority: HIGH)

#### 1.1 Add Edge Case Variants
For each mapped rule, create 3 variants:

```rust
// EXAMPLE: Q70 (Cannot place member same turn)
#[test]
fn test_q70_cannot_place_same_turn() { /* baseline */ }

#[test]
fn test_q70_variant_effect_triggered() {
    // Someone uses effect to place member same turn
    // → Should also be blocked per Q70
}

#[test]
fn test_q70_boundary_turn_boundary() {
    // Verify behavior changes when it becomes next turn
    // Place member turn 1 slot 0 → Try next turn → Should work
}

#[test]
fn test_q70_all_three_slots() {
    // Fill all 3 slots same turn
    // Then attempt baton touch on each → All should fail
}
```

#### 1.2 Add Question Content Verification
For each test, explicitly validate **question text interpretation**:

```rust
#[test]
fn test_q65_triple_name_card_mixing_interpretation() {
    // Q65 Original: "「上原歩夢&澁谷かのん&日野下花帆」を1枚と
    //               （3人のいずれの名前も持たない）任意のカードを2枚
    //               の組み合わせでコストを支払うことはできますか？"
    // Expected: NO - Cannot mix card that has **all 3 names** with other cards
    
    let db = load_real_db();
    let mut state = create_test_state();
    
    // Get exact card specified in Q65
    let triple_card = db.id_by_no("LL-bp1-001")  // Exact number from Q&A
        .or_else(|| db.card_no_to_id.get("LL-bp1-001-R＋").copied())
        .or_else(|| db.card_no_to_id.get("LL-bp1-001-P").copied())
        .expect("LL-bp1-001 not in database");
    
    let card_other = 3001;  // Some card NOT Ayumu/Kanon/Kaho
    
    // Verify: Can use **3x same name** (Q69 allows this)
    // Verify: CANNOT use triple-card + other-card combo (Q65 forbids this)
    state.players[0].hand = vec![triple_card, card_other, card_other].into();
    
    // Compare with Q69 allowance
    // Assert Q65 stricter than Q69
}
```

### Phase 2: Fill Remaining 46.8% Gap (Priority: MEDIUM)

#### 2.1 Categorize Unmapped Rules
Review `qa_test_matrix.md` for ℹ️ entries and bucket into categories:

- **Category A: Core Mechanics** (Q14-Q21, Q28, Q40-Q45, Q50-Q51, Q54, Q57-Q61)
  - *Priority*: HIGH - foundational rules
  - *Effort*: MEDIUM - standard state machine tests
  
- **Category B: Complex Filters** (Q74, Q76, Q88)
  - *Priority*: MEDIUM - ability-specific
  - *Effort*: HIGH - require nuanced bytecode understanding
  
- **Category C: Meta/Outside Engine Scope** (Q1-Q12, Q20-Q22)
  - *Priority*: LOW - tournament/setup rules
  - *Skip*: Don't test these

#### 2.2 Systematic Test Generation
For each unmapped rule in Category A/B:

```bash
# Step 1: Identify card references in Q&A JSON
python tools/card_finder.py "Q[ID]"

# Step 2: Verify card exists + extract actual ability
# See bytecode, compare with question text

# Step 3: Create minimal test
# Answer "Can X happen?" or "Does state Y result from action Z?"

# Step 4: Update coverage
uv run python tools/gen_full_matrix.py
```

### Phase 3: Improve Real Card Coverage (Priority: MEDIUM)

#### 3.1 Coverage of Mentioned Cards
Audit `data/qa_data.json` for card mentions:

```bash
# Find all unique card numbers mentioned in Q&A
grep -oP 'PL!?[A-Z]+[0-9\-\+]+' data/qa_data.json | sort -u

# For each: verify we have a test that uses it
# Target: 100% of explicitly mentioned cards used in at least one test
```

#### 3.2 Ability Bytecode Validation Tests
For each card with advanced abilities, create verification tests:

```rust
#[test]
fn test_bytecode_validation_card_4369() {
    let db = load_real_db();
    let card = db.get_member(4369).expect("Card not found");
    
    // Verify bytecode encodes intended ability
    println!("Card: {}", card.name);
    println!("Ability 0: {:?}", &card.abilities[0]);
    
    // For Q160/Q161/Q162 - verify this bytecode implements:
    // "When 3+ members entered stage this turn, draw until hand=5"
    assert_eq!(card.abilities[0].bytecode[0], O_CHECK_HAS_KEYWORD);
    assert_eq!(card.abilities[0].bytecode[1], 3); // Check count >= 3
    assert_eq!(card.abilities[0].bytecode[5], O_DRAW_UNTIL);
    assert_eq!(card.abilities[0].bytecode[6], 5); // Draw until hand=5
}
```

---

## 📋 Action Items for Next Session

### Immediate (Do First):
- [ ] Categorize the 111 unmapped rules by scope
- [ ] Identify Category A rules (Core Mechanics) - ~20-30 likely
- [ ] For each Category A rule, find real card reference or use synthetic minimal test

### Short-term (Week 1):
- [ ] Create 10-15 new tests for Category A rules
- [ ] Add 2-3 edge case variants for existing tests (start with Q70, Q84)
- [ ] Run `gen_full_matrix.py` to verify coverage increase

### Medium-term (Week 2):
- [ ] Expand Category B tests (complex filters)
- [ ] Audit for card bytecode consistency (Q160/4369 focus)
- [ ] Document any inconsistencies found

### Long-term (Ongoing):
- [ ] Reach 75% coverage (177/237)
- [ ] Ensure every real card mentioned in Q&A has test usage
- [ ] Maintain bytecode accuracy audit

---

## 🔍 Quality Checklist for New Tests

When adding a test, verify:

- [ ] **Question Fidelity**: Test directly addresses the Q&A question text
- [ ] **Real Cards**: Uses `db.id_by_no()` or finds actual card from DB when possible
- [ ] **Edge Cases**: Includes at least one variant or boundary condition
- [ ] **Bytecode Accuracy**: For ability tests, bytecode matches intended behavior
- [ ] **Comments**: Includes Q&A question + expected answer + reasoning
- [ ] **Naming**: Follows pattern `test_q[ID]_[descriptor]`
- [ ] **Matrix Updated**: Script runs to update coverage ✅ indicator
- [ ] **No Synthetic Hardcoding**: Avoids magic numbers like `1001`, uses real IDs

---

## 🎓 Example: From Q&A to Test

### Original Q&A (Q82):
```
Q82: この能力の効果でライブカードの「[PL!HS-bp1-023]ド！ド！ド！」や
     「[PL!HS-PR-012]アイデンティティ」を手札に加えることはできますか？
A82: はい、できます。
```

### Test Implementation Pattern:
```rust
#[test]
fn test_q82_mirakura_live_card_search() {
    let db = load_real_db();
    
    // 1. Find exact cards mentioned
    let live_card_1 = db.id_by_no("PL!HS-bp1-023").expect("Live card 1");
    let live_card_2 = db.id_by_no("PL!HS-PR-012").expect("Live card 2");
    
    // 2. Verify they ARE live cards
    assert!(db.get_live(live_card_1).map(|c| c.is_some()).unwrap_or(false));
    assert!(db.get_live(live_card_2).map(|c| c.is_some()).unwrap_or(false));
    
    // 3. Simulate ability resolution
    // (requires: ability context showing they were added via effect)
    
    // 4. Assert: Both can be added to hand per Q82
    assert_eq!(state.players[0].hand.contains(&live_card_1), true);
    assert_eq!(state.players[0].hand.contains(&live_card_2), true);
}
```

---

## 📈 Progress Tracking

Current: 126/237 (53.2%)

**After Phase 1** (Edge cases + depth): +15-20 tests → 70-75%
**After Phase 2** (Fill gaps): +50-60 tests → 100%

Estimated timeline: 4-6 weeks at 1-2 hrs/day
