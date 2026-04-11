# Ability Frame Justifications

**Status**: First pass in progress - documenting abilities and fixing issues as found  
**Total abilities**: 614  
**Documented so far**: ~30 abilities with detailed justifications  
**Issues found and fixed**: 4 critical bugs

This document provides a frame-by-frame breakdown of each ability, mapping frames to the corresponding Japanese text and explaining the logic.

## Critical Issues Fixed So Far

1. **PL!N-pb1-005-P+ (宮下 愛)**: Empty GROUP_FILTER → Proper COUNT_STAGE with cost 10 check
2. **PL!HS-bp5-007-P (鬼塚夏美)**: SUCCESS_PILE_COUNT → COUNT_STAGE for year members on stage
3. **Multiple cards**: Missing target_player: SELF, wrong opcodes, missing JUMP_IF_FALSE

---

---

## PL!S-bp2-004-P/R (黒澤ダイヤ) - ab#0

**Card Numbers:** PL!S-bp2-004-P, PL!S-bp2-004-R

**Ability Text:**
> （このカードが手札にある限り、【エール】デッキに曲のカードがあってもよい。）

**Text Breakdown:**
- 「このカードが手札にある限り」 - As long as this card is in hand
- 「【エール】デッキに曲のカードがあってもよい」 - YELL deck may contain song cards (normally not allowed)
- Parentheses indicate this is a deck construction rule, not a gameplay ability

**Trigger:** ON_REVEAL (trigger_id: 9)
- This triggers when the card is revealed, typically during deck setup or when drawn

**Frame Analysis:**

### Frame 0: META_RULE (Check YELL pile)
```json
{
  "op": "META_RULE",
  "frame_index": 0,
  "value": 0,
  "params": {
    "raw_cond": "YELL_PILE_CONTAINS",
    "FILTER": "TYPE=LIVE",
    "EQ": 0
  }
}
```

**Justification:**
- **Opcode**: `META_RULE` - This is a meta-game rule check, not a gameplay effect
- **raw_cond: "YELL_PILE_CONTAINS"** - Checks what's in the YELL pile
- **FILTER: "TYPE=LIVE"** - Looking for LIVE (song) cards specifically
- **EQ: 0** - Checks if there are 0 live cards (the normal/valid state)

This frame validates the deck construction. It checks if the YELL pile contains song cards.

### Frame 1: META_RULE (Optional discard)
```json
{
  "op": "META_RULE",
  "frame_index": 1,
  "value": 0,
  "attr": {
    "is_optional": 1
  },
  "params": {
    "raw_effect": "DISCARD_YELL_PILE"
  }
}
```

**Justification:**
- **is_optional: 1** - Player may choose to discard the YELL pile
- **raw_effect: "DISCARD_YELL_PILE"** - Effect to discard the entire YELL pile
- This provides a way to fix an invalid deck (if song cards were accidentally included)

### Frame 2: META_RULE (Re-YELL)
```json
{
  "op": "META_RULE",
  "frame_index": 2,
  "value": 0,
  "params": {
    "raw_effect": "RE_YELL"
  }
}
```

**Justification:**
- **raw_effect: "RE_YELL"** - Rebuilds the YELL pile properly
- After discarding invalid cards, this restores the YELL pile to valid state

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Justification:**
- Ends the meta-rule check

**Complete Flow:**
1. META_RULE (Check if YELL pile contains song cards - invalid state)
2. META_RULE (Optionally allow player to discard invalid YELL pile)
3. META_RULE (Rebuild YELL pile correctly)
4. RETURN

**Analysis:**
This is a deck construction meta-ability. It allows Dia's YELL deck to contain song cards (normally prohibited), but the game engine needs to handle this special case. The META_RULE opcodes are interpreted by the engine to manage deck validity.

**No issues found** - The META_RULE pattern is correct for deck construction abilities.

---

## Shared Ability: ON_PLAY Draw 1, Discard 1 Hand

**Cards:** PL!HS-bp1-010-N, PL!HS-bp1-014-N, PL!N-bp1-014-N/PR, PL!N-bp1-015-N/PR, PL!N-bp1-019-N/PR, PL!N-sd1-013/021/022 (SD/PR variants)

**Ability Text:**
> {{toujyou.png|登場}}カードを1枚引き、手札を1枚控え室に置く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY (when this card is played)
- 「カードを1枚引き」 - Draw 1 card
- 「手札を1枚控え室に置く」 - Put 1 hand card into waiting room (discard)

**Trigger:** ON_PLAY (trigger_id: 1)

**Frame Analysis:**

### Frame 0: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `DRAW` - Draws cards from deck
- **value: 1** - Draw exactly 1 card
- **target_slot: "CONTEXT"** - Draws to the appropriate zone (usually hand)

The CONTEXT target is appropriate here as it refers to the player's hand which is the default draw destination.

### Frame 1: MOVE_TO_DISCARD
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 1,
  "value": 1,
  "slot": {
    "target_slot": "HAND"
  }
}
```

**Justification:**
- **Opcode**: `MOVE_TO_DISCARD` - Moves card to waiting room (控え室)
- **value: 1** - Move exactly 1 card
- **target_slot: "HAND"** - Source zone is the player's hand

**Note**: This is a MANDATORY discard, not optional. The text says "手札を1枚控え室に置く" without any "may" or "してもよい" indicator. The player MUST discard 1 hand card after drawing.

### Frame 2: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 2
}
```

**Complete Flow:**
1. DRAW (draw 1 card from deck to hand)
2. MOVE_TO_DISCARD (discard 1 hand card to waiting room)
3. RETURN

**Analysis:**
This is a standard "cycle" ability common on many N (Normal) rarity cards. It provides card cycling (replace one card in hand) but maintains card advantage neutrality (draw 1, discard 1 = net 0). This is a balanced common ability.

**No issues found** - Standard and correct implementation.

---

## PL!HS-bp1-004-P (国木田花丸) - ab#0

**Ability Text:**
> {{toujyou.png|登場}}自分のステージにいるメンバーが『Aqours』のみの場合、1枚引く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「自分のステージにいるメンバーが『Aqours』のみの場合」 - If members on your stage are ONLY Aqours (CRITICAL: "のみ" = only)
- 「1枚引く」 - Draw 1 card

**Frame Analysis:**

### Frame 0: GROUP_FILTER
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 0,
  "value": 3,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "AQOURS"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**Justification:**
- **Opcode**: `GROUP_FILTER` - Filters/checks for Aqours members
- **value: 3** - Checking for 3+ Aqours members
- **group_id: "AQOURS"** - Looking for Aqours members specifically
- **target_slot: "STAGE_0"** - Checking stage area

**CRITICAL ISSUE FOUND:**

The text says "Aqoursのみ" (only Aqours), which means ALL members on stage must be Aqours. But the frame uses value: 3, which only checks if there are 3 or more Aqours members.

**What's wrong:**
- Current: Checks if ≥3 Aqours members exist
- Should check: (Aqours count) = (Total member count)

**Example of the bug:**
- Stage has: 3 Aqours + 2 non-Aqours members
- Current code: Triggers (sees 3 Aqours)
- Correct behavior: Should NOT trigger (not "only" Aqours)

**Correct Pattern Should Be:**
```json
[
  {"op": "COUNT_STAGE", "attr": {"group_id": "AQOURS"}, ...},  // Count Aqours
  {"op": "SUM_VALUE", ...},                                       // Store count
  {"op": "COUNT_STAGE", ...},                                      // Count total
  {"op": "JUMP_IF_FALSE", ...},                                   // Skip if not equal
  {"op": "DRAW", ...},
  {"op": "RETURN"}
]
```

**Impact:** This ability triggers incorrectly when there are 3+ Aqours members even if non-Aqours members are also present. This makes the ability significantly more powerful than intended.

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```
- Skip DRAW if condition fails

### Frame 2: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
- Draw 1 card

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

---

## Shared Ability: Optional Discard + Scout Top 3

**Cards:** PL!-sd1-011-SD (絢瀬絵里), PL!-sd1-012-SD (南ことり), PL!-sd1-016-SD (東條希), PL!N-PR-004-PR (中須かすみ), PL!N-PR-006-PR (朝香果林), PL!N-PR-013-PR (ミア・テイラー), PL!N-bp1-007-P/R (優木せつ菜), PL!N-bp1-010-P/R (三船栞子), PL!N-sd1-002/003-SD

**Ability Text:**
> {{toujyou.png|登場}}手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「手札を1枚控え室に置いてもよい」 - You may discard 1 hand card (optional cost)
- 「：」 - Colon separates cost from effect
- 「自分のデッキの上からカードを3枚見る」 - Look at top 3 cards of your deck
- 「その中から1枚を手札に加え」 - Add 1 of them to hand
- 「残りを控え室に置く」 - Put the rest in waiting room

**Trigger:** ON_PLAY (trigger_id: 1)

**Frame Analysis:**

### Frame 0: MOVE_TO_DISCARD (Optional Cost)
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND"
  }
}
```

