# Rustエンジン（engine_rust_src）問題点分析レポート

## 概要

Rustエンジンのコードベースを詳細に調査し、以下の問題点を特定しました。

---

## 1. ビルドエラー（コンパイル不能）

### 1.1 未解決のインポートエラー

**ファイル**: [`src/core/logic.rs:17`](engine_rust_src/src/core/logic.rs:17)
```
error[E0432]: unresolved import `models::Goal`
```
- `Goal`型が`core::logic::models`に存在しない

**ファイル**: [`src/semantic_assertions.rs:3`](engine_rust_src/src/semantic_assertions.rs:3)
```
error[E0432]: unresolved import `crate::core::models::TriggerType`
```
- `TriggerType`は`core::enums`にあるが、間違ったパスからインポートしようとしている

### 1.2 定数が見つからないエラー

複数のファイルで`ACTION_BASE_*`定数が`crate::core::logic`から見つからない:
- `ACTION_BASE_LIVESET`
- `ACTION_BASE_HAND_CHOICE`
- `ACTION_BASE_HAND`
- `ACTION_BASE_STAGE`
- `ACTION_BASE_MULLIGAN`
- `ACTION_BASE_CHOICE`
- `ACTION_BASE_ENERGY`
- `ACTION_BASE_HAND_SELECT`
- `ACTION_BASE_STAGE_SLOTS`

これらの定数は[`src/core/generated_constants.rs`](engine_rust_src/src/core/generated_constants.rs:79)で定義されているが、適切に再エクスポートされていない。

**推奨修正**: `core/logic/mod.rs`でこれらの定数を再エクスポートするか、使用側で`crate::core::ACTION_BASE_*`を直接使用するよう修正。

---

## 2. テスト失敗の分析

### 2.1 テスト結果サマリー
- **総テスト数**: 172
- **成功**: 167
- **失敗**: 4
- **無視**: 1

### 2.2 失敗テストの詳細

#### Test 1: `test_meta_rule_pl_sp_bp1_024_l_heart_buffs`

**場所**: [`src/meta_rule_card_tests.rs:72`](engine_rust_src/src/meta_rule_card_tests.rs:72)

**問題**: `O_ADD_HEARTS`ハンドラで`ctx.area_idx`が正しく設定されていない

**原因分析**:
```rust
// score_hearts.rs:44
if (target_slot == 4 || target_slot == 0) && ctx.area_idx >= 0 {
    state.core.players[p_idx].heart_buffs[ctx.area_idx as usize].add_to_color(color, v as i32);
}
```
- `O_SELECT_MEMBER`で選択後、`ctx.area_idx`が後続の`O_ADD_HEARTS`に正しく伝播していない可能性

#### Test 2: `test_meta_rule_pl_sp_bp1_024_l_live_success_draw`

**場所**: [`src/meta_rule_card_tests.rs:125`](engine_rust_src/src/meta_rule_card_tests.rs:125)

**問題**: バイトコードデータの問題（メンバーIDが0になっている）

**原因**: これはエンジンのバグではなく、カードデータのコンパイル問題

#### Test 3: `test_card_275_sequential_interaction_resumption`

**場所**: [`src/repro_card_fixes.rs:111`](engine_rust_src/src/repro_card_fixes.rs:111)

**問題**: インタラクションスタックの順序が期待と異なる

**原因**: `O_MOVE_TO_DISCARD`が予期せず`SELECT_DISCARD`インタラクションを生成している可能性

#### Test 4: `test_archetype_sd1_001_success_live_cond`

**場所**: [`src/semantic_assertions.rs:673`](engine_rust_src/src/semantic_assertions.rs:673)

**問題**: `C_SUCCESS_LIVES`条件のチェックまたはドロー効果の実行に問題がある可能性

---

## 3. アーキテクチャ上の問題

### 3.1 レガシーコードの混在

**問題**: [`interpreter_legacy.rs`](engine_rust_src/src/core/logic/interpreter_legacy.rs)（130KB、約3500行）が新しいモジュラー構造と並存している

**影響**:
- コードの重複
- どちらのインタープリタを使用すべきか不明確
- メンテナンスコストの増大

**推奨**: レガシー版を削除し、モジュラー版に統一する

### 3.2 グローバル状態の使用

**問題**: [`interpreter/mod.rs:23`](engine_rust_src/src/core/logic/interpreter/mod.rs:23)
```rust
pub static GLOBAL_OPCODE_TRACKER: Lazy<Mutex<HashSet<i32>>> = ...
```

**影響**:
- マルチスレッド環境でのデバッグが困難
- テスト間での状態漏洩の可能性

