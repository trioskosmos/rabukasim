# パス率向上改善計画

## 現在の状態

**全体パス率: 97.1% (894/921 abilities)**

### 環境別パス率

| 環境 | パス | 失敗 | パス率 |
|------|------|------|--------|
| Standard | 713 | 15 | 97.9% |
| Minimal | 674 | 54 | 92.6% |
| NoEnergy | 652 | 76 | 89.6% |
| NoHand | 705 | 23 | 96.8% |
| FullHand | 713 | 15 | 97.9% |
| OppEmpty | 713 | 15 | 97.9% |
| TappedMbr | 699 | 29 | 96.0% |
| LowScore | 700 | 28 | 96.2% |

## 失敗パターン分析

### 1. 全環境で失敗するカード（SEGMENT_STUCK）

これらのカードは根本的な問題があり、実行が途中で止まっている:

| カード | アビリティ | 推定原因 |
|--------|-----------|----------|
| PL!-bp4-009-P/R | Ab0 | バイトコード実行エラー |
| PL!-bp4-011-N | Ab1 | 条件判定の問題 |
| PL!-pb1-009-P+/R | Ab0 | 未実装オペコード |
| PL!N-bp1-003-P/P+/R+/SEC | Ab1 | コスト支払い問題 |
| PL!N-bp3-017-N | Ab2 | 複雑な条件 |
| PL!N-bp3-023-N | Ab2 | 複雑な条件 |
| PL!N-sd1-001-SD | Ab1 | 特殊トリガー |
| PL!S-bp3-021-L | Ab0 | ライブカード問題 |

**対策**:
- 各カードのバイトコードを調査
- `resolve_interaction`のロジックを改善
- 未実装オペコードを特定して対応

### 2. NoEnergy環境の失敗（76件）

**問題**: エネルギーコストを検出できていないアビリティが実行を試みて失敗

**現在の検出ロジック**:
```rust
fn ability_requires_energy(&self, sequence: &[SemanticSegment]) -> bool {
    for segment in sequence {
        for delta in &segment.deltas {
            if delta.tag == "ENERGY_DELTA" {
                return true;
            }
        }
    }
    false
}
```

**改善策**:
1. `ENERGY_COST`デルタも検出対象に追加
2. バイトコードから直接エネルギーコストを検出
3. 条件付きエネルギーコスト（X能源など）の処理

### 3. Minimal環境の失敗（54件）

**問題**: リソース不足で実行できないアビリティ

**改善策**:
1. `ability_requires_resources`の検出精度を向上
2. 以下のリソース要件を追加検出:
   - DISCARD_DELTA（捨て札必要）
   - LIVE_DELTA（ライブカード必要）
   - SCORE_DELTA正値（スコア条件）

### 4. TappedMbr環境の失敗（29件）

**問題**: タップ状態に依存するアビリティ

**改善策**:
1. タップ状態を必要とするアビリティの検出
2. `MEMBER_TAP_DELTA`、`OPPONENT_MEMBER_TAP_DELTA`の処理改善
3. 「アンタップ」効果の検出

### 5. LowScore環境の失敗（28件）

**問題**: スコア条件を持つアビリティ

**改善策**:
1. スコア条件を持つアビリティの検出
2. `SCORE_DELTA`の条件付き処理
3. 「ファンファーレ」等のスコア依存効果の検出

## 実装計画

### Phase 1: エネルギー検出改善

```rust
fn ability_requires_energy(&self, sequence: &[SemanticSegment]) -> bool {
    for segment in sequence {
        for delta in &segment.deltas {
            match delta.tag.as_str() {
                "ENERGY_DELTA" | "ENERGY_COST" | "ENERGY_COST_DELTA" => return true,
                _ => {}
            }
        }
    }
    false
}
```

### Phase 2: リソース検出拡張

```rust
fn ability_requires_resources(&self, sequence: &[SemanticSegment]) -> bool {
    for segment in sequence {
        for delta in &segment.deltas {
            match delta.tag.as_str() {
                "DISCARD_DELTA" | "ENERGY_DELTA" | "DECK_DELTA" | "LIVE_DELTA"
                | "ENERGY_COST" | "ENERGY_COST_DELTA" => return true,
                "SCORE_DELTA" if delta.value.as_i64().map(|v| v > 0).unwrap_or(false) => return true,
                "HAND_DELTA" if delta.value.as_i64().map(|v| v < 0).unwrap_or(false) => return true,
                _ => {}
            }
        }
    }
    false
}
```

### Phase 3: 環境固有の検出追加

```rust
// TappedMbr環境用
fn ability_requires_untapped_members(&self, sequence: &[SemanticSegment]) -> bool {
    for segment in sequence {
        for delta in &segment.deltas {
            if delta.tag == "MEMBER_TAP_DELTA" && delta.value.as_i64().map(|v| v < 0).unwrap_or(false) {
                return true; // アンタップ効果
            }
        }
    }
    false
}

// LowScore環境用
fn ability_requires_score_condition(&self, sequence: &[SemanticSegment]) -> bool {
    for segment in sequence {
        for delta in &segment.deltas {
            if delta.tag == "SCORE_DELTA" {
                return true;
            }
        }
    }
    false
}
```

### Phase 4: 全環境失敗カードの調査

各カードのバイトコードを調査し、SEGMENT_STUCKの原因を特定:

1. `PL!-bp4-009-P` - バイトコードダンプを確認
2. `PL!-bp4-011-N Ab1` - 条件オペコードを確認
3. `PL!-pb1-009-P+` - 未実装オペコードの可能性

## 期待される改善

| 改善 | 期待パス率 |
|------|-----------|
| 現在 | 97.1% |
| Phase 1完了 | 97.5% |
| Phase 2完了 | 98.0% |
| Phase 3完了 | 98.5% |
| Phase 4完了 | 99.0%+ |

## 次のステップ

1. Codeモードに切り替えて実装
2. 各Phaseを実装してテスト
3. 結果を確認して次のPhaseへ