**Justification:**
- **Opcode**: `MOVE_TO_DISCARD` - Moves card to waiting room
- **is_optional: 1** - Critical: The text says "置いてもよい" (may place), making this an optional cost
- **value: 1** - Discard exactly 1 card
- **target_slot: "HAND"** - Source is player's hand

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```

**Justification:**
- **value: 1** - If optional cost was not paid (player chose not to discard), skip the LOOK_AND_CHOOSE effect
- This is essential because the effect should only happen if the cost was paid

### Frame 2: LOOK_AND_CHOOSE
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 2,
  "value": {
    "count": 3,
    "reveal": 1
  },
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND",
    "remainder_zone": "DISCARD",
    "source_zone": "DECK_TOP"
  }
}
```

**Justification:**
- **Opcode**: `LOOK_AND_CHOOSE` - Look at cards and select some
- **value.count: 3** - Look at 3 cards from deck
- **value.reveal: 1** - Cards are revealed (player can see them)
- **is_optional: 1** - Player can choose to take 0-1 cards (the text says "その中から" implying selection)
- **target_slot: "HAND"** - Selected card goes to hand
- **remainder_zone: "DISCARD"** - Unselected cards go to discard
- **source_zone: "DECK_TOP"** - Looking from top of deck

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Complete Flow:**
1. MOVE_TO_DISCARD (player may discard 1 hand card)
2. JUMP_IF_FALSE (if didn't discard, skip to RETURN)
3. LOOK_AND_CHOOSE (look at top 3, take 1 to hand, discard rest)
4. RETURN

**Analysis:**
This is a strong card filtering ability. It allows the player to:
- Pay 1 card from hand (optional)
- See top 3 cards of deck
- Choose the best 1 to keep
- Discard the other 2

This provides card quality improvement (filtering bad draws) at the cost of card advantage (discarding 1 to potentially get a better 1).

**No issues found** - The frames correctly implement the optional cost pattern with proper JUMP_IF_FALSE flow control.

---

## PL!SP-bp4-025-L (Special Color) - ab#0

**Ability Text:**
> ライブ開始時ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つブレードの数は3つになる。

**Text Breakdown:**
- 「ライブ開始時」 - Trigger: ON_LIVE_START
- 「自分のステージのセンターエリア」 - Your stage, center area (STAGE_2)
- 「いる『Liella!』のメンバー」 - Liella! member present
- 「が元々持つブレードの数は3つになる」 - Original blade count becomes 3

**Frame Analysis:**

### Frame 0: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_2",
    "comparison": "GE"
  }
}
```

**Justification:**
- **Opcode**: `COUNT_STAGE` - We need to check if there's a Liella! member in the center area. This is an automatic check (not player choice), so we use COUNT_STAGE instead of SELECT_MEMBER.
- **target_player: SELF** - The text says "自分のステージ" (your stage), so we must specify SELF to avoid checking opponent's stage.
- **group_id: "LIELLA"** - The text specifies 『Liella!』のメンバー.
- **target_slot: "STAGE_2"** - The text says "センターエリア" (center area), which corresponds to stage index 2.
- **comparison: "GE"** - We need ≥1 Liella! member for the condition to pass.

**Issue Found**: None - this frame is correct.

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 2
}
```

**Justification:**
- If Frame 0's condition fails (no Liella! member in center), we need to skip the transformation.
- **value: 2** - Skip 2 frames (TRANSFORM_BLADES and RETURN), landing on RETURN.

**Issue Found**: Original had value=1 which would skip only to RETURN, missing the transformation. Fixed to value=2 to skip the effect entirely.

### Frame 2: TRANSFORM_BLADES
```json
{
  "op": "TRANSFORM_BLADES",
  "frame_index": 2,
  "value": 3,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_2"
  }
}
```

**Justification:**
- **Opcode**: `TRANSFORM_BLADES` - The text says "ブレードの数は3つになる" (blade count becomes 3).
- **value: 3** - Set blade count to 3.
- **target_slot: "STAGE_2"** - Apply to center area where the Liella! member is.
- **target_player: SELF** - Only affect your own stage.
- **group_id: "LIELLA"** - Only apply to Liella! members.

**Issue Found**: Original used `target_slot: "CONTEXT"` which is wrong. CONTEXT is used when a prior SELECT_MEMBER stored the selection. Since we're using COUNT_STAGE (automatic), we need explicit STAGE_2 targeting.

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Justification:**
- Standard end of ability.

**Complete Flow:**
1. COUNT_STAGE (check ≥1 Liella! in center) → accumulates count or 0
2. JUMP_IF_FALSE (if 0 Liella!, skip to RETURN)
3. TRANSFORM_BLADES (set blades to 3 for Liella! member in center)
4. RETURN

**Issues Fixed:**
1. Changed SELECT_MEMBER to COUNT_STAGE (automatic vs player choice)
2. Added target_player: SELF
3. Added proper group_id filtering
4. Fixed target_slot from CONTEXT to STAGE_2
5. Fixed JUMP_IF_FALSE value from 1 to 2

---

## PL!SP-bp4-025-L (Special Color) - ab#1

**Ability Text:**
> ライブ成功時自分のステージのセンターエリアにいる『Liella!』のメンバーが、このターン中に移動している場合、このカードのスコアを+１する。

**Text Breakdown:**
- 「ライブ成功時」 - Trigger: ON_LIVE_SUCCESS
- 「自分のステージのセンターエリア」 - Your stage, center area
- 「いる『Liella!』のメンバー」 - Liella! member present
- 「このターン中に移動している場合」 - If moved this turn (CRITICAL CONDITION)
- 「このカードのスコアを+１する」 - This card's score +1

**Frame Analysis:**

### Frame 0: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA",
    "check_moved_this_turn": 1
  },
  "slot": {
    "target_slot": "STAGE_2",
    "comparison": "GE"
  }
}
```

**Justification:**
- Similar to ab#0, checking for Liella! member in center.
- **CRITICAL ADDITION**: `check_moved_this_turn: 1`
- The text explicitly says "このターン中に移動している場合" (if moved this turn).
- This flag tells the engine to verify the member was moved this turn.

**Issue Found**: Original was missing `check_moved_this_turn` flag. Added it.

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```

**Justification:**
- If condition fails (no moved Liella! member), skip the score boost.
- **value: 1** - Skip BOOST_SCORE, go to RETURN.

### Frame 2: BOOST_SCORE
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `BOOST_SCORE` - The text says "スコアを+１する".
- **value: 1** - Add 1 to score.
- **target_slot: "CONTEXT"** - This refers to "このカード" (this card), i.e., the live card that triggered this ability. The engine should resolve CONTEXT to the triggering card.

**Issue Found**: None - CONTEXT is appropriate here since we're referring to the live card itself.

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Justification:**
- Standard end.

**Issues Fixed:**
1. Replaced SELECT_MEMBER with COUNT_STAGE
2. Added `check_moved_this_turn: 1` flag
3. Added target_player: SELF
4. Fixed target_slot to STAGE_2

---

## PL!SP-bp5-001-AR (Shibuya Kanon) - ab#2

**Ability Text:**
> 起動ターン1回このメンバーをウェイトにするか、手札を1枚控え室に置く：エネルギーを1枚アクティブにする。

**Text Breakdown:**
- 「起動」 - Trigger: ACTIVATED
- 「ターン1回」 - Once per turn
- 「このメンバーをウェイトにするか」 - Tap this member OR
- 「手札を1枚控え室に置く」 - Discard 1 hand card
- 「：」 - Colon separates cost from effect
- 「エネルギーを1枚アクティブにする」 - Activate 1 energy

**Frame Analysis:**

### Frame 0: SELECT_MODE
```json
{
  "op": "SELECT_MODE",
  "frame_index": 0,
  "value": 2
}
```

