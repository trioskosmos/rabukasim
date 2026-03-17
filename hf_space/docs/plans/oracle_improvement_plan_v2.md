# Pseudocode Oracle 改善計画 v2

## 現状分析

### セマンティック監査結果
- **パス率**: 533/983 アビリティ (54.2%)
- **前回比**: 87.1% → 54.2% (低下)
- **原因**: PseudocodeOracleの解析精度不足

### 特定された問題点

#### 1. トリガー正規化の問題
```json
// 現在の出力 (誤り)
"trigger": "ONPLAY"

// 期待される出力
"trigger": "ON_PLAY"
```
- `TRIGGER_MAP`の値にアンダースコアが含まれていない
- `ON_LIVE_START` → `ONLIVESTART` に変換されている

#### 2. 動的値の処理不足
```pseudocode
EFFECT: DRAW(COUNT_STAGE)     // ステージ上のカード数
EFFECT: TAP_OPPONENT(99)      // 99 = 全て/条件なし
EFFECT: ACTIVATE_MEMBER(ALL)  // ALL = 全て
```
- 動的パラメータが数値として解析されていない
- `99` は「条件なし」または「全て」を意味する特殊値

#### 3. 条件付き効果の未処理
```pseudocode
TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE {MIN=1}
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1)
```
- `CONDITION:` ブロックが完全に無視されている
- 条件付きで効果が発動しないケースを考慮していない

#### 4. モーダル選択の不完全な処理
```pseudocode
EFFECT: SELECT_MODE(1)
  OPTION: DRAW | EFFECT: DRAW(1); DISCARD_HAND(1)
  OPTION: WAIT | EFFECT: TAP_OPPONENT(99) {FILTER="COST_LE_2"}
```
- 現在は `MODAL_CHOICE` として単一のデルタのみ生成
- 各オプションの効果が展開されていない

#### 5. フィルター構文の未解析
```pseudocode
EFFECT: TAP_OPPONENT(99) {FILTER="COST_LE_4"}
EFFECT: RECOVER_LIVE(1) {FILTER="HEARTS_GE_3, COLOR_PINK"}
```
- フィルター条件がデルタに反映されていない
- ターゲット制限が考慮されていない

#### 6. 効果マッピングの不足
現在の `EFFECT_TO_DELTA` は基本的な効果のみ:
```python
EFFECT_TO_DELTA = {
    "DRAW": "HAND_DELTA",
    "DISCARD_HAND": "HAND_DISCARD",
    # ... 約15種類のみ
}
```

不足している効果:
- `CHEER_REVEAL` → 適切なデルタなし
- `BUFF_POWER` → `POWER_DELTA`
- `LOOK_AND_CHOOSE_REVEAL` → 複合デルタ
- `ADD_HEARTS` → `HEART_DELTA`

---

## 改善計画

### Phase 1: 基本修正

#### 1.1 トリガー正規化の修正
```python
TRIGGER_MAP = {
    "ON_PLAY": "ON_PLAY",        # 正しい
    "ON_LIVE_START": "ON_LIVE_START",  # 正しい
    "ONLIVESTART": "ON_LIVE_START",    # エイリアス追加
    # ...
}
```

#### 1.2 動的値の処理
```python
DYNAMIC_VALUES = {
    "COUNT_STAGE": "DYNAMIC:stage_count",
    "COUNT_SUCCESS_LIVE": "DYNAMIC:success_live_count",
    "99": "ALL",
    "ALL": "ALL",
}

def parse_value(value_str: str) -> Union[int, str]:
    if value_str in DYNAMIC_VALUES:
        return DYNAMIC_VALUES[value_str]
    try:
        return int(value_str)
    except ValueError:
        return value_str
```

### Phase 2: 条件処理

#### 2.1 CONDITION ブロック解析
```python
def extract_conditions(self, block: str) -> list:
    conditions = []
    cond_match = re.search(r'CONDITION:\s*(.+?)(?=\nCOST:|\nEFFECT:|\Z)', block, re.DOTALL)
    if cond_match:
        # COUNT_SUCCESS_LIVE {MIN=1}
        # COUNT_HAND {FILTER="Ayumu"}
        conditions.append({
            "type": "PRECONDITION",
            "expression": cond_match.group(1).strip()
        })
    return conditions
```

#### 2.2 条件付きアビリティのマーク
```python
return {
    "trigger": trigger_type,
    "sequence": sequence,
    "conditions": conditions,  # 追加
    "optional": is_optional,
    "once_per_turn": once_per_turn
}
```

### Phase 3: モーダル選択

#### 3.1 SELECT_MODE 処理
```python
def parse_modal_options(self, block: str) -> list:
    options = []
    # OPTION: <name> | EFFECT: ...
    option_matches = re.finditer(r'OPTION:\s*([^|]+)\|\s*EFFECT:\s*(.+?)(?=\nOPTION:|\Z)', block, re.DOTALL)
    for match in option_matches:
        options.append({
            "name": match.group(1).strip(),
            "effects": self.extract_effects(match.group(2))
        })
    return options
```

