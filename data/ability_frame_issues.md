# Ability Frame Issues - Mismatches Between Frames and JP Text

**File analyzed:** `ability_frame_source.json`
**Generated:** 2026-04-09
**Issues found:** 1

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 1 |
| MEDIUM | 0 |

---

## Issue 1: ``
**Severity:** HIGH

**Cards:**
- PL!S-bp3-005-P | 渡辺 曜
- PL!S-bp3-005-R | 渡辺 曜

**Frame opcodes:** `NOP → JUMP_IF_FALSE → DRAW → RETURN`

**Primary JP Text:**
> {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。

**Problem(s):**
- Text compares publicly revealed card counts; Frame still uses REDUCE_YELL_COUNT placeholder

---
