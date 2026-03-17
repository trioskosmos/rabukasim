# 未テストOpcode調査と実装計画

## 調査結果サマリー

未テストの21個のOpcodeについて、カードデータ内での使用状況を調査しました。

---

## 1. Effect Opcodes（9個）

### 1.1 使用されているがテストされていない（優先度高）

| Opcode | Name | カード数 | 実装状況 |
|--------|------|---------|---------|
| 26 | FormationChange | 2 | ✅ 実装済み ([`member_state.rs:72`](engine_rust_src/src/core/logic/interpreter/handlers/member_state.rs:72)) |
| 80 | PreventSetToSuccessPile | 6 | ⚠️ 未実装 |
| 83 | SetHeartCost | 6 | ⚠️ 未実装 |

### 1.2 使用されていない（優先度低）

| Opcode | Name | 実装状況 | 備考 |
|--------|------|---------|-----|
| 0 | Nop | ✅ 実装済み | 何もしない |
| 22 | SearchDeck | ✅ 実装済み | [`deck_zones.rs:17`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:17) |
| 34 | Flavor | ❌ 未実装 | フレーバーテキスト用 |
| 38 | SwapZone | ✅ 実装済み | [`deck_zones.rs:222`](engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs:222) |
| 46 | ReplaceEffect | ❌ 未実装 | 複雑な効果置換 |
| 52 | AddContinuous | ❌ 未実装 | 継続効果追加 |

---

## 2. Condition Opcodes（12個）

### 2.1 使用されているがテストされていない（優先度高）

| Opcode | Name | カード数 | 実装状況 |
|--------|------|---------|---------|
| 202 | HasColor | 4 | ✅ 実装済み ([`conditions.rs:132`](engine_rust_src/src/core/logic/interpreter/conditions.rs:132)) |
| 228 | HasMoved | 4 | ✅ 実装済み ([`conditions.rs:369`](engine_rust_src/src/core/logic/interpreter/conditions.rs:369)) |

### 2.2 使用されていない（優先度低）

| Opcode | Name | 実装状況 | 備考 |
|--------|------|---------|-----|
| 0 | None | ✅ 実装済み | 条件なし |
| 207 | LifeLead | ✅ 実装済み | [`conditions.rs:265`](engine_rust_src/src/core/logic/interpreter/conditions.rs:265) |
| 210 | OpponentHas | ✅ 実装済み | [`conditions.rs:261`](engine_rust_src/src/core/logic/interpreter/conditions.rs:261) |
| 211 | SelfIsGroup | ✅ 実装済み | [`conditions.rs:290`](engine_rust_src/src/core/logic/interpreter/conditions.rs:290) |
| 216 | RarityCheck | ✅ 実装済み | [`conditions.rs:239`](engine_rust_src/src/core/logic/interpreter/conditions.rs:239) |
| 217 | HandHasNoLive | ✅ 実装済み | [`conditions.rs:310`](engine_rust_src/src/core/logic/interpreter/conditions.rs:310) |
| 221 | HasChoice | ✅ 実装済み | [`conditions.rs:329`](engine_rust_src/src/core/logic/interpreter/conditions.rs:329) |
| 222 | OpponentChoice | ✅ 実装済み | [`conditions.rs:330`](engine_rust_src/src/core/logic/interpreter/conditions.rs:330) |
| 229 | HandIncreased | ✅ 実装済み | [`conditions.rs:370`](engine_rust_src/src/core/logic/interpreter/conditions.rs:370) |
| 233 | IsInDiscard | ✅ 実装済み | [`conditions.rs:394`](engine_rust_src/src/core/logic/interpreter/conditions.rs:394) |

---

## 3. 優先度別アクションプラン

### 高優先度：実装が必要

#### O_PREVENT_SET_TO_SUCCESS_PILE (80)
- **カード数**: 6枚
- **現状**: 未実装
- **実装場所**: `meta_control.rs`に追加
- **効果**: ライブを成功ポイルに置くことを防止

```rust
O_PREVENT_SET_TO_SUCCESS_PILE => {
    state.core.players[p_idx].prevent_success_pile_set = v as u8;
}
```

