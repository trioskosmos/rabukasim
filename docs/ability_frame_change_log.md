# Ability Frame Change Log

Append-only record of direct frame edits made to `data/ability_frame_source.json`.

## 2026-04-11 18:24:51 +10:00

- `idx 31`
  - Trigger: `LIVE_START`
  - Text: `『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。`
  - Change: replaced `RETURN`-only stub with `BATON -> COUNT_ENERGY -> ENERGY_CHARGE`
- `idx 37`
  - Trigger: `ON_PLAY`
  - Text: `手札のライブカードを1枚控え室に置いてもよい：カードを3枚引く。`
  - Change: inserted optional discard cost before `DRAW 3`
- `idx 40`
  - Trigger: `LIVE_START`
  - Text: `手札を1枚控え室に置いてもよい：自分の控え室から『虹ヶ咲』のライブカードを1枚手札に加える。`
  - Change: inserted optional discard cost before `RECOVER_LIVE`
- `idx 58`
  - Trigger: `LIVE_START`
  - Text: `このメンバーをウェイトにし、手札を1枚控え室に置いてもよい：自分のデッキの上からカードを5枚見る。その中からコスト9以上の『μ's』のメンバーカードを1枚公開して手札に加えてもよい。残りを控え室に置く。`
  - Change: replaced `RETURN`-only stub with tap/discard/look/select/recover/remainder flow
- `idx 179`
  - Trigger: `LIVE_START`
  - Text: `自分のデッキの上からカードを5枚控え室に置く。それらの中にライブカードがある場合、カードを1枚引く。`
  - Change: replaced `RETURN`-only stub with mill-5 plus conditional draw

## Notes

- This log records only direct source edits, not analysis output.
- `META_RULE` entries are intentionally left for later.

## 2026-04-11 18:39:49 +10:00

- `idx 2`
  - Trigger: `LIVE_START`
  - Change: replaced `RETURN`-only stub with `COUNT_LIVE_HEARTS -> JUMP_IF_FALSE -> ADD_HEARTS`
- `idx 39`
  - Trigger: `LIVE_START`
  - Change: replaced `RETURN`-only stub with optional discard cost plus `LOOK_AND_CHOOSE` for 7 cards / up to 3 picks
- Engine note: added `COUNT_LIVE_HEARTS` support for the live-card heart-sum condition
- `idx 92`
  - Trigger: `LIVE_START`
  - Change: replaced `RETURN`-only stub with optional self-tap, `COUNT_STAGE` for `Printemps`, then accumulated `ACTIVATE_ENERGY`
  - Engine note: `ACTIVATE_ENERGY` now consumes accumulated count when `compare_accumulated` is set
- `idx 361`
  - Trigger: `ON_LIVE_START`
  - Change: replaced `RETURN`-only stub with two `COUNT_SUCCESS_LIVE_SCORE` checks and two score boosts
  - Engine note: added `COUNT_SUCCESS_LIVE_SCORE` support for success-pile score filtering


## 2026-04-11 18:55:00 +10:00

- `idx 511`
  - Trigger: `ACTIVATED`
  - Change: corrected `RECOVER_LIVE` heart filter from `heart03`-mismatch to `heart03` (`heart_type = 2`)
- `idx 512`
  - Trigger: `ACTIVATED`
  - Change: corrected `RECOVER_LIVE` heart filter for `heart01` (`heart_type = 0`)
- `idx 514`
  - Trigger: `ACTIVATED`
  - Change: corrected `RECOVER_LIVE` heart filter for `heart06` (`heart_type = 5`)


## 2026-04-11 19:10:00 +10:00

- `idx 362`
  - Trigger: `ON_LIVE_START`
  - Change: added missing `value = 0` to `COUNT_SUCCESS_LIVE` so the zero-success-live condition is explicit


## 2026-04-11 19:15:00 +10:00

- `idx 362`
  - Trigger: `ON_LIVE_START`
  - Change: corrected `COUNT_STAGE` from `value = 4` to `value = 3` for the three-stage `lilywhite only` check


## 2026-04-11 19:25:00 +10:00

- `idx 8`
  - Trigger: `ON_PLAY`
  - Change: replaced non-engine `BOTTOM_DECK` opcode with `MOVE_TO_DECK` for the deck-bottom placement
- `idx 9`
  - Trigger: `ON_PLAY`
  - Change: added missing `value = 10` to `MOVE_TO_DISCARD` for the mill-10 effect


## 2026-04-11 19:35:00 +10:00

- `idx 34`
  - Trigger: `ON_PLAY`
  - Change: replaced placeholder `NOP` with `BATON` on the baton-entry condition