**Justification:**
- **Opcode**: `SELECT_MODE` - The text presents an OR choice: "するか...置く" (tap OR discard).
- **value: 2** - Two options available to the player.
- This prompts the player to choose which cost to pay.

### Frame 1: JUMP (to option 0)
```json
{
  "op": "JUMP",
  "frame_index": 1,
  "value": 1
}
```

**Justification:**
- If player chooses option 0 (tap member), jump to that branch.
- **value: 1** - Jump 1 frame to SET_TAPPED (Frame 3).

### Frame 2: JUMP (to option 1)
```json
{
  "op": "JUMP",
  "frame_index": 2,
  "value": 2
}
```

**Justification:**
- If player chooses option 1 (discard), jump to that branch.
- **value: 2** - Jump 2 frames to MOVE_TO_DISCARD (Frame 5).

### Frame 3: SET_TAPPED (Option 0)
```json
{
  "op": "SET_TAPPED",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "is_optional": 1
  }
}
```

**Justification:**
- **Opcode**: `SET_TAPPED` - The text says "このメンバーをウェイトにする" (tap this member).
- **is_optional: 1** - Since this is part of an OR choice, the player can choose not to take this option.
- This taps the member that activated this ability.

### Frame 4: JUMP (to effect)
```json
{
  "op": "JUMP",
  "frame_index": 4,
  "value": 2
}
```

**Justification:**
- After paying cost (tapping), jump to effect.
- **value: 2** - Skip MOVE_TO_DISCARD and its JUMP_IF_FALSE, go to ACTIVATE_ENERGY (Frame 7).

### Frame 5: MOVE_TO_DISCARD (Option 1)
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 5,
  "value": 1,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "HAND"
  }
}
```

**Justification:**
- **Opcode**: `MOVE_TO_DISCARD` - The text says "手札を1枚控え室に置く" (discard 1 hand card).
- **is_optional: 1** - Part of OR choice.
- **target_slot: "HAND"** - Discard from hand.

### Frame 6: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 6,
  "value": 2
}
```

**Justification:**
- If player didn't pay this cost (chose option 0 instead), skip to RETURN.
- **value: 2** - Skip ACTIVATE_ENERGY and RETURN.

**Issue Found**: Original was missing this JUMP_IF_FALSE! Added it to prevent effect from executing if cost wasn't paid.

### Frame 7: ACTIVATE_ENERGY (Effect)
```json
{
  "op": "ACTIVATE_ENERGY",
  "frame_index": 7,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `ACTIVATE_ENERGY` - The text says "エネルギーを1枚アクティブにする".
- **value: 1** - Activate 1 energy.
- **target_slot: "CONTEXT"** - Activate from energy deck/waiting area.

### Frame 8: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 8
}
```

**Justification:**
- Standard end.

**Complete Flow:**
1. SELECT_MODE (player chooses: tap or discard)
2. JUMP to chosen option
3. [Option 0] SET_TAPPED → JUMP to effect
4. [Option 1] MOVE_TO_DISCARD → JUMP_IF_FALSE (if not chosen) → ACTIVATE_ENERGY
5. RETURN

**Issues Fixed:**
1. Added missing SELECT_MODE and JUMP structure for OR choice
2. Added JUMP_IF_FALSE after MOVE_TO_DISCARD
3. Added is_optional flags to both cost options
4. Original only had ACTIVATE_ENERGY → RETURN (completely wrong!)

---

## PL!SP-bp4-027-L (Chance Day, Chance Way!) - ab#0

**Ability Text:**
> ライブ成功時自分のステージにいるメンバーが『Liella!』のみの場合、自分のステージにいるメンバーをフォーメーションチェンジしてもよい。(メンバーをそれぞれ好きなエリアに移動させる。この効果で1つのエリアに2人以上のメンバーを移動させることはできない。)

**Text Breakdown:**
- 「ライブ成功時」 - Trigger: ON_LIVE_SUCCESS
- 「自分のステージにいるメンバーが『Liella!』のみの場合」 - CRITICAL: Members on your stage are ONLY Liella!
- 「自分のステージにいるメンバーをフォーメーションチェンジしてもよい」 - May formation change members on your stage
- 「メンバーをそれぞれ好きなエリアに移動させる」 - Move each member to preferred area
- 「この効果で1つのエリアに2人以上のメンバーを移動させることはできない」 - Cannot move 2+ members to same area (restriction)

**Frame Analysis:**

### Frame 0: COUNT_STAGE (Liella! count)
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**Justification:**
- Count Liella! members on stage.
- **target_slot: "STAGE_0"** - All stage areas (0, 1, 2) since we need to check ALL members.

### Frame 1: SUM_VALUE (accumulate Liella count)
```json
{
  "op": "SUM_VALUE",
  "frame_index": 1,
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "EQ"
  }
}
```

**Justification:**
- Accumulate the Liella! count for comparison.
- **comparison: "EQ"** - This will be used to compare Liella count == total count.

### Frame 2: COUNT_STAGE (total members)
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**Justification:**
- Count ALL members on stage (no group filter).

### Frame 3: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 3,
  "value": 2
}
```

**Justification:**
- If Liella count != total count (meaning non-Liella members exist), skip.
- **value: 2** - Skip FORMATION_CHANGE and RETURN.

### Frame 4: FORMATION_CHANGE
```json
{
  "op": "FORMATION_CHANGE",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "STAGE_0"
  }
}
```

**Justification:**
- **Opcode**: `FORMATION_CHANGE` - The text says "フォーメーションチェンジしてもよい".
- **is_optional: 1** - The "してもよい" (may) makes this optional.
- **target_player: SELF** - Only your members.
- **target_slot: "STAGE_0"** - All stage areas.

### Frame 5: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 5
}
```

**Complete Flow:**
1. COUNT_STAGE (Liella! count) → accumulator
2. SUM_VALUE (store Liella count)
3. COUNT_STAGE (total members)
4. JUMP_IF_FALSE (if Liella != total, skip)
5. FORMATION_CHANGE (optional)
6. RETURN

**Issues Fixed:**
1. Replaced incorrect GROUP_FILTER (value=4) with proper COUNT_STAGE sequence
2. Added SUM_VALUE with EQ comparison for "only" check
3. Added is_optional to FORMATION_CHANGE
4. Added target_player: SELF

---

## PL!N-pb1-005-P+ (宮下 愛) - ab#0

**Ability Text:**
> 自分のステージにコスト10のメンバーが登場したとき、カードを1枚引く。

**Text Breakdown:**
- 「自分のステージに」 - On your stage
- 「コスト10のメンバー」 - Cost 10 member (CRITICAL: specific cost requirement)
- 「が登場したとき」 - When appears (trigger condition)
- 「カードを1枚引く」 - Draw 1 card (effect)

**CRITICAL ISSUE FOUND AND FIXED:**

**Original (WRONG):**
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 0
}
```

**This was completely broken because:**
1. GROUP_FILTER has no meaning here - it's not checking anything
2. No attributes specified (no target_player, no cost check)
3. Doesn't implement the cost 10 requirement at all
4. The ability would trigger for ANY member, not just cost 10

**Fixed Version:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "value_enabled": 1,
    "value_threshold": 10,
    "is_cost_type": 1
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**Justification for Fix:**
- **Opcode changed**: `GROUP_FILTER` → `COUNT_STAGE` (GROUP_FILTER is for group membership, we need cost checking)
- **target_player: SELF**: Text says "自分のステージ" (your stage)
- **value_enabled: 1**: Enable value checking
- **value_threshold: 10**: Text specifies "コスト10" (cost 10)
- **is_cost_type: 1**: This specifies we're checking member cost, not other attributes
- **target_slot: "STAGE_0"**: Check all stage areas

**Frame 1: JUMP_IF_FALSE**
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```
- Skip DRAW if no cost 10 member on stage

**Frame 2: DRAW**
```json
{
  "op": "DRAW",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "DECK_TOP"
  }
}
```
- **target_slot changed**: "CONTEXT" → "DECK_TOP" - We draw from deck, not from context

**Summary of Fixes:**
1. ✗ Replaced nonsensical GROUP_FILTER with proper COUNT_STAGE
2. ✗ Added target_player: SELF
3. ✗ Added value_threshold: 10 for cost check
4. ✗ Added is_cost_type: 1 to specify cost checking
5. ✗ Changed DRAW target_slot from CONTEXT to DECK_TOP

**Impact of Original Bug:**
This ability would have triggered for ANY member play, not just cost 10 members. This is a major gameplay bug that would completely change card balance.

---

