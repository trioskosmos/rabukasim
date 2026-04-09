# Ability Frame Issues - Mismatches Between Frames and JP Text

**File analyzed:** `ability_frame_source.json`  
**Generated:** 2026-04-09  
**Total unique abilities:** 544  
**Issues found:** 10 signatures with clear mismatches

---

## Issue 1: T1|6eab94976ce3fea5f3acc7dbeeda0d41ef24be2b

**Cards:**
- PL!HS-bp1-005-P | 大沢瑠璃乃
- PL!HS-bp5-011-N | 大沢瑠璃乃
- PL!N-bp5-014-N | 中須かすみ
- PL!S-bp5-014-N | 渡辺 曜
- PL!S-bp5-015-N | 津島善子
- etc.

**Frame opcodes:** `DRAW(2)` → `MOVE_TO_DISCARD(1)`

**Primary JP Text:**
> {{toujyou.png|登場}}手札を3枚まで控え室に置いてもよい：これにより置いた枚数分カードを引く。

**Problem:**
- Frame does DRAW first then MOVE_TO_DISCARD, but text describes MOVE_TO_DISCARD first then DRAW
- Frame only discards 1 card (`value: 1`) while text says "up to 3 cards" (3枚まで)
- Frame draws fixed 2 cards regardless of discard count, but text says draw "same number as discarded"

**Severity:** HIGH - Mechanic doesn't match card text

---

## Issue 2: T6|40b13fa6810811e59c6180a03d2dee80cd041225

**Cards:**
- PL!HS-bp5-018-L | AURORA FLOWER
- PL!N-bp5-006-AR | 近江彼方
- PL!SP-bp1-001-P | 澁谷かのん

**Frame opcodes:** `RETURN` only (no-op frame)

**Primary JP Text (AURORA FLOWER):**
> {{jyouji.png|常時}}すべての領域にあるこのカードは『スリーズブーケ』、『DOLLCHESTRA』、『みらくらぱーく！』として扱う。

**Problem:**
- Frame is completely empty - just a RETURN opcode
- No implementation of the group tagging meta-rule
- Card should be treated as multiple groups simultaneously but frame does nothing

**Severity:** CRITICAL - Ability not implemented at all

---

## Issue 3: T1|e139dc8878e4906085cb5de8c5ec4ce010776b6b

**Cards:**
- PL!SP-bp4-011-P | 鬼塚冬毬

**Frame opcodes:** `NOP` → `SELECT_MEMBER` → `MOVE_MEMBER`

**Primary JP Text:**
> {{jidou.png|自動}}このメンバーが登場か、エリアを移動したとき、相手のステージにいる元々持つ{{icon_blade.png|ブレード}}の数が3つ以下のメンバー1人をウェイトにする。

**Problem:**
- Frame lacks the "original blade count ≤ 3" condition check
- The NOP check only verifies STAGE_0 exists, not blade count condition
- Targets any opponent member instead of filtering by blade count ≤ 3

**Severity:** HIGH - Missing critical targeting condition

---

## Issue 4: T1|2a6040441970a725ac5cabbde288467fb0154619

**Cards:**
- PL!N-bp4-010-P | 三船栞子

**Frame opcodes:** `JUMP_IF_FALSE` → `RECOVER_LIVE`

**Primary JP Text:**
> {{toujyou.png|登場}}自分の成功ライブカード置き場にある『虹ヶ咲』のライブカードを1枚控え室に置いてもよい。そうした場合、自分の控え室にある『虹ヶ咲』のライブカードを1枚成功ライブカード置き場に置く。

**Problem:**
- Frame only implements the second half (recover from discard → success pile)
- Missing the first part: moving from success pile → discard
- This is a swap/exchange mechanic but frame only does one direction

**Severity:** HIGH - Only half of ability implemented

---

## Issue 5: T1|8792aceb310d1f255d4565f6007b88e1c3d768d3

**Cards:**
- PL!SP-bp2-006-P | 桜小路きな子

**Frame opcodes:** `BATON` → `RECOVER_MEMBER` from DISCARD

**Primary JP Text:**
> {{toujyou.png|登場}}バトンタッチして登場した場合、このバトンタッチで控え室に置かれた『Liella!』のメンバーカードを1枚手札に加える。

**Problem:**
- Frame recovers ANY 'Liella!' member from discard
- Should specifically recover the card that was just put there by THIS baton touch
- Missing "track specific card discarded by baton" logic

**Severity:** MEDIUM - Can recover wrong card from discard

---

## Issue 6: T0|686fd7af1ff738fb6c085dcfda4c9c5ce08aec7a

**Cards:**
- PL!S-bp2-004-P | 黒澤ダイヤ

**Frame opcodes:** `META_RULE(1)` → `RETURN`

**Primary JP Text:**
> {{jidou.png|自動}}［ターン1回］エールにより公開された自分のカードの中にライブカードがないとき、それらのカードをすべて控え室に置いてもよい。これにより1枚以上のカードが控え室に置かれた場合、そのエールで得たブレードハートを失い、もう一度エールを行う。

