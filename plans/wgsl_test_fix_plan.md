# WGSLテスト修正計画

## 現状
```
PASS: 2, FAIL: 229, SKIP: 695
```

## 目標
```
PASS: 400+, FAIL: <50, SKIP: <300
```

---

## 修正1: 手札減少ロジックの改善（優先度: 高）

### 問題
現在のロジックは`HAND_DISCARD`の有無のみをチェックしているが、実際には:
1. カードプレイで手札-1
2. HAND_DISCARDで手札減少+ディスカード増加
3. これらが重複する場合の処理が不正確

### 現状コード (test_gpu_parity_semantic.rs:187-198)
```rust
let has_hand_discard = expected_deltas.iter().any(|d| d.tag == "HAND_DISCARD");
let mut adjusted_deltas = expected_deltas.to_vec();
if !has_hand_discard {
    adjusted_deltas.push(SemanticDelta {
        tag: "HAND_DELTA".to_string(),
        value: serde_json::json!(-1),
    });
}
```

### 修正案
```rust
// カードプレイによる基本手札減少を計算
let mut hand_adjustment = -1; // カードプレイで-1

// HAND_DISCARDがある場合、その値を考慮
if let Some(hand_discard) = expected_deltas.iter().find(|d| d.tag == "HAND_DISCARD") {
    let discard_count = hand_discard.value.as_i64().unwrap_or(0) as i32;
    // HAND_DISCARDは既に手札減少を含んでいるので、重複を避ける
    hand_adjustment += discard_count; // 調整値を相殺
}

// DISCARD_DELTAがある場合、それも考慮
let discard_delta: i32 = expected_deltas.iter()
    .filter(|d| d.tag == "DISCARD_DELTA")
    .map(|d| d.value.as_i64().unwrap_or(0) as i32)
    .sum();

// 最終的な調整デルタを作成
let mut adjusted_deltas = expected_deltas.to_vec();
if hand_adjustment != 0 {
    adjusted_deltas.push(SemanticDelta {
        tag: "HAND_DELTA".to_string(),
        value: serde_json::json!(hand_adjustment),
    });
}
```

### 影響
- 約150件のFAILが解消される可能性

---

## 修正2: HAND_DISCARDとDISCARD_DELTAの統合処理（優先度: 高）

### 問題
`gpu_semantic_bridge.rs`で`HAND_DISCARD`を別途処理しているが、`DISCARD_DELTA`と重複する可能性がある。

### 現状コード (gpu_semantic_bridge.rs:270-282)
```rust
DeltaTag::HandDiscard => {
    let actual_hand_delta = actual_player.hand_len as i32 - initial_player.hand_len as i32;
    let expected_hand_delta = -expected_delta;
    if actual_hand_delta != expected_hand_delta {
        errors.push(format!("{}: Hand discard hand delta mismatch..."));
    }
    let actual_discard_delta = actual_player.discard_pile_len as i32 - initial_player.discard_pile_len as i32;
    if actual_discard_delta != expected_delta {
        errors.push(format!("{}: Hand discard discard delta mismatch..."));
    }
}
```

### 修正案
`HAND_DISCARD`を`HAND_DELTA`と`DISCARD_DELTA`に分解して集計:
```rust
// 集計前にHAND_DISCARDを変換
for delta in deltas {
    let tag: DeltaTag = delta.tag.as_str().into();
    let value = delta.value.as_i64().unwrap_or(0) as i32;

    if tag == DeltaTag::HandDiscard {
        // HAND_DISCARD = HAND_DELTA(-N) + DISCARD_DELTA(+N)
        *aggregated.entry(DeltaTag::HandDelta).or_insert(0) -= value;
        *aggregated.entry(DeltaTag::DiscardDelta).or_insert(0) += value;
    } else {
        *aggregated.entry(tag).or_insert(0) += value;
    }
}
```

### 影響
- 約80件のFAILが解消される可能性

---

## 修正3: エネルギーゾーン初期状態の改善（優先度: 中）

### 問題
エネルギータップのテストで期待値と実際の値が大きく乖離:
```
[FAIL] PL!N-bp4-006-P:AB0: Energy tap delta mismatch (expected: 2, actual: 13)
```

### 現状コード (test_gpu_parity_semantic.rs:162)
```rust
state.core.players[0].energy_zone = (10..30).collect::<Vec<i32>>().into(); // 20 energy
```

