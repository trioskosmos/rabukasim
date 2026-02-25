# 新しいオペコードのテスト計画

## 概要

BP05シリーズで追加された新しいアビリティに対応するため、7つの新しいオペコードと4つの新しい条件を追加しました。このドキュメントでは、各オペコードの仕様と、それを使用するカードのアビリティテキストに基づいたテストケースを定義します。

## 新しいオペコード一覧

| オペコード | ID | 説明 |
|-----------|-----|------|
| LOOK_DECK_DYNAMIC | 91 | ライブスコアに基づいてデッキを見る |
| REDUCE_SCORE | 92 | ライブスコアを減らす |
| REPEAT_ABILITY | 93 | アビリティを繰り返す |
| LOSE_EXCESS_HEARTS | 94 | 余剰ハートを失う |
| SKIP_ACTIVATE_PHASE | 95 | アクティブフェーズをスキップ |
| PAY_ENERGY_DYNAMIC | 96 | カードスコアに基づいてエネルギーを支払う |
| PLACE_ENERGY_UNDER_MEMBER | 97 | エネルギーをメンバーの下に配置 |

## 新しい条件一覧

| 条件 | ID | 説明 |
|------|-----|------|
| COUNT_ENERGY_EXACT | 301 | エネルギーの正確な数をチェック |
| COUNT_BLADE_HEART_TYPES | 302 | ブレード/ハートタイプをカウント |
| OPPONENT_HAS_EXCESS_HEART | 303 | 相手が余剰ハートを持つかチェック |
| SCORE_TOTAL_CHECK | 304 | 合計スコアをチェック |

---

## テストケース

### 1. LOOK_DECK_DYNAMIC (91)

**カード例**: PL!-bp5-001-AR
**元のテキスト**: 
> ライブ成功時、手札を1枚控え室に置いてもよい：自分のデッキの上から、自分のライブの合計スコアに2を足した数に等しい枚数見る。その中からカードを1枚手札に加える。残りを控え室に置く。

**現在のコンパイル状態**: `effect_type: 29` (META_RULE)

**期待される動作**:
1. ライブ成功時にトリガー
2. オプションコスト: 手札を1枚捨てる
3. ライブの合計スコア + 2枚のカードをデッキの上から見る
4. その中から1枚を手札に加える
5. 残りを控え室に置く

**テストシナリオ**:
```
GIVEN: ライブスコアが5の状態
WHEN: アビリティが発動
THEN: デッキの上から7枚(5+2)を見る
AND: 1枚を選んで手札に加える
AND: 残り6枚を控え室に置く
```

**Rustテストコード**:
```rust
#[test]
fn test_opcode_look_deck_dynamic_score() {
    let mut state = create_test_state();
    // Setup: ライブスコア5、デッキに10枚以上
    state.core.players[0].live_score = 5;
    // ... デッキのセットアップ
    
    // Execute: LOOK_DECK_DYNAMIC(2)を実行
    // 期待: 7枚を見る
    
    // Assert: looked_cardsに7枚が含まれる
    assert_eq!(state.core.players[0].looked_cards.len(), 7);
}
```

---

### 2. REDUCE_SCORE (92)

**説明**: ライブスコアを減少させる効果

**期待される動作**:
- 指定された値だけライブスコアを減らす
- スコアは0以下にならない

**テストシナリオ**:
```
GIVEN: ライブスコアが10の状態
WHEN: REDUCE_SCORE(3)を実行
THEN: ライブスコアが7になる
```

**Rustテストコード**:
```rust
#[test]
fn test_opcode_reduce_score() {
    let mut state = create_test_state();
    state.core.players[0].live_score = 10;
    
    // Execute: REDUCE_SCORE(3)
    // 期待: live_score = 7
    
    assert_eq!(state.core.players[0].live_score, 7);
}
```

---

### 3. REPEAT_ABILITY (93)

**説明**: アビリティを指定回数繰り返す

