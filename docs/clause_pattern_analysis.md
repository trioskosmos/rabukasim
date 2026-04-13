# Clause Pattern Analysis

## Game Mechanics from rules.txt

### Card Movement
- Draw (引く): Draw X cards from deck
- Place (置く): Place card to zone
- Look at top (上から見る): Look at X cards from deck top
- Shuffle (シャッフルする): Shuffle deck/zone
- Swap (入れ替える): Swap cards between zones
- Position change (ポジションチェンジ): Move member to area (swap if occupied)

### State Changes
- Activate (アクティブにする): Set card to active state
- Wait (ウェイトにする): Set card to wait state
- Face up (表にする): Set card to face-up
- Face down (裏にする): Set card to face-down

### Resource Management
- Pay energy (エネルギーを支払う): Pay X energy
- Gain hearts (ハートを得る): Gain X hearts
- Gain blades (ブレードを得る): Gain X blades
- Gain score (スコアを+Xする): Add X to score
- Place energy under member (エネルギーをメンバーの下に置く): Attach energy to member

### Zone Operations
- From hand (手札から): From hand zone
- From discard (控え室から): From discard zone
- From deck top (デッキの上から): From deck top
- To hand (手札に加える): To hand zone
- To discard (控え室に置く): To discard zone
- To deck top (デッキの上に置く): To deck top
- To deck bottom (デッキの一番下に置く): To deck bottom
- To stage (ステージに登場させる): To member area
- To live card area (ライブカード置き場に置く): To live card area

### Conditions
- Card count comparison (カード枚数がX以上/以下): Compare card counts
- Cost condition (コストX以下): Cost threshold
- Group presence (『Group』のメンバーがいる): Group member presence
- Area presence (エリアにメンバーがいる): Area member presence
- Heart condition (ハートX以上): Heart threshold

### Restrictions
- Cannot play (プレイできない): Cannot play card
- Cannot activate (起動できない): Cannot activate ability
- Cannot use (使用できない): Cannot use effect

## Atomic Patterns Layer Implementation

### Working Atomic Patterns (total ~1346 matches)

#### Duration (386 matches)
- atomic_duration_end_live: "ライブ終了時まで" (203 matches)
- atomic_duration_end_turn: "このターン" (30 matches)
- atomic_duration_permanent: "常時" (153 matches)

#### Resource Management (52 matches)
- atomic_gain_score: "スコアを+Xする" (52 matches)

#### Zone Operations (601 matches)
- atomic_to_deck_top: "デッキの上に置く" (8 matches)
- atomic_to_deck_bottom: "デッキの一番下に置く" (13 matches)
- atomic_to_hand: "手札に加える" (193 matches)
- atomic_to_discard: "控え室に置く" (290 matches)
- atomic_from_deck_top: "デッキの上から" (71 matches)
- atomic_from_hand: "手札から" (3 matches)
- atomic_from_discard: "控え室から" (23 matches)

#### State Changes (119 matches)
- atomic_state_wait: "ウェイトにする" (67 matches)
- atomic_state_activate: "アクティブにする" (52 matches)

#### Conditions (10 matches)
- atomic_group_presence: "『Group』のメンバーがいる" (10 matches)

#### Card Operations (153 matches)
- atomic_reveal_card: "公開する" (33 matches)
- atomic_draw_card: "カードをX枚引く" (97 matches)
- atomic_select_card: "X枚選ぶ" (9 matches)
- atomic_choose_option: "以下からXつを選ぶ" (14 matches)

#### Member Operations (25 matches)
- atomic_move_member: "移動させる" (25 matches)

#### Optionality (473 matches)
- atomic_optional: "てもよい" (473 matches)

### Attempted but Non-Matching Patterns (phrasing differences in actual data)
- atomic_restriction_cannot_play: "プレイできない" (0 matches)
- atomic_restriction_cannot_activate: "起動できない" (0 matches)
- atomic_restriction_cannot_use: "使用できない" (0 matches)
- atomic_condition_heart: "ハートX以上" (0 matches)
- atomic_shuffle_deck: "デッキをシャッフルする" (0 matches)
- atomic_look_at_deck: "デッキの上からX枚見る" (0 matches)
- atomic_place_energy: "エネルギーを置く" (0 matches)

### Notes
- Many theoretical patterns from rules.txt don't match due to phrasing differences in actual ability text
- Atomic patterns focus on smallest semantic units that actually appear in the data
- Position change patterns attempted but too specific (0 matches each), removed
- Clause-level patterns use atomic patterns as building blocks where appropriate

## Current Clause-Level Patterns

### Present
- basic_action_draw: Draw X cards
- discard_from_hand: Discard X cards from hand
- place_to_discard_deck_top: Place to discard from deck top (22 matches)
- place_to_discard_remaining: Place to discard (91 matches)
- state_change_wait_this_member: Wait this member (2 matches)
- state_change_activate: Activate (3 matches)
- gain_resource_specific: Gain resource with duration (17 matches)
- move_member: Move member (4 matches)
- look_fragment: Look at deck (2 matches)
- place_to_zone: Place to zone (5 matches)
- place_to_discard: Place to discard (3 matches)

### Variables that should be separate clauses
- conditional_present_fragment: "選んだエリアにメンバー", "そのメンバーは、このメンバーがいたエリアに移動させる" → member movement clauses
- conditional_generic: "代わりにスコアを+２する" → score modification clause
- trigger_when: "これによりウェイト状態のメンバーが3人以上アクティブ状態になった", "このカードのスコアを+１する" → state change clause, score modification clause
- parenthetical_note: "この効果で登場したメンバーのいるエリアには、このターンにメンバーは登場できない" → restriction clause
- place_to_zone: "好きな順番でデッキの上" → card placement clause
- look_fragment: "自分は、そのプレイヤーのデッキの上からカード" → look at deck clause
- gain_resource_specific: "ライブ終了時まで、選んだハート" → gain resource with duration clause

## Current Status

- Clause count: 1973 (100% compression maintained)
- Pattern count: 47
- Atomic patterns: ~1346 matches across game mechanics
- Documentation: docs/clause_pattern_analysis.md

## Next Steps
1. Continue adding atomic patterns for game mechanics that actually match the data
2. Focus on patterns present in actual ability text rather than theoretical patterns
3. Update pattern documentation as atomic patterns are added
