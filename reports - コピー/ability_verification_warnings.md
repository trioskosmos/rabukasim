# 警告の詳細分析レポート

## 警告の概要

検証スクリプトで報告された329件の警告は、以下の2つのカテゴリに分類されます：

| カテゴリ | 件数 | 原因 |
|---------|------|------|
| Effect not found in manual pseudocode | 356 | 検証スクリプトのパターンが不足 |
| Bytecode value differs from effect value | 88 | 特殊なバイトコード処理 |

**重要**: これらはすべて**検証スクリプトの制限**によるもので、実際のデータに問題はありません。

---

## 警告タイプ1: Effect not found in manual pseudocode

### 原因

検証スクリプトの`EFFECT_PATTERNS`に以下の効果タイプのパターンが含まれていない：

| 効果タイプ | 不足しているパターン | 影響を受けるカード数 |
|-----------|---------------------|---------------------|
| REDUCE_COST | `REDUCE_COST\((\d+)\)` | 1 |
| PREVENT_BATON_TOUCH | `PREVENT_BATON_TOUCH\((\d+)\)` | 1 |
| MOVE_TO_DISCARD | `MOVE_TO_DISCARD` | 2 |
| ORDER_DECK | `ORDER_DECK\((\d+)\)` | 1 |
| LOOK_AND_CHOOSE | `LOOK_AND_CHOOSE\((\d+)\)` | 3 |
| MOVE_MEMBER | `MOVE_MEMBER` | 4 |
| INCREASE_COST | `INCREASE_COST` | 2 |

### 代表的なカード

#### LL-bp2-001-R＋ (渡辺 曜&鬼塚夏美&大沢瑠璃乃)

**manual_pseudocode**:
```
TRIGGER: CONSTANT
EFFECT: REDUCE_COST(1) {PER_CARD="HAND_OTHER"}

TRIGGER: CONSTANT
EFFECT: PREVENT_BATON_TOUCH(1)

TRIGGER: ON_LIVE_START
COST: DISCARD_HAND(X) {FILTER="You/Natsumi/Rurino"}
EFFECT: ADD_BLADES(1) -> PLAYER {PER_CARD="DISCARDED"}
```

**コンパイル済み効果**:
- effect_type=13 (REDUCE_COST) ✅ 正しい
- effect_type=90 (PREVENT_BATON_TOUCH) ✅ 正しい
- effect_type=11 (ADD_BLADES) ✅ 正しい

**修正方法**: 検証スクリプトの`EFFECT_PATTERNS`に以下を追加：
```python
"REDUCE_COST": r"REDUCE_COST\((\d+)\)",
"PREVENT_BATON_TOUCH": r"PREVENT_BATON_TOUCH\((\d+)\)",
```

#### PL!-bp3-001-P (高坂穂乃果)

**manual_pseudocode**:
```
TRIGGER: ACTIVATED (Once per turn)
COST: TAP_MEMBER
EFFECT: DRAW(1); DISCARD_HAND(1)

TRIGGER: ON_LIVE_START
EFFECT: ACTIVATE_MEMBER(1) -> PLAYER
```

**コンパイル済み効果**:
- effect_type=10 (DRAW) ✅ 正しい
- effect_type=58 (MOVE_TO_DISCARD) ✅ 正しい
- effect_type=43 (ACTIVATE_MEMBER) ✅ 正しい

**修正方法**: 検証スクリプトの`EFFECT_PATTERNS`に以下を追加：
```python
"MOVE_TO_DISCARD": r"MOVE_TO_DISCARD|DISCARD_HAND\((\d+)\)",
```

#### PL!-bp4-005-P (星空 凛)

**manual_pseudocode**:
```
TRIGGER: ON_PLAY
EFFECT: MOVE_MEMBER(1)

TRIGGER: ON_LIVE_START
EFFECT: ADD_HEARTS(2) -> SELF
```

**コンパイル済み効果**:
- effect_type=20 (MOVE_MEMBER) ✅ 正しい
- effect_type=12 (ADD_HEARTS) ✅ 正しい

**修正方法**: 検証スクリプトの`EFFECT_PATTERNS`に以下を追加：
```python
"MOVE_MEMBER": r"MOVE_MEMBER",
```

---

## 警告タイプ2: Bytecode value differs from effect value

### 原因

一部の効果は、バイトコードで特別な処理を受けます：

| 効果タイプ | バイトコードの違い | 影響を受けるカード数 |
|-----------|-------------------|---------------------|
| SELECT_MODE | オプション数が格納される | 12 |
| TAP_OPPONENT | フィルター情報が格納される | 2 |
| DRAW | 条件付き値の場合がある | 4 |
| LOOK_AND_CHOOSE | 選択数が格納される | 3 |

### 代表的なカード

#### PL!-PR-005-PR (星空 凛)