#### 3.2 モーダル出力形式
```json
{
  "trigger": "ON_PLAY",
  "sequence": [
    {
      "text": "EFFECT: SELECT_MODE(1)",
      "deltas": [{"tag": "MODAL_CHOICE", "value": 1}],
      "options": [
        {
          "name": "DRAW",
          "sequence": [
            {"text": "EFFECT: DRAW(1)", "deltas": [{"tag": "HAND_DELTA", "value": 1}]},
            {"text": "EFFECT: DISCARD_HAND(1)", "deltas": [{"tag": "HAND_DISCARD", "value": 1}]}
          ]
        },
        {
          "name": "WAIT",
          "sequence": [
            {"text": "EFFECT: TAP_OPPONENT(99)", "deltas": [{"tag": "MEMBER_TAP_DELTA", "value": 1}]}
          ]
        }
      ]
    }
  ]
}
```

### Phase 4: フィルター処理

#### 4.1 フィルター解析
```python
FILTER_PATTERNS = {
    "COST_LE": r'COST_LE[_=](\d+)',
    "HEARTS_GE": r'HEARTS_GE[_=](\d+)',
    "COLOR": r'COLOR[_=](\w+)',
    "GROUP_ID": r'GROUP_ID[_=](\d+)',
    "CHARACTER": r'FILTER="([^"]+)"',
}

def parse_filter(self, filter_str: str) -> dict:
    filters = {}
    for name, pattern in FILTER_PATTERNS.items():
        match = re.search(pattern, filter_str)
        if match:
            filters[name] = match.group(1)
    return filters
```

#### 4.2 フィルター付きデルタ
```json
{
  "text": "EFFECT: TAP_OPPONENT(99)",
  "deltas": [{"tag": "MEMBER_TAP_DELTA", "value": 1}],
  "filter": {"COST_LE": 4}
}
```

### Phase 5: 効果マッピング拡充

#### 5.1 新しい効果マッピング
```python
EFFECT_TO_DELTA = {
    # 既存
    "DRAW": "HAND_DELTA",
    "DISCARD_HAND": "HAND_DISCARD",
    "TAP_OPPONENT": "MEMBER_TAP_DELTA",
    "ADD_BLADES": "BLADE_DELTA",
    "BOOST_SCORE": "SCORE_DELTA",

    # 追加
    "RECOVER_MEMBER": "HAND_DELTA",
    "RECOVER_LIVE": "LIVE_RECOVER",
    "ACTIVATE_ENERGY": "ENERGY_ACTIVATE",
    "ACTIVATE_MEMBER": "ENERGY_ACTIVATE",
    "ADD_HEARTS": "HEART_DELTA",
    "BUFF_POWER": "POWER_DELTA",
    "LOOK_AND_CHOOSE": "DECK_SEARCH",
    "LOOK_AND_CHOOSE_REVEAL": "DECK_SEARCH",
    "LOOK_AND_CHOOSE_ORDER": "DECK_SEARCH",
    "SELECT_MODE": "MODAL_CHOICE",
    "REVEAL_UNTIL": "DECK_SEARCH",
    "MOVE_TO_DECK": "DISCARD_DELTA",
    "MOVE_TO_DISCARD": "DISCARD_DELTA",
    "PAY_ENERGY": "ENERGY_COST",
    "CHEER_REVEAL": "CHEER_REVEAL",
    "REDUCE_COST": "COST_REDUCTION",
    "REDUCE_HEART_REQ": "HEART_REQ_REDUCTION",
    "PREVENT_ACTIVATE": "PREVENT_ACTIVATE",
    "PREVENT_BATON_TOUCH": "PREVENT_BATON_TOUCH",
}
```

---

## 実装優先順位

1. **Phase 1** (高): トリガー正規化 - 基本的な解析精度に影響
2. **Phase 5** (高): 効果マッピング拡充 - 多くのカードで効果が空になる問題を解決
3. **Phase 2** (中): 条件処理 - 条件付きアビリティの正確な判定
4. **Phase 3** (中): モーダル選択 - 選択肢を持つカードの正確な処理
5. **Phase 4** (低): フィルター処理 - ターゲット制限の正確な表現

---

## 期待される改善

### 改善前
- パス率: 54.2% (533/983)
- 空シーケンス: 多数
- トリガー不一致: 多数

### 改善後 (目標)
- パス率: 75%+ (737+/983)
- 空シーケンス: 大幅削減
- トリガー一致: 95%+

---

## 次のステップ

1. `pseudocode_oracle.py` の修正実装
2. テスト実行による検証
3. 失敗ケースの分析と追加修正
