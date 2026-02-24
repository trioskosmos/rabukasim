# WGSLテスト結果分析

## テスト結果サマリー

```
PASS: 2, FAIL: 229, SKIP: 695
```

## PASSの例: PL!SP-bp4-002-P:AB0

### Semantic Truth定義
```json
{
  "trigger": "ONPLAY",
  "sequence": [
    {
      "text": "COST: TAP_MEMBER(1)",
      "deltas": [
        { "tag": "MEMBER_TAP_DELTA", "value": 1 }
      ]
    }
  ]
}
```

### なぜPASSするのか
1. **トリガーがONPLAY** - テスト対象のトリガー
2. **シンプルなデルタ** - MEMBER_TAP_DELTAのみ
3. **GPUシェーダーがTAP_MEMBERを正しく実装** - オペコードが機能している
4. **手札減少の調整が不要** - MEMBER_TAP_DELTAは手札に影響しない

---

## SKIPの原因分析（695件）

### スキップ理由1: 非対応トリガー（約60%）

```rust
if trigger_type != TriggerType::OnPlay && trigger_type != TriggerType::Constant {
    println!("  [SKIP] {} (trigger: {})", test_name, ability.trigger);
    skip_count += 1;
    continue;
}
```

**スキップされるトリガー:**
- `ONLIVESTART` - ライブ開始時トリガー
- `ONLIVESUCCESS` - ライブ成功時トリガー
- `ACTIVATED` - アクティベート能力
- `ONLEAVES` - 退場時トリガー
- `ONREVEAL` - 公開時トリガー

**例:**
```
[SKIP] PL!HS-bp2-022-L:AB0 (trigger: ONLIVESTART)
[SKIP] PL!SP-bp1-024-L:AB1 (trigger: ONLIVESUCCESS)
[SKIP] PL!-pb1-015-R:AB2 (trigger: ACTIVATED)
```

### スキップ理由2: 条件付きCONSTANTトリガー（約5%）

```rust
if trigger_type == TriggerType::Constant && !ability.conditions.is_empty() {
    println!("  [SKIP] {} (conditional constant)", test_name);
    skip_count += 1;
    continue;
}
```

**例:** 条件付きの常時効果はテスト環境で条件を満たすのが難しい

### スキップ理由3: 空のシーケンス（約15%）

```rust
if ability.sequence.is_empty() {
    println!("  [SKIP] {} (empty sequence)", test_name);
    skip_count += 1;
    continue;
}
```

**例:**
```
[SKIP] PL!-bp3-005-R:AB0 (empty sequence)
[SKIP] PL!SP-bp2-006-P＋:AB0 (empty sequence)
```

### スキップ理由4: デルタなし（約20%）

```rust
if all_deltas.is_empty() {
    println!("  [SKIP] {} (no deltas)", test_name);
    skip_count += 1;
    continue;
}
```

**例:**
```
[SKIP] PL!-bp4-019-L:AB0 (no deltas)
[SKIP] PL!N-pb1-004-P＋:AB0 (no deltas)
```

---

## FAILの原因分析（229件）

### 失敗パターン1: Hand delta mismatch（最頻出）

**例:**
```
[FAIL] PL!N-pb1-016-R:AB0: Hand delta mismatch (expected: 0, actual: -1)
[FAIL] PL!-pb1-011-P＋:AB0: Hand delta mismatch (expected: -1, actual: -2)
```

**原因:**
- カードプレイ時の手札減少(-1)の調整ロジックに問題
- HAND_DISCARDがある場合の二重カウント
- GPUシェーダーが追加のドローやディスカードを実行している可能性

### 失敗パターン2: Discard delta mismatch

**例:**
```
[FAIL] PL!N-pb1-016-R:AB0: Discard delta mismatch (expected: 1, actual: 3)
[FAIL] PL!-bp4-005-SEC:AB0: Discard delta mismatch (expected: -1, actual: 2)
```