**推奨**: GameState内に移動するか、テスト用にリセット機能を追加

### 3.3 ファイルへの直接書き込み

**問題**: [`interpreter/mod.rs:25-35`](engine_rust_src/src/core/logic/interpreter/mod.rs:25)
```rust
fn log_opcode_to_file(op: i32) {
    // reports/telemetry_raw.log に直接書き込み
}
```

**影響**:
- パフォーマンスへの悪影響
- ファイルシステムへの依存
- テスト環境での問題

**推奨**: ログ収集はGameStateまたは専用のロガーに委譲

---

## 4. 未実装・未テストのOpcode

### 4.1 未テストのOpcode（21個）

| Opcode | Name | Type |
|--------|------|------|
| 0 | Nop | Effect |
| 22 | SearchDeck | Effect |
| 26 | FormationChange | Effect |
| 34 | Flavor | Effect |
| 38 | SwapZone | Effect |
| 46 | ReplaceEffect | Effect |
| 52 | AddContinuous | Effect |
| 80 | PreventSetToSuccessPile | Effect |
| 83 | SetHeartCost | Effect |
| 202 | HasColor | Condition |
| 207 | LifeLead | Condition |
| 210 | OpponentHas | Condition |
| 211 | SelfIsGroup | Condition |
| 216 | RarityCheck | Condition |
| 217 | HandHasNoLive | Condition |
| 221 | HasChoice | Condition |
| 222 | OpponentChoice | Condition |
| 228 | HasMoved | Condition |
| 229 | HandIncreased | Condition |
| 233 | IsInDiscard | Condition |

**推奨**: これらのOpcodeに対応するカードが存在するか確認し、必要に応じてテストを追加

---

## 5. エラーハンドリングの問題

### 5.1 無限ループ保護

**問題**: [`interpreter/mod.rs:91`](engine_rust_src/src/core/logic/interpreter/mod.rs:91)
```rust
if executor.steps >= 1000 {
    // 無限ループ検出
    break;
}
```

**懸念**:
- 1000ステップが適切かどうか不明
- エラーメッセージがログに出るだけで、呼び出し元に通知されない

**推奨**: エラー状態を返すか、設定可能な閾値にする

### 5.2 条件バイパス機能

**問題**: [`conditions.rs:84-89`](engine_rust_src/src/core/logic/interpreter/conditions.rs:84)
```rust
if !result && state.debug.debug_ignore_conditions {
    // 条件をバイパス
    return true;
}
```

**懸念**: デバッグ機能が本番コードに残っている

**推奨**: コンパイル時フラグで制御するか、feature flagを使用

---

## 6. 型安全性の問題

### 6.1 マジックナンバーの使用

**問題**: 多くの場所でスロット番号にマジックナンバーを使用
```rust
if target_slot == 4  // コンテキストから取得
if ctx.area_idx < 3  // ステージスロット
```

**推奨**: 定数またはenumを定義
```rust
const SLOT_FROM_CONTEXT: i32 = 4;
const MAX_STAGE_SLOTS: usize = 3;
```

### 6.2 ビット演算の過度な使用

**問題**: [`score_hearts.rs:9`](engine_rust_src/src/core/logic/interpreter/handlers/score_hearts.rs:9)
```rust
let target_slot = s & 0xFF;
```

**推奨**: 意味のある定数を定義し、コメントで説明を追加

---

## 7. ドキュメント不足

### 7.1 バイトコードフォーマット

バイトコードの4ワード形式（op, v, a, s）の各フィールドの意味が文書化されていない

### 7.2 ハンドラの責任範囲

各ハンドラモジュール（`draw_hand`, `member_state`, `deck_zones`等）がどのOpcodeを担当するか明確でない

---

## 8. 推奨される優先順位

### 高優先度
1. ビルドエラーの修正（インポートパス、定数の再エクスポート）
2. `test_meta_rule_pl_sp_bp1_024_l_heart_buffs`の修正（ctx.area_idx伝播）
3. レガシーインタープリタの削除

### 中優先度
4. グローバル状態の削除
5. ファイル直接書き込みの削除
6. 未テストOpcodeのカバレッジ追加

### 低優先度
7. マジックナンバーの定数化
8. ドキュメントの整備
9. エラーハンドリングの改善

---

## 9. 次のステップ

1. **ビルドエラー修正**: `core/logic/mod.rs`で必要な定数を再エクスポート
2. **ctx.area_idx問題の調査**: デバッグログを追加して原因を特定
3. **リファクタリング計画**: レガシーコード削除のタイムライン作成
