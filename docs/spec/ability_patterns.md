# Ability Pattern Catalog (from 50-card Manual Review)

## Pattern Groups Identified

### 1. **Recovery from Discard** (10+ cards)
**Pattern**: "控え室から○○を手札に加える"

**Examples**:
- Card #1 (高坂 穂乃果): "控え室からライブカードを1枚手札に加える"
- Card #2 (絢瀬 絵里): "控え室からメンバーカードを1枚手札に加える"
- Card #10 (絢瀬絵里): "控え室から『μ's』のライブカードを1枚手札に加える"
- Card #15 (星空 凛): "控え室からコスト2以下のメンバーカードを1枚手札に加える"
- Card #42 (高海千歌): "控え室からライブカードを1枚手札に加える"

**Implementation Needed**:
- `RECOVER_MEMBER` - with cost filter
- `RECOVER_LIVE` - basic
- `GROUP_FILTER` - for group-specific recovery (e.g., "『μ's』のライブカード")
- `COST_FILTER` - for cost restrictions (e.g., "コスト2以下")

---

### 2. **Opponent Interaction** (12+ cards)
**Pattern**: "相手の○○" / "対戦相手"

#### 2a. Tap/Wait Opponent Members
- Card #17 (東條 希): "相手のステージにいるコスト4以下のメンバー1人をウェイトにする"
- Card #5, #6, #8 (Multiple): "相手のステージにいるすべてのコスト2以下のメンバーをウェイトにする"

**Implementation**: `TAP_OPPONENT` with target selection and cost filtering

#### 2b. Opponent Choice/Interaction
- Card #38 (鬼塚冬毬): "相手はそれらのカードのうち1枚を選ぶ"
- Card #44 (桜内梨子): "相手は手札からライブカードを1枚控え室に置いてもよい"
- Card #48 (津島善子): "相手は手札を1枚控え室に置いてもよい"

**Implementation**: New choice type `OPPONENT_CHOICE` with optional/mandatory flags

#### 2c. Opponent State Checks
- Card #46 (渡辺 曜): "相手のエネルギーが自分より多い場合"
- Card #42 (高海千歌): "相手の手札の枚数が自分より2枚以上多い場合"
- Card #32 (高海千歌): "相手の成功ライブカード置き場にカードが1枚以上ある場合"

**Implementation**: New conditions `OPPONENT_ENERGY`, `OPPONENT_HAND_COUNT`, `OPPONENT_SUCCESS_COUNT`

---

### 3. **Position Manipulation** (6+ cards)
**Pattern**: "ポジションチェンジ" / "エリアに移動"

- Card #14 (星空 凛): "このメンバーはセンターエリア以外にポジションチェンジする"
- Card #27/28 (嵐 千砂都): "センターエリアのメンバーを左サイドエリアに..." (全体回転)
- Card #29/30 (桜小路きな子): "このメンバーが登場か、エリアを移動するたび" (trigger on move)

**Implementation**:
- `FORMATION_CHANGE` - bulk repositioning
- `MOVE_MEMBER` - self-move
- New trigger: `ON_POSITION_CHANGE` for Card #29

---

### 4. **Conditional Buffs/Effects** (15+ cards)
**Pattern**: "○○の場合、～"

#### 4a. Success Pile Conditions
- Card #1: "成功ライブカード置き場にカードが2枚以上ある場合"
- Card #10: "成功ライブカード置き場にあるカードのスコアの合計が６以上の場合"
- Card #32: "成功ライブカード置き場のカードが0枚で、かつ相手の成功ライブカード置き場にカードが1枚以上ある場合"

**Implementation**: `COUNT_SUCCESS_PILE`, `SCORE_TOTAL_CHECK`

#### 4b. Group/Name Filters
- Card #8: "ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合"
- Card #27: "ステージにいるメンバーが『5yncri5e!』のみの場合"
- Card #63: "ステージに『蓮ノ空』のメンバーがいる場合"

**Implementation**: Enhanced `GROUP_FILTER` with "only" logic and location checks

#### 4c. Live Card Conditions
- Card #10: "ライブ中のライブカードに、{{live_start}}能力も{{live_success}}能力も持たないカードがあるかぎり"

**Implementation**: `LIVE_CARD_CHECK` for ability presence

#### 4d. Member Cost Checks
- Card #14: "ステージに{{blade}}を5つ以上持つ『μ's』のメンバーがいない場合"
- Card #20-22: "自分か相手のステージにコスト13以上のメンバーがいる場合"

**Implementation**: `HAS_MEMBER_WITH_STAT` condition

---

### 5. **Unique/Special Mechanics** (8+ cards)

#### 5a. Flavor/Interactive
- Card #23 (愛♡スクリーム！): "相手に何が好き？と聞く" → 複数分岐
**Implementation**: Already done (`FLAVOR_ACTION`)

#### 5b. Reveal/Public Information
- Card #48: "手札のライブカードを1枚公開する"
- Card #50: "そのプレイヤーのデッキの上からカードを2枚見る"

**Implementation**: `REVEAL_CARDS` + player targeting

#### 5c. Dynamic Requirements
- Card #8: "このカードを使用するためのコストは..." (変更)
- Card #4: "必要ハートは○○少なくなる/多くなる"

**Implementation**: `REDUCE_COST`, `MODIFY_HEARTS_REQUIRED`

#### 5d. Yell Manipulation
- Card #5 (VIVID WORLD): "エールによって公開される自分のカードが持つ[桃ブレード]、[赤ブレード]...は、すべて[青ブレード]になる"
- Card #34-37 (ウィーン): "エールによって公開される自分のカードの枚数が8枚減る"

**Implementation**: `TRANSFORM_COLOR`, `MODIFY_YELL_COUNT`

#### 5e. Score Manipulation
- Card #24 (Poppin' Up!): "ライブの合計スコアが相手より高い場合"
- Card #40/41: "カードのスコアを＋１する"

**Implementation**: `BOOST_SCORE` (exists), `COMPARE_SCORE` condition

---

## Implementation Priority

### Phase 2A: Recovery (HIGH - affects ~200 cards)
1. ✅ Basic `RECOVER_LIVE`
2. ✅ Basic `RECOVER_MEMBER`
3. 🆕 `COST_FILTER` condition
4. 🆕 `SELECT_FROM_DISCARD` choice handler

### Phase 2B: Opponent Interaction (MEDIUM-HIGH - ~150 cards)
1. 🆕 `TAP_OPPONENT` with cost filtering
2. 🆕 `OPPONENT_CHOICE` (May/Must structure)
3. 🆕 Opponent state conditions

### Phase 2C: Conditional Logic (HIGH - ~180 cards)
1. 🆕 `COUNT_SUCCESS_PILE`
2. 🆕 `SCORE_TOTAL_CHECK`
3. 🆕 Enhanced `GROUP_FILTER` (only, multi-location)
4. 🆕 `HAS_MEMBER_WITH_STAT`

### Phase 2D: Position/Movement (MEDIUM - ~80 cards)
1. ✅ `MOVE_MEMBER` (basic exists)
2. 🆕 `FORMATION_CHANGE`
3. 🆕 `ON_POSITION_CHANGE` trigger

### Phase 3: Unique Mechanics (LOW-MEDIUM - edge cases)
1. 🆕 `REVEAL_CARDS`
2. 🆕 `TRANSFORM_COLOR`
3. 🆕 `MODIFY_YELL_COUNT`
4. 🆕 `MODIFY_HEARTS_REQUIRED`

## Next Steps

Start with **Phase 2A** (Recovery) as it has the highest card coverage and builds naturally on Phase 1 work.
