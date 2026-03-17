# アビリティ解決コードの問題点分析

## 概要

`engine_rust_src/src/core/logic/interpreter/` ディレクトリ以下のアビリティ解決コードを調査し、以下の問題点を特定しました。

---

## 1. アーキテクチャ上の問題

### 1.1 条件フラグのリセットタイミングが不明確

**ファイル**: [`mod.rs`](engine_rust_src/src/core/logic/interpreter/mod.rs:183-186)

```rust
if real_op == crate::core::enums::O_JUMP_IF_FALSE as i32 {
    if !executor.cond {
        frame.ip = (ip as i32 + 4 + (v * 4)) as usize;
    }
    // Reset cond after JUMP_IF_FALSE
    executor.cond = true;
```

**問題点**:
- `cond` フラグが `JUMP_IF_FALSE` の後で常にリセットされるが、条件が `true` でジャンプしなかった場合もリセットされる
- ネストした条件ブロックで正しく動作しない可能性がある
- 条件評価とジャンプの関係が直感的でない

### 1.2 無限ループ検出の閾値が任意

**ファイル**: [`mod.rs`](engine_rust_src/src/core/logic/interpreter/mod.rs:90-95)

```rust
if executor.steps >= 1000 {
    if state.debug.debug_mode {
        println!("[ERROR] Interpreter infinite loop detected (1000 steps)");
    }
    break;
}
```

**問題点**:
- 1000ステップという閾値が任意で、正当な長いアビリティも中断される可能性がある
- エラー後も処理が継続され、ゲーム状態が壊れる可能性がある
- ユーザーへのフィードバックが不十分

### 1.3 実行フレームのスタック管理が脆弱

**ファイル**: [`mod.rs`](engine_rust_src/src/core/logic/interpreter/mod.rs:64-67)

```rust
fn pop_frame(&mut self) {
    self.stack.pop();
}
```

**問題点**:
- 空のスタックからpopする可能性がある
- `O_RETURN` 処理でフレームをpopした後の状態検証がない

---

## 2. 条件チェックの問題

### 2.1 未実装の条件オペコード

**ファイル**: [`conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs:328)

```rust
C_HAS_KEYWORD => false,
```

**問題点**:
- `C_HAS_KEYWORD` が常に `false` を返す
- キーワード能力を持つカードの判定ができない
- 実装が保留されたままになっている

### 2.2 深さ制限がハードコード

**ファイル**: [`conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs:18)

```rust
if depth > 10 { return false; }
```

**問題点**:
- 深さ制限10がハードコードされている
- 制限に達した場合 `false` を返すが、これが意図した動作か不明
- 再帰的な条件評価で問題が発生する可能性

### 2.3 ビット演算の過度な使用

**ファイル**: [`conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs:102-112)

```rust
C_HAS_MEMBER => {
    let filter_attr = attr & 0x00000000FFFFFFFF;
    let check_self = (attr & (1u64 << 41)) == 0;
    let check_opp = (attr & (1u64 << 40)) != 0 || (attr & (1u64 << 41)) != 0;
    // ...
}
```

**問題点**:
- マジックナンバー（ビット位置40, 41など）が多用されている
- 各ビットの意味がコードから読み取れない
- 定数定義にリファクタリングすべき

### 2.4 条件カウント関数の不完全な実装

**ファイル**: [`conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs:491)

```rust
_ => 0
```

**問題点**:
- 不明な条件IDで0を返すが、これが適切なデフォルト値か不明
- エラーログや警告がない
- デバッグが困難

---

## 3. コスト処理の問題

### 3.1 コスト支払いの失敗時のロールバックがない

**ファイル**: [`costs.rs`](engine_rust_src/src/core/logic/interpreter/costs.rs:168-199)

```rust
AbilityCostType::DiscardHand => {
    let count = cost.value as usize;
    // ...
    for cid in to_discard {
        if let Some(pos) = state.core.players[p_idx].hand.iter().position(|&x| x == cid) {
            state.core.players[p_idx].hand.remove(pos);
            state.core.players[p_idx].discard.push(cid);
        }
    }
    true
}
```

**問題点**:
- 複数カードを捨てる際、途中で失敗しても既に捨てたカードは戻らない
- トランザクション的な処理が必要
- ゲーム状態の一貫性が損なわれる可能性

