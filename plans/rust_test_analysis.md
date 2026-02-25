# Rustテスト分析レポート

## 実行日時
2026-02-25

## テスト結果サマリー

| 項目 | 値 |
|------|-----|
| 総テスト数 | 252 |
| 合格 | 248 |
| 失敗 | 2 |
| 無視 | 2 |
| 合格率 | 98.4% |

## 失敗したテスト

### 1. `repro::fix_kimi_no_kokoro::test_kimi_no_kokoro_prevention`

**ファイル**: [`src/repro/fix_kimi_no_kokoro.rs`](engine_rust_src/src/repro/fix_kimi_no_kokoro.rs)

**概要**: 「君の心」カード(ID: 431)のPrevention効果のテスト

**テスト内容**:
- ライブ成功時のOnLiveSuccessアビリティ発動
- DRAW(2); MOVE_TO_DISCARD(1) のコスト支払い
- Prevention効果による成功ライブラリーへの移動阻止

**推定失敗原因**:
- `state.step(&db, 8000)`の選択肢処理が正しく動作していない可能性
- `interaction_stack`の`choice_type`または`card_id`の不一致
- ライブゾーンからのカード除去処理の不具合

### 2. `semantic_assertions::tests::test_semantic_mass_verification`

**ファイル**: [`src/semantic_assertions.rs`](engine_rust_src/src/semantic_assertions.rs)

**概要**: 全カードのセマンティック検証テスト

**結果**:
- 880/921 Abilities Passed (95.5%)
- 閾値: 96%
- **不合格**: 閾値を下回る

**失敗カテゴリ**:

| カテゴリ | 失敗数 | 説明 |
|----------|--------|------|
| HAND_DELTA | 2 | 手札増減の期待値と実際の不一致 |
| SEGMENT_STUCK | 39 | バイトコード実行が停止 |

## SEGMENT_STUCK問題の詳細

[`semantic_assertions.rs`](engine_rust_src/src/semantic_assertions.rs:13)に定義された既知の問題カード:

```rust
pub const KNOWN_PROBLEMATIC_CARDS: &[(&str, usize)] = &[
    ("PL!-bp4-009-P", 0),
    ("PL!-bp4-009-R", 0),
    ("PL!-bp4-011-N", 1),
    ("PL!-pb1-009-P＋", 0),
    ("PL!-pb1-009-R", 0),
    ("PL!N-bp1-003-P", 1),
    ("PL!N-bp1-003-P＋", 1),
    ("PL!N-bp1-003-R＋", 1),
    ("PL!N-bp1-003-SEC", 1),
    ("PL!N-bp3-017-N", 2),
    ("PL!N-bp3-023-N", 2),
    ("PL!N-sd1-001-SD", 1),
    ("PL!SP-bp4-011-P", 1),
    ("PL!SP-bp4-011-P＋", 1),
    ("PL!SP-bp4-011-R＋", 1),
    ("PL!SP-bp4-011-SEC", 1),
    ("PL!SP-pb1-006-P＋", 1),
    ("PL!SP-pb1-006-R", 1),
];
```

**SEGMENT_STUCKの原因**:
1. バイトコード実行ループが無限ループに陥る
2. 条件分岐で進行不能になる
3. 必要なリソースが不足して実行が停止

## 警告

### 1. 未使用変数
**ファイル**: [`src/core/logic/interpreter/handlers/score_hearts.rs:116`](engine_rust_src/src/core/logic/interpreter/handlers/score_hearts.rs:116)
```
warning: unused variable: `player`
```

**修正**: 変数名を`_player`に変更

### 2. 未使用定数
**ファイル**: [`src/semantic_assertions.rs:9`](engine_rust_src/src/semantic_assertions.rs:9)
```
warning: constant `BYTECODE_WORDS_PER_INSTRUCTION` is never used
```

**修正**: 使用するか、削除する

## 修正計画

### 優先度1: テスト合格率の向上

1. **HAND_DELTA失敗(2件)の修正**
   - 失敗しているカードIDを特定
   - 手札増減ロジックの検証
   - 期待値の調整またはロジック修正

2. **SEGMENT_STUCK失敗の削減**
   - 既知の問題カードのバイトコードを調査
   - 無限ループ防止のタイムアウト実装
   - 条件分岐の修正

### 優先度2: 個別テストの修正

1. **test_kimi_no_kokoro_prevention**
   - デバッグログを追加して失敗箇所を特定
   - `interaction_stack`の状態を確認
   - 選択肢処理のロジック検証

### 優先度3: 警告の解消

1. `score_hearts.rs`の未使用変数を`_player`に変更
2. `BYTECODE_WORDS_PER_INSTRUCTION`の使用または削除

## 次のステップ

1. 個別テストを詳細実行してエラーメッセージを確認
2. HAND_DELTA失敗のカードを特定
3. SEGMENT_STUCK問題のバイトコード解析
4. 修正実装