**原因:**
- GPUシェーダーがディスカードを余分に実行している
- コストのディスカードと効果のディスカードの区別が不明確

### 失敗パターン3: Hand discard double mismatch

**例:**
```
[FAIL] PL!S-bp2-008-SEC:AB0: Hand discard hand delta mismatch (expected: -1, actual: -3)
[FAIL] PL!S-bp2-008-SEC:AB0: Hand discard discard delta mismatch (expected: 1, actual: 2)
```

**原因:**
- HAND_DISCARDタグの処理ロジックに問題
- 手札減少とディスカード増加の両方で不一致

### 失敗パターン4: Energy tap delta mismatch

**例:**
```
[FAIL] PL!N-bp4-006-P:AB0: Energy tap delta mismatch (expected: 2, actual: 13)
[FAIL] PL!N-pb1-017-P＋:AB0: Energy tap delta mismatch (expected: 2, actual: 9)
```

**原因:**
- エネルギーゾーンの初期状態が実際のゲームと異なる
- GPUシェーダーがエネルギータップを過剰に実行している

---

## PASSを増やす方法

### 1. 手札減少ロジックの修正

**現状:**
```rust
let has_hand_discard = expected_deltas.iter().any(|d| d.tag == "HAND_DISCARD");
if !has_hand_discard {
    adjusted_deltas.push(SemanticDelta {
        tag: "HAND_DELTA".to_string(),
        value: serde_json::json!(-1),
    });
}
```

**改善案:**
- HAND_DISCARDの値を考慮して調整
- DISCARD_COSTとDISCARD_EFFECTを区別
- カードタイプ（メンバー/エネルギー/ライブ）で処理を分ける

### 2. GPUシェーダーのデバッグ

**必要な調査:**
- WGSLシェーダーでディスカードが正しくカウントされているか
- O_TAP_MEMBERなどのオペコードが正しく実行されているか
- エネルギータップの実装を確認

### 3. Semantic Truth生成の改善

**問題点:**
- 一部の効果が正しいデルタタグで記録されていない
- DISCARD_DELTAの値が負になる場合がある（回復効果）

---

## SKIPを減らす方法

### 1. ONLIVESTARTトリガーのサポート追加

**必要な実装:**
```rust
// ライブフェーズをシミュレート
state.core.phase = Phase::Live;
state.step_live_start(db);
```

### 2. ACTIVATEDトリガーのサポート追加

**必要な実装:**
```rust
// アクティベートアクションを実行
let action = Action::Activate { member_idx: 0 }.id();
state.step(db, action);
```

### 3. 条件付きCONSTANTの条件充足

**必要な実装:**
- 条件を満たすゲーム状態を自動構築
- 例: 「自分の場に○○がいる場合」→該当カードを配置

### 4. 空シーケンス/デルタなしの調査

**原因調査:**
- パースエラーでシーケンスが正しく生成されていない
- 効果のないカード（コストのみ）が正しく記録されていない

---

## 優先順位

### 高優先度
1. **手札減少ロジックの修正** - 最も多くのFAILに影響
2. **GPUシェーダーのディスカード実装確認** - 2番目に多いFAIL

### 中優先度
3. **ONLIVESTARTトリガーのサポート** - 多くのSKIPを解消
4. **ACTIVATEDトリガーのサポート** - 多くのSKIPを解消

### 低優先度
5. **条件付きCONSTANTのサポート** - 複雑な条件処理が必要
6. **空シーケンスの調査** - パース問題の可能性

---

## 次のステップ

1. **詳細な失敗ケースの調査**
   - 特定のカードのGPU実行をデバッグ出力
   - CPUとGPUの状態を比較

2. **テスト環境の改善**
   - より現実的な初期状態を構築
   - エネルギーゾーン、デッキ、ディスカードの適切な設定

3. **Semantic Truth生成の検証**
   - 手動で正しいデルタを定義したテストケースを作成
   - 自動生成との比較
