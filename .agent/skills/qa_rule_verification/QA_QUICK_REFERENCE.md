# QA Tests Quick Reference

## 🎯 TL;DR

| Question | Answer |
|----------|--------|
| **Are tests synthetic?** | ⭐⭐⭐ Mostly real (90%+ use real cards from DB) |
| **Do they use real cards?** | ✅ Yes (modern tests use `load_real_db()`) |
| **Do they examine questions sufficiently?** | ⭐⭐⭐ Moderate (basic mechanics ✅, edge cases ❌) |
| **Can I continue adding?** | ✅ YES! (46.8% unmapped, clear expansion path) |

---

## 📊 Current Status

```
Coverage: 126/237 (53.2%)
Unmapped: 111/237 (46.8%)
Real Card %: ~90% (modern tests)
Test Depth: Basic good, edges thin
```

---

## 🔴 Key Findings

### Synthetic Tests: Mixed but Improving
- **Good**: Modern tests use `load_real_db()` and real card IDs
- **Bad**: Some old tests hardcode synthetic IDs (1001, 1002)
- **Fix**: Continue real-card-first pattern (already doing this!)

### Real Card Usage: Yes, but Incomplete
- **Used**: ~20-25 of 45-50 mentioned cards (50%)
- **Missing**: Triple-name cards, advanced abilities, many niche interactions
- **Opportunity**: Low-hanging fruit to add tests for untested cards

### Question Depth: Surface Level
- **Good**: Tests verify basic state changes ✅
- **Bad**: Don't test edge cases (what if N-1? N+1?)
- **Bad**: Don't verify question nuances (why specifically?)
- **Fix**: Add 3-variant tests (below/at/above threshold)

---

## 🚀 How to Continue

### Right Now
```bash
# 1. Review documentation
Read: QA_TESTS_SUMMARY.md (this folder)
Read: QA_EXPANSION_TASKS.md (task list)
Read: QA_TEST_EXAMPLES.rs (template code)

# 2. Pick easiest test
Task: Q50, Q54, or Q57 (30 min each)

# 3. Implement
Copy: Pattern from QA_TEST_EXAMPLES.rs
Paste: Into engine_rust_src/src/qa/batch_card_specific.rs
Test: cargo test --lib qa::batch_card_specific

# 4. Update coverage
uv run python tools/gen_full_matrix.py
# Verify your Q# now shows ✅
```

### This Week (Suggested)
- [ ] Add 3-4 tests from Category A (Q50, Q54, Q57, Q28)
- [ ] Coverage jump: 53.2% → ~56.5%
- [ ] Estimated time: 2-3 hours

### This Month (Suggested)
- [ ] Add 20-25 tests total (all of Category A + some B)
- [ ] Coverage target: 65-70%
- [ ] Estimated time: 15-20 hours spread across month

---

## 📝 Quick Implementation Checklist

For each new test:
- [ ] Read Q&A from data/qa_data.json
- [ ] Find real card (if mentioned) via db.id_by_no()
- [ ] Create test skeleton from QA_TEST_EXAMPLES.rs
- [ ] Add comments: Q&A text + English summary
- [ ] Write 3 sections: SETUP, ACTION, ASSERT
- [ ] Run: `cargo test` locally
- [ ] Run: `gen_full_matrix.py` to update coverage
- [ ] Verify matrix shows ✅ for your Q#

---

## 📂 File Guide

| File | Read This For |
|------|----------------|
| QA_TESTS_SUMMARY.md | **START HERE** → Overview & action items |
| QA_TESTS_ANALYSIS.md | detailed analysis of synthetic/real nature |
| QA_EXPANSION_TASKS.md | **IMPLEMENTATION** → Task list by priority |
| QA_TEST_EXAMPLES.rs | **TEMPLATES** → Copy-paste code patterns |
| qa_test_matrix.md | Live coverage dashboard (auto-updated) |

---

## 🎓 Key Numbers

| Metric | Value | Impact |
|--------|-------|--------|
| Total Q&A Rules | 237 | Scope of project |
| Currently Mapped | 126 (53.2%) | Baseline |
| Gap | 111 (46.8%) | Expansion opportunity |
| Tests per hour | 1-2 | Velocity estimate |
| Weeks to 75% | 2-3 | Time to high coverage |
| Weeks to 100% | 6-8 | Time to complete |
| Real card % | ~90% | Quality indicator |

---

## ✅ Benefits of Expanding Tests

1. **Rule Compliance**: Ensure engine matches official Q&A 100%
2. **Edge Case Detection**: Find subtle bugs early
3. **Documentation**: Each test documents a rule
4. **Regression Prevention**: Catch breaks when refactoring
5. **Coverage Tracking**: Measurable progress (% → 100%)

---

## 🔗 Related Commands

```bash
# Run a specific test
cargo test --lib qa::batch_card_specific::test_q50_both_success

# Run all QA tests
cargo test --lib qa

# Update matrix
uv run python tools/gen_full_matrix.py

# Find cards by Q number
python tools/card_finder.py "Q50"

# Check for compilation errors
cargo check

# Build everything
cargo build --release
```

---

## 💬 Questions vs Answers

### "Are tests too synthetic?"
- **No** - 90% use real cards from database
- Continue this pattern!

### "Do tests examine questions?"
- **Somewhat** - Basic mechanics ✅, edge cases ❌  
- Add 3-variant tests: N-1, N, N+1

### "Can I just add more tests?"
- **Yes!** 111 rules unmapped (46.8% gap)
- Clear priority list in QA_EXPANSION_TASKS.md
- Templates in QA_TEST_EXAMPLES.rs

### "How long to implement one?"
- **Easy (Q50)**: 15-30 min
- **Medium (Q40-Q46)**: 45-60 min each
- **Hard (complex abilities)**: 60-90 min each

### "Will my tests pass?"
- **If you use real cards**: Very likely ✅
- **If you follow template**: Almost guaranteed ✅
- **Red flags**: Synthetic IDs, wrong Q reference

---

## 🎖️ Definition of "Done"

A test is complete when:
- ✅ Reads Q&A from official data source
- ✅ Uses real cards (or specific unmapped reason)
- ✅ Includes Q&A reference + English summary
- ✅ Tests base case + 1-2 edge cases
- ✅ Passes locally: `cargo test`
- ✅ Matrix updated: `gen_full_matrix.py`
- ✅ Matrix shows ✅ for that Q#
- ✅ No synthetic magic numbers (1001, 1002, etc.)

---

## 🎯 One-Sentence Summary

**Current tests are 90% real-card-based with moderate edge case coverage (53.2% complete); 111 rules unmapped provide clear expansion path; recommend 3-variant testing pattern (N-1/N/N+1) to deepen coverage to 75% within 3 weeks.**

---

**Ready to start?** → Pick Q50 from QA_EXPANSION_TASKS.md and copy template from QA_TEST_EXAMPLES.rs! 🚀