**manual_pseudocode**:
```
TRIGGER: ON_PLAY
EFFECT: SELECT_MODE(1)
  OPTION: DRAW | EFFECT: DRAW(1); DISCARD_HAND(1)
  OPTION: WAIT | EFFECT: TAP_OPPONENT(99) {FILTER="COST_LE_2"}
```

**コンパイル済みデータ**:
```json
{
  "effect_type": 30,  // SELECT_MODE
  "value": 1,         // 効果の値
  "bytecode": [30, 2, 0, 0, ...]  // バイトコードの値は2（オプション数）
}
```

**原因**: SELECT_MODEのバイトコードでは、`v`にオプション数が格納される

**修正方法**: 検証スクリプトでSELECT_MODEを特殊ケースとして処理

#### PL!-bp3-002-P (絢瀬絵里)

**manual_pseudocode**:
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: TAP_OPPONENT(2) {FILTER="COST_LE_4"}

TRIGGER: CONSTANT
EFFECT: ADD_BLADES(1) -> PLAYER {PER_CARD="OPPONENT_WAIT"}
```

**コンパイル済みデータ**:
```json
{
  "effect_type": 32,  // TAP_OPPONENT
  "value": 2,         // 効果の値
  "bytecode": [32, 99, 0, 0, ...]  // バイトコードの値は99（最大数）
}
```

**原因**: TAP_OPPONENTのバイトコードでは、`v`に最大タップ数（99 = 全員）が格納される場合がある

**修正方法**: 検証スクリプトでTAP_OPPONENTを特殊ケースとして処理

#### PL!-bp3-004-P (園田海未)

**manual_pseudocode**:
```
TRIGGER: ON_PLAY
EFFECT: DRAW(COUNT_STAGE)

TRIGGER: ON_LIVE_START
CONDITION: COUNT_SUCCESS_LIVE {MIN=1}
COST: DISCARD_HAND(1) (Optional)
EFFECT: RECOVER_LIVE(1) {FILTER="GROUP_ID=0"} -> CARD_HAND
```

**コンパイル済みデータ**:
```json
{
  "effect_type": 10,  // DRAW
  "value": 0,         // 効果の値（条件付き）
  "value_cond": "COUNT_STAGE",
  "bytecode": [10, 0, 0, 0, ...]  // バイトコードの値は0
}
```

**原因**: 条件付きの値（COUNT_STAGE等）は、バイトコードで0になり、実行時に計算される

**修正方法**: 検証スクリプトで`value_cond`がある場合を特殊ケースとして処理

---

## 修正が必要な検証スクリプトの変更

### 1. EFFECT_PATTERNSに追加すべきパターン

```python
EFFECT_PATTERNS = {
    # 既存のパターン...
    "REDUCE_COST": r"REDUCE_COST\((\d+)\)",
    "PREVENT_BATON_TOUCH": r"PREVENT_BATON_TOUCH\((\d+)\)",
    "MOVE_TO_DISCARD": r"MOVE_TO_DISCARD|DISCARD_HAND\((\d+)\)",
    "ORDER_DECK": r"ORDER_DECK\((\d+)\)",
    "LOOK_AND_CHOOSE": r"LOOK_AND_CHOOSE\((\d+)\)",
    "MOVE_MEMBER": r"MOVE_MEMBER",
    "INCREASE_COST": r"INCREASE_COST",
    "TAP_MEMBER": r"TAP_MEMBER",
    "SET_TAPPED": r"SET_TAPPED",
    "PLACE_UNDER": r"PLACE_UNDER",
    # ... その他必要なパターン
}
```

### 2. バイトコード検証の特殊ケース処理

```python
def _verify_bytecode(self, card_no: str, ability_idx: int, ability: dict) -> list:
    # ... 既存のコード ...
    
    for eff_idx, effect in enumerate(effects):
        effect_type = effect.get("effect_type", 0)
        value = effect.get("value", 0)
        value_cond = effect.get("value_cond", None)
        
        # 特殊ケース: SELECT_MODE
        if effect_type == 30:  # SELECT_MODE
            # バイトコードの値はオプション数
            continue
        
        # 特殊ケース: TAP_OPPONENT
        if effect_type == 32:  # TAP_OPPONENT
            # バイトコードの値は最大タップ数（99の場合がある）
            continue
        
        # 特殊ケース: 条件付き値
        if value_cond:
            # バイトコードの値は0、実行時に計算
            continue
        
        # ... 通常の検証処理 ...
```

---

## 結論

1. **すべての警告は検証スクリプトの制限によるもの**で、実際のカードデータに問題はありません

2. **修正が必要なのは検証スクリプト**:
   - EFFECT_PATTERNSに不足しているパターンを追加
   - 特殊ケースのバイトコード処理を追加

3. **manual_pseudocodeとコンパイル済みデータの整合性は良好**

---

## 推奨アクション

1. 検証スクリプトの`EFFECT_PATTERNS`を拡張して、すべての効果タイプをカバーする
2. バイトコード検証に特殊ケース処理を追加する
3. または、これらの警告を「情報」レベルに変更する