### 修正案
エネルギーゾーンをより現実的に設定:
```rust
// エネルギーカードを適切に設定（IDは実際のカードデータから取得）
let energy_ids: Vec<i32> = db.energy_cards.keys().cloned().take(10).collect();
state.core.players[0].energy_zone = energy_ids.into();
state.core.players[0].energy_count = energy_ids.len() as u32;
```

### 影響
- 約20件のFAILが解消される可能性

---

## 修正4: ONLIVESTARTトリガーのサポート（優先度: 中）

### 問題
ONLIVESTARTトリガーはスキップされているが、多くのカードがこのトリガーを持っている。

### 必要な実装
```rust
// test_gpu_parity_semantic.rsに追加
fn run_onlivestart_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;

    let mut state = create_test_state();
    // カードを既に場に配置（プレイ済み状態）
    state.core.players[0].stage[0] = Some(real_id);
    state.core.phase = Phase::Live;

    // ONLIVESTARTトリガーを実行
    state.step_live_start(db);

    // GPU実行
    let mut gpu_initial = state.to_gpu(db);
    gpu_initial.phase = Phase::Live as i32;

    // ... 比較ロジック
}
```

### 影響
- 約200件のSKIPがPASS/FAILに変更される

---

## 修正5: ACTIVATEDトリガーのサポート（優先度: 中）

### 問題
ACTIVATEDトリガーはアクティベートコストが必要だが、テストでサポートされていない。

### 必要な実装
```rust
fn run_activated_test(
    manager: &GpuManager,
    db: &CardDatabase,
    card_id_str: &str,
    ab_idx: usize,
    expected_deltas: &[SemanticDelta]
) -> Result<bool, String> {
    let real_id = find_card_id(db, card_id_str)?;

    let mut state = create_test_state();
    // カードを場に配置
    state.core.players[0].stage[0] = Some(real_id);
    // アクティベート可能な状態に設定
    state.core.players[0].can_activate = true;

    // アクティベートアクションを実行
    let action = Action::Activate { member_idx: 0 }.id();
    state.step(db, action)?;

    // ... 比較ロジック
}
```

### 影響
- 約100件のSKIPがPASS/FAILに変更される

---

## 修正6: 空シーケンスの調査と修正（優先度: 低）

### 問題
多くのカードで`sequence`が空になっている。

### 調査項目
1. `pseudocode_oracle.py`でのパースエラー
2. 元データのpseudocodeフィールドの欠落
3. 複雑な効果のパース失敗

### 修正アプローチ
```python
# pseudocode_oracle.pyでデバッグ出力を追加
if not sequence:
    print(f"WARNING: Empty sequence for {card_id}")
    print(f"  Raw pseudocode: {raw_pseudocode}")
```

### 影響
- 約100件のSKIPが解消される可能性

---

## 修正7: 条件なしCONSTANTトリガーの処理改善（優先度: 低）

### 問題
条件なしCONSTANTトリガーはテストされるが、正しく検出されない場合がある。

### 現状
```rust
if trigger_type == TriggerType::Constant && !ability.conditions.is_empty() {
    println!("  [SKIP] {} (conditional constant)", test_name);
    skip_count += 1;
    continue;
}
```

### 修正案
条件なしCONSTANTは即座に効果を適用:
```rust
if trigger_type == TriggerType::Constant {
    if !ability.conditions.is_empty() {
        // 条件あり: 条件を満たす状態を構築
        setup_condition_state(&mut state, &ability.conditions);
    }
    // CONSTANT効果を適用
    // (通常のプレイフローではなく、直接効果適用)
}
```

---

## 実装順序

### フェーズ1: FAIL削減（高優先度）
1. **修正1**: 手札減少ロジック改善
2. **修正2**: HAND_DISCARD統合処理
3. **修正3**: エネルギーゾーン初期状態改善

### フェーズ2: SKIP削減（中優先度）
4. **修正4**: ONLIVESTARTサポート
5. **修正5**: ACTIVATEDサポート

### フェーズ3: 品質向上（低優先度）
6. **修正6**: 空シーケンス調査
7. **修正7**: CONSTANT処理改善

---

## 期待される結果

| フェーズ | PASS | FAIL | SKIP |
|----------|------|------|------|
| 現状 | 2 | 229 | 695 |
| フェーズ1後 | 150+ | 80 | 695 |
| フェーズ2後 | 400+ | 80 | 350 |
| フェーズ3後 | 450+ | 50 | 300 |

---

## 検証方法

各修正後にテストを実行:
```bash
cd engine_rust_src
cargo run --release --bin test_gpu_parity_semantic
```

結果を記録し、改善を確認。
