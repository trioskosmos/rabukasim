# スキップされるテストを実行可能にするプラン

## 現状
```
PASS: 57, FAIL: 168, SKIP: 701
```

## 目標
すべてのスキップされたテストを少なくとも実行可能にする（失敗してもOK）

---

## スキップ原因の分析

テストコード [`test_gpu_parity_semantic.rs`](engine_rust_src/src/bin/test_gpu_parity_semantic.rs) を分析した結果、以下の5つのスキップ条件が見つかりました：

### 1. トリガータイプによるスキップ (lines 53-59)

```rust
// Skip triggers that need special setup not yet implemented
let trigger_type = map_trigger_type(&ability.trigger);
if trigger_type != TriggerType::OnPlay
    && trigger_type != TriggerType::Constant {
    println!("  [SKIP] {} (trigger: {})", test_name, ability.trigger);
    skip_count += 1;
    continue;
}
```

**影響**: ONLIVESTART, ACTIVATED, ONLIVESUCCESS, ONLEAVES, ONREVEAL などのトリガー

**対応策**:
- このチェックを削除または緩和
- 各トリガータイプ用のテスト関数を実装（一部は既に実装済み）

---

### 2. 条件付きCONSTANTトリガーのスキップ (lines 61-66)

```rust
// Skip CONSTANT triggers with conditions (conditions not evaluated in test)
if trigger_type == TriggerType::Constant && !ability.conditions.is_empty() {
    println!("  [SKIP] {} (conditional constant)", test_name);
    skip_count += 1;
    continue;
}
```

**影響**: 条件を持つCONSTANTトリガー

**対応策**:
- 条件評価をスキップして実行
- または条件を無視して実行

---

### 3. 空シーケンスのスキップ (lines 68-73)

```rust
// Skip abilities with empty sequences
if ability.sequence.is_empty() {
    println!("  [SKIP] {} (empty sequence)", test_name);
    skip_count += 1;
    continue;
}
```

**影響**: パースエラーまたは元データが空

**対応策**:
- このチェックを削除
- 空シーケンスは「何もしない」として成功とみなす

---

### 4. デルタなしのスキップ (lines 80-85)

```rust
// Skip if no deltas to verify
if all_deltas.is_empty() {
    println!("  [SKIP] {} (no deltas)", test_name);
    skip_count += 1;
    continue;
}
```

**影響**: 状態変化を伴わない効果

**対応策**:
- このチェックを削除
- デルタなしは「何も検証しない」として成功とみなす

---

### 5. サポートされていないトリガー (lines 98-102)

```rust
_ => {
    println!("  [SKIP] {} (unsupported trigger: {})", test_name, ability.trigger);
    skip_count += 1;
    continue;
}
```

**影響**: ONLIVESUCCESS, TURNSTART, TURNEND, ONLEAVES, ONREVEAL, ONPOSITIONCHANGE

**対応策**:
- 各トリガー用のテスト関数を実装
- またはデフォルトのテスト関数を作成

---

## 実装プラン

### フェーズ1: スキップチェックの緩和

1. **トリガータイプチェックの削除** (lines 53-59)
   - このチェックを削除
   - 代わりにmatch文で各トリガーを処理

2. **条件付きCONSTANTチェックの削除** (lines 61-66)
   - このチェックを削除
   - 条件は無視して実行

3. **空シーケンスチェックの削除** (lines 68-73)
   - このチェックを削除
   - 空シーケンスは成功として扱う

4. **デルタなしチェックの削除** (lines 80-85)
   - このチェックを削除
   - デルタなしは成功として扱う

### フェーズ2: トリガー別テスト関数の実装

既存のテスト関数:
- [`run_single_semantic_test()`](engine_rust_src/src/bin/test_gpu_parity_semantic.rs:164) - OnPlay/Constant用
- [`run_onlivestart_test()`](engine_rust_src/src/bin/test_gpu_parity_semantic.rs:247) - OnLiveStart用
- [`run_activated_test()`](engine_rust_src/src/bin/test_gpu_parity_semantic.rs:306) - Activated用