### 3.2 コストタイプのフォールスルー

**ファイル**: [`costs.rs`](engine_rust_src/src/core/logic/interpreter/costs.rs:96)

```rust
_ => true
```

**問題点**:
- 不明なコストタイプで `true` を返す
- コストが実際には支払われていない
- 新しいコストタイプの追加時にバグを見逃す可能性

### 3.3 タップ状態の不整合

**ファイル**: [`costs.rs`](engine_rust_src/src/core/logic/interpreter/costs.rs:135-154)

```rust
AbilityCostType::TapMember => {
    let player = &mut state.core.players[p_idx];
    let mut needed = cost.value as usize;
    // ...
    for i in 0..3 {
        if !player.is_tapped(i) && player.stage[i] >= 0 {
            player.set_tapped(i, true);
            needed -= 1;
            if needed == 0 { break; }
        }
    }
    needed == 0
}
```

**問題点**:
- タップするメンバーの選択順序が固定（インデックス順）
- プレイヤーの意図しないメンバーがタップされる可能性
- 選択UIとの連携が不明確

---

## 4. サスペンション（中断/再開）の問題

### 4.1 重複する関数定義

**ファイル**: [`suspension.rs`](engine_rust_src/src/core/logic/interpreter/suspension.rs:12-69) と [`suspension.rs`](engine_rust_src/src/core/logic/interpreter/suspension.rs:72-124)

```rust
pub fn suspend_interaction(...) -> bool { ... }
pub fn suspend_interaction_with_db(...) -> bool { ... }
```

**問題点**:
- ほぼ同じ機能の関数が2つ存在
- 片方はソフトロック検出があり、もう片方にはない
- どちらを使うべきか判断が難しい

### 4.2 ソフトロック検出の不完全な実装

**ファイル**: [`suspension.rs`](engine_rust_src/src/core/logic/interpreter/suspension.rs:114-122)

```rust
if actions.len() <= 1 && (actions.is_empty() || actions.contains(&0)) && choice_type != "OPPONENT_CHOOSE" {
    if state.debug.debug_mode {
        println!("[DEBUG] Softlock prevented: {} has no legal actions. Skipping suspension.", choice_type);
    }
    state.interaction_stack.pop();
    state.phase = original_phase;
    state.current_player = original_cp;
    return false;
}
```

**問題点**:
- `actions.contains(&0)` の意味が不明（アクションID 0は何を意味する？）
- すべての選択タイプでソフトロック検出が機能するわけではない
- 検出後の処理が適切かどうか不明

### 4.3 ターゲットスロット解決の複雑なロジック

**ファイル**: [`suspension.rs`](engine_rust_src/src/core/logic/interpreter/suspension.rs:128-140)

```rust
pub fn resolve_target_slot(target_slot: i32, ctx: &AbilityContext) -> usize {
    if target_slot == 0 && ctx.target_slot >= 0 {
        return ctx.target_slot as usize;
    }
    if target_slot == 4 && ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else if target_slot == -1 || target_slot == 4 {
        if ctx.area_idx >= 0 { ctx.area_idx as usize } else { 0 }
    } else {
        target_slot.max(0) as usize
    }
}
```

**問題点**:
- 条件分岐が複雑で理解しにくい
- スロット0とスロット4の特別扱いの理由が不明確
- マジックナンバー（-1, 0, 4）の意味が文書化されていない

---

## 5. ハンドラーの問題

### 5.1 エラーハンドリングの欠如

**ファイル**: [`deck_zones.rs`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:17-50)

```rust
O_SEARCH_DECK => {
    let search_target = ctx.target_slot as usize;
    if search_target < state.core.players[p_idx].deck.len() {
        let cid = state.core.players[p_idx].deck.remove(search_target);
        // ...
    }
    // else の場合の処理がない
}
```

**問題点**:
- `search_target` がデッキ長以上の場合、何も起こらない
- エラーログや警告がない
- 無効な選択が黙って無視される

### 5.2 状態遷移の複雑さ

**ファイル**: [`deck_zones.rs`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:222-335)

