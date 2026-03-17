# RS Engine Logic Analysis Report

## 概要 (Executive Summary)

RSエンジン (`engine_rust_src`) は、130以上のオペコードを持つ複雑なカードゲームロジック 시스템을実装しています。ロジック코드는複数の责務が混杂しており、変更とテストが困難な状態にあります。

---

## 1. 現在のアーキテクチャ

### 1.1 ディレクトリ構造

```
engine_rust_src/src/core/logic/
├── action_factory.rs      # Action ID <-> Struct 変換
├── action_gen/           # アクション生成
│   ├── response.rs       # 応答アクション生成 (大きなmatch文)
│   ├── main_phase.rs     # メインフェーズ
│   ├── mulligan.rs       # マリガン
│   └── live_set.rs      # Liveセット
├── handlers.rs           # PhaseHandlers トレイト (大きなtrait)
├── interpreter/          # バイトコードインタープリタ
│   ├── mod.rs            # メインループ (BytecodeExecutor)
│   ├── handlers.rs       # ★ 最大ファイル: オペコードディスパッチ (130k+ 行)
│   ├── conditions.rs     # 条件チェック (43k+ 行)
│   ├── costs.rs          # コストチェック
│   ├── suspension.rs      # ユーザーインタラクション一時停止
│   └── constants.rs      # フラグ定数
├── game.rs               # GameState 実装 (56k+ 行)
├── card_db.rs            # カードデータベース (29k+ 行)
├── rules.rs              # ルールチェック
├── filter.rs             # カードフィルタリング
├── player.rs             # プレイヤー状態
└── models.rs             # Ability, AbilityContext など
```

---

## 2. 複雑性の主要原因

### 2.1 HandlerRegistry (interpreter/handlers.rs)

**問題点:**
- 130k行以上の单一の大きなファイル
- 100以上のオペコードを1つの大きな`match`文で处理
- すべての Handler 関数がこのファイルに定义されている

**现状のコード例:**
```rust
// interpreter/handlers.rs より
match op {
    O_SELECT_MODE => { /* ... */ }
    // 1. Meta / Control
    O_NEGATE_EFFECT | O_REDUCE_YELL_COUNT | O_RESTRICTION | ... => {
        handle_meta_control(state, db, ctx, op, v, a, s, instr_ip)
            .unwrap_or(HandlerResult::Continue)
    }
    // 2. Draw / Hand
    O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => {
        handle_draw(state, db, ctx, op, v, a, s).unwrap_or(HandlerResult::Continue)
    }
    // ... 100+ cases
    _ => { /* unhandled warning */ }
}
```

### 2.2 ResponseGenerator (action_gen/response.rs)

**問題点:**
- 複雑な `choice_type` ストリングベースの分支
- 40种类以上の choice_type を処理

**现状のコード例:**
```rust
// action_gen/response.rs より
match choice_type.as_str() {
    "OPTIONAL" => { /* ... */ }
    "PAY_ENERGY" => { /* ... */ }
    "SELECT_CARDS" => { /* ... */ }
    "LOOK_AND_CHOOSE" => { /* ... */ }
    "SELECT_MEMBER" => { /* ... */ }
    // ... 40+ types
}
```

### 2.3 PhaseHandlers Trait (handlers.rs)

**问题点:**
- 30以上のメソッドを持つ大きなトレイト
- すべてのメソッドが GameState に実装されている
- 责任が混杂 (RPS處理、マリガン、メインフェーズ、レスポンド)

**现状のコード例:**
```rust
// handlers.rs (PhaseHandlers trait)
pub trait PhaseHandlers {
    fn handle_rps(&mut self, action: i32) -> Result<(), String>;
    fn handle_turn_choice(&mut self, action: i32) -> Result<(), String>;
    fn handle_mulligan(&mut self, action: i32) -> Result<(), String>;
    fn handle_main(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    fn handle_liveset(&mut self, action: i32) -> Result<(), String>;
    fn handle_liveresult(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    fn handle_response(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    // ... 20+ more methods
}
```

### 2.4 Constants の分散

**问题点:**
- `generated_constants.rs`: オペコード、定数のベースID
- `interpreter/constants.rs`: インタープリタ用フラグ
- `enums.rs`: 列挙型
- 重複と不整合のリスク

