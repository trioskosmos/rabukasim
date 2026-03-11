# Card-Specific QA Test Prioritization Matrix

**Generated**: 2026-03-11  
**Purpose**: Identify the HIGHEST-IMPACT unmapped card-specific QA tests for engineimplementation

---

## Critical Priority: Card-Specific Tests Requiring Real Cards

### Tier 1: Foundational + Multiple Real Card References (HIGHEST IMPACT)

| QA # | Title | Cards Referenced | Engine Impact | Difficulty | Est. Time |
|------|-------|------------------|---------------|-----------|-----------|
| **Q62/Q65/Q69/Q90** | Triple-name card validation | `LL-bp1-001-R+` (3 names) | Name matching, group resolution | High | 60-90 min |
| **Q168-Q170** | Mutual effect placement | `PL!-pb1-018-R` (Nico) | Dual placement, slot blocking | High | 90-120 min |
| **Q174** | Surplus heart color tracking | `PL!N-bp3-027-L` | Color validation | Medium | 60 min |
| **Q175** | Unit name filtering | Multiple Liella! members | Unit vs group distinction | Medium | 60 min |
| **Q183** | Cost target isolation | Multiple stage members | Selection boundary | Medium | 45 min |

**Rationale**: These combine real card mechanics with rule interactions that spawn multiple test variants

---

### Tier 2: Complex Ability Chains (HIGH IMPACT)

| QA # | Title | Cards Referenced | Engine Impact | Difficulty | Est. Time |
|------|-------|------------------|---------------|-----------|-----------|
| **Q75-Q80** | Activation cost + zone effects | Various cards with costs | Cost validation, effect chaining | High | 120-150 min |
| **Q108** | Ability nesting (source card context) | `PL!SP-bp1-002-R` | Ability source tracking | High | 90 min |
| **Q141** | Under-member energy mechanics | Any card w/ energy placement | State stacking | Medium | 75 min |
| **Q176-Q179** | Conditional activation (turn state) | `PL!-pb1-013` | Activation guard checks | Medium | 60-90 min |
| **Q200-Q202** | Nested ability resolution | Multiple cards w/ play abilities | Recursion depth | Hard | 120 min |

**Rationale**: These establish foundational engine patterns that enable 10+ follow-on tests

---

### Tier 3: Group/Name Mechanics (MEDIUM-HIGH IMPACT)

| QA # | Title | Cards Referenced | Engine Impact | Difficulty | Est. Time |
|------|-------|------------------|---------------|-----------|-----------|
| **Q81** | Member name counting w/ multi-name | `LL-bp2-001-R+` variations | Name enumeration | Medium | 60 min |
| **Q204-Q213** | Complex group conditions | Aqours, Liella!, 5yncri5e! members | Group filtering | Medium | 90-120 min |
| **Q216-Q224** | Heart requirements (multi-member) | Various heart-bearing members | Aggregate conditions | Medium | 75 min |

**Rationale**: Once group validation works, many tests become simple variations

---

## Quick Wins: Moderate Impact, Lower Effort

| QA # | Title | Cards | Impact | Time | Notes |
|------|-------|-------|--------|------|-------|
| Q91 | No-live condition (no trigger) | Cards w/ live-start abilities | Rule boundary | 30 min | Setup only |
| Q125 | Cannot-place restriction | Restricted live cards | Placement guard | 45 min | Lookup-based |
| Q145 | Optional cost empty zones | Cards w/ optional costs | Partial resolution | 45 min | Already patterns exist |
| Q160-Q162 ✅ | Play count tracker | **ALREADY DONE** | Foundational | - | Template reuseble |
| Q197 | Baton-touch ability trigger | Member w/ special conditions | Boundary check | 45 min | State comparison |
| Q220 | Movement invalidation | Aqours members | Event invalidation | 45 min | Familiar pattern |
| Q230-Q231 | Zero-equality edge cases | Any live cards | Scorecard edge | 45 min | Simple logic |
| Q234 | Kinako deck cost check | `PL!SP-bp5-005-R` | Deck state validation | 50 min | Counter check |
| Q235-Q237 | Multi-live simultaneous | Multiple cards | Simultaneous resolution | 60 min | Familiar pattern |