```rust
fn handle_move_to_discard(...) -> Option<bool> {
    // 100行以上の複雑な状態遷移ロジック
}
```

**問題点**:
- 単一関数が複数の責任を持っている
- 状態遷移が追いにくい
- テストが困難

### 5.3 v_remaining の使用が一貫していない

**ファイル**: [`deck_zones.rs`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:163-173)

```rust
if ctx.choice_index == 99 || ctx.choice_index == 999 || (v > 0 && ctx.v_remaining == 1) {
    // Done
} else {
    let next_v = if v > 0 { (if ctx.v_remaining > 0 { ctx.v_remaining } else { v as i16 }) - 1 } else { 0 };
    // ...
}
```

**問題点**:
- `v_remaining` の意味と使用方法が一貫していない
- ネストした三項演算子で可読性が低い
- マジックナンバー（99, 999）の意味が不明

---

## 6. フィルター処理の問題

### 6.1 フィルター文字列解析の脆弱性

**ファイル**: [`filter.rs`](engine_rust_src/src/core/logic/interpreter/filter.rs:5-106)

```rust
pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    let mut attr: u64 = 0;
    for part in filter.split(',') {
        // 多数の if-else チェーン
    }
    attr
}
```

**問題点**:
- 不明なフィルター文字列が黙って無視される
- エラー報告がない
- 新しいフィルタータイプの追加が困難

### 6.2 グループIDのマッピングが不完全

**ファイル**: [`filter.rs`](engine_rust_src/src/core/logic/interpreter/filter.rs:36-40)

```rust
let unit_id = match unit_name.as_str() {
    "BIBI" => 0, "LILY_WHITE" | "LILYWHITE" => 2, "QU4RTZ" => 12, "AZUNA" => 11, "DIVERDIVA" => 13, "A_ZU_NA" => 11,
    _ => -1,
};
```

**問題点**:
- 一部のユニットしかマッピングされていない
- `-1` の場合の処理が不適切（`unit_id >= 0` チェックはあるが、何も起こらない）
- データベースとの整合性が不明

---

## 7. 全体的な設計問題

### 7.1 グローバル状態の使用

**ファイル**: [`mod.rs`](engine_rust_src/src/core/logic/interpreter/mod.rs:22)

```rust
pub static GLOBAL_OPCODE_TRACKER: Lazy<Mutex<HashSet<i32>>> = Lazy::new(|| Mutex::new(HashSet::<i32>::new()));
```

**問題点**:
- グローバルな可変状態がテストを困難にする
- 並行実行時の安全性が保証されない
- デバッグ目的で使われているが、より良い方法があるはず

### 7.2 ログ出力の不統一

**ファイル**: 各ファイル

```rust
// 様々なログパターン
println!("[DEBUG] ...");
println!("[ERROR] ...");
state.log("...".to_string());
```

**問題点**:
- ログ出力方法が統一されていない
- 本番環境でのログ制御が困難
- 構造化ログではないため解析が困難

### 7.3 テスト可能性の欠如

**問題点**:
- 多くの関数が `GameState` への可変参照を取り、純粋関数としてテストできない
- モックの使用が困難
- 統合テストに依存せざるを得ない

---

## 推奨される改善策

### 短期的改善

1. **マジックナンバーの定数化**: すべてのビット位置、特殊値（99, 999, -1など）を定数として定義
2. **エラーログの追加**: 黙って失敗する箇所に警告ログを追加
3. **ドキュメントの追加**: 複雑な条件分岐にコメントを追加

### 中期的改善

1. **条件チェックのリファクタリング**: ビット演算をヘルパー関数でカプセル化
2. **コスト処理のトランザクション化**: 失敗時のロールバック機能
3. **状態遷移の明示化**: 状態マシンパターンの導入検討

### 長期的改善

1. **アーキテクチャの見直し**: インタープリターパターンの再設計
2. **型安全性の向上**: ビットフィールドを構造体に置き換え
3. **テストインフラの整備**: ユニットテスト可能な設計への変更

---

## 結論

アビリティ解決コードは機能しているが、保守性と信頼性に多くの問題を抱えています。特に、エラーハンドリングの欠如、複雑な状態管理、マジックナンバーの多用が顕著です。段階的なリファクタリングで改善することを推奨します。
