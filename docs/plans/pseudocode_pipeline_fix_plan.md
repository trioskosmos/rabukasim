# Pseudocode Pipeline 修正計画

## 概要

`manual_pseudocode.json` → `parser_v2.py` → `interpreter.rs` のパイプラインにおける不整合を修正する計画。

---

## 修正項目

### 1. フィルタマッピングの拡張 (interpreter.rs)

**ファイル**: `engine_rust_src/src/core/logic/interpreter.rs`
**関数**: `map_filter_string_to_attr` (行32-105)

**現状の問題**:
- `COST_LE_REVEALED` が認識されない
- `BLADE_LE_*` が認識されない
- `BLADE_GE_*` が認識されない

**修正内容**:
```rust
// 追加するフィルタマッピング
} else if part.starts_with("BLADE_LE") {
    if let Some(val_str) = part.split('_').last() {
        if let Ok(threshold) = val_str.parse::<i32>() {
            attr |= 0x01000000 | ((threshold as u64) << 25);
            attr |= 0x40000000u64; // LE flag
        }
    }
} else if part.starts_with("BLADE_GE") {
    if let Some(val_str) = part.split('_').last() {
        if let Ok(threshold) = val_str.parse::<i32>() {
            attr |= 0x01000000 | ((threshold as u64) << 25);
        }
    }
} else if part == "COST_LE_REVEALED" {
    // 特殊フラグ: 公開されたカードのコスト制限
    attr |= 0x01000000 | (1u64 << 25); // COST_LE_1 + REVEALED flag
    attr |= 0x40000000u64; // LE flag
    attr |= 1u64 << 43; // Bit 43: REVEALED context
}
```

---

### 2. トリガーエイリアスの修正 (parser_v2.py)

**ファイル**: `compiler/parser_v2.py`
**関数**: `_parse_single_pseudocode` (行765-910)

**現状の問題**:
- `ON_OPPONENT_TAP` → `ON_LEAVES` は不正確な近似

**修正内容**:
```python
alias_map = {
    "ON_YELL": "ON_REVEAL",
    "ON_YELL_SUCCESS": "ON_REVEAL",
    "ON_ACTIVATE": "ACTIVATED",
    "JIDOU": "ON_REVEAL",
    "ON_MEMBER_DISCARD": "ON_LEAVES",
    "ON_DISCARDED": "ON_LEAVES",
    "ON_REMOVE": "ON_LEAVES",
    "ON_SET": "ON_PLAY",
    "ON_STAGE_ENTRY": "ON_PLAY",
    "ON_PLAY_OTHER": "ON_PLAY",
    "ON_REVEAL_OTHER": "ON_REVEAL",
    "ON_LIVE_SUCCESS_OTHER": "ON_LIVE_SUCCESS",
    "ON_TURN_START": "TURN_START",
    "ON_TURN_END": "TURN_END",
    # 削除: "ON_OPPONENT_TAP": "ON_LEAVES",  # 不正確
    "ON_TAP": "ACTIVATED",
    "ON_REVEAL_SELF": "ON_REVEAL",
    "ON_LIVE_SUCCESS_SELF": "ON_LIVE_SUCCESS",
    "ACTIVATED_FROM_DISCARD": "ACTIVATED",
    "ON_ENERGY_CHARGE": "ACTIVATED",
    "ON_DRAW": "ACTIVATED",
    # 新規追加
    "ON_OPPONENT_TAP": "ON_OPPONENT_ACTION",  # 新しいトリガータイプが必要
}
```

**追加作業**:
- `engine/models/ability.py` の `TriggerType` に `ON_OPPONENT_ACTION` を追加
- `engine_rust_src/src/core/enums.rs` にも同様に追加

---

### 3. 条件タイプの追加

**ファイル1**: `engine_rust_src/src/core/generated_constants.rs`

```rust
// 追加する条件タイプ
pub const C_COST_LEAD: i32 = 240;
pub const C_SCORE_LEAD: i32 = 241;
pub const C_HEART_LEAD: i32 = 242;
pub const C_HAS_EXCESS_HEART: i32 = 243;
pub const C_NOT_HAS_EXCESS_HEART: i32 = 244;
pub const C_TOTAL_BLADES: i32 = 245;
pub const C_COST_COMPARE: i32 = 246;
```

**ファイル2**: `engine_rust_src/src/core/logic/interpreter.rs`
**関数**: `check_condition_opcode`

```rust
// 追加する条件チェック
C_COST_LEAD => {
    let self_cost = /* 自分の場のコスト合計 */;
    let opp_cost = /* 相手の場のコスト合計 */;
    let reversed = (attr & 0x01) != 0;
    if reversed { opp_cost > self_cost } else { self_cost > opp_cost }
},
C_SCORE_LEAD => {
    let self_score = state.players[p_idx].score;
    let opp_score = state.players[1 - p_idx].score;
    let reversed = (attr & 0x01) != 0;
    if reversed { opp_score > self_score } else { self_score > opp_score }
},
C_HEART_LEAD => {
    let self_hearts = state.get_total_hearts(p_idx, db, 0);
    let opp_hearts = state.get_total_hearts(1 - p_idx, db, 0);
    let reversed = (attr & 0x01) != 0;
    if reversed {
        opp_hearts.total() > self_hearts.total()
    } else {
        self_hearts.total() > opp_hearts.total()
    }
},
C_HAS_EXCESS_HEART => {
    // ライブ成功後の余剰ハートチェック
    state.players[p_idx].excess_hearts > 0
},
C_NOT_HAS_EXCESS_HEART => {
    state.players[p_idx].excess_hearts == 0
},
C_TOTAL_BLADES => {
    let total = state.get_total_blades(p_idx, db, 0);
    let min_val = val as u32;
    total >= min_val
},
```

