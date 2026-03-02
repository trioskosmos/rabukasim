# 100%パス率達成に向けた分析

## 現在の状況

### 全体パス率: 97.1% (894/921 abilities)

### 環境別パス率

| 環境 | パス率 | 失敗数 |
|------|--------|--------|
| Standard | 97.9% | 15 |
| Minimal | 92.6% | 54 |
| NoEnergy | 89.6% | 76 |
| NoHand | 96.8% | 23 |
| FullHand | 97.9% | 15 |
| OppEmpty | 97.9% | 15 |
| TappedMbr | 96.0% | 29 |
| LowScore | 96.2% | 28 |

## 失敗パターンの分類

### 1. 全環境で失敗するカード（SEGMENT_STUCK）

これらは根本的な実装問題がある：

| カード | アビリティ | 推定原因 |
|--------|-----------|----------|
| PL!-bp4-009-P | Ab0 | OPPONENT_MEMBER_TAP_DELTA未処理 |
| PL!-bp4-009-R | Ab0 | 同上 |
| PL!-bp4-011-N | Ab1 | 要調査 |
| PL!-pb1-009-P+ | Ab0 | 要調査 |
| PL!-pb1-009-R | Ab0 | 要調査 |
| PL!N-bp1-003-P | Ab1 | 要調査 |
| PL!N-bp1-003-P+ | Ab1 | 要調査 |
| PL!N-bp1-003-R+ | Ab1 | 要調査 |
| PL!N-bp1-003-SEC | Ab1 | 要調査 |
| PL!N-bp3-017-N | Ab2 | 要調査 |
| PL!N-bp3-023-N | Ab2 | 要調査 |
| PL!N-sd1-001-SD | Ab1 | 要調査 |
| PL!SP-bp4-011-P | Ab1 | 要調査 |
| PL!SP-bp4-011-P+ | Ab1 | 要調査 |
| PL!SP-bp4-011-R+ | Ab1 | 要調査 |
| PL!SP-bp4-011-SEC | Ab1 | 要調査 |
| PL!SP-pb1-006-P+ | Ab1 | 要調査 |
| PL!SP-pb1-006-R | Ab1 | 要調査 |

### 2. 特定環境でのみ失敗するカード

#### Minimal環境 (54失敗)
- リソース不足でアビリティが実行できない
- ほとんどはスキップロジックで処理済みだが、残りは条件検出の改善が必要

#### NoEnergy環境 (76失敗)
- エネルギー依存アビリティの検出が不完全
- `ability_requires_energy()`の改善が必要

#### NoHand環境 (23失敗)
- 手札依存アビリティの検出が不完全
- `ability_requires_hand()`の改善が必要

#### TappedMbr環境 (29失敗)
- タップ状態に関連するアビリティ
- タップされたメンバーが必要な条件の処理

#### LowScore環境 (28失敗)
- スコアに関連するアビリティ
- 低スコア状態での条件処理

## 100%達成に必要な修正

### 優先度1: 全環境失敗の修正（約18件）

1. **OPPONENT_MEMBER_TAP_DELTA処理の追加**
   ```rust
   // diff_snapshots()に追加
   let p1_tapped_before = baseline.opponent_tapped_count;
   let p1_tapped_current = current.opponent_tapped_count;
   let d_opp_tap = p1_tapped_current as i32 - p1_tapped_before as i32;
   if d_opp_tap != 0 {
       deltas.push(SemanticDelta {
           tag: "OPPONENT_MEMBER_TAP_DELTA".to_string(),
           value: serde_json::json!(d_opp_tap)
       });
   }
   ```

2. **ZoneSnapshotへのフィールド追加**
   ```rust
   pub struct ZoneSnapshot {
       // 既存フィールド...
       pub opponent_tapped_count: usize,  // 追加
   }
   ```

### 優先度2: 環境固有の問題修正

1. **NoEnergy環境**
   - エネルギーコストを持つアビリティの検出を改善
   - truthデータのコスト情報を解析

2. **NoHand環境**
   - 手札コストを持つアビリティの検出を改善
   - DISCARD_HAND等のコストを解析

3. **TappedMbr環境**
   - タップ状態を必要とするアビリティのスキップ処理

4. **LowScore環境**
   - スコア条件を持つアビリティのスキップ処理

### 優先度3: HAND_DELTA失敗の修正（4件）

- 手札の変化が期待通りでないケースの調査
- ドロー/捨て札のタイミング問題の解決

## 推定効果

| 修正 | 推定効果 |
|------|----------|
| OPPONENT_MEMBER_TAP_DELTA追加 | +2件 (全環境) |
| その他全環境失敗の修正 | +16件 |
| NoEnergyスキップ改善 | +24件 |
| NoHandスキップ改善 | +8件 |
| TappedMbrスキップ改善 | +10件 |
| LowScoreスキップ改善 | +9件 |
| **合計** | **+69件 → 100%到達可能** |

## 次のステップ

1. `ZoneSnapshot`に`opponent_tapped_count`フィールドを追加
2. `diff_snapshots()`に`OPPONENT_MEMBER_TAP_DELTA`処理を追加
3. 残りの全環境失敗カードを個別に調査
4. 環境固有のスキップロジックを改善