---

## 3. 改善方案

### 3.1 HandlerRegistry のリファクタリング

**目标:** 责任每の分离 + ファイルサイズの缩小

**方案 A: オペコードカテゴリ每のモジュール分割**

```
interpreter/handlers/
├── mod.rs           # HandlerRegistry (简单的ディスパッチのみ)
├── control.rs       # O_NEGATE_EFFECT, O_RESTRICTION, etc.
├── draw.rs          # O_DRAW, O_DRAW_UNTIL, O_ADD_TO_HAND
├── member.rs        # O_ACTIVATE_MEMBER, O_MOVE_MEMBER, etc.
├── energy.rs        # O_ENERGY_CHARGE, O_PAY_ENERGY, etc.
├── deck.rs          # O_SEARCH_DECK, O_LOOK_DECK, etc.
├── score.rs         # O_BOOST_SCORE, O_BUFF_POWER, etc.
└── choice.rs        # O_SELECT_MODE, O_SELECT_MEMBER, etc.
```

**方案 B: Procedural Macro による自动化**

```rust
// 想要の形
#[opcode_handler(O_DRAW)]
fn handle_draw(ctx: &mut AbilityContext, v: i32, a: i64, s: i32) -> HandlerResult {
    // ...
}

#[opcode_handler(O_DRAW_UNTIL)]
fn handle_draw_until(ctx: &mut AbilityContext, v: i32, a: i64, s: i32) -> HandlerResult {
    // ...
}
```

### 3.2 ResponseGenerator の改善

**目标:** ストリングベースの分支を排除

**方案: Enum への置換**

```rust
// 現在の形 (string matching)
match choice_type.as_str() {
    "OPTIONAL" => { /* ... */ }
    "PAY_ENERGY" => { /* ... */ }
}

// 改善后的形 (type-safe enum)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ChoiceType {
    Optional,
    PayEnergy,
    SelectCards { min: u8, max: u8 },
    LookAndChoose,
    SelectMember,
    // ...
}

impl ChoiceType {
    pub fn from_str(s: &str) -> Option<Self> { /* ... */ }
}
```

### 3.3 PhaseHandlers の分割

**目标:** トレイトの缩小 + 责任の明确化

**方案:**

```rust
// 分割后的形
pub trait TurnController {
    fn handle_rps(&mut self, action: i32) -> Result<(), String>;
    fn handle_turn_choice(&mut self, action: i32) -> Result<(), String>;
}

pub trait MulliganController {
    fn handle_mulligan(&mut self, action: i32) -> Result<(), String>;
    fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>);
}

pub trait MainPhaseController {
    fn handle_main(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    fn play_member(&mut self, /* ... */) -> Result<(), String>;
}

pub trait ResponseController {
    fn handle_response(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
}
```

### 3.4 Constants の统合

**目标:** 单一の情報源

```rust
// constants/mod.rs
pub mod opcodes {
    include!("generated_opcodes.rs"); // ツールで自动生成
}

pub mod interpreter_flags {
    include!("generated_interpreter_flags.rs");
}
```

---

## 4. 推奨される实施顺路

| 顺路 | 作业 | 期待效果 | 风险 |
|------|------|----------|------|
| 1 | ResponseGenerator の Enum 化 | 高 (タイプセーフティ向上) | 低 |
| 2 | HandlerRegistry のモジュール分割 | 高 (ファイルサイズ缩小) | 中 (API変更) |
| 3 | PhaseHandlers の分割 | 中 (责任明确化) | 中 (実装変更) |
| 4 | Constants の统合 | 低 (保守性向上) | 低 |

---

## 5. 结论

現在のRSエンジンは、130以上のオペコードと复雑な状态管理を持つ坚牢なシステムですが、以下の问題があります：

1. **大きな单一ファイル**: interpreter/handlers.rs が非常に大きく、ナビゲーションが困难
2. **ストリングベース Dispatch**: choice_type の string matching がエラーorman
3. **责任の混杂**: PhaseHandlers トレイトが多くの责務を持つ

**最优先で实施すべきは ResponseGenerator の Enum 化です。** これは比较的小さく、效果が大きく、风险が低い作业です。

---

*Report generated: 2026-03-04*
