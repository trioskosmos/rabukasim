# オペコード全組み合わせテスト計画

## 概要

このドキュメントは、全オペコードと条件の組み合わせを体系的にテストするための計画です。
ゲーム状態（カード、エネルギー、デッキ、捨て札サイズなど）の変数を考慮した包括的なテストマトリックスを定義します。

---

## 1. オペコード分類

### 1.1 基本操作オペコード（Core Opcodes）

| オペコード | ID | 説明 | テスト優先度 |
|-----------|-----|------|-------------|
| `O_DRAW` | 10 | カードを引く | 高 |
| `O_ADD_BLADES` | 11 | ブレード追加 | 高 |
| `O_ADD_HEARTS` | 12 | ハート追加 | 高 |
| `O_REDUCE_COST` | 13 | コスト削減 | 中 |
| `O_LOOK_DECK` | 14 | デッキを見る | 高 |
| `O_RECOVER_LIVE` | 15 | ライブ回復 | 高 |
| `O_BOOST_SCORE` | 16 | スコア増加 | 高 |
| `O_RECOVER_MEMBER` | 17 | メンバー回復 | 高 |
| `O_BUFF_POWER` | 18 | パワーバフ | 中 |
| `O_IMMUNITY` | 19 | 免疫付与 | 中 |
| `O_MOVE_MEMBER` | 20 | メンバー移動 | 高 |
| `O_SWAP_CARDS` | 21 | カード交換 | 中 |
| `O_SEARCH_DECK` | 22 | デッキ検索 | 高 |
| `O_ENERGY_CHARGE` | 23 | エネルギーチャージ | 高 |
| `O_SET_BLADES` | 24 | ブレード設定 | 中 |
| `O_SET_HEARTS` | 25 | ハート設定 | 中 |
| `O_FORMATION_CHANGE` | 26 | フォーメーション変更 | 低 |
| `O_NEGATE_EFFECT` | 27 | 効果無効化 | 高 |
| `O_ORDER_DECK` | 28 | デッキ順序変更 | 中 |
| `O_META_RULE` | 29 | メタルール | 中 |

### 1.2 選択・検索オペコード（Selection Opcodes）

| オペコード | ID | 説明 | テスト優先度 |
|-----------|-----|------|-------------|
| `O_SELECT_MODE` | 30 | モード選択 | 高 |
| `O_MOVE_TO_DECK` | 31 | デッキに移動 | 高 |
| `O_TAP_OPPONENT` | 32 | 相手をタップ | 高 |
| `O_PLACE_UNDER` | 33 | 下に配置 | 中 |
| `O_REVEAL_CARDS` | 40 | カード公開 | 高 |
| `O_LOOK_AND_CHOOSE` | 41 | 見て選ぶ | 高 |
| `O_CHEER_REVEAL` | 42 | チア公開 | 低 |
| `O_ACTIVATE_MEMBER` | 43 | メンバー活性化 | 高 |
| `O_ADD_TO_HAND` | 44 | 手札に追加 | 高 |
| `O_COLOR_SELECT` | 45 | 色選択 | 高 |
| `O_REPLACE_EFFECT` | 46 | 効果置換 | 中 |
| `O_TRIGGER_REMOTE` | 47 | リモートトリガー | 中 |
| `O_REDUCE_HEART_REQ` | 48 | ハート要件削減 | 中 |
| `O_MODIFY_SCORE_RULE` | 49 | スコアルール変更 | 低 |
| `O_ADD_STAGE_ENERGY` | 50 | ステージエネルギー追加 | 中 |
| `O_SET_TAPPED` | 51 | タップ状態設定 | 高 |
| `O_ADD_CONTINUOUS` | 52 | 継続効果追加 | 中 |
| `O_TAP_MEMBER` | 53 | メンバーをタップ | 高 |

### 1.3 特殊操作オペコード（Special Opcodes）

