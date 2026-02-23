# 失敗テスト修正計画

## 現在の失敗テスト (3件)

### 1. `test_opcode_tap_opponent_dynamic`

**根本原因**: 
カードPL!-pb1-015-R (ID: 4196) のバイトコード:
```
[206, 0, 0, 0, 53, 1, 2, 4, 32, 99, 99, 2, 1, 0, 0, 0]
```
- 206 = IS_CENTER条件
- 53 = O_TAP_MEMBER（オプショナルコスト）
- 32 = O_TAP_OPPONENT

オプショナルコスト(O_TAP_MEMBER)が最初に"OPTIONAL"インタラクションを生成するため、テストの期待値"TAP_O"と実際の"OPTIONAL"が一致しない。

**解決策**: テストを修正して、オプショナルコストがある場合の正しい動作を検証する。

---

### 2. `test_repro_bp4_002_p_wait_flow`

**根本原因**: 
WAIT選択後、フェーズが`Main`に戻ってしまい、`LOOK_AND_CHOOSE`インタラクションが続いていない。カード558のWAITメカニクスが正しく処理されていない。

**調査が必要**: カード558のバイトコードとWAITメカニクスの実装を確認。

---

### 3. `test_archetype_sd1_001_success_live_cond`

**根本原因**: 
カードPL!-sd1-001-SD (ID: 120) のバイトコード:
```
[218, 2, 0, 0, 15, 1, 0, 6, 1, 0, 0, 0]
```
- 218 = C_COUNT_SUCCESS_LIVE条件
- 15 = O_RECOVER_LIVE

**インタプリタの問題**: 条件オペコード(218)の後、`executor.cond`フラグが設定されるが、次の効果オペコード(15)がこのフラグをチェックせずに実行される。

**解決策**: インタプリタを修正して、`cond`がfalseの場合は効果オペコードをスキップする。

---

## 修正の優先順位

1. **インタプリタ修正** (test_archetype_sd1_001_success_live_cond)
   - `engine_rust_src/src/core/logic/interpreter/mod.rs`の`resolve_bytecode`関数を修正
   - 条件がfalseの場合、効果オペコードをスキップするロジックを追加

2. **テスト修正** (test_opcode_tap_opponent_dynamic)
   - テストの期待値を修正
   - オプショナルコストがある場合の正しい動作を検証

3. **調査と修正** (test_repro_bp4_002_p_wait_flow)
   - カード558のバイトコードを確認
   - WAITメカニクスの実装を確認

---

## インタプリタ修正の詳細

### 現在のコード (interpreter/mod.rs)

```rust
// 条件オペコード処理
if real_op >= 200 && real_op <= 255 {
    let passed = conditions::check_condition_opcode(...);
    executor.cond = executor.cond && if is_negated { !passed } else { passed };
    continue;
}

// 効果オペコード処理 - condチェックなし
match registry.dispatch(...) { ... }
```

### 修正後のコード

```rust
// 条件オペコード処理
if real_op >= 200 && real_op <= 255 {
    let passed = conditions::check_condition_opcode(...);
    executor.cond = executor.cond && if is_negated { !passed } else { passed };
    continue;
}

// 制御フローオペコードは常に実行
if real_op == O_JUMP as i32 || real_op == O_JUMP_IF_FALSE as i32 
   || real_op == O_RETURN as i32 || real_op == O_NOP as i32 {
    // 制御フローの処理...
}

// 条件がfalseの場合、効果オペコードをスキップ
if !executor.cond {
    // condがfalseの場合、このオペコードをスキップ
    // ただし、condをリセットしない（JUMP_IF_FALSEが処理する）
    continue;
}

// 効果オペコード処理
match registry.dispatch(...) { ... }
```

---

## 検証方法

1. 修正後に全テストを実行
2. 特に条件付き能力を持つカードの動作を確認
3. リグレッションテストを実行して既存のテストが壊れていないことを確認