#### O_SET_HEART_COST (83)
- **カード数**: 6枚
- **現状**: 未実装
- **実装場所**: `score_hearts.rs`に追加
- **効果**: ハートコストを設定

```rust
O_SET_HEART_COST => {
    if (s as usize) < 7 {
        state.core.players[p_idx].heart_cost_override = Some((s as u8, v as u8));
    }
}
```

### 中優先度：テストを追加

#### O_FORMATION_CHANGE (26)
- **カード数**: 2枚
- **現状**: 実装済みだがテストなし
- **テストケース**: ステージ位置の入れ替え

#### C_HAS_COLOR (202)
- **カード数**: 4枚
- **現状**: 実装済みだがテストなし
- **テストケース**: 特定色のメンバーがいるか

#### C_HAS_MOVED (228)
- **カード数**: 4枚
- **現状**: 実装済みだがテストなし
- **テストケース**: メンバーが移動したか

### 低優先度：使用されていないOpcode

これらは現在のカードプールで使用されていないため、実装確認のみ行う：
- O_NOP, O_SEARCH_DECK, O_FLAVOR, O_SWAP_ZONE, O_REPLACE_EFFECT, O_ADD_CONTINUOUS
- C_NONE, C_LIFE_LEAD, C_OPPONENT_HAS, C_SELF_IS_GROUP, C_RARITY_CHECK, etc.

---

## 4. テストケース設計

### Test 1: O_PREVENT_SET_TO_SUCCESS_PILE
```rust
#[test]
fn test_prevent_set_to_success_pile() {
    // カードID: 122190付近のカードを使用
    // 1. ライブ成功後に成功ポイルへの移動を防止
    // 2. prevent_success_pile_setフラグが設定されることを確認
}
```

### Test 2: O_SET_HEART_COST
```rust
#[test]
fn test_set_heart_cost() {
    // カードID: 115899付近のカードを使用
    // 1. ハートコストを設定
    // 2. 次のライブでコストが変更されることを確認
}
```

### Test 3: O_FORMATION_CHANGE
```rust
#[test]
fn test_formation_change() {
    // カードID: 128350付近のカードを使用
    // 1. ステージ上のメンバー位置を入れ替え
    // 2. OnPositionChangeトリガーが発火することを確認
}
```

### Test 4: C_HAS_COLOR
```rust
#[test]
fn test_has_color_condition() {
    // カードID: 57294付近のカードを使用
    // 1. 特定色のメンバーがステージにいる場合
    // 2. 条件がtrueになることを確認
}
```

### Test 5: C_HAS_MOVED
```rust
#[test]
fn test_has_moved_condition() {
    // カードID: 56220付近のカードを使用
    // 1. メンバーが移動した後
    // 2. is_movedフラグが立っていることを確認
}
```

---

## 5. 実装スケジュール

### Phase 1: 未実装Opcode（高優先度）
1. `O_PREVENT_SET_TO_SUCCESS_PILE`の実装
2. `O_SET_HEART_COST`の実装
3. 実装後のユニットテスト追加

### Phase 2: テスト追加（中優先度）
1. `O_FORMATION_CHANGE`のテスト
2. `C_HAS_COLOR`のテスト
3. `C_HAS_MOVED`のテスト

### Phase 3: 検証（低優先度）
1. 使用されていないOpcodeの実装確認
2. ドキュメント更新

---

## 6. 関連ファイル

- [`engine_rust_src/src/core/logic/interpreter/handlers/meta_control.rs`](engine_rust_src/src/core/logic/interpreter/handlers/meta_control.rs)
- [`engine_rust_src/src/core/logic/interpreter/handlers/score_hearts.rs`](engine_rust_src/src/core/logic/interpreter/handlers/score_hearts.rs)
- [`engine_rust_src/src/core/logic/interpreter/handlers/member_state.rs`](engine_rust_src/src/core/logic/interpreter/handlers/member_state.rs)
- [`engine_rust_src/src/core/logic/interpreter/conditions.rs`](engine_rust_src/src/core/logic/interpreter/conditions.rs)
