# Semantic Assertions改善計画

## 現状分析

### テスト結果サマリー
- **総カード数**: 680
- **合格**: 321 (47.2%)
- **不合格**: 359 (52.8%)

### 失敗パターンの分類

監査レポートの分析から、以下の主要な失敗パターンが特定されました：

```mermaid
pie title 失敗パターンの分布
    HAND_DELTA不整合 : 35
    ENERGY_DELTA不整合 : 20
    SCORE_DELTA不整合 : 15
    HEART_DELTA不整合 : 10
    BLADE_DELTA不整合 : 10
    DECK_SEARCH不整合 : 15
    MEMBER_TAP不整合 : 12
    ACTION_PREVENTION不整合 : 5
    その他 : 10
```

---

## 改善アプローチ

### アプローチ1: Truth Data品質の向上

**問題**: `semantic_truth.json`の期待値が不正確または不完全

**解決策**:

1. **自動Truth生成の改善**
   - [`generate_v2_truth()`](engine_rust_src/src/semantic_assertions.rs:833)を拡張して、より正確な期待値を生成
   - 実際のゲームログから期待値を抽出する機能を追加

2. **Truth検証パイプライン**
   ```
   カードJSON → コンパイラ → バイトコード → 実行 → 自動記録 → Truth生成
   ```

3. **手動検証済みサンプルセット**
   - 高信頼性のカードセット（現在PASSしているカード）をベースラインとして使用
   - 新しいカードは段階的に追加

---

### アプローチ2: オートボットの知能向上

**問題**: [`resolve_interaction()`](engine_rust_src/src/semantic_assertions.rs:253)が最適でない選択をすることがある

**現在の問題点**:
```rust
// 現在: 常に最初の選択肢を選ぶ
let selected_idx = 0;
```

**解決策**:

1. **フィルタ対応の選択**
   ```rust
   // 改善案: フィルタに一致するカードを優先
   if pi.filter_attr != 0 {
       let filter = CardFilter::from_attr(pi.filter_attr);
       for (i, &cid) in state.core.players[p_idx].hand.iter().enumerate() {
           if filter.matches(&self.db, cid, false) {
               selected_idx = i as i32;
               break;
           }
       }
   }
   ```

2. **コンテキスト対応の選択**
   - コスト支払い: 利用可能なエネルギー/手札を優先
   - リカバリー: 最も価値の高いカードを選択
   - タップ: まだタップされていないメンバーを選択

3. **マルチセレクト対応**
   - 複数選択が必要なインタラクションの処理

---

### アプローチ3: Delta追跡の拡張

**問題**: [`diff_snapshots()`](engine_rust_src/src/semantic_assertions.rs:511)が多くの状態変化を捕捉していない

**現在追跡されていない項目**:

| カテゴリ | 追跡されていない状態 |
|---------|-------------------|
| タップ状態 | `tapped_members`は追跡済みだが、`tapped_energy`が未追跡 |
| 予防フラグ | `prevent_activate`, `prevent_baton_touch`等は部分的に追跡 |
| 修飾子 | `cost_reduction`, `heart_requirements`等 |
| 変換 | `color_transforms`, `heart_transforms` |
| ステージエネルギー | `stage_energy`配列 |

**解決策**:

1. **ZoneSnapshotの拡張**
   ```rust
   pub struct ZoneSnapshot {
       // 既存フィールド...
       pub tapped_energy_mask: u32,      // 追加
       pub restrictions: Vec<Restriction>, // 追加
       pub color_transforms: Vec<(i32, u8)>, // 追加
       pub abilities_granted: Vec<(i32, Ability)>, // 追加
   }
   ```

2. **新しいDeltaタグの追加**
   ```rust
   "TAP_ENERGY_DELTA"     // エネルギータップ
   "RESTRICTION_SET"      // 制限追加
   "TRANSFORM_APPLIED"    // 変換適用
   "ABILITY_GRANTED"      // 能力付与
   ```

---

### アプローチ4: トリガータイプの拡張

**問題**: 一部のトリガータイプがサポートされていない

**現在サポート済み**:
- `OnPlay`, `OnLiveStart`, `OnLiveSuccess`, `Activated`, `Constant`, `None`

**未サポート**:
- `OnLeavesStage` - ステージ離脱時
- `OnTurnEnd` - ターン終了時
- `OnBatonTouch` - バトンタッチ時
- `OnYell` - エール時
- `OnLiveFail` - ライブ失敗時

**解決策**:

```rust
match trigger_type {
    // 既存...
    TriggerType::OnLeavesStage => {
        // カードをステージから除去してトリガー
        state.core.players[0].stage[0] = -1;
        // トリガーキューに追加
    }
    TriggerType::OnTurnEnd => {
        // ターンを進めて終了フェーズに
        state.turn += 1;
        state.phase = Phase::TurnEnd;
        // トリガー実行
    }
    // 他のトリガータイプも同様に実装
}
```

---

### アプローチ5: 条件評価の改善

**問題**: アビリティの条件が満たされていないために効果が発動しない

**失敗例**:
```
PL!-bp3-005-P: Mismatch ENERGY_DELTA for ACTIVATE_MEMBER(99): Exp 99, Got 0
```
→ 「すべてのメンバーをタップ」効果が、条件不足で発動していない可能性

**解決策**:

1. **条件事前チェック**
   ```rust
   fn check_ability_conditions(&self, state: &GameState, card_id: i32, ab_idx: usize) -> bool {
       // バイトコードを解析して条件を特定
       // 必要なリソースが揃っているか確認
   }
   ```

2. **環境セットアップの自動調整**
   ```rust
   fn setup_for_ability(&mut state: &mut GameState, ability: &Ability) {
       // 条件に基づいて必要なリソースを追加
       if ability.requires_success_lives {
           ensure_success_lives(&mut state, 3);
       }
       if ability.requires_discard_cards {
           ensure_discard_cards(&mut state, 5);
       }
   }
   ```

---

### アプローチ6: 実ゲームデータとの照合

**問題**: テスト環境が実際のゲームプレイと異なる

**解決策**:

1. **ゲームログの収集**
   - 実際のプレイからゲームログを収集
   - ログをテストケースに変換

2. **回帰テストスイート**
   ```
   実ゲームログ → テストケース生成 → 自動実行 → 結果比較
   ```

3. **不整合検出**
   - 実ゲームの結果とエンジンの結果を比較
   - 差異を自動レポート

---

## 実装優先順位

### Phase 1: 基盤改善（高優先度）
1. [ ] Truth Data品質の検証と修正
2. [ ] オートボットのフィルタ対応選択の実装
3. [ ] 失敗テストの原因分析と分類

### Phase 2: 機能拡張（中優先度）
4. [ ] ZoneSnapshotの拡張
5. [ ] 新しいDeltaタグの追加
6. [ ] 追加トリガータイプのサポート

### Phase 3: 高度な機能（低優先度）
7. [ ] 条件評価の自動チェック
8. [ ] 実ゲームデータとの照合
9. [ ] 回帰テストスイートの構築

---

## 具体的な失敗パターンと対処法

### パターン1: HAND_DELTA不整合

**例**: `Exp 1, Got 0` for RECOVER_MEMBER

**原因候補**:
1. ディスカードに回収可能なカードがない
2. フィルタ条件に一致するカードがない
3. インタラクションが正しく解決されていない

**対処**:
```rust
// setup_oracle_environmentで確実に回収可能カードを配置
state.core.players[0].discard.extend(
    db.members.keys().take(10).cloned()
);
```

### パターン2: ENERGY_DELTA不整合

**例**: `Exp 1, Got 0` for ACTIVATE_MEMBER

**原因候補**:
1. タップ可能なメンバーがいない
2. すでにタップされている
3. タップ状態の追跡が不正確

**対処**:
```rust
// タップ状態をリセット
for i in 0..3 {
    state.core.players[0].tap_member(i, false);
}
```

### パターン3: DECK_SEARCH不整合

**例**: `No cards revealed or added to hand`

**原因候補**:
1. デッキにカードがない
2. LOOK_AND_CHOOSEが正しく実行されていない
3. `looked_cards_len`の追跡が不正確

**対処**:
```rust
// デッキに十分なカードを確保
if state.core.players[0].deck.len() < 10 {
    state.core.players[0].deck.extend(
        db.members.keys().take(10).cloned()
    );
}
```

---

## 成功指標

| 指標 | 現在 | 目標 |
|-----|------|------|
| パス率 | 47.2% | 80%+ |
| カバー済みオペコード | 26% | 70%+ |
| サポート済みトリガー | 6種類 | 10種類+ |
| 自動解決可能なインタラクション | 50% | 90%+ |

---

## 次のステップ

1. **詳細な失敗分析**: 各失敗カードのバイトコードと期待値を詳細に分析
2. **Truth修正**: 明らかに間違っている期待値を修正
3. **環境改善**: テスト環境のセットアップを改善
4. **段階的実装**: 優先度の高い改善から順に実装