**Problem:**
- META_RULE(1) is just a rule flag - no actual implementation
- Missing: yell result checking (no live cards)
- Missing: optional discard of revealed cards
- Missing: blade heart loss on discard
- Missing: repeat yell mechanic

**Severity:** CRITICAL - Complex ability not implemented

---

## Issue 7: T1|6b3d982e5e058d8642e43e6a451193f2e4620340

**Cards:**
- PL!HS-bp5-001-AR | 日野下花帆

**Frame opcodes:** `MOVE_TO_DISCARD(4)` → `DISCARDED_CARDS` check → `ADD_BLADES(2)`

**Primary JP Text:**
> {{toujyou.png|登場}}自分のデッキの上からカードを4枚控え室に置く。それらの中にライブカードがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Problem:**
- `DISCARDED_CARDS` check with `card_type:LIVE` may check wrong scope
- Should check if ANY of the 4 just-discarded cards were live cards
- Frame logic may not properly correlate the check with the specific 4 cards

**Severity:** MEDIUM - Condition check may not work correctly

---

## Issue 8: T1|75dc8f4de8fe6e45fe2c8f05e94f2a078db2dd15

**Cards:**
- PL!SP-bp4-005-P | 葉月 恋

**Frame opcodes:** `BATON` (group LIELLA) → `ENERGY_CHARGE(2)`

**Primary JP Text:**
> {{toujyou.png|登場}}『Liella!』のメンバーからバトンタッチして登場しており、かつ自分のエネルギーが7枚以上ある場合、自分のエネルギーデッキから、エネルギーカードを2枚ウェイト状態で置く。

**Problem:**
- Frame checks BATON condition and group LIELLA
- Missing the "energy ≥ 7" condition check entirely
- Energy charge happens regardless of energy count

**Severity:** HIGH - Missing critical resource condition

**Status:** FIXED in frame data. The ability now gates the energy charge behind the `COUNT_ENERGY >= 7` check.

---

## Issue 9: T1|a71ca3f9f06c9e38ed1b86c5afd923e00bd0a6e8

**Cards:**
- PL!S-bp2-008-P | 小原鞠莉
- PL!SP-bp2-013-N | 唐 可可
- PL!SP-bp2-014-N | 嵐 千砂都
- PL!SP-bp2-018-N | 米女メイ

**Frame opcodes:** `SELECT_CARDS(1)` from DISCARD → `MOVE_TO_DECK`