---

## Batch Implementation Plan

### Batch A: Foundation (2-3 hours)
```
Priority: Q160-Q162 (✅ DONE), Q125, Q145, Q197, Q230-Q231
Result: 5-8 tests, unlocks 1-2 follow-ons
```

### Batch B: Real Card Mastery (4-5 hours)

```
Priority: Q62/Q65/Q69/Q90 (multi-name), Q81 (member count)
Result: 6-8 tests, establishes name-matching patterns
```

### Batch C: Complex Chains (5-6 hours)
```
Priority: Q75-Q80 (costs), Q108 (nesting), Q200-Q202 (recursion)
Result: 8-10 tests, enables 15+ follow-on tests
```

### Batch D: Groups & Aggregates (3-4 hours)
```
Priority: Q175 (units), Q204-Q213 (groups), Q216-Q224 (hearts)
Result: 10-12 tests, high reusability
```

**Total Estimated Effort**: 14-18 hours → **+40-50 tests implemented** (60-85% coverage achievable)

---

## Test Dependency Graph

```
Q62/Q65/Q69/Q90 (Multi-name)
    ↓
Q81 (Member counting)
    ↓
Q175 (Unit filtering)
    ↓
Q204-Q213 (Group conditions)

Q160-Q162 (Play count) ✅
    ↓
Q197 (Baton identity)
    ↓
Q200-Q202 (Nested abilities)

Q108 (Ability source)
    ↓
Q75-Q80 (Cost chains)
    ↓
Q141 (Energy stacking)
    ↓
Q176-Q179 (Conditional guards)
```

---

## Known Real Cards (Lookup Reference)

### Triple-Name Cards
```
LL-bp1-001-R+   上原歩夢&澁谷かのん&日野下花帆       (Liella! core trio)
LL-bp2-001-R+   渡辺 曜&鬼塚夏美&大沢瑠璃乃          (Aqours subunit)
LL-bp3-001-R+   園田海未&津島善子&天王寺璃奈          (Saint Snow variant)
```

### Major Ability Cards
```
PL!-pb1-018-R   矢澤にこ                              (Nico mutual effect)
PL!S-bp3-001-R+ ウィーン・マルガレーテ                (Vienna yell-down)
PL!N-bp3-001-R+ ???                                   (Energy under-member)
```

### Group-Specific Cards
```
PL!SP-bp1-001-R 澁谷かのん (5yncri5e!)               (Group marker)
PL!HS-bp1-001-R ??? (Hello Happy World)              (Group marker)
```

---

## Testing Vocabulary

- **Real Card Lookup**: Use `db.id_by_no("CARD_NO")`
- **Engine Call Signature**: Direct method invocation (e.g., `state.do_live_result()`)
- **High-Fidelity**: Tests calling actual engine, not just state mutations
- **Fidelity Score**: # assertions + # engine calls + # real cards = points
- **Quick Win**: Fidelity score >= 2, implementation time <= 1 hour

---

## Success Metrics

- ✅ **Each test**: >= 2 fidelity points
- ✅ **Batch**: Unlock 2+ tests vs. 1 test ratio
- ✅ **Coverage**: 60% → 75% → 90%+ with each batch
- ✅ **Velocity**: 1-2 tests per hour (quick wins), 20-30 min per test (average)

---

## Integration Steps

1. **Choose Tier 1 card** (e.g., Q62-Q90 multi-name)
2. **Create test file** or add to `batch_card_specific.rs`
3. **Implement 3 parallel tests** (positive, negative, edge case)
4. **Run**: `cargo test --lib qa::batch_card_specific::test_q*`
5. **Update matrix**: `python tools/gen_full_matrix.py`
6. **Measure**: fidelity score should be 4+

---

## References
- [qa_test_matrix.md](qa_test_matrix.md) - Full Q&A list with status
- [qa_card_specific_batch_tests.rs](../../engine_rust_src/src/qa/qa_card_specific_batch_tests.rs) - Benchmark tests (13 done)
- [SKILL.md](SKILL.md) - Full testing workflow