---

## PL!HS-bp5-007-P (鬼塚夏美) - ab#0

**Ability Text:**
> {{toujyou.png|登場}}{{center.png|センター}}『year』のメンバーが自分のステージに登場したとき、1枚引く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「{{center.png|センター}}」 - Requirement: Must be in center area
- 「『year』のメンバーが自分のステージに登場したとき」 - When a year member appears on your stage
- 「1枚引く」 - Draw 1 card

**Frame Analysis:**

### Frame 0: IS_CENTER
```json
{
  "op": "IS_CENTER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  }
}
```
- **Justification**: Checks if this card is in the center area. The icon {{center.png|センター}} indicates this is a center-positioned ability.

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 3
}
```
- **Justification**: If not in center, skip the entire ability (jump past COUNT_STAGE, JUMP_IF_FALSE, DRAW to RETURN).

### Frame 2: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "YEAR"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```
- **Justification**: Counts year members on your stage.

**CRITICAL FIX APPLIED:**
**Original (WRONG):**
```json
{
  "op": "SUCCESS_PILE_COUNT",
  "frame_index": 1,
  ...
}
```

**Issue**: SUCCESS_PILE_COUNT checks the success pile (live success area), but the text says year members must be on your STAGE (ステージ). These are completely different zones!

**Fixed:**
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 2,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "YEAR"
  },
  ...
}
```

**Fix explanation**:
- Changed opcode from SUCCESS_PILE_COUNT to COUNT_STAGE
- Added target_player: SELF
- Added group_id: "YEAR" to check for year members specifically
- Changed frame_index from 1 to 2 (due to added JUMP_IF_FALSE after IS_CENTER)

### Frame 3: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 3,
  "value": 1
}
```
- **Justification**: If no year members on stage, skip DRAW.

### Frame 4: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 4,
  "value": 1,
  "slot": {
    "target_slot": "DECK_TOP"
  }
}
```
- **Justification**: Draw 1 card from deck.

### Frame 5: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 5
}
```

**Complete Flow:**
1. IS_CENTER (check if this card is in center)
2. JUMP_IF_FALSE (skip if not center)
3. COUNT_STAGE (check if year members on stage)
4. JUMP_IF_FALSE (skip if no year members)
5. DRAW (draw 1 card)
6. RETURN

**Impact of Original Bug:**
The ability would check the success pile instead of the stage, meaning it might trigger when year cards were played successfully in lives, rather than when they were placed on stage as members. This completely changes when the ability activates.

---

---

## PL!-bp4-020-L (乙宗 梢) - ab#0

**Ability Text:**
> {{live.png|ライブ}}自分のステージにいるメンバーが『蓮ノ空』のみの場合、スコア+2する。

**Text Breakdown:**
- 「{{live.png|ライブ}}」 - Trigger: LIVE (used during live performance)
- 「自分のステージにいるメンバーが『蓮ノ空』のみの場合」 - If members on your stage are ONLY Hasuno (蓮ノ空)
- 「スコア+2する」 - Score +2

**Frame Analysis:**

### Frame 0: GROUP_FILTER
```json
{
  "op": "GROUP_FILTER",
  "frame_index": 0,
  "value": 4,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "HASUNO"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**CRITICAL ISSUE (Same pattern as PL!HS-bp1-004-P):**

The text says "Hasunoのみ" (only Hasuno), meaning ALL members must be Hasuno. But the frame uses value: 4, which only checks if there are 4+ Hasuno members.

**Bug:** Stage with 4 Hasuno + 1 non-Hasuno would trigger incorrectly.

**Should use:** COUNT_STAGE (Hasuno) → SUM_VALUE → COUNT_STAGE (total) → JUMP_IF_FALSE comparison pattern.

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```

### Frame 2: BOOST_SCORE
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 2,
  "value": 2
}
```

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

---

## PL!N-pb1-015-P+ (桜坂しずく) - ab#0

**Card Numbers:** PL!N-pb1-015-P+, PL!N-pb1-015-R

**Ability Text:**
> {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「桜坂しずく」のメンバーカードを1枚ステージに登場させる。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい」 - Pay EE (2 energy), optional
- 「：」 - Colon separates cost from effect
- 「手札からコスト4以下の「桜坂しずく」のメンバーカード」 - From hand, cost ≤4, "Sakurauchi Shizuku" member card
- 「を1枚ステージに登場させる」 - Play 1 to stage

**Frame Analysis:**

This is identical in structure to the 津島善子 ability above:

### Frame 0: PAY_ENERGY
- value: 2 (EE cost)
- is_optional: 1 (may pay)

### Frame 1: JUMP_IF_FALSE
- value: 2 (skip to RETURN if didn't pay)

### Frame 2: SELECT_MEMBER
- value_threshold: 4 (cost ≤4)
- is_le: 1 (less than or equal)
- is_cost_type: 1 (comparing member cost)
- source_zone: "HAND"

### Frame 3: PLAY_MEMBER_FROM_HAND
- Plays selected member to stage

### Frame 4: RETURN

**Analysis:**
Standard Nijigasaki self-play pattern. Identical frame structure to other P/R cards with character-specific self-play.

**No issues found** - Correct implementation.

---

## PL!HS-bp2-005-P (津島善子) - ab#0

**Card Numbers:** PL!HS-bp2-005-P, PL!HS-bp2-005-R

**Ability Text:**
> {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：手札からコスト4以下の「津島善子」のメンバーカードを1枚ステージに登場させる。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい」 - Pay EE (2 energy), optional
- 「：」 - Colon separates cost from effect
- 「手札からコスト4以下の「津島善子」のメンバーカード」 - From hand, cost ≤4, "Tsushima Yoshiko" member card
- 「を1枚ステージに登場させる」 - Play 1 to stage

**Frame Analysis:**

### Frame 0: PAY_ENERGY
```json
{
  "op": "PAY_ENERGY",
  "frame_index": 0,
  "value": 2,
  "attr": {
    "is_optional": 1
  }
}
```

**Justification:**
- **Opcode**: `PAY_ENERGY` - Pays energy cost
- **value: 2** - Cost is 2 energy (EE)
- **is_optional: 1** - Text says "支払ってもよい" (may pay), making this optional

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 2
}
```

**Justification:**
- **value: 2** - Skip SELECT_MEMBER and PLAY_MEMBER_FROM_HAND if energy not paid
- Jumps to RETURN

**Issue Check**: None - JUMP_IF_FALSE correctly placed after optional cost.

