# interpreter.rs リファクタリング計画

## 現状分析

### ファイル概要
- **ファイルサイズ**: 約2487行、130KB
- **場所**: `engine_rust_src/src/core/logic/interpreter.rs`

### 主要関数の構成

| 関数名 | 行数 | 責任 |
|--------|------|------|
| `map_filter_string_to_attr` | 33-134 (101行) | フィルタ文字列解析 |
| `check_condition` | 137-196 (60行) | 条件チェックラッパー |
| `suspend_interaction` | 203-248 (46行) | インタラクション中断 |
| `resolve_target_slot` | 252-264 (13行) | スロット解決 |
| `check_condition_opcode` | 266-627 (362行) | 条件オペコード処理 |
| `check_cost` | 633-730 (98行) | コスト確認 |
| `pay_cost` | 732-950 (219行) | コスト支払い |
| `get_condition_count` | 952-1001 (50行) | カウント取得 |
| `resolve_bytecode` | 1003-1947 (945行) | **メインバイトコードインタープリタ** |
| `process_trigger_queue` | 1949-1967 (19行) | トリガーキュー処理 |
| `handle_*` 関数群 | 1984-2487 (503行) | 各種ハンドラ |

### 問題点

1. **巨大な `resolve_bytecode` 関数**
   - 約945行の単一関数
   - 60以上のオペコードを巨大なmatch文で処理
   - 深いネストと複雑な制御フロー

2. **関心の分離不足**
   - 条件チェック、コスト処理、バイトコード実行が混在
   - ハンドラ関数がファイル末尾に散在

3. **コード重複**
   - カード選択、ゾーン操作の類似パターン
   - `suspend_interaction` の呼び出しパターン

4. **マジックナンバー**
   - 多くのハードコードされた値
   - 定数が分散

---

## リファクタリング目標

1. **可読性向上**: 各モジュールの責任を明確化
2. **保守性向上**: 機能追加・修正が容易な構造
3. **テスタビリティ向上**: 個別関数のユニットテストが可能
4. **パフォーマンス維持**: リファクタリングによる性能劣化を回避

---

## 提案する新しいファイル構成

```
engine_rust_src/src/core/logic/
├── interpreter/
│   ├── mod.rs              # 公開API、メインループ
│   ├── conditions.rs       # 条件チェック関連
│   ├── costs.rs            # コスト確認・支払い
│   ├── handlers/           # オペコードハンドラ
│   │   ├── mod.rs
│   │   ├── draw.rs         # O_DRAW, O_DRAW_UNTIL 等
│   │   ├── movement.rs     # O_MOVE_MEMBER, O_SWAP_AREA 等
│   │   ├── selection.rs    # O_SELECT_*, O_COLOR_SELECT 等
│   │   ├── recovery.rs     # O_RECOVER_*, O_PLAY_*_FROM_DISCARD
│   │   ├── deck_ops.rs     # O_SEARCH_DECK, O_ORDER_DECK 等
│   │   ├── buffs.rs        # O_ADD_BLADES, O_ADD_HEARTS 等
│   │   └── misc.rs         # その他
│   ├── suspension.rs       # suspend_interaction関連
│   └── filter.rs           # フィルタ文字列解析
├── interpreter.rs          # 後方互換性のためのre-export（最終的に削除）
```

---

## 詳細実装手順

### フェーズ1: 条件・コスト関数の抽出

#### ステップ1.1: `conditions.rs` の作成

```rust
// engine_rust_src/src/core/logic/interpreter/conditions.rs

use crate::core::logic::{GameState, CardDatabase, AbilityContext};

/// 条件チェックの結果型
pub struct ConditionResult {
    pub passed: bool,
    pub bypassed: bool,
}

/// 条件オペコードを処理
pub fn check_condition_opcode(
    state: &GameState,
    db: &CardDatabase,
    op: i32,
    val: i32,
    attr: u64,
    slot: i32,
    ctx: &AbilityContext,
    depth: u32
) -> bool { ... }

/// 条件構造体をチェック
pub fn check_condition(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    cond: &Condition,
    ctx: &AbilityContext,
    depth: u32
) -> bool { ... }

/// カウント系条件の取得
pub fn get_condition_count(
    state: &GameState,
    db: &CardDatabase,
    cond_id: i32,
    attr: i32,
    ctx: &AbilityContext
) -> i32 { ... }
```

**移動対象**:
- `map_filter_string_to_attr` → `filter.rs`
- `check_condition` → `conditions.rs`
- `check_condition_opcode` → `conditions.rs`
- `get_condition_count` → `conditions.rs`

#### ステップ1.2: `costs.rs` の作成

```rust
// engine_rust_src/src/core/logic/interpreter/costs.rs

/// コスト確認
pub fn check_cost(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    cost: &Cost,
    ctx: &AbilityContext
) -> bool { ... }

/// コスト支払い
pub fn pay_cost(
    state: &mut GameState,
    db: &CardDatabase,
    p_idx: usize,
    cost: &Cost,
    ctx: &AbilityContext
) -> bool { ... }
```

