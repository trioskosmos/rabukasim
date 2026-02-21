# Lovecasim: Technical Roadmap (Post-Audit)

Following the logic audit and idempotency fix, we are rebuilding the engine foundations for maximum stability.

## 🏁 Phase 1: Engine Verification
- [ ] **Compilation Check**: Ensure Rust engine and Python bindings build correctly.
- [ ] **Basic Playability**: Verify the game loop still runs via `play_vs_ai.py`.

## 🧪 Phase 2: "New Testament" Test Suite
- [ ] **Integration Baseline**: Create `tests/test_game_flow.py` (Complete loop).
- [ ] **Idempotency Proof**: Create `tests/test_performance_idempotency.py` to verify the fix for redundant triggers.
- [ ] **Opcode Matrix**: Test complex opcodes in isolation (Look & Choose, Select Mode).

## 💎 Phase 3: Action ID Unification
- [ ] **Refactor Response IDs**: Move all interactive choice IDs (Select Mode, Generic List) into a unified, collision-free range (e.g., `2000+` or dedicated `550-999` block).
- [ ] **Update Frontend**: Ensure `main.js` and `ability_translator.js` reflect the unified ID mapping.

## 🚀 Phase 4: Meta Rule Completion
- [ ] Implement `heart_rule` (Blades as Hearts).
- [ ] Implement `YELL_AGAIN` and `RE_CHEER` logic.
- [ ] Implement `PREVENT_SET_PILE` (Prevents moving to success pile).

---
*Roadmap initiated on 2026-02-07*