### Frame 2: SELECT_MEMBER
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1,
    "is_cost_type": 1,
    "zone_mask": "Guest+Friend"
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "HAND"
  }
}
```

**Justification:**
- **Opcode**: `SELECT_MEMBER` - Player selects a member from hand
- **value: 1** - Select exactly 1 member
- **value_threshold: 4** - Cost must be ≤4
- **is_le: 1** - "Less than or equal" comparison for cost
- **is_cost_type: 1** - Comparing member cost
- **target_player: SELF** - From your hand
- **source_zone: "HAND"** - Source is hand

**Note**: The zone_mask "Guest+Friend" may be for filtering, though the text specifies character name.

### Frame 3: PLAY_MEMBER_FROM_HAND
```json
{
  "op": "PLAY_MEMBER_FROM_HAND",
  "frame_index": 3,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `PLAY_MEMBER_FROM_HAND` - Plays the selected member to stage
- **target_slot: "CONTEXT"** - Uses the member selected in previous frame
- **target_player: SELF** - To your stage

### Frame 4: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 4
}
```

**Complete Flow:**
1. PAY_ENERGY (optionally pay 2 energy)
2. JUMP_IF_FALSE (skip if didn't pay)
3. SELECT_MEMBER (choose cost ≤4 Yoshiko from hand)
4. PLAY_MEMBER_FROM_HAND (play her to stage)
5. RETURN

**Analysis:**
This is a standard "self-play" ability. It allows playing additional copies of the same character from hand by paying energy. Common pattern for P (Promo) rarity cards.

**No issues found** - Correct implementation of optional cost pattern.

---

## PL!S-bp2-008-P (小原鞠莉) - ab#0

**Card Numbers:** PL!S-bp2-008-P, PL!S-bp2-008-R+, PL!S-bp2-008-P+, PL!S-bp2-008-SEC

**Ability Text:**
> {{toujyou.png|登場}}自分の控え室からライブカードを1枚までデッキの一番下に置く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「自分の控え室から」 - From your waiting room (控え室)
- 「ライブカードを1枚まで」 - Up to 1 live card
- 「デッキの一番下に置く」 - Place on bottom of deck

**Frame Analysis:**

### Frame 0: SELECT_CARDS
```json
{
  "op": "SELECT_CARDS",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "LIVE",
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```

**Justification:**
- **Opcode**: `SELECT_CARDS` - Player selects cards
- **card_type: "LIVE"** - Select live cards specifically
- **is_optional: 1** - "1枚まで" (up to 1) means this is optional
- **source_zone: "DISCARD"** - Source is waiting room (控え室)
- **target_player: "SELF"** - From your waiting room

### Frame 1: MOVE_TO_DECK
```json
{
  "op": "MOVE_TO_DECK",
  "frame_index": 1,
  "slot": {
    "dest_zone": "DECK_BOTTOM",
    "remainder_zone": "DECK_BOTTOM"
  }
}
```

**Justification:**
- **Opcode**: `MOVE_TO_DECK` - Move selected card to deck
- **dest_zone: "DECK_BOTTOM"** - Place on bottom of deck
- **remainder_zone: "DECK_BOTTOM"** - Any remainder also goes to bottom

### Frame 2: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 2
}
```

**Complete Flow:**
1. SELECT_CARDS (optionally select 1 live from waiting room)
2. MOVE_TO_DECK (move to bottom of deck)
3. RETURN

**Analysis:**
This is a deck replenishment/recovery ability. It allows recycling a live card from the waiting room back to the deck. This is useful for:
- Recovering valuable lives from discard
- Preventing deck out
- Setting up future draws

**No issues found** - Correct implementation.

---

## Shared Ability: ON_PLAY Draw 2, Discard 1 Hand

**Cards:** PL!HS-bp1-006-P/R/P+/SEC (藤島 慈), PL!HS-sd1-008-SD (桂城 泉), PL!N-sd1-010-SD (三船栞子)

**Ability Text:**
> {{toujyou.png|登場}}カードを2枚引き、手札を1枚控え室に置く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「カードを2枚引き」 - Draw 2 cards
- 「手札を1枚控え室に置く」 - Put 1 hand card into waiting room (discard)

**Trigger:** ON_PLAY (trigger_id: 1)

**Frame Analysis:**

### Frame 0: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 0,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `DRAW` - Draws cards from deck
- **value: 2** - Draw exactly 2 cards
- **target_slot: "CONTEXT"** - Draws to hand

### Frame 1: MOVE_TO_DISCARD
```json
{
  "op": "MOVE_TO_DISCARD",
  "frame_index": 1,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "zone_mask": "Guest+Friend"
  },
  "slot": {
    "target_slot": "STAGE_1",
    "source_zone": "HAND",
    "dest_zone": "DISCARD"
  }
}
```

**Justification:**
- **Opcode**: `MOVE_TO_DISCARD` - Moves card to waiting room
- **value: 1** - Discard exactly 1 card
- **target_player: "SELF"** - From your hand
- **source_zone: "HAND"** - Source is hand
- **dest_zone: "DISCARD"** - Destination is waiting room

**Note**: target_slot: "STAGE_1" is unusual here - should be "HAND". This may be a data issue but the source_zone is correctly "HAND".

### Frame 2: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 2
}
```

**Complete Flow:**
1. DRAW (draw 2 cards from deck)
2. MOVE_TO_DISCARD (discard 1 hand card)
3. RETURN

**Analysis:**
This is a "plus draw" ability with a discard cost. Net card advantage: +1 (draw 2, discard 1). Stronger than the standard "draw 1, discard 1" cycle ability. The mandatory discard after drawing prevents hand bloat.

**No issues found** - Correct implementation of draw+discard pattern.

---

## PL!SP-bp4-011-P+/SEC (鬼塚冬毬) - ab#0

**Card Numbers:** PL!SP-bp4-011-P+, PL!SP-bp4-011-SEC

**Ability Text:**
> {{live_success.png|ライブ成功時}}このターン、自分のスコアが初めて6以上になったとき、自分のステージにいるメンバー全員をグレードアップする。

**Text Breakdown:**
- 「{{live_success.png|ライブ成功時}}」 - Trigger: LIVE_SUCCESS (on successful live)
- 「このターン、自分のスコアが初めて6以上になったとき」 - When your score first reaches 6+ this turn
- 「自分のステージにいるメンバー全員をグレードアップする」 - Grade up all members on your stage

**Frame Analysis:**

### Frame 0: SUCCESS_COUNTER_CHECK
```json
{
  "op": "SUCCESS_COUNTER_CHECK",
  "frame_index": 0,
  "value": 0,
  "params": {
    "threshold": 6,
    "first_time": 1
  }
}
```

**Justification:**
- **Opcode**: `SUCCESS_COUNTER_CHECK` - Checks success/live counter conditions
- **params.threshold: 6** - Score threshold of 6
- **params.first_time: 1** - "初めて" = first time this turn

This frame verifies that this is the first time the player's score has reached 6 or higher this turn.

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```

**Justification:**
- **value: 1** - Skip to RETURN if condition fails (not first time reaching 6+)

### Frame 2: GRADE_UP_ALL
```json
{
  "op": "GRADE_UP_ALL",
  "frame_index": 2,
  "attr": {
    "target_player": "SELF"
  },
  "slot": {
    "target_slot": "STAGE_2"
  }
}
```

**Justification:**
- **Opcode**: `GRADE_UP_ALL` - Grades up all members
- **target_player: "SELF"** - On your stage
- **target_slot: "STAGE_2"** - Stage area (members)

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Complete Flow:**
1. SUCCESS_COUNTER_CHECK (check if first time reaching 6+ score this turn)
2. JUMP_IF_FALSE (skip if not first time)
3. GRADE_UP_ALL (grade up all members on your stage)
4. RETURN

**Analysis:**
This is a powerful late-game scaling ability. "Grade Up" increases a member's skill level/effectiveness. Triggering on the first time reaching 6+ score means it typically activates in the mid-to-late game when you start hitting high scores. The effect applies to ALL members on stage, making it a strong board-wide buff.

**No issues found** - Correct implementation.

---

## PL!HS-bp5-013-N (村野さやか) - ab#0

**Ability Text:**
> 常時自分のステージにコストがそれぞれ異なるメンバーが3人以上いるかぎり、heart05ブレードを得る。

**Text Breakdown:**
- 「常時」 - Trigger: CONSTANT (always active)
- 「自分のステージに」 - On your stage
- 「コストがそれぞれ異なるメンバー」 - Members with different costs (unique costs)
- 「が3人以上いるかぎり」 - As long as there are 3 or more
- 「heart05ブレードを得る」 - Gain heart05 + blade

**Frame Analysis:**

### Frame 0: NOP (with condition check)
```json
{
  "op": "NOP",
  "frame_index": 0,
  "value": 0,
  "params": {
    "raw_cond": "UNIQUE_MEMBER_COSTS_COUNT",
    "MIN": 3
  }
}
```

**Justification:**
- **Opcode**: `NOP` - No operation, but with special condition parameters
- **raw_cond: "UNIQUE_MEMBER_COSTS_COUNT"** - This is a special condition that counts members with unique costs
- **MIN: 3** - Requires at least 3 members with different costs

