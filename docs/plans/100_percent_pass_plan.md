# 100%パス達成プラン

## 現状
```
PASS: 386, FAIL: 540, SKIP: 0
```

## 目標
```
PASS: 926 (100%), FAIL: 0, SKIP: 0
```

---

## 失敗パターンの分析

テスト出力から、以下の失敗パターンが見つかりました：

### カテゴリ1: Hand delta mismatch（手札デルタ不一致）

最も多い失敗パターン。期待値と実際の手札変化が異なる。

```
[FAIL] PL!SP-bp4-008-P＋:AB0: Hand delta mismatch (expected: -1, actual: 0)
[FAIL] PL!N-bp1-011-R:AB0: Hand delta mismatch (expected: -1, actual: -2)
```

**原因**:
1. カードプレイ時の手札減少が正しく計算されていない
2. ドロー効果が正しく実装されていない
3. デッキから手札への移動が正しくない

**修正方法**:
- `shader_rules.wgsl`で手札操作のオペコードを確認
- `O_DRAW`, `O_DISCARD`の実装を確認

---

### カテゴリ2: Discard delta mismatch（捨て札デルタ不一致）

2番目に多い失敗パターン。

```
[FAIL] PL!S-bp2-007-SEC:AB0: Discard delta mismatch (expected: -1, actual: 0)
[FAIL] PL!N-bp1-009-R:AB0: Discard delta mismatch (expected: 4, actual: 3)
```

**原因**:
1. 捨て札効果が正しく実行されていない
2. 捨て札から他の場所への移動が正しくない
3. `O_MOVE_TO_DECK`, `O_MOVE_TO_HAND`の実装問題

**修正方法**:
- `O_DISCARD`の実装を確認
- ゾーン間移動のオペコードを確認

---

### カテゴリ3: Energy tap delta mismatch（エネルギータップ不一致）

```
[FAIL] PL!SP-bp1-012-N:AB0: Energy tap delta mismatch (expected: 1, actual: 5)
[FAIL] PL!N-pb1-017-P＋:AB0: Energy tap delta mismatch (expected: 2, actual: 9)
```

**原因**:
1. テスト初期状態のエネルギーゾーン設定が実際と異なる
2. エネルギータップの実装が正しくない
3. タップ済みエネルギーのマスク処理

**修正方法**:
- テスト初期状態で`tapped_energy_mask`を正しく設定
- `O_TAP_ENERGY`の実装を確認

---

### カテゴリ4: Member tap expected but not detected

```
[FAIL] PL!-pb1-008-R:AB0: Member tap expected but not detected
[FAIL] PL!-bp3-003-R:AB0: Member tap expected but not detected
```

**原因**:
1. メンバーのタップ効果が実装されていない
2. `O_TAP_MEMBER`の実装問題

**修正方法**:
- `O_TAP_MEMBER`の実装を確認・修正

---

### カテゴリ5: 空シーケンス/デルタなしのテスト

```
[INFO] PL!SP-bp4-008-P＋:AB0 has empty sequence, testing anyway
[FAIL] PL!SP-bp4-008-P＋:AB0: Hand delta mismatch (expected: -1, actual: 0)
```

**原因**:
1. `semantic_truth_v3.json`のデータが不完全
2. パースエラーでシーケンスが空になっている

**修正方法**:
- `pseudocode_oracle.py`でパースを修正
- 手動で正しいシーケンスを追加

---

## 100%パスへのロードマップ

### フェーズ1: GPUシェーダー修正（推定効果: +200 PASS）

最も効果が大きいカテゴリ1と2の修正。

1. **手札操作の修正**
   - `shader_rules.wgsl`で`O_DRAW`を確認
   - `O_DISCARD`を確認
   - 手札枚数の計算ロジックを確認

2. **捨て札操作の修正**
   - `O_MOVE_TO_DECK`の実装
   - `O_MOVE_TO_HAND`の実装
   - ゾーン間移動の統一

### フェーズ2: テスト初期状態の改善（推定効果: +100 PASS）

カテゴリ3の修正。

1. **エネルギーゾーン初期化**
   - テスト開始時にエネルギーを正しく配置
   - タップ状態を正しく設定

2. **メンバータップの修正**
   - `O_TAP_MEMBER`の実装確認
   - テストでの検証方法を改善

### フェーズ3: semantic_truthの修正（推定効果: +150 PASS）

カテゴリ5の修正。

1. **空シーケンスの修正**
   - `pseudocode_oracle.py`でパースエラーを修正
   - 手動で重要なカードのシーケンスを追加

2. **デルタ生成の改善**
   - デルタ生成ロジックを見直し
   - 状態変化を伴わない効果を正しく処理

### フェーズ4: トリガー実装の改善（推定効果: +90 PASS）

各トリガータイプのテスト関数を改善。

1. **ONLIVESTART**
   - フェーズ変更時のトリガー発火を確認
   - ライブ開始時の状態遷移

2. **ACTIVATED**
   - アクティベートコストの支払い
   - アクティベート効果の実行

3. **ONLIVESUCCESS**
   - ライブ成功時のトリガー発火
   - 成功判定の実装

---

## 優先順位

1. **フェーズ1: GPUシェーダー修正** - 最も効果が大きい
2. **フェーズ2: テスト初期状態の改善** - エネルギー関連の失敗を減らす
3. **フェーズ3: semantic_truthの修正** - データ品質の向上
4. **フェーズ4: トリガー実装の改善** - 残りの失敗を解消

---

## 推定結果

| フェーズ | PASS | FAIL | 累計PASS率 |
|----------|------|------|------------|
| 現状 | 386 | 540 | 42% |
| フェーズ1後 | 586 | 340 | 63% |
| フェーズ2後 | 686 | 240 | 74% |
| フェーズ3後 | 836 | 90 | 90% |
| フェーズ4後 | 926 | 0 | 100% |

---

## 次のステップ

1. 失敗しているテストの詳細を分析
2. `shader_rules.wgsl`のオペコード実装を確認
3. フェーズ1から順に実装
