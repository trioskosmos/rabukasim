---
description: Unified workflow for mass QA audits and official rule verification.
---

# QA Process Workflow

Use this workflow for large-scale quality assurance and ensuring adherence to official rules.

## Phase 1: Mass Audits
1. **Identify Gaps**: `uv run python tools/analysis/analyze_translation_coverage.py`.
2. **Semantic Mass Audit**: `cd engine_rust_src && cargo test test_semantic_mass_verification -- --nocapture`.
3. **Crash Triage**: `cargo test crash_triage -- --nocapture`.

## Phase 2: Official Rule Verification (Q&A)
1. **Data Update**: `uv run python tools/qa_scraper.py`.
2. **Matrix Review**: Open [.agent/skills/qa_rule_verification/qa_test_matrix.md](file:///c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/.agent/skills/qa_rule_verification/qa_test_matrix.md).
3. **Implementation**:
   - Pick a pending rule (e.g., Q195).
   - Implement test in `qa_verification_tests.rs`.
   - Use `load_real_db()` and real IDs.

## Phase 3: Telemetry & Rigor
1. **Filter Telemetry**: Identify opcodes relying solely on dry runs.
2. **Assess Rigor**: Ensure critical opcodes have **Level 3** (Interaction Cycle) coverage.
3. **Regenerate Matrix**: `uv run python tools/gen_full_matrix.py`.

## Phase 4: Reporting
- Check `reports/COMPREHENSIVE_SEMANTIC_AUDIT.md`.
- Check `reports/ERROR_PATTERN_ANALYSIS.md`.
