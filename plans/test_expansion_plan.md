# テスト拡張計画：ネガティブテストと条件テスト

## 現状の問題点

### 1. ネガティブテスト
- **現状**: `verify_card_negative()`は存在するが、INFOログとして出力されるのみ
- **問題**: 条件が満たされない場合にアビリティが発動すべきでないことを検証していない

### 2. 条件テスト
- **現状**: 単一の環境（`setup_oracle_environment()`）でのみテスト
- **問題**: 条件のtrue/false両方をテストしていない

### 3. モーダルテスト
- **現状**: モーダル選択を持つカードが最初のオプションのみテスト
- **問題**: 全ての選択肢をテストしていない

---

## 推奨される拡張アプローチ

### アプローチA: 環境バリエーション（推奨）

**概念**: 複数のテスト環境を定義し、各環境でアビリティを実行

```rust
enum TestEnvironment {
    Standard,      // 現在の setup_oracle_environment()
    Minimal,       // エネルギーなし、手札なし、相手なし
    NoEnergy,      // エネルギーのみなし
    NoHand,        // 手札のみなし
    FullHand,      // 手札満杯
    OpponentEmpty, // 相手のステージが空
}
```

**実装**:
```rust
pub fn verify_card_with_env(
    &self, 
    card_id: &str, 
    ab_idx: usize, 
    env: TestEnvironment
) -> Result<(), String> {
    let mut state = create_test_state();
    match env {
        TestEnvironment::Standard => Self::setup_oracle_environment(&mut state, &self.db, real_id),
        TestEnvironment::Minimal => Self::setup_minimal_environment(&mut state, real_id),
        TestEnvironment::NoEnergy => Self::setup_no_energy_environment(&mut state, &self.db, real_id),
        // ...
    }
    // 既存の検証ロジック
}
```

### アプローチB: 条件付き期待値（推奨）

**概念**: `semantic_truth_v3.json`に条件ごとの期待値を定義

```json
{
  "PL!-bp3-002-P": {
    "id": "PL!-bp3-002-P",
    "abilities": [
      {
        "trigger": "ONPLAY",
        "test_cases": [
          {
            "name": "standard",
            "environment": "standard",
            "sequence": [
              {
                "text": "COST: DISCARD_HAND(1)",
                "deltas": [
                  { "tag": "HAND_DISCARD", "value": 1 },
                  { "tag": "DISCARD_DELTA", "value": 1 }
                ]
              }
            ]
          },
          {
            "name": "no_hand",
            "environment": "no_hand",
            "sequence": [
              {
                "text": "COST: DISCARD_HAND(1)",
                "deltas": [],
                "note": "Cannot pay cost - no cards in hand"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

### アプローチC: モーダルテスト拡張

**概念**: モーダル選択ごとにテストケースを生成

```json
{
  "LL-PR-004-PR": {
    "id": "LL-PR-004-PR",
    "abilities": [
      {
        "trigger": "ONLIVESTART",
        "modal_options": [
          {
            "option_index": 0,
            "name": "チョコミント/ストロベリー/クッキー＆クリーム",
            "sequence": [
              {
                "text": "DISCARD_HAND(1) -> PLAYER; DISCARD_HAND(1) -> OPPONENT",
                "deltas": [
                  { "tag": "HAND_DISCARD", "value": 1 },
                  { "tag": "OPPONENT_HAND_DISCARD", "value": 1 }
                ]
              }
            ]
          },
          {
            "option_index": 1,
            "name": "あなた",
            "sequence": [
              {
                "text": "DRAW(1) -> PLAYER; DRAW(1) -> OPPONENT",
                "deltas": [
                  { "tag": "HAND_DELTA", "value": 1 },
                  { "tag": "OPPONENT_HAND_DELTA", "value": 1 }
                ]
              }
            ]
          },
          {
            "option_index": 2,
            "name": "その他",
            "sequence": [
              {
                "text": "ADD_BLADES(1) -> PLAYER; ADD_BLADES(1) -> OPPONENT",
                "deltas": [
                  { "tag": "BLADE_DELTA", "value": 1 },
                  { "tag": "OPPONENT_BLADE_DELTA", "value": 1 }
                ]
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

## 実装ロードマップ

### フェーズ1: ネガティブテストの強化（優先度: 高）

1. **`verify_card_negative()`の結果を記録**
   - INFOログからテスト結果に変更
   - レポートに「Negative Test」列を追加

2. **最小環境の定義**
   ```rust
   fn setup_minimal_environment(state: &mut GameState, real_id: i32) {
       state.core.players[0].stage[0] = real_id;
       state.core.players[0].energy_zone.clear();
       state.core.players[0].hand.clear();
       state.core.players[0].discard.clear();
       state.core.players[1].stage[0] = -1;
   }
   ```

### フェーズ2: 条件テストの実装（優先度: 中）

1. **環境バリエーションの追加**
   - `TestEnvironment` enumを定義
   - 各環境のセットアップ関数を実装

2. **条件付き期待値のサポート**
   - `semantic_truth_v3.json`のスキーマを拡張
   - `test_cases`配列をサポート

### フェーズ3: モーダルテストの実装（優先度: 中）

1. **モーダル選択の自動検出**
   - `SELECT_MODE`オペコードを検出
   - 選択肢数を自動取得

2. **選択肢ごとのテスト生成**
   - `resolve_interaction()`で選択肢を指定可能に
   - 各選択肢の期待値を定義

---

## テスト数の増加予測

| 現在 | 拡張後（推定） |
|------|--------------|
| 815アビリティ | 815 × (1 + 環境数 + モーダル数) |

**例**:
- 単純なカード: 1テスト → 2テスト（標準 + 最小）
- 条件付きカード: 1テスト → 3テスト（標準 + 条件なし + 条件あり）
- モーダルカード: 1テスト → 4テスト（標準 + 3選択肢）

**推定総テスト数**: 2000-3000テスト

---

## 次のステップ

1. **フェーズ1の実装**: `verify_card_negative()`の結果をレポートに含める
2. **スキーマ設計**: `semantic_truth_v4.json`のスキーマを設計
3. **移行スクリプト**: v3からv4への変換スクリプトを作成
