# High-Priority QA Test Expansion Queue

## 📊 Quick Stats
- **Unmapped ℹ️ Rules**: 50+ found in grep
- **Total Unmapped**: ~111 (to reach 100% of 237)
- **Current Coverage**: 126/237 (53.2%)
- **Target Next**: +20-30 tests → 70-75%

---

## 🎯 Category A: Core Mechanics (HIGHEST PRIORITY)

These rules form the **foundation** of the engine. Implement these first.

### Turn/Phase Mechanics (Q14-Q22):
- [ ] **Q14** - Shuffle randomization (meta-rule)
- [ ] **Q15** - Energy zone face orientation
- [ ] **Q28** - Placement without baton touch (redirects to special logic)

### Live/Yell Mechanics (Q40-Q46):
- [ ] **Q40** - Cannot skip yell checks mid-resolution
- [ ] **Q41** - Yell card timing (when moved to discard)
- [ ] **Q42** - Blade heart effects timing during yell
- [ ] **Q43** - Draw icon resolution during yell
- [ ] **Q44** - Score icon resolution during yell
- [ ] **Q45** - ALL Blade (wildcard) resolution rules

### Turn Order Changes (Q50-Q54):
- [ ] **Q50** - Both players succeed → order stays same
- [ ] **Q51** - One player can't place → other becomes leader
- [ ] **Q54** - 3+ cards in success zone → draw game

### Effect Resolution (Q57-Q61):
- [ ] **Q57** - Restrictions override effects
- [ ] **Q58** - Same card ×2 on stage = 2 separate turn-once uses
- [ ] **Q59** - Card that moves = new card (resets turn-once)
- [ ] **Q60** - Forced non-optional vs optional abilities
- [ ] **Q61** - Can defer turn-once ability to later timing

### Summary: ~15-18 tests to implement

---

## 🎓 Category B: Complex Ability Interactions (MEDIUM PRIORITY)

These require deep bytecode verification and card-specific scenarios.

### Multi-Name Card Rules (Q65, Q69, Q74):
- [x] **Q65** ✅ - Cannot mix triple-name card with other cards
- [x] **Q69** ✅ - Can use any combination of the 3 names
- [ ] **Q74** - Multi-name card referenced as one of its names

### Center/Formation (Q143-Q144):
- [ ] **Q143** - Center slot enables special abilities
- [ ] **Q144** - "Up to X" allows choosing fewer

### Activated Ability Restrictions (Q76, Q79-Q80, Q95):
- [ ] **Q76** - Can place on occupied slot (if not blocked by same-turn rule)
- [ ] **Q79** - Area becomes available after activation cost removes card
- [ ] **Q80** - Effect can place after activation cost removes blocking card
- [ ] **Q95** - Resurrection ability has specific card restriction

### Simultaneous Trigger Order (Q84):
- [ ] Already exists but could expand edge cases

### Member State Effects:
- [ ] **Q133** - Wait state members don't add to yell count
- [ ] **Q134** - Can baton touch wait state (returns to active)
- [ ] **Q135** - Wait state → active on your active phase
- [ ] **Q136** - Wait state preserved during area move
- [ ] **Q137** - Cannot "set to wait" if already waiting
- [ ] **Q138** - Can't use energy under members as cost

### Live Success Conditions:
- [ ] **Q128** - Draw icon converts timing (↑ after card draw)
- [ ] **Q132** - Live success ability fires even if you're first
- [ ] **Q142** - Excess heart definition (winning threshold)
- [ ] **Q147** - 0-score card still places if success

### Summary: ~25-30 tests to implement

---

## 📋 Category C: Edge Cases & Boundary Conditions (LOWER PRIORITY)

These are specific corner scenarios. Implement after A + B.

### Deck/Refresh Edge Cases (Q85-Q86):
- [x] **Q85** ✅ - Refresh during "view N cards" if deck < N
- [x] **Q86** ✅ - No refresh if deck == N cards being viewed

### Specific Card Rules (Q88-Q99):
- [ ] **Q88** - Cannot arbitrarily manipulate state (meta)
- [ ] **Q92** - "Optional" cost (can choose not to pay)
- [ ] **Q93** - Partial resolution when target count insufficient
- [ ] **Q98** - Moved and entered same turn count as 1, not 2
- [ ] **Q99** - Entered + moved same turn still counts as 1