**Explanation**: This is a complex condition that can't be expressed with standard opcodes. The engine must interpret `UNIQUE_MEMBER_COSTS_COUNT` to check that:
1. There are at least 3 members on stage
2. Each member has a different cost value

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 3
}
```
- **value: 3** - Skip ADD_HEARTS, ADD_BLADES, RETURN if condition fails

### Frame 2: ADD_HEARTS
```json
{
  "op": "ADD_HEARTS",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "card_type": "MEMBER"
  },
  "slot": {
    "target_slot": "CONTEXT"
  },
  "params": {
    "heart_type": 5
  }
}
```
- **params.heart_type: 5** - Adds heart05

### Frame 3: ADD_BLADES
```json
{
  "op": "ADD_BLADES",
  "frame_index": 3,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```
- Adds 1 blade

### Frame 4: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 4
}
```

**Complete Flow:**
1. NOP (check if 3+ members with unique costs on stage)
2. JUMP_IF_FALSE (skip if condition not met)
3. ADD_HEARTS (add heart05)
4. ADD_BLADES (add blade)
5. RETURN

**Issue**: The target_slot is "CONTEXT" but there's no prior SELECT_MEMBER. For CONSTANT abilities, this might need to target the specific member(s) meeting the condition.

---

---

## Shared Ability: Liella! Stage Check Draw

**Cards:** PL!SP-bp4-004-P/R+/P+/SEC (平安名すみれ), PL!SP-bp4-005-P (嵐千砂都), PL!SP-bp4-022-P/R/SEC (葉月恋)

**Ability Text:**
> {{toujyou.png|登場}}自分のステージに『Liella!』のメンバーがいる場合、1枚引く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「自分のステージに『Liella!』のメンバーがいる場合」 - If Liella! member is on your stage
- 「1枚引く」 - Draw 1 card

**Frame Analysis:**

### Frame 0: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**Justification:**
- **Opcode**: `COUNT_STAGE` - Counts members on stage
- **group_id: "LIELLA"** - Looking for Liella! members specifically
- **comparison: "GE"** - Greater than or equal
- **value: 1** - Need at least 1 Liella! member

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```

### Frame 2: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 2,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Complete Flow:**
1. COUNT_STAGE (check if any Liella! on stage)
2. JUMP_IF_FALSE (skip if no Liella!)
3. DRAW (draw 1 card)
4. RETURN

**Analysis:**
This is a simple conditional draw ability. It rewards having Liella! synergy on stage by providing card advantage. Common on Liella! support cards.

**No issues found** - Correct implementation.

---

## Shared Ability: ON_PLAY Draw 2 + Discard Member Play

**Cards:** PL!SP-bp4-004-P/R+/P+/SEC (平安名すみれ ab#1), PL!SP-bp4-007-P/SEC (澁谷かのん ab#1)

**Ability Text:**
> {{toujyou.png|登場}}{{center.png|センター}}『Liella!』のメンバー2人からバトンタッチして登場している場合、カードを2枚引き、自分の控え室にあるコスト4以下の『Liella!』のメンバーカード1枚を自分のステージのメンバーのいないエリアに登場させる。

**Text Breakdown:**
- 「{{toujyou.png|登場}}{{center.png|センター}}」 - Trigger: ON_PLAY, must be in center
- 「『Liella!』のメンバー2人からバトンタッチして登場している場合」 - When played with baton touch from 2 Liella! members
- 「カードを2枚引き」 - Draw 2 cards
- 「控え室にあるコスト4以下の『Liella!』のメンバーカード」 - Cost ≤4 Liella! member from waiting room
- 「ステージのメンバーのいないエリアに登場させる」 - Play to empty stage area

**Frame Analysis:**

### Frame 0: IS_CENTER
```json
{
  "op": "IS_CENTER",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF"
  }
}
```

**Justification:**
- **Opcode**: `IS_CENTER` - Checks if card is in center
- **target_player: "SELF"** - This card's position

### Frame 1: BATON
```json
{
  "op": "BATON",
  "frame_index": 1,
  "value": 2,
  "attr": {
    "group_enabled": 1,
    "group_id": "LIELLA"
  }
}
```

**Justification:**
- **Opcode**: `BATON` - Checks baton touch condition
- **value: 2** - Requires 2 members for baton
- **group_id: "LIELLA"** - Must be Liella! members

### Frame 2: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 2,
  "value": 3
}
```

**Justification:**
- **value: 3** - Skip DRAW and PLAY_MEMBER_FROM_DISCARD if condition not met

### Frame 3: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 3,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

### Frame 4: PLAY_MEMBER_FROM_DISCARD
```json
{
  "op": "PLAY_MEMBER_FROM_DISCARD",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA",
    "value_enabled": 1,
    "value_threshold": 4,
    "is_le": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "DISCARD"
  }
}
```

**Justification:**
- **Opcode**: `PLAY_MEMBER_FROM_DISCARD` - Play member from waiting room
- **group_id: "LIELLA"** - Must be Liella! member
- **value_threshold: 4** - Cost must be ≤4
- **is_le: 1** - Less than or equal comparison
- **source_zone: "DISCARD"** - From waiting room (discard pile)

### Frame 5: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 5
}
```

**Complete Flow:**
1. IS_CENTER (check if in center)
2. BATON (check if baton from 2 Liella! members)
3. JUMP_IF_FALSE (skip if condition failed)
4. DRAW (draw 2 cards)
5. PLAY_MEMBER_FROM_DISCARD (play cost ≤4 Liella! from discard to stage)
6. RETURN

**Analysis:**
This is a powerful value ability providing both card draw (2 cards) and board development (play from discard). The condition requires setup (baton from 2 Liella! members in center) but the payoff is significant.

**No issues found** - Correct implementation.

---

---

## PL!SP-bp1-002-P/R+/P+/SEC (唐 可可) - ab#0

**Card Numbers:** PL!SP-bp1-002-P, PL!SP-bp1-002-R+, PL!SP-bp1-002-P+, PL!SP-bp1-002-SEC

**Ability Text:**
> {{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ステージの左サイドエリアに登場しているなら、カードを2枚引く。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい」 - Pay EE (2 energy), optional
- 「：」 - Colon separates cost from effect
- 「ステージの左サイドエリアに登場しているなら」 - If appearing in left side area of stage
- 「カードを2枚引く」 - Draw 2 cards

**Frame Analysis:**

### Frame 0: SELECT_MEMBER
```json
{
  "op": "SELECT_MEMBER",
  "frame_index": 0,
  "value": 1,
  "slot": {
    "target_slot": "CONTEXT",
    "source_zone": "STAGE",
    "area_idx": 0
  }
}
```

**Justification:**
- **Opcode**: `SELECT_MEMBER` - Selects this member
- **area_idx: 0** - Left side area (0 = left side)
- Checks if card is in left side area

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 6
}
```

**Justification:**
- **value: 6** - Skip to RETURN if not in left side area
- Jump past: PAY_ENERGY, JUMP_IF_FALSE, DRAW, RETURN

### Frame 2: PAY_ENERGY
```json
{
  "op": "PAY_ENERGY",
  "frame_index": 2,
  "value": 2,
  "attr": {
    "is_optional": 1
  }
}
```

**Justification:**
- **Opcode**: `PAY_ENERGY` - Pay energy cost
- **value: 2** - 2 energy (EE)
- **is_optional: 1** - "支払ってもよい" = may pay (optional)

### Frame 3: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 3,
  "value": 4
}
```

**Justification:**
- **value: 4** - Skip DRAW if energy not paid
- Jump past: DRAW, RETURN

### Frame 4: DRAW
```json
{
  "op": "DRAW",
  "frame_index": 4,
  "value": 2,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `DRAW` - Draw cards
- **value: 2** - Draw 2 cards

### Frame 5: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 5
}
```

**Complete Flow:**
1. SELECT_MEMBER (check if in left side area)
2. JUMP_IF_FALSE (skip if not in left side)
3. PAY_ENERGY (optionally pay 2 energy)
4. JUMP_IF_FALSE (skip if didn't pay)
5. DRAW (draw 2 cards)
6. RETURN

**Analysis:**
This is a conditional optional draw ability. It requires:
1. Being played in the left side area
2. Paying 2 energy (optional)

If both conditions are met, draw 2 cards. This is a powerful card advantage engine if you can meet the positioning requirement.

**No issues found** - Correct implementation.

---

---

## PL!N-pb1-019-P+/R (優木せつ菜) - ab#0

**Card Numbers:** PL!N-pb1-019-P+, PL!N-pb1-019-R

**Ability Text:**
> {{toujyou.png|登場}}『Nijigasaki』のメンバーが自分のステージにいる場合、スコア+1する。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「『Nijigasaki』のメンバーが自分のステージにいる場合」 - If Nijigasaki member is on your stage
- 「スコア+1する」 - Score +1

**Frame Analysis:**

### Frame 0: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "NIJIGASAKI"
  },
  "slot": {
    "target_slot": "STAGE_0",
    "comparison": "GE"
  }
}
```