**期待される動作**:
- 現在のアビリティを指定回数実行する
- 繰り返し回数は動的に計算可能

**テストシナリオ**:
```
GIVEN: アビリティが「1枚引く」
WHEN: REPEAT_ABILITY(2)を実行
THEN: 2枚引く
```

---

### 4. LOSE_EXCESS_HEARTS (94)

**説明**: 余剰ハートを失う効果

**期待される動作**:
- 必要ハート数を超えているハートを失う
- ライブ成功条件に影響する可能性がある

**テストシナリオ**:
```
GIVEN: 必要ハートが[1,0,1,0,7,1,0]、現在のハートが[2,1,2,0,8,2,1]
WHEN: LOSE_EXCESS_HEARTSを実行
THEN: ハートが[1,0,1,0,7,1,0]になる（余剰分を失う）
```

---

### 5. SKIP_ACTIVATE_PHASE (95)

**説明**: アクティブフェーズをスキップする

**期待される動作**:
- プレイヤーのアクティブフェーズをスキップ
- 次のフェーズに進む

**テストシナリオ**:
```
GIVEN: アクティブフェーズ
WHEN: SKIP_ACTIVATE_PHASEを実行
THEN: アクティブフェーズがスキップされる
```

---

### 6. PAY_ENERGY_DYNAMIC (96)

**説明**: カードのスコアに基づいてエネルギーを支払う

**期待される動作**:
- カードのスコア分のエネルギーを支払う
- 動的なコスト計算

**テストシナリオ**:
```
GIVEN: エネルギーゾーンに5枚、カードスコアが3
WHEN: PAY_ENERGY_DYNAMICを実行
THEN: エネルギーを3枚支払う
```

---

### 7. PLACE_ENERGY_UNDER_MEMBER (97)

**説明**: エネルギーをメンバーの下に配置

**期待される動作**:
- エネルギーカードをメンバーの下に移動
- 特殊な状態管理が必要

**テストシナリオ**:
```
GIVEN: エネルギーゾーンにカード、ステージにメンバー
WHEN: PLACE_ENERGY_UNDER_MEMBERを実行
THEN: エネルギーがメンバーの下に配置される
```

---

## 新しい条件のテスト

### COUNT_ENERGY_EXACT (301)

**テストシナリオ**:
```
GIVEN: エネルギーゾーンに3枚
WHEN: COUNT_ENERGY_EXACT(3)を評価
THEN: true

WHEN: COUNT_ENERGY_EXACT(4)を評価
THEN: false
```

### COUNT_BLADE_HEART_TYPES (302)

**テストシナリオ**:
```
GIVEN: メンバーが3種類のブレード/ハートを持つ
WHEN: COUNT_BLADE_HEART_TYPES(3)を評価
THEN: true
```

### OPPONENT_HAS_EXCESS_HEART (303)

**テストシナリオ**:
```
GIVEN: 相手が余剰ハートを持つ
WHEN: OPPONENT_HAS_EXCESS_HEARTを評価
THEN: true
```

### SCORE_TOTAL_CHECK (304)

**テストシナリオ**:
```
GIVEN: 合計スコアが10
WHEN: SCORE_TOTAL_CHECK(10)を評価
THEN: true
```

---

## 実装優先順位

1. **LOOK_DECK_DYNAMIC** - 最も多くのカードで使用
2. **REDUCE_SCORE** - スコア計算に重要
3. **PAY_ENERGY_DYNAMIC** - エネルギーコスト管理
4. **LOSE_EXCESS_HEARTS** - ライブメカニクス
5. **SKIP_ACTIVATE_PHASE** - フェーズ管理
6. **REPEAT_ABILITY** - 複雑な効果
7. **PLACE_ENERGY_UNDER_MEMBER** - 特殊な状態管理

---

## 次のステップ

1. CodeモードでRustエンジンにオペコードハンドラーを実装
2. 各オペコードのテストを追加
3. BP05カードをテストスイートに追加
4. カードコンパイラを更新して新しいオペコードを使用