### Card-Specific Abilities (Q126-Q155):
- [ ] Multiple card-specific rules requiring real card usage
- [ ] **Examples**: Q126 (area move = no discard move), Q128 (timing), Q131 (self-only live start)

### Summary: ~20+ tests

---

## 🚀 Recommended Implementation Order

### Week 1 (Highest ROI):
1. **Q28** - Placement without baton touch (extend Q23-Q27)
2. **Q50-Q51-Q54** - Turn order changes (3 tests, core rule)
3. **Q57** - Restrictions override
4. **Q132** - Live success timing
5. **Q14-Q15** - Meta/zone rules (simple, foundational)

**Expected**: +8 tests → 134/237 (56.5%)

### Week 2:
1. **Q40-Q46** - Yell mechanics (6 tests, core)
2. **Q58-Q61** - Turn-once variants (4 tests)
3. **Q133-Q137** - Wait state (5 tests)

**Expected**: +15 tests → 149/237 (62.8%)

### Week 3:
1. **Q76, Q79-Q80** - Area/activation timing (3 tests)
2. **Q92-Q93** - Optional/partial costs (2 tests)
3. **Q128, Q142, Q147** - Live timing edge cases (3 tests)

**Expected**: +8 tests → 157/237 (66.2%)

### Continue:
- Fill remaining Category B/C
- Target: 75% (177/237) in 4 weeks

---

## 📝 Test Template for New Rules

Use this template for each new test:

```rust
#[test]
fn test_qXX_brief_description() {
    // =========================================================================
    // RULE REFERENCE
    // =========================================================================
    // QXX Question: Japanese question text (from qa_data.json)
    // QXX Answer:   Japanese answer text
    // 
    // English Summary: What this rule means in plain English
    //
    // Related Q&A: QX, QY (if any companion rules)
    // =========================================================================
    
    let db = load_real_db();
    let mut state = create_test_state();
    state.debug.debug_mode = true;
    state.ui.silent = true;
    
    // SETUP: Create game state matching the Q&A scenario
    // (use real cards where mentioned, synthetic only for filler)
    
    // VERIFY INITIAL: Assert preconditions are correct
    
    // ACTION: Perform the action described in the Q&A
    
    // ASSERT RESULT: Verify outcome matches Q&A answer
    
    println!("[QXX] PASS: Behavior verified against official ruling");
}
```

---

## ✅ Verification Checklist

Before marking test as complete:

- [ ] Question text matches what's in `qa_data.json`
- [ ] Test uses real card IDs when specific cards mentioned
- [ ] Comments include original Japanese Q&A + English summary
- [ ] Tests pass with `cargo test qa::batch_card_specific::test_qXX`
- [ ] No synthetic magic numbers like `1001` (use real IDs or symbolic names)
- [ ] Update matrix: `uv run python tools/gen_full_matrix.py`
- [ ] Verify ✅ icon appears in matrix for that Q
- [ ] Coverage % increases (expected +0.4% per test)

---

## 📌 Notes

### Why Prioritize This Way?

1. **Category A first** because they're tested via other rules - early discovery of bugs
2. **Within A**: Core mechanics before edge cases
3. **Category B next** because it's higher value (complex scenarios) but needs A stable
4. **Category C last** since it's rare edge cases

### Real Card Strategy

For rules without specific card mentions:
- Use **filler cards**: Any member with `abilities.is_empty()` to avoid interference
- Use **signature members**: 虹ヶ咲, Liella, Aqours representatives for group filters
- Use **data cards**: Real cards from test coverage analysis

For rules WITH specific card mentions:
- MUST use exact card number from Q&A
- Search `data/qa_data.json` for the card_no
- If not in database, mark as **POTENTIAL DATA BUG** and report

---

## 🔗 Related Resources

- Current test file: `engine_rust_src/src/qa/batch_card_specific.rs`
- Matrix: `.agent/skills/qa_rule_verification/qa_test_matrix.md`
- Q&A data: `data/qa_data.json`
- Cards DB: `data/cards_compiled.json`
- Tools: `tools/card_finder.py` (find cards by Q number)