---

### 4. PER_CARD処理の実装 (interpreter.rs)

**ファイル**: `engine_rust_src/src/core/logic/interpreter.rs`
**関数**: `resolve_bytecode`

**現状の問題**:
- `PER_CARD="OPPONENT_WAIT"` などの乗算処理が未実装

**修正内容**:
```rust
// 効果処理の前に乗算値を計算
let multiplier = if effect.params.contains_key("per_card") {
    let per_card_type = effect.params["per_card"].as_str().unwrap_or("");
    match per_card_type {
        "OPPONENT_WAIT" => {
            let opp_idx = 1 - p_idx;
            (0..3).filter(|&i| state.players[opp_idx].is_tapped(i)).count() as i32
        },
        "SUCCESS_LIVE" => {
            state.players[p_idx].success_lives.len() as i32
        },
        "STAGE" => {
            (0..3).filter(|&i| state.players[p_idx].stage[i] >= 0).count() as i32
        },
        _ => 1
    }
} else {
    1
};

let final_v = v * multiplier;
```

---

### 5. 動的値フラグの修正 (parser_v2.py)

**ファイル**: `compiler/parser_v2.py`
**関数**: `_parse_pseudocode_effects`

**現状の問題**:
- `DRAW(COUNT_STAGE)` などの動的値が正しくフラグ設定されない

**修正内容**:
```python
# 勤的値の検出とフラグ設定
DYNAMIC_VALUE_TYPES = [
    "COUNT_STAGE", "COUNT_HAND", "COUNT_DISCARD", "COUNT_SUCCESS_LIVE",
    "COUNT_ENERGY", "COUNT_BLADES", "COUNT_HEARTS", "COUNT_LIVE_ZONE",
    "COUNT_MEMBER", "TOTAL_BLADES", "TOTAL_HEARTS",
]

if val_str in DYNAMIC_VALUE_TYPES:
    # 動的値フラグ (bit 6 of 'a' parameter)
    a_flags = 64  # 0x40
    val_cond = getattr(ConditionType, val_str, ConditionType.NONE)
else:
    a_flags = 0
    val_cond = ConditionType.NONE
    try:
        val_int = int(val_str)
    except ValueError:
        val_int = 1
```

---

### 6. テストケースの追加

**新規ファイル**: `engine_rust_src/tests/pseudocode_pipeline.rs`

```rust
#[test]
fn test_filter_blade_le() {
        """BLADE_LE_* フィルタが正しくパースされる"""
        parser = AbilityParserV2()
        abilities = parser.parse("TRIGGER: ON_PLAY\nEFFECT: TAP_OPPONENT(1) {FILTER=\"BLADE_LE_3\"}")
        assert len(abilities) == 1
        # フィルタがバイトコードに正しく反映されることを確認

    def test_dynamic_value_count_stage(self):
        """COUNT_STAGE 動的値が正しく処理される"""
        parser = AbilityParserV2()
        abilities = parser.parse("TRIGGER: ON_PLAY\nEFFECT: DRAW(COUNT_STAGE)")
        assert len(abilities) == 1
        # 動的値フラグが設定されることを確認

    def test_per_card_multiplier(self):
        """PER_CARD 乗算が正しく処理される"""
        parser = AbilityParserV2()
        abilities = parser.parse("TRIGGER: ON_LIVE_START\nEFFECT: ADD_BLADES(1) {PER_CARD=\"SUCCESS_LIVE\"}")
        assert len(abilities) == 1
        # PER_CARD パラメータが設定されることを確認

    def test_condition_score_lead(self):
        """SCORE_LEAD 条件が正しくパースされる"""
        parser = AbilityParserV2()
        abilities = parser.parse("TRIGGER: ON_PLAY\nCONDITION: SCORE_LEAD {TARGET=\"OPPONENT\", MODE=\"REVERSED\"}\nEFFECT: DRAW(1)")
        assert len(abilities) == 1
        # 条件が正しく設定されることを確認
```

---

## 実装順序

1. **Phase 1: 基盤修正** (優先度: 高)
   - [ ] `generated_constants.rs` に条件タイプを追加
   - [ ] `interpreter.rs` の `map_filter_string_to_attr` を拡張
   - [ ] `interpreter.rs` に条件チェックを追加

2. **Phase 2: パーサー修正** (優先度: 高)
   - [ ] `parser_v2.py` のトリガーエイリアスを修正
   - [ ] `parser_v2.py` の動的値フラグ設定を修正

3. **Phase 3: 実行ロジック修正** (優先度: 中)
   - [ ] `interpreter.rs` に PER_CARD 処理を実装

4. **Phase 4: テストと検証** (優先度: 高)
   - [ ] テストケースを追加
   - [ ] 既存のカード能力が正しく動作することを確認

---

## 影響範囲

- **parser_v2.py**: トリガーエイリアス、動的値処理
- **interpreter.rs**: フィルタマッピング、条件チェック、PER_CARD処理
- **generated_constants.rs**: 新しい条件タイプの定義
- **enums.rs** (Rust): 新しいトリガータイプの追加（必要に応じて）

---

## リスク評価

| リスク | 影響度 | 軽減策 |
|--------|--------|--------|
| 既存能力の破損 | 高 | 全カードの回帰テストを実施 |
| パフォーマンス低下 | 中 | PER_CARD計算をキャッシュ |
| 新バイトコード形式への移行 | 中 | バージョニングと後方互換性を維持 |