新規実装が必要:
- `run_onlivesuccess_test()` - OnLiveSuccess用
- `run_turnstart_test()` - TurnStart用
- `run_turnend_test()` - TurnEnd用
- `run_onleaves_test()` - OnLeaves用
- `run_onreveal_test()` - OnReveal用
- `run_onpositionchange_test()` - OnPositionChange用

### フェーズ3: デフォルトテスト関数の作成

汎用的なテスト関数を作成し、未知のトリガータイプでも実行可能にする：

```rust
fn run_generic_trigger_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    trigger_type: TriggerType,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    // カードを適切な位置に配置
    // トリガーを発火
    // デルタを検証
}
```

---

## コード変更の詳細

### 変更1: メインループのスキップチェック削除

```rust
// Before (lines 52-85)
// Skip triggers that need special setup not yet implemented
let trigger_type = map_trigger_type(&ability.trigger);
if trigger_type != TriggerType::OnPlay
    && trigger_type != TriggerType::Constant {
    println!("  [SKIP] {} (trigger: {})", test_name, ability.trigger);
    skip_count += 1;
    continue;
}

// Skip CONSTANT triggers with conditions
if trigger_type == TriggerType::Constant && !ability.conditions.is_empty() {
    println!("  [SKIP] {} (conditional constant)", test_name);
    skip_count += 1;
    continue;
}

// Skip abilities with empty sequences
if ability.sequence.is_empty() {
    println!("  [SKIP] {} (empty sequence)", test_name);
    skip_count += 1;
    continue;
}

// Collect all deltas from the sequence
let all_deltas: Vec<SemanticDelta> = ability.sequence.iter()
    .flat_map(|seg| seg.deltas.clone())
    .collect();

// Skip if no deltas to verify
if all_deltas.is_empty() {
    println!("  [SKIP] {} (no deltas)", test_name);
    skip_count += 1;
    continue;
}
```

```rust
// After
let trigger_type = map_trigger_type(&ability.trigger);

// Collect all deltas from the sequence
let all_deltas: Vec<SemanticDelta> = ability.sequence.iter()
    .flat_map(|seg| seg.deltas.clone())
    .collect();

// Log skip reasons but continue execution
if ability.sequence.is_empty() {
    println!("  [INFO] {} has empty sequence", test_name);
}
if all_deltas.is_empty() {
    println!("  [INFO] {} has no deltas", test_name);
}
```

### 変更2: match文の拡張

```rust
// Before (lines 88-103)
let result = match trigger_type {
    TriggerType::OnPlay | TriggerType::Constant => {
        run_single_semantic_test(&manager, &db, card_id, ab_idx, trigger_type, &all_deltas)
    }
    TriggerType::OnLiveStart => {
        run_onlivestart_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::Activated => {
        run_activated_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    _ => {
        println!("  [SKIP] {} (unsupported trigger: {})", test_name, ability.trigger);
        skip_count += 1;
        continue;
    }
};
```

```rust
// After
let result = match trigger_type {
    TriggerType::OnPlay | TriggerType::Constant => {
        run_single_semantic_test(&manager, &db, card_id, ab_idx, trigger_type, &all_deltas)
    }
    TriggerType::OnLiveStart => {
        run_onlivestart_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::Activated => {
        run_activated_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::OnLiveSuccess => {
        run_onlivesuccess_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::TurnStart => {
        run_turnstart_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::TurnEnd => {
        run_turnend_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::OnLeaves => {
        run_onleaves_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    TriggerType::OnReveal => {
        run_onreveal_test(&manager, &db, card_id, ab_idx, &all_deltas)
    }
    _ => {
        // Unknown trigger - try generic test
        run_generic_trigger_test(&manager, &db, card_id, ab_idx, trigger_type, &all_deltas)
    }
};
```

---

## 期待される結果

| 変更前 | 変更後 |
|--------|--------|
| PASS: 57, FAIL: 168, SKIP: 701 | PASS: ~57, FAIL: ~600, SKIP: ~0 |

スキップされたテストの多くは失敗する可能性が高いですが、少なくとも実行されるようになります。

---

## 次のステップ

1. このプランをユーザーに確認
2. Codeモードに切り替えて実装
3. テスト実行して結果を確認