**Primary JP Text (小原鞠莉):**
> {{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。

**Primary JP Text (唐 可可):**
> {{toujyou.png|登場}}自分の控え室からカードを1枚までデッキの一番上に置く。

**Problem:**
- All cards share same frame but have different ability texts
- Frame allows selecting any card, not just live cards (for cards that require live)
- Frame doesn't specify deck position (top vs bottom)
- Some cards should put to bottom, some to top - frame doesn't differentiate

**Severity:** MEDIUM - Shared frame for different abilities

---

## Issue 10: T2|a346b70a1dc561ba190c0427c356242c1aa94be1

**Cards:**
- PL!S-bp3-003-P | 松浦果南

**Frame opcodes:** `SELECT_MEMBER` → `ADD_BLADES` with dynamic scalar calculation

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}手札を2枚まで控え室に置いてもよい：ライブ終了時まで、これによって控え室に置いたカード1枚につき、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Problem:**
- Frame uses complex `compare_accumulated` dynamic calculation
- Text clearly states: per discarded card = 2 blades
- Frame's dynamic scalar (`base_value:2, divisor:1`) with remainder_zone STAGE doesn't match the simple "2 blades per discarded card" scaling
- Should be: discard 1 card → 2 blades, discard 2 cards → 4 blades (up to 2 cards)

**Severity:** MEDIUM - Scaling logic overcomplicated/mismatched

---

## Issue 11: T1|fcdb4734ffc7d57e34d3f32f9d8c7c6b69c51345

**Cards:**
- PL!S-pb1-013-N | 黒澤ダイヤ
- PL!S-pb1-014-N | 渡辺 曜
- PL!S-pb1-015-N | 津島善子

**Frame opcodes:** `MOVE_TO_DISCARD(1)` → `SUM_VALUE` → `LOOK_AND_CHOOSE`

**Primary JP Text (黒澤ダイヤ):**
> {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを4枚見る。その中からハートに{{heart_04.png|heart04}}を2個以上持つメンバーカードか、必要ハートに{{heart_04.png|heart04}}を2以上含むライブカードを1枚公開して手札に加えてもよい。

**Problem:**
- **Same frame shared by 3 cards with different heart requirements!**
- 黒澤ダイヤ requires heart_04 (green)
- 渡辺 曜 requires heart_02 (red)
- 津島善子 requires heart_05 (purple)
- Frame doesn't check for specific heart colors - missing heart color filter in LOOK_AND_CHOOSE

**Severity:** HIGH - Shared frame doesn't match different card requirements

---

## Issue 12: T1|34f62fee5737420f80dcc601930fc0b9964af5ec

**Cards:**
- PL!-pb1-006-P+ | 西木野真姫

**Frame opcodes:** `RECOVER_LIVE(1)` → `SELECT_MEMBER` → `DRAW(1)`

**Primary JP Text:**
> {{toujyou.png|登場}}自分の控え室から『μ's』のライブカードを1枚までデッキの一番上に置く。その後、相手のステージにウェイト状態のメンバーがいる場合、カードを1枚引く。

**Problem:**
- Frame uses `RECOVER_LIVE` with `zone_mask: "ALL"` but text specifies "put to top of deck"
- Should use `MOVE_TO_DECK_TOP` opcode, not `RECOVER_LIVE`
- Missing deck position specification in frame

**Severity:** MEDIUM - Wrong destination zone

**Status:** FIXED in frame data. The ability now selects the live card from discard, puts it on top of the deck, then checks for the tapped opponent member draw.

---

## Issue 13: T1|7927e4e487d073efe731543f0239eabe22d67277

**Cards:**
- PL!N-bp4-021-N | 天王寺璃奈

**Frame opcodes:** `MOVE_TO_DECK(1)`

**Primary JP Text:**
> {{toujyou.png|登場}}自分の控え室にあるカード1枚をデッキの一番上に置いてもよい。

**Problem:**
- Frame uses `MOVE_TO_DECK` without specifying deck position
- Text explicitly says "top of deck" (一番上)
- Should use `MOVE_TO_DECK_TOP` opcode

**Severity:** MEDIUM - Missing deck position specification

**Status:** FIXED in frame data. The ability now selects from discard and moves the chosen card to the top of the deck.

---

## Issue 14: T2|0a90cf8ed615d01e7079f28f909bed842e8e60a6

**Cards:**
- PL!N-bp4-031-L | NEO SKY, NEO MAP!

**Frame opcodes:** `NOP` → `GROUP_FILTER` → `SCORE_COMPARE` → `DRAW(3)`

**Primary JP Text:**
> {{live_start.png|ライブ開始時}}自分のステージのエリアすべてに『虹ヶ咲』のメンバーがいて、かつそれらのコストの合計が20以上の場合、カードを3枚引き、自分の手札を3枚好きな順番でデッキの上に置く。

**Problem:**
- Frame does `DRAW(3)` but **missing second part of ability!**
- Text says: "put 3 hand cards on top of deck in any order"
- Frame lacks: hand selection + MOVE_TO_DECK_TOP operation
- Only half of ability implemented

**Severity:** HIGH - Incomplete ability implementation

**Status:** FIXED in frame data. The ability now draws 3 and then lets the player choose 3 hand cards to place on top of the deck.

---

## Issue 15: T3|2590a675fbfded82a1e0fa79721194ddb5094948

**Cards:**
- PL!S-bp3-005-P | 渡辺 曜 (ON_LIVE_SUCCESS)

**Frame opcodes:** `NOP` → `JUMP_IF_FALSE` → `DRAW(1)`

**Primary JP Text:**
> {{live_success.png|ライブ成功時}}エールにより公開された自分のカードの枚数が、相手がエールによって公開したカードの枚数より少ない場合、カードを1枚引く。

**Problem:**
- Frame uses `NOP` check on `STAGE_0` which doesn't compare yell counts
- Text requires comparing player's revealed card count vs opponent's
- Missing proper yell count comparison logic
- Current frame would trigger incorrectly

**Severity:** MEDIUM - Wrong condition check logic

---

## Summary of all issues with their required fixes

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 2 | Ability not implemented or severely broken |
| HIGH | 7 | Major mechanic mismatch or missing condition |
| MEDIUM | 6 | Minor logic issue or wrong targeting |

## Common Issue Patterns

1. **Missing conditional checks** - Frame doesn't verify resource counts (energy ≥ X, blade count ≤ Y)
2. **Incomplete implementations** - Only half of a two-part ability is coded
3. **Shared frames for different cards** - One signature used for cards with different ability texts
4. **Wrong ordering** - Operations happen in wrong sequence vs text description
5. **Meta rules as placeholders** - Complex abilities flagged with META_RULE but not implemented
6. **Missing deck position specs** - "Top/bottom of deck" not specified in frame
7. **Missing heart color filters** - Heart color requirements not checked in frames

## Recommendations

1. Review all BATON-related frames for proper discard tracking
2. Implement missing energy count checks (COUNT_ENERGY with threshold)
3. Add blade count filtering for targeting conditions
4. Split shared signatures where card texts differ meaningfully
5. Replace META_RULE placeholders with actual frame implementations
6. Add deck position specifications (TOP/BOTTOM) where text requires it
7. Add heart color filtering for cards with heart-specific requirements