### フェーズ2: オペコードハンドラの抽出

#### ステップ2.1: ハンドラトレイトの定義

```rust
// engine_rust_src/src/core/logic/interpreter/handlers/mod.rs

use crate::core::logic::{GameState, CardDatabase, AbilityContext};

/// オペコードハンドラの結果
pub enum HandlerResult {
    /// 継続実行
    Continue,
    /// 条件値を更新
    SetCond(bool),
    /// 中断（ユーザー入力待ち）
    Suspend,
    /// リターン（終了）
    Return,
}

/// オペコードハンドラトレイト
pub trait OpcodeHandler {
    fn handle(
        &self,
        state: &mut GameState,
        db: &CardDatabase,
        ctx: &mut AbilityContext,
        v: i32,
        a: i32,
        s: i32,
        instr_ip: usize,
    ) -> HandlerResult;
}
```

#### ステップ2.2: ハンドラモジュールの実装例

```rust
// engine_rust_src/src/core/logic/interpreter/handlers/draw.rs

use super::{HandlerResult, OpcodeHandler};

pub struct DrawHandler;
pub struct DrawUntilHandler;
pub struct EnergyChargeHandler;

impl OpcodeHandler for DrawHandler {
    fn handle(
        &self,
        state: &mut GameState,
        db: &CardDatabase,
        ctx: &mut AbilityContext,
        v: i32,
        a: i32,
        s: i32,
        _instr_ip: usize,
    ) -> HandlerResult {
        let p_idx = ctx.player_id as usize;
        let count = v as u32;

        if s == 2 {
            state.draw_cards(1 - p_idx, count);
        } else if s == 3 {
            state.draw_cards(0, count);
            state.draw_cards(1, count);
        } else {
            state.draw_cards(p_idx, count);
        }

        state.log_turn_event(
            "EFFECT",
            ctx.source_card_id,
            ctx.ability_index,
            p_idx as u8,
            &format!("Draw {} card(s)", count)
        );

        HandlerResult::Continue
    }
}
```

#### ステップ2.3: ハンドラのカテゴリ分け

| モジュール | オペコード | 説明 |
|------------|-----------|------|
| `draw.rs` | O_DRAW, O_DRAW_UNTIL, O_ADD_TO_HAND | ドロー関連 |
| `movement.rs` | O_MOVE_MEMBER, O_SWAP_AREA, O_SWAP_ZONE, O_FORMATION_CHANGE | 移動・交換 |
| `selection.rs` | O_SELECT_MEMBER, O_SELECT_LIVE, O_COLOR_SELECT, O_SELECT_MODE | 選択系 |
| `recovery.rs` | O_RECOVER_LIVE, O_RECOVER_MEMBER, O_PLAY_MEMBER_FROM_DISCARD | 回復・再利用 |
| `deck_ops.rs` | O_SEARCH_DECK, O_ORDER_DECK, O_LOOK_DECK, O_REVEAL_CARDS | デッキ操作 |
| `buffs.rs` | O_ADD_BLADES, O_ADD_HEARTS, O_SET_HEARTS, O_REDUCE_HEART_REQ | バフ・デバフ |
| `cost_ops.rs` | O_PAY_ENERGY, O_REDUCE_COST, O_INCREASE_COST | コスト操作 |
| `tap.rs` | O_TAP_MEMBER, O_TAP_OPPONENT, O_ACTIVATE_MEMBER, O_SET_TAPPED | タップ関連 |
| `restrictions.rs` | O_RESTRICTION, O_PREVENT_*, O_NEGATE_EFFECT | 制限・防止 |
| `misc.rs` | O_NOP, O_RETURN, O_JUMP, O_JUMP_IF_FALSE, O_FLAVOR | その他 |

### フェーズ3: メインループのリファクタリング

#### ステップ3.1: 新しい `resolve_bytecode` 構造

```rust
// engine_rust_src/src/core/logic/interpreter/mod.rs

mod conditions;
mod costs;
mod handlers;
mod suspension;
mod filter;

use handlers::{HandlerRegistry, HandlerResult};

pub fn resolve_bytecode(
    state: &mut GameState,
    db: &CardDatabase,
    bytecode: &[i32],
    ctx_in: &AbilityContext
) {
    // ハードコード処理のチェック
    if ctx_in.program_counter == 0 {
        if crate::core::hardcoded::execute_hardcoded_ability(...) {
            return;
        }
    }

    // スタック初期化
    let mut executor = BytecodeExecutor::new(bytecode, ctx_in);

    // ハンドラレジストリ初期化
    let registry = HandlerRegistry::new();

    // メインループ
    while let Some(frame) = executor.current_frame() {
        let op = frame.read_opcode();

        // 条件オペコードの処理
        if is_condition_opcode(op) {
            executor.cond = conditions::check_condition_opcode(...);
            continue;
        }

        // ジャンプ命令の処理
        if is_jump_opcode(op) {
            executor.handle_jump(op);
            continue;
        }

        // 通常オペコードの処理
        match registry.dispatch(state, db, &mut executor.ctx, op, v, a, s, instr_ip) {
            HandlerResult::Continue => {},
            HandlerResult::SetCond(c) => executor.cond = c,
            HandlerResult::Suspend => return,
            HandlerResult::Return => break,
        }

        // choice_indexのリセット
        executor.ctx.choice_index = -1;
    }
}
```

