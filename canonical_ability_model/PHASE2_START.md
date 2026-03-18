# Phase 2: Mechanic Cluster Migration

Development has shifted from **Pipeline Repair** (Phase 1) to **Vocabulary Expansion** (Phase 2).

## Current Standing
- **Authored Coverage**: 614/614 (100%)
- **Runtime Coverage**: 614/1,357 (45.2%)
- **Target**: Convert the remaining 743 legacy slots by pattern clusters.

## The Path to Continue

The next logical step is to pick a high-frequency mechanic cluster from the backlog and implement its canonical mapping.

### 1. Review the Backlog
The prioritized list of legacy patterns is in:
[reports/legacy_pattern_backlog.md](reports/legacy_pattern_backlog.md)

### 2. Recommended Next Task: RECOVER_LIVE
The top cluster is **RECOVER_LIVE** (26 instances).
- **Goal**: Define a canonical operation for "adding cards from discard to hand".
- **Action**: 
    1. Search for existing `RECOVER_LIVE` logic in `scripts/`.
    2. Define the `RECOVER_LIVE` canonical op in `tools/canonical_semantic_validator.js`.
    3. Bulk-author the 26 cards in `drafts/canonical_full_draft.json`.

### 3. Verify Progress
After any updates, run:
```bash
node tools/build_hybrid_runtime_preview.js
node tools/build_fallback_runtime.js
```
The canonical coverage in `reports/fallback_runtime_preview.json` should increase from 614.

---
*For general architecture, see [SOURCE_OF_TRUTH.md](SOURCE_OF_TRUTH.md)*
*For authoring rules, see [docs/CANONICAL_AUTHORING_GUIDE.md](docs/CANONICAL_AUTHORING_GUIDE.md)*