| オペコード | ID | 説明 | テスト優先度 |
|-----------|-----|------|-------------|
| `O_PLAY_MEMBER_FROM_HAND` | 57 | 手札からプレイ | 高 |
| `O_MOVE_TO_DISCARD` | 58 | 捨て札に移動 | 高 |
| `O_GRANT_ABILITY` | 60 | アビリティ付与 | 中 |
| `O_INCREASE_HEART_COST` | 61 | ハートコスト増加 | 低 |
| `O_REDUCE_YELL_COUNT` | 62 | エール数削減 | 中 |
| `O_PLAY_MEMBER_FROM_DISCARD` | 63 | 捨て札からプレイ | 高 |
| `O_PAY_ENERGY` | 64 | エネルギー支払い | 高 |
| `O_SELECT_MEMBER` | 65 | メンバー選択 | 高 |
| `O_DRAW_UNTIL` | 66 | 指定枚数までドロー | 高 |
| `O_SELECT_PLAYER` | 67 | プレイヤー選択 | 中 |
| `O_SELECT_LIVE` | 68 | ライブ選択 | 高 |
| `O_REVEAL_UNTIL` | 69 | 条件まで公開 | 高 |
| `O_INCREASE_COST` | 70 | コスト増加 | 低 |
| `O_PREVENT_PLAY_TO_SLOT` | 71 | スロットプレイ禁止 | 中 |
| `O_SWAP_AREA` | 72 | エリア交換 | 低 |
| `O_TRANSFORM_HEART` | 73 | ハート変換 | 中 |
| `O_SELECT_CARDS` | 74 | カード選択 | 高 |
| `O_OPPONENT_CHOOSE` | 75 | 相手が選択 | 中 |
| `O_PLAY_LIVE_FROM_DISCARD` | 76 | 捨て札からライブプレイ | 高 |
| `O_REDUCE_LIVE_SET_LIMIT` | 77 | ライブセット制限削減 | 低 |
| `O_PREVENT_ACTIVATE` | 82 | 活性化禁止 | 中 |
| `O_ACTIVATE_ENERGY` | 81 | エネルギー活性化 | 高 |
| `O_PREVENT_SET_TO_SUCCESS_PILE` | 80 | 成功山札への配置禁止 | 低 |
| `O_PREVENT_BATON_TOUCH` | 90 | バトンタッチ禁止 | 中 |
| `O_SET_HEART_COST` | 83 | ハートコスト設定 | 中 |

---

## 2. 条件分類

### 2.1 カウント条件（Count Conditions）

| 条件 | ID | 説明 | テスト変数 |
|------|-----|------|-----------|
| `C_COUNT_STAGE` | 203 | ステージ枚数 | 0, 1, 2, 3 |
| `C_COUNT_HAND` | 204 | 手札枚数 | 0, 1, 3, 5, 7, 10 |
| `C_COUNT_DISCARD` | 205 | 捨て札枚数 | 0, 1, 3, 5, 10 |
| `C_COUNT_ENERGY` | 213 | エネルギー枚数 | 0, 1, 3, 5 |
| `C_COUNT_SUCCESS_LIVE` | 218 | 成功ライブ数 | 0, 1, 2, 3 |
| `C_COUNT_LIVE_ZONE` | 230 | ライブゾーン枚数 | 0, 1, 2, 3 |
| `C_COUNT_GROUP` | 208 | グループ枚数 | 0, 1, 2, 3 |
| `C_COUNT_HEARTS` | 223 | ハート数 | 0, 1, 5, 10 |
| `C_COUNT_BLADES` | 224 | ブレード数 | 0, 1, 3, 5 |

### 2.2 状態条件（State Conditions）

| 条件 | ID | 説明 | テスト変数 |
|------|-----|------|-----------|
| `C_TURN_1` | 200 | ターン1かどうか | true, false |
| `C_IS_CENTER` | 206 | センターかどうか | true, false |
| `C_LIFE_LEAD` | 207 | ライフリード | true, false |
| `C_HAS_MEMBER` | 201 | メンバー所持 | card_id |
| `C_HAS_COLOR` | 202 | 色所持 | color_idx |
| `C_HAS_LIVE_CARD` | 214 | ライブカード所持 | true, false |
| `C_HAND_HAS_NO_LIVE` | 217 | 手札にライブなし | true, false |
| `C_DECK_REFRESHED` | 227 | デッキリフレッシュ済み | true, false |
| `C_HAS_MOVED` | 228 | 移動済み | true, false |
| `C_HAND_INCREASED` | 229 | 手札増加済み | true, false |
| `C_BATON` | 231 | バトン状態 | true, false |