#### ステップ3.2: `BytecodeExecutor` 構造体

```rust
/// バイトコード実行コンテキスト
struct BytecodeExecutor<'a> {
    stack: [ExecutionFrame<'a>; MAX_DEPTH],
    sp: usize,
    cond: bool,
    steps: u32,
}

struct ExecutionFrame<'a> {
    bytecode: &'a [i32],
    ip: usize,
    ctx: AbilityContext,
}

impl<'a> BytecodeExecutor<'a> {
    fn new(bytecode: &'a [i32], ctx: &AbilityContext) -> Self { ... }

    fn current_frame(&mut self) -> Option<&mut ExecutionFrame<'a>> { ... }

    fn handle_jump(&mut self, op: i32, v: i32) { ... }

    fn push_frame(&mut self, bytecode: &'a [i32], ctx: AbilityContext) -> bool { ... }

    fn pop_frame(&mut self) { ... }
}
```

### フェーズ4: suspension モジュールの整理

```rust
// engine_rust_src/src/core/logic/interpreter/suspension.rs

/// インタラクション中断処理
pub fn suspend_interaction(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    instr_ip: usize,
    effect_opcode: i32,
    target_slot: i32,
    choice_type: &str,
    choice_text: &str,
    filter_attr: u64,
    v_remaining: i16,
) -> bool { ... }

/// 選択テキスト取得
pub fn get_choice_text(db: &CardDatabase, ctx: &AbilityContext) -> String { ... }

/// ターゲットスロット解決
pub fn resolve_target_slot(target_slot: i32, ctx: &AbilityContext) -> usize { ... }
```

---

## 移行戦略

### 段階的移行

1. **後方互換性維持**
   - 元の `interpreter.rs` は re-export として残す
   - すべての公開関数を再エクスポート

```rust
// engine_rust_src/src/core/logic/interpreter.rs
// 後方互換性のための再エクスポート

#[deprecated(note = "Use logic::interpreter::conditions::check_condition instead")]
pub use super::interpreter::conditions::check_condition;

#[deprecated(note = "Use logic::interpreter::costs::check_cost instead")]
pub use super::interpreter::costs::check_cost;

// ... その他
```

2. **テストによる検証**
   - 各移行ステップで既存テストを実行
   - 新しいモジュールごとにユニットテストを追加

3. **インポートパスの更新**
   - 新しいパスへの移行を段階的に実施
   - deprecation 警告を活用

---

## テスト計画

### ユニットテスト

各モジュールに以下のテストを追加:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_check_condition_opcode_has_member() { ... }

    #[test]
    fn test_check_cost_energy() { ... }

    #[test]
    fn test_draw_handler() { ... }
}
```

### 統合テスト

- 既存のカードテスト（`tests/repro_bp4_001.rs` 等）が引き続き通ることを確認
- オペコード組み合わせテスト（`plans/opcode_combination_test_plan.md`）の実行

---

## リスクと対策

| リスク | 影響 | 対策 |
|--------|------|------|
| パフォーマンス劣化 | 高 | ベンチマーク測定、インライン最適化の維持 |
| 動作変更 | 高 | 既存テストの維持、段階的移行 |
| 循環依存 | 中 | モジュール境界の明確化、依存関係図の作成 |
| コンパイル時間増加 | 低 | 増分コンパイルの活用 |

---

## 推定作業項目

### 必須項目
- [ ] `interpreter/` ディレクトリ構造の作成
- [ ] `conditions.rs` の抽出
- [ ] `costs.rs` の抽出
- [ ] `suspension.rs` の抽出
- [ ] `filter.rs` の抽出
- [ ] ハンドラトレイトの定義
- [ ] 各ハンドラモジュールの実装
- [ ] `BytecodeExecutor` の実装
- [ ] メインループのリファクタリング
- [ ] 後方互換re-exportの追加
- [ ] テストの移行・追加

### オプション項目
- [ ] 定数の整理（マジックナンバーの定数化）
- [ ] ドキュメントコメントの追加
- [ ] エラーハンドリングの改善

---

## 成功基準

1. **機能**: すべての既存テストが通る
2. **可読性**: 各ファイルが500行以下
3. **保守性**: 新しいオペコード追加が1ファイルの編集で完結
4. **パフォーマンス**: ベンチマークで5%以内の性能変化

---

## 参考資料

- [`interpreter.rs`](../engine_rust_src/src/core/logic/interpreter.rs) - 現在の実装
- [`handlers.rs`](../engine_rust_src/src/core/logic/handlers.rs) - 既存のフェーズハンドラ
- [`game.rs`](../engine_rust_src/src/core/logic/game.rs) - ゲーム状態管理