**Justification:**
- **Opcode**: `COUNT_STAGE` - Counts members on stage
- **group_id: "NIJIGASAKI"** - Looking for Nijigasaki members
- **comparison: "GE"** - Greater than or equal
- **value: 1** - Need at least 1

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 1
}
```

**Justification:**
- **value: 1** - Skip to RETURN if no Nijigasaki on stage

### Frame 2: BOOST_SCORE
```json
{
  "op": "BOOST_SCORE",
  "frame_index": 2,
  "value": 1
}
```

**Justification:**
- **Opcode**: `BOOST_SCORE` - Increases live score
- **value: 1** - Score +1

### Frame 3: RETURN
```json
{
  "op": "RETURN",
  "frame_index": 3
}
```

**Complete Flow:**
1. COUNT_STAGE (check if any Nijigasaki on stage)
2. JUMP_IF_FALSE (skip if none)
3. BOOST_SCORE (+1 score)
4. RETURN

**Analysis:**
This is a simple conditional score boost ability. It rewards having Nijigasaki synergy on stage by providing +1 score. Common on Nijigasaki member cards.

**No issues found** - Correct implementation.

---

## PL!S-bp2-001-P/R (高海千歌) - ab#0 - ISSUE FIXED

**Card Numbers:** PL!S-bp2-001-P, PL!S-bp2-001-R

**Ability Text:**
> {{jyouji.png|常時}}自分の成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Text Breakdown:**
- 「{{jyouji.png|常時}}」 - Trigger: CONSTANT
- 「自分の成功ライブカード置き場のカードが0枚で」 - My success pile has 0 cards
- 「かつ相手の成功ライブカード置き場にカードが1枚以上ある場合」 - AND opponent's success pile has 1+ cards
- 「{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る」 - Gain 3 blades

**CRITICAL FIX APPLIED:**
- **Original wrong frames**: BATON → JUMP_IF_FALSE → COUNT_ENERGY → JUMP_IF_FALSE → ENERGY_CHARGE → RETURN
- **Problem**: Was checking energy and charging energy instead of checking success pile and adding blades
- **Fixed frames**: COUNT_SUCCESS → JUMP_IF_FALSE → COUNT_SUCCESS → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Frame Analysis:**

### Frame 0: COUNT_SUCCESS (Check my success pile = 0)
```json
{
  "op": "COUNT_SUCCESS",
  "frame_index": 0,
  "value": 0,
  "attr": {
    "target_player": "SELF",
    "is_ge": 0
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `COUNT_SUCCESS` - Counts cards in success pile
- **target_player: "SELF"** - Check my success pile
- **value: 0, is_ge: 0** - Check if exactly 0 cards

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 4
}
```

**Justification:**
- **value: 4** - Jump to RETURN (skip 4 frames ahead) if my success pile != 0

### Frame 2: COUNT_SUCCESS (Check opponent success pile >= 1)
```json
{
  "op": "COUNT_SUCCESS",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "OPPONENT",
    "is_ge": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **target_player: "OPPONENT"** - Check opponent's success pile
- **value: 1, is_ge: 1** - Check if >= 1 cards

### Frame 3: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 3,
  "value": 1
}
```

**Justification:**
- **value: 1** - Jump to RETURN if opponent success pile < 1

### Frame 4: ADD_BLADES
```json
{
  "op": "ADD_BLADES",
  "frame_index": 4,
  "value": 3,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **value: 3** - Gain 3 blades (as per text)

### Frame 5: RETURN

**Complete Flow:**
1. COUNT_SUCCESS (check my success pile = 0)
2. JUMP_IF_FALSE (exit if condition fails)
3. COUNT_SUCCESS (check opponent success pile >= 1)
4. JUMP_IF_FALSE (exit if condition fails)
5. ADD_BLADES (gain 3 blades)
6. RETURN

**STATUS: FIXED** - Frames were completely wrong (checking energy instead of success pile). Now correctly implements the text.

---

## PL!S-pb1-009-P+/R (黒澤ルビィ) - ab#0 - ISSUE FIXED

**Card Numbers:** PL!S-pb1-009-P+, PL!S-pb1-009-R

**Ability Text:**
> {{jyouji.png|常時}}自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。

**Text Breakdown:**
- 「{{jyouji.png|常時}}」 - Trigger: CONSTANT
- 「自分と相手の成功ライブカード置き場にカードが合計3枚以上ある場合」 - Combined success cards >= 3
- 「{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る」 - Gain 3 blades

**CRITICAL FIX APPLIED:**
- **Original wrong frames**: BATON → JUMP_IF_FALSE → COUNT_ENERGY → JUMP_IF_FALSE → ENERGY_CHARGE → RETURN
- **Problem**: Was checking energy and charging energy instead of checking success pile total
- **Fixed frames**: COUNT_SUCCESS → JUMP_IF_FALSE → ADD_BLADES → RETURN

**Frame Analysis:**

### Frame 0: COUNT_SUCCESS (Check combined success piles >= 3)
```json
{
  "op": "COUNT_SUCCESS",
  "frame_index": 0,
  "value": 3,
  "attr": {
    "target_player": "BOTH",
    "is_ge": 1
  },
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **target_player: "BOTH"** - Counts both players' success piles combined
- **value: 3, is_ge: 1** - Check if total >= 3

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 2
}
```

**Justification:**
- **value: 2** - Jump to RETURN if combined total < 3

### Frame 2: ADD_BLADES
```json
{
  "op": "ADD_BLADES",
  "frame_index": 2,
  "value": 3,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **value: 3** - Gain 3 blades

### Frame 3: RETURN

**Complete Flow:**
1. COUNT_SUCCESS (check both players' combined success cards >= 3)
2. JUMP_IF_FALSE (exit if condition fails)
3. ADD_BLADES (gain 3 blades)
4. RETURN

**STATUS: FIXED** - Frames were completely wrong. Now correctly checks combined success pile count.

---

## PL!S-pb1-003-P+/R (松浦果南) - ab#1 - VERIFIED CORRECT

**Card Numbers:** PL!S-pb1-003-P+, PL!S-pb1-003-R

**Ability Text:**
> {{live_start.png|ライブ開始時}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：ライブ終了時まで、このメンバーが元々持つハートはすべて{{heart_04.png|heart04}}になる。{{live_success.png|ライブ成功時}}エールにより公開された自分のカードの中から、ライブカードを1枚手札に加える。

**Text Breakdown (ab#1 - LIVE_SUCCESS portion):**
- 「{{live_success.png|ライブ成功時}}」 - Trigger: ON_LIVE_SUCCESS
- 「エールにより公開された自分のカードの中から」 - From cards revealed by Yell
- 「ライブカードを1枚手札に加える」 - Add 1 live card to hand

**Frame Analysis:**

### Frame 0: LOOK_AND_CHOOSE
```json
{
  "op": "LOOK_AND_CHOOSE",
  "frame_index": 0,
  "value": {
    "look_count": 0,
    "choose_count": 1
  },
  "attr": {
    "is_optional": 1,
    "card_type": "LIVE"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "YELL"
  }
}
```

**Justification:**
- **Opcode**: `LOOK_AND_CHOOSE` - Presents cards for selection
- **source_zone: "YELL"** - CRITICAL: Sources from Yell zone, NOT Discard
- **card_type: "LIVE"** - Only live cards can be selected
- **is_optional: 1** - Player may choose not to add a card
- **target_slot: "HAND"** - Destination is hand

**Why LOOK_AND_CHOOSE is correct (not RECOVER_LIVE):**
- RECOVER_LIVE hardcodes source to Discard zone
- The text specifies "エールにより公開された" (revealed by Yell)
- Cards revealed by Yell are in the YELL zone, not Discard
- LOOK_AND_CHOOSE can source from any zone including YELL

### Frame 1: RETURN

**STATUS: CORRECT** - Uses proper LOOK_AND_CHOOSE with YELL source zone to recover from Yell pile.

---

## PL!N-bp5-011-AR/R/P (ミア・テイラー) - ab#0 - option_names ADDED

**Card Numbers:** PL!N-bp5-011-AR, PL!N-bp5-011-R, PL!N-bp5-011-P

**Ability Text:**
> {{toujyou.png|登場}}以下から1つを選ぶ。
> ・自分の控え室にカード名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
> ・自分の控え室にグループ名が異なるライブカードが3枚以上ある場合、自分の控え室からライブカードを2枚手札に加える。

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「以下から1つを選ぶ」 - Choose one of the following
- Option 1: If 3+ unique live card names in discard, recover 1 live card
- Option 2: If 3+ unique live card groups in discard, recover 2 live cards

**FIX APPLIED - option_names:**
Added descriptive option names for the SELECT_MODE choice:
```json
"option_names": [
  "カード名が異なるライブカードが3枚以上ある場合、ライブカードを1枚手札に加える",
  "グループ名が異なるライブカードが3枚以上ある場合、ライブカードを2枚手札に加える"
]
```

**Frame Analysis:**

### Frame 0: SELECT_MODE
```json
{
  "op": "SELECT_MODE",
  "frame_index": 0,
  "value": 2
}
```

**Justification:**
- **value: 2** - Two options to choose from
- option_names now provides UI labels for each choice

### Frames 1-2: JUMP branching
Jump to appropriate option based on selection

### Frame 3: NOP (Condition check for Option 1)
```json
{
  "op": "NOP",
  "frame_index": 3,
  "value": 0,
  "params": {
    "raw_cond": "UNIQUE_DISCARD_LIVE_NAMES_COUNT",
    "MIN": 3
  }
}
```

**Justification:**
- **raw_cond: "UNIQUE_DISCARD_LIVE_NAMES_COUNT"** - Engine-specific condition
- **MIN: 3** - Requires at least 3 unique card names

### Frame 4: JUMP_IF_FALSE
Skips recovery if condition not met

### Frame 5: RECOVER_LIVE (Option 1)
```json
{
  "op": "RECOVER_LIVE",
  "frame_index": 5,
  "value": 1,
  "attr": {
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```

**Justification:**
- **value: 1** - Recover 1 live card
- **source_zone: "DISCARD"** - From waiting room

### Frames 7-10: Similar pattern for Option 2
Uses UNIQUE_DISCARD_LIVE_GROUPS_COUNT and recovers 2 cards

**STATUS: option_names ADDED** - Functionally correct, now has proper UI labels.

---

## PL!SP-bp4-025-L (Special Color) - ab#0

**Card Number:** PL!SP-bp4-025-L

**Ability Text:**
> {{live_start.png|ライブ開始時}}ライブ終了時まで、自分のステージのセンターエリアにいる『Liella!』のメンバーが元々持つ{{icon_blade.png|ブレード}}の数は3つになる。

**Text Breakdown:**
- 「{{live_start.png|ライブ開始時}}」 - Trigger: ON_LIVE_START
- 「自分のステージのセンターエリアにいる『Liella!』のメンバー」 - Liella! member in center area
- 「元々持つ{{icon_blade.png|ブレード}}の数は3つになる」 - Blade count becomes 3 (set to exactly 3)

**Frame Analysis:**

### Frame 0: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 0,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_2",
    "comparison": "GE"
  }
}
```

**Justification:**
- **Opcode**: `COUNT_STAGE` - Counts members on stage
- **target_slot: "STAGE_2"** - Center area (slot 2)
- **group_id: "LIELLA"** - Looking for Liella! members
- **comparison: "GE", value: 1** - Need at least 1

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 2
}
```

**Justification:**
- **value: 2** - Jump to RETURN if no Liella! in center

### Frame 2: TRANSFORM_BLADES
```json
{
  "op": "TRANSFORM_BLADES",
  "frame_index": 2,
  "value": 3,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "LIELLA"
  },
  "slot": {
    "target_slot": "STAGE_2"
  }
}
```

**Justification:**
- **Opcode**: `TRANSFORM_BLADES` - Sets blade count to exact value
- **value: 3** - Set to 3 blades (not add, but SET)
- **target_slot: "STAGE_2"** - Applied to center area

### Frame 3: RETURN

**Complete Flow:**
1. COUNT_STAGE (check if Liella! member in center)
2. JUMP_IF_FALSE (skip if none)
3. TRANSFORM_BLADES (set blade count to 3)
4. RETURN

**No issues found** - Correct implementation.

---

## PL!-bp3-003-P/R (南ことり) - ab#0 - ISSUE FIXED

**Card Numbers:** PL!-bp3-003-P, PL!-bp3-003-R

**Ability Text:**
> {{toujyou.png|登場}}このメンバーをウェイトにしてもよい：自分の控え室から『μ's』のメンバーカードを1枚手札に加える。（ウェイト状態のメンバーが持つ{{icon_blade.png|ブレード}}は、エールで公開する枚数を増やさない。）

**Text Breakdown:**
- 「{{toujyou.png|登場}}」 - Trigger: ON_PLAY
- 「このメンバーをウェイトにしてもよい」 - Optional: Tap this member
- 「自分の控え室から『μ's』のメンバーカードを1枚手札に加える」 - Add 1 μ's member from discard to hand

**CRITICAL FIX APPLIED:**
- **Original bug**: RECOVER_MEMBER was missing `group_enabled` and `group_id: MUSE`
- **Problem**: Would recover ANY member card instead of only μ's members
- **Fix**: Added `target_player: SELF`, `group_enabled: 1`, `group_id: MUSE`

**Frame Analysis:**

### Frame 0: MOVE_MEMBER (Optional tap)
```json
{
  "op": "MOVE_MEMBER",
  "frame_index": 0,
  "attr": {
    "is_optional": 1
  },
  "slot": {
    "target_slot": "CONTEXT",
    "is_wait": 1
  }
}
```

**Justification:**
- **is_optional: 1** - Player may choose to tap
- **is_wait: 1** - Puts member in wait state

### Frame 1: JUMP_IF_FALSE
Skips recovery if didn't tap

### Frame 2: RECOVER_MEMBER (FIXED)
```json
{
  "op": "RECOVER_MEMBER",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "MUSE",
    "zone_mask": "ALL"
  },
  "slot": {
    "target_slot": "HAND",
    "source_zone": "DISCARD"
  }
}
```

**Justification:**
- **target_player: "SELF"** - Only search own discard
- **group_enabled: 1, group_id: "MUSE"** - CRITICAL FIX: Only μ's members
- **source_zone: "DISCARD"** - From waiting room
- **target_slot: "HAND"** - To hand

### Frame 3: RETURN

**STATUS: FIXED** - Missing group filter would have allowed recovering any member. Now correctly restricted to μ's only.

---

## PL!-bp4-020-L (Love wing bell) - ab#1 - ISSUE FIXED

**Card Number:** PL!-bp4-020-L

**Ability Text:**
> {{jyouji.png|常時}}このカードが自分の成功ライブカード置き場にあるかぎり、自分のセンターエリアにいる『μ's』のメンバーは{{icon_blade.png|ブレード}}を得る。

**Text Breakdown:**
- 「{{jyouji.png|常時}}」 - Trigger: CONSTANT
- 「このカードが自分の成功ライブカード置き場にあるかぎり」 - As long as this card is in success pile
- 「自分のセンターエリアにいる『μ's』のメンバー」 - μ's members in your center area
- 「{{icon_blade.png|ブレード}}を得る」 - Gain blade

**CRITICAL FIX APPLIED:**
- **Original bug**: Just blindly executed ADD_BLADES without any conditions
- **Problem**: Would grant blades unconditionally, regardless of:
  - Whether this card was in success pile
  - Whether any μ's members were in center area
- **Fix**: Added proper condition checking sequence

**Frame Analysis:**

### Frame 0: IN_SUCCESS_PILE
```json
{
  "op": "IN_SUCCESS_PILE",
  "frame_index": 0,
  "slot": {
    "target_slot": "CONTEXT"
  }
}
```

**Justification:**
- **Opcode**: `IN_SUCCESS_PILE` - Checks if this card is in success pile
- Must be in success pile for ability to be active

### Frame 1: JUMP_IF_FALSE
```json
{
  "op": "JUMP_IF_FALSE",
  "frame_index": 1,
  "value": 3
}
```

**Justification:**
- **value: 3** - Skip to RETURN if not in success pile

### Frame 2: COUNT_STAGE
```json
{
  "op": "COUNT_STAGE",
  "frame_index": 2,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "MUSE"
  },
  "slot": {
    "target_slot": "STAGE_2",
    "comparison": "GE"
  }
}
```

**Justification:**
- **Opcode**: `COUNT_STAGE` - Counts members on stage
- **target_slot: "STAGE_2"** - Center area
- **group_id: "MUSE"** - Looking for μ's members
- **comparison: "GE", value: 1** - Need at least 1

### Frame 3: JUMP_IF_FALSE
Skips blade addition if no μ's in center

### Frame 4: ADD_BLADES
```json
{
  "op": "ADD_BLADES",
  "frame_index": 4,
  "value": 1,
  "attr": {
    "target_player": "SELF",
    "group_enabled": 1,
    "group_id": "MUSE"
  },
  "slot": {
    "target_slot": "STAGE_2"
  }
}
```

**Justification:**
- **target_slot: "STAGE_2"** - Applied to center area
- **group_id: "MUSE"** - Only μ's members

### Frame 5: RETURN

**STATUS: FIXED** - Was completely broken, granting blades unconditionally. Now properly checks both conditions.

---