### 2.3 比較条件（Comparison Conditions）

| 条件 | ID | 説明 | テスト変数 |
|------|-----|------|-----------|
| `C_COST_CHECK` | 215 | コスト確認 | threshold, LE/GE |
| `C_RARITY_CHECK` | 216 | レアリティ確認 | rarity |
| `C_SCORE_COMPARE` | 220 | スコア比較 | diff |
| `C_OPPONENT_HAND_DIFF` | 219 | 相手手札差 | diff |
| `C_OPPONENT_ENERGY_DIFF` | 225 | 相手エネルギー差 | diff |
| `C_COST_LEAD` | 240 | コストリード | true, false |
| `C_SCORE_LEAD` | 241 | スコアリード | true, false |
| `C_HEART_LEAD` | 242 | ハートリード | true, false |
| `C_COST_COMPARE` | 246 | コスト比較 | diff |
| `C_BLADE_COMPARE` | 247 | ブレード比較 | diff |
| `C_HEART_COMPARE` | 248 | ハート比較 | diff |

### 2.4 フィルター条件（Filter Conditions）

| 条件 | ID | 説明 | テスト変数 |
|------|-----|------|-----------|
| `C_GROUP_FILTER` | 209 | グループフィルター | group_id |
| `C_SELF_IS_GROUP` | 211 | 自分のグループ | group_id |
| `C_TYPE_CHECK` | 232 | タイプ確認 | member/live |
| `C_IS_IN_DISCARD` | 233 | 捨て札にいる | true, false |
| `C_AREA_CHECK` | 234 | エリア確認 | area |
| `C_OPPONENT_HAS` | 210 | 相手が所持 | card_id |
| `C_OPPONENT_HAS_WAIT` | 249 | 相手がWAIT状態 | count |

---

## 3. ゲーム状態変数

### 3.1 プレイヤー状態

```rust
struct PlayerStateVariables {
    // カードゾーン
    hand_size: usize,        // 0-10
    deck_size: usize,        // 0-50
    discard_size: usize,     // 0-20
    energy_size: usize,      // 0-10
    live_zone_size: usize,   // 0-3
    success_lives_size: usize, // 0-3

    // ステージ
    stage: [i32; 3],         // card_id or -1
    stage_tapped: [bool; 3], // tap state

    // バフ
    blade_buffs: [i32; 3],
    heart_buffs: [[u8; 7]; 3],
    live_score_bonus: i32,

    // フラグ
    has_moved: bool,
    hand_increased: bool,
    deck_refreshed: bool,
}
```

### 3.2 グローバル状態

```rust
struct GlobalStateVariables {
    turn: i32,               // 1-20
    current_player: usize,   // 0 or 1
    phase: Phase,
    modal_answer: i32,       // -1, 0, 1, 2
}
```

---

## 4. テストマトリックス

### 4.1 ドロー系オペコードテスト

#### O_DRAW テストマトリックス

| テストID | デッキサイズ | 手札サイズ | ドロー数 | 期待結果 |
|---------|------------|-----------|---------|---------|
| DRAW-01 | 5 | 0 | 1 | hand=1, deck=4 |
| DRAW-02 | 5 | 5 | 3 | hand=8, deck=2 |
| DRAW-03 | 0 | 3 | 1 | デッキリフレッシュ発生 |
| DRAW-04 | 2 | 7 | 3 | hand=9, deck=0, refresh=1 |
| DRAW-05 | 10 | 0 | 10 | hand=10, deck=0 |

#### O_DRAW_UNTIL テストマトリックス

| テストID | デッキサイズ | 現在手札 | 目標枚数 | ドロー数 | 期待結果 |
|---------|------------|---------|---------|---------|---------|
| DUNTIL-01 | 10 | 2 | 5 | 3 | hand=5 |
| DUNTIL-02 | 10 | 7 | 5 | 0 | hand=7（変更なし） |
| DUNTIL-03 | 2 | 3 | 7 | 2 | hand=5, deck=0 |
| DUNTIL-04 | 0 | 3 | 5 | refresh | リフレッシュ後ドロー |

### 4.2 回復系オペコードテスト

#### O_RECOVER_MEMBER テストマトリックス

| テストID | 捨て札内容 | フィルター | 期待結果 |
|---------|-----------|-----------|---------|
| RECM-01 | [M1, M2, M3] | なし | いずれか1枚回復 |
| RECM-02 | [M1(cost=3), M2(cost=5)] | cost<=4 | M1のみ選択可能 |
| RECM-03 | [L1, L2] | type=member | 選択不可 |
| RECM-04 | [] | なし | 効果なし |
| RECM-05 | [M1(μ's), M2(Aqours)] | group=μ's | M1のみ選択可能 |

#### O_RECOVER_LIVE テストマトリックス

| テストID | 捨て札内容 | フィルター | 期待結果 |
|---------|-----------|-----------|---------|
| RECL-01 | [L1, L2] | なし | いずれか1枚回復 |
| RECL-02 | [L1(μ's), L2(Aqours)] | group=μ's | L1のみ選択可能 |
| RECL-03 | [M1, M2] | type=live | 選択不可 |
| RECL-04 | [L1(hearts=8)] | hearts>=5 | L1選択可能 |

### 4.3 検索・選択系オペコードテスト

#### O_LOOK_AND_CHOOSE テストマトリックス

| テストID | デッキ内容 | 見る枚数 | 選択枚数 | フィルター | 期待結果 |
|---------|-----------|---------|---------|-----------|---------|
| LAC-01 | [M1, M2, M3, M4, M5] | 3 | 1 | なし | 1枚handへ、2枚discard |
| LAC-02 | [M1(cost=3), M2(cost=5), M3(cost=2)] | 3 | 1 | cost>=4 | M2のみ選択可能 |
| LAC-03 | [L1, M1, M2] | 3 | 1 | type=live | L1のみ選択可能 |
| LAC-04 | [M1, M2] | 5 | 1 | なし | デッキ不足で2枚のみ |
| LAC-05 | [M1(μ's), M2(Aqours), M3(μ's)] | 3 | 2 | group=μ's | M1, M3選択可能 |

#### O_REVEAL_UNTIL テストマトリックス

| テストID | デッキ内容 | 条件 | 期待結果 |
|---------|-----------|------|---------|
| REVU-01 | [M1, M2, L1, M3] | type=live | L1をhandへ、M1,M2をdiscard |
| REVU-02 | [M1, M2, M3] | type=live | 全枚discard、条件不一致 |
| REVU-03 | [M1(cost=2), M2(cost=5), M3] | cost>=4 | M2をhandへ、M1をdiscard |
| REVU-04 | [L1, L2, L3] | type=live | L1をhandへ |

### 4.4 エネルギー系オペコードテスト

#### O_PAY_ENERGY テストマトリックス

| テストID | エネルギー数 | タップ済み | 支払い数 | 期待結果 |
|---------|------------|-----------|---------|---------|
| PAYE-01 | 3 | 0 | 1 | tapped=1, energy=3 |
| PAYE-02 | 3 | 1 | 2 | tapped=3, energy=3 |
| PAYE-03 | 2 | 0 | 3 | 支払い不可 |
| PAYE-04 | 5 | 2 | 3 | tapped=5 |
| PAYE-05 | 0 | 0 | 1 | 支払い不可 |

#### O_ACTIVATE_ENERGY テストマトリックス

| テストID | エネルギー数 | 活性化数 | 期待結果 |
|---------|------------|---------|---------|
| ACTE-01 | 3 | 2 | tapped=2 |
| ACTE-02 | 3 | 5 | 全枚タップ |
| ACTE-03 | 0 | 1 | 効果なし |

### 4.5 タップ系オペコードテスト

#### O_TAP_OPPONENT テストマトリックス

| テストID | 相手ステージ | フィルター | タップ数 | 期待結果 |
|---------|------------|-----------|---------|---------|
| TAPO-01 | [M1, M2, M3] | なし | 1 | 1枚タップ |
| TAPO-02 | [M1(cost=2), M2(cost=5)] | cost<=3 | 1 | M1のみタップ可能 |
| TAPO-03 | [M1(tapped), M2] | なし | 1 | M2タップ |
| TAPO-04 | [M1, M2] | tapped=true | 1 | 既にタップ済みは対象外 |
| TAPO-05 | [-1, -1, -1] | なし | 1 | 効果なし |

#### O_SET_TAPPED テストマトリックス

| テストID | 対象 | 現在状態 | 設定値 | 期待結果 |
|---------|------|---------|-------|---------|
| SETT-01 | stage[0] | untapped | 1 | tapped |
| SETT-02 | stage[0] | tapped | 0 | untapped |
| SETT-03 | stage[0] | tapped | 1 | tapped（変更なし） |

### 4.6 スコア・バフ系オペコードテスト

#### O_BOOST_SCORE テストマトリックス

| テストID | 現在スコア | 増加値 | 期待結果 |
|---------|-----------|-------|---------|
| BOOS-01 | 0 | 3 | score=3 |
| BOOS-02 | 1000 | 5 | score=1005 |
| BOOS-03 | 0 | 0 | score=0 |

#### O_ADD_BLADES テストマトリックス

| テストID | 現在ブレード | 追加数 | 対象 | 期待結果 |
|---------|------------|-------|------|---------|
| ADDB-01 | 0 | 2 | player | blades=2 |
| ADDB-02 | 3 | 1 | member[0] | blade_buffs[0]=1 |
| ADDB-03 | 0 | 0 | player | blades=0 |

#### O_ADD_HEARTS テストマトリックス

| テストID | 現在ハート | 追加数 | 色 | 期待結果 |
|---------|-----------|-------|-----|---------|
| ADDH-01 | [0,0,0,0,0,0,0] | 2 | pink | heart_buffs[0]=2 |
| ADDH-02 | [1,1,0,0,0,0,0] | 1 | blue | heart_buffs[2]=1 |
| ADDH-03 | [0,0,0,0,0,0,0] | 0 | pink | 変化なし |

### 4.7 条件分岐テスト

#### C_COUNT_HAND 条件テスト

| テストID | 手札枚数 | 閾値 | 比較 | 期待結果 |
|---------|---------|-----|------|---------|
| CCH-01 | 3 | 3 | >= | true |
| CCH-02 | 3 | 4 | >= | false |
| CCH-03 | 0 | 1 | >= | false |
| CCH-04 | 10 | 5 | >= | true |

#### C_COST_CHECK 条件テスト

| テストID | カードコスト | 閾値 | 比較 | 期待結果 |
|---------|------------|-----|------|---------|
| CCOST-01 | 5 | 5 | >= | true |
| CCOST-02 | 5 | 5 | <= | true |
| CCOST-03 | 3 | 5 | >= | false |
| CCOST-04 | 7 | 5 | <= | false |

#### C_LIFE_LEAD 条件テスト

| テストID | P0成功ライブ | P1成功ライブ | 期待結果 |
|---------|------------|------------|---------|
| CLIF-01 | 2 | 1 | true |
| CLIF-02 | 1 | 2 | false |
| CLIF-03 | 1 | 1 | false |
| CLIF-04 | 0 | 0 | false |

---

## 5. 複合テストシナリオ

### 5.1 コスト支払い＋効果の複合テスト

```rust
#[test]
fn test_cost_discard_hand_with_filter() {
    // コスト: 手札を3枚捨てる（フィルター: 歩夢/かのん/花帆）
    // 効果: スコア+3

    // Setup
    let hand = vec![Ayumu, Kanon, Kaho, Other];
    // Expected: 3枚捨ててスコア+3
}

#[test]
fn test_cost_pay_energy_with_insufficient() {
    // コスト: エネルギー3支払い
    // 状態: エネルギー2のみ

    // Expected: 効果発動なし
}
```

### 5.2 連鎖効果テスト

```rust
#[test]
fn test_on_leaves_trigger_chain() {
    // メンバーがステージを離れる時、OnLeaves効果が発動
    // その効果がさらに別のカードを移動させる

    // Setup: stage[0] = CardWithOnLeaves
    // Execute: O_MOVE_TO_DISCARD
    // Expected: OnLeaves効果が発動
}

#[test]
fn test_trigger_remote_chain() {
    // O_TRIGGER_REMOTEで別のカードのアビリティを発動
    // そのアビリティがさらにO_TRIGGER_REMOTE

    // Expected: 連鎖的にアビリティ発動
}
```

### 5.3 エッジケーステスト

```rust
#[test]
fn test_empty_zone_operations() {
    // 空のゾーンに対する操作
    // - 空のデッキからドロー
    // - 空の捨て札から回復
    // - 空のステージでタップ

    // Expected: エラーなく処理
}

#[test]
fn test_full_zone_operations() {
    // 満杯のゾーンに対する操作
    // - 手札10枚でドロー
    // - ライブゾーン3枚で追加

    // Expected: ルールに従った処理
}
```

---

## 6. テスト実装構造

### 6.1 テストヘルパー関数

```rust
/// ゲーム状態ビルダー
struct GameStateBuilder {
    state: GameState,
}

impl GameStateBuilder {
    fn new() -> Self;
    fn with_hand(mut self, cards: Vec<i32>) -> Self;
    fn with_deck(mut self, cards: Vec<i32>) -> Self;
    fn with_discard(mut self, cards: Vec<i32>) -> Self;
    fn with_energy(mut self, cards: Vec<i32>) -> Self;
    fn with_stage(mut self, slot: usize, card_id: i32) -> Self;
    fn with_success_lives(mut self, cards: Vec<i32>) -> Self;
    fn with_tapped(mut self, slot: usize, tapped: bool) -> Self;
    fn build(self) -> GameState;
}

/// アサーションヘルパー
fn assert_hand_size(state: &GameState, player: usize, expected: usize);
fn assert_deck_size(state: &GameState, player: usize, expected: usize);
fn assert_discard_size(state: &GameState, player: usize, expected: usize);
fn assert_score(state: &GameState, player: usize, expected: i32);
fn assert_blades(state: &GameState, player: usize, expected: i32);
fn assert_tapped(state: &GameState, player: usize, slot: usize, expected: bool);
```

### 6.2 テストファイル構成

```
engine_rust_src/src/
├── opcode_tests/
│   ├── mod.rs
│   ├── draw_tests.rs        # O_DRAW, O_DRAW_UNTIL
│   ├── recover_tests.rs     # O_RECOVER_MEMBER, O_RECOVER_LIVE
│   ├── search_tests.rs      # O_LOOK_DECK, O_SEARCH_DECK, O_LOOK_AND_CHOOSE
│   ├── reveal_tests.rs      # O_REVEAL_CARDS, O_REVEAL_UNTIL
│   ├── energy_tests.rs      # O_PAY_ENERGY, O_ACTIVATE_ENERGY, O_ENERGY_CHARGE
│   ├── tap_tests.rs         # O_TAP_OPPONENT, O_SET_TAPPED, O_TAP_MEMBER
│   ├── score_tests.rs       # O_BOOST_SCORE, O_SET_SCORE
│   ├── buff_tests.rs        # O_ADD_BLADES, O_ADD_HEARTS, O_BUFF_POWER
│   ├── move_tests.rs        # O_MOVE_MEMBER, O_MOVE_TO_DECK, O_MOVE_TO_DISCARD
│   ├── select_tests.rs      # O_SELECT_MODE, O_SELECT_MEMBER, O_SELECT_CARDS
│   └── condition_tests.rs   # 全条件テスト
├── integration_tests/
│   ├── chain_effects.rs     # 連鎖効果テスト
│   ├── edge_cases.rs        # エッジケーステスト
│   └── full_game_flow.rs    # ゲームフローテスト
└── test_helpers.rs
```

---

## 7. テスト実行戦略

### 7.1 ユニットテスト

- 各オペコード単体のテスト
- 各条件単体のテスト
- パラメータ化テストでバリエーションをカバー

### 7.2 統合テスト

- 複数オペコードの組み合わせ
- トリガー連鎖
- ゲームフェーズ遷移

### 7.3 プロパティベーステスト

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn test_draw_never_exceeds_max(
        deck_size in 0usize..50,
        hand_size in 0usize..10,
        draw_count in 1usize..5
    ) {
        // ドロー後の手札が最大値を超えないことを確認
    }

    #[test]
    fn test_energy_payment_never_negative(
        energy in 0usize..10,
        tapped in 0usize..10,
        payment in 1usize..5
    ) {
        // エネルギー支払い後のタップ数が負にならないことを確認
    }
}
```

---

## 8. 実カードを使用したテスト

### 8.1 実カードデータの活用

テストでは `load_real_db()` を使用して実際のカードデータベースを読み込みます：

```rust
use crate::test_helpers::load_real_db;

fn get_card_id(db: &CardDatabase, card_no: &str) -> i32 {
    db.card_no_to_id.get(card_no).copied().expect("Card not found")
}
```

### 8.2 実カードテストケース

#### O_RECOVER_MEMBER テスト（実カード使用）

| テストID | カード | 日本語テキスト | テスト内容 |
|---------|--------|---------------|-----------|
| RECM-R01 | PL!-sd1-001-SD | 登場:自分の控え室からライブカードを1枚手札に加える | discard=[L1], handにL1追加 |
| RECM-R02 | PL!-sd1-002-SD | 起動:控え室からメンバーカードを1枚手札に加える | discard=[M1], handにM1追加 |
| RECM-R03 | PL!-sd1-003-SD | 登場:控え室からコスト4以下のμ'sメンバーを1枚手札に加える | フィルター条件確認 |

#### O_LOOK_AND_CHOOSE テスト（実カード使用）

| テストID | カード | 日本語テキスト | テスト内容 |
|---------|--------|---------------|-----------|
| LAC-R01 | PL!-sd1-004-SD | 登場:デッキ上5枚を見てμ'sライブを1枚手札に加える | フィルター: group=μ's, type=live |
| LAC-R02 | PL!-sd1-005-SD | 登場:デッキ上3枚を見て1枚手札に加え、残りをデッキに戻す | 順序選択テスト |

#### O_PAY_ENERGY テスト（実カード使用）

| テストID | カード | 日本語テキスト | テスト内容 |
|---------|--------|---------------|-----------|
| PAYE-R01 | LL-bp3-001-R＋ | ライブ開始時:エネルギー6支払い、ブレード+3 | energy=6, blades+=3 |
| PAYE-R02 | LL-bp3-001-R＋ | エネルギー不足時 | energy=3, 効果発動不可 |

#### O_DISCARD_HAND（コスト）テスト（実カード使用）

| テストID | カード | 日本語テキスト | テスト内容 |
|---------|--------|---------------|-----------|
| DISC-R01 | LL-bp1-001-R＋ | 手札の「歩夢/かのん/花帆」を3枚捨ててスコア+3 | フィルター条件確認 |
| DISC-R02 | LL-bp1-001-R＋ | フィルター不一致 | hand=[Other], 効果発動不可 |

### 8.3 実カードテストコード例

```rust
/// PL!-sd1-001-SD: 高坂 穂乃果
/// 日本語: 登場:自分の成功ライブカード置き場にカードが2枚以上ある場合、
///         自分の控え室からライブカードを1枚手札に加える。
#[test]
fn test_real_card_pl_sd1_001_honoka() {
    let db = load_real_db();
    let card_id = get_card_id(&db, "PL!-sd1-001-SD");

    let mut state = create_test_state();
    state.ui.silent = true;

    // Setup: 成功ライブ2枚、控え室にライブカード
    state.players[0].success_lives = vec![
        get_card_id(&db, "PL!-sd1-020-SD"),  // ライブカード
        get_card_id(&db, "PL!-sd1-021-SD"),  // ライブカード
    ];
    let live_in_discard = get_card_id(&db, "PL!-sd1-022-SD");
    state.players[0].discard = vec![live_in_discard];

    // Execute: 登場時トリガー
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ..Default::default()
    };
    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);

    // Assert: 控え室から手札にライブカードが移動
    assert!(state.players[0].hand.contains(&live_in_discard),
        "ライブカードが手札に追加されるべき");
}

/// LL-bp1-001-R＋: 上原歩夢&澁谷かのん&日野下花帆
/// 日本語: ライブ開始時:手札の「歩夢/かのん/花帆」を3枚捨ててスコア+3
#[test]
fn test_real_card_ll_bp1_001_ayumu_kanon_kaho() {
    let db = load_real_db();
    let card_id = get_card_id(&db, "LL-bp1-001-R＋");

    let mut state = create_test_state();
    state.ui.silent = true;
    state.phase = Phase::PerformanceP1;

    // Setup: 手札に歩夢、かのん、花帆
    let ayumu = find_card_by_char_name(&db, "歩夢");
    let kanon = find_card_by_char_name(&db, "かのん");
    let kaho = find_card_by_char_name(&db, "花帆");
    state.players[0].hand = vec![ayumu, kanon, kaho, 9999];  // 9999は他のカード

    // Execute: ライブ開始時トリガー
    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: card_id,
        ..Default::default()
    };
    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

    // Assert: スコア+3
    assert_eq!(state.players[0].live_score_bonus, 3,
        "スコア+3されるべき");
}
```

### 8.4 実カードID参照テーブル

| カード番号 | card_id | 名前 | 主なオペコード |
|-----------|---------|------|---------------|
| PL!-sd1-001-SD | 1 | 高坂 穂乃果 | O_RECOVER_LIVE, O_ADD_BLADES |
| PL!-sd1-002-SD | 2 | 絢瀬 絵里 | O_RECOVER_MEMBER |
| PL!-sd1-003-SD | 3 | 南 ことり | O_RECOVER_MEMBER, O_ADD_HEARTS |
| PL!-sd1-004-SD | 4 | 園田 海未 | O_LOOK_AND_CHOOSE |
| PL!-sd1-005-SD | 5 | 星空 凛 | O_LOOK_AND_CHOOSE |
| LL-bp1-001-R＋ | 9 | 上原歩夢&澁谷かのん&日野下花帆 | O_RECOVER_MEMBER, O_DISCARD_HAND, O_BOOST_SCORE |

---

## 9. 優先順位と実装順序

1. **Phase 1: 基本オペコード（実カード使用）** (高優先度)
   - O_DRAW, O_ADD_BLADES, O_ADD_HEARTS
   - O_RECOVER_MEMBER, O_RECOVER_LIVE
   - O_PAY_ENERGY, O_ACTIVATE_ENERGY
   - 実カード: PL!-sd1-001〜005

2. **Phase 2: 選択・検索オペコード（実カード使用）** (高優先度)
   - O_LOOK_AND_CHOOSE, O_REVEAL_UNTIL
   - O_SELECT_MODE, O_SELECT_MEMBER
   - 実カード: PL!-sd1-004, PL!-sd1-005

3. **Phase 3: 条件テスト（実カード使用）** (中優先度)
   - C_COUNT_*, C_COST_CHECK
   - C_LIFE_LEAD, C_HAS_*
   - 実カード: LL-bp1-001-R＋

4. **Phase 4: 複合・統合テスト** (中優先度)
   - コスト＋効果の組み合わせ
   - トリガー連鎖

5. **Phase 5: エッジケース** (低優先度)
   - 空ゾーン操作
   - 境界値テスト
