# parser_v2.py 追加改善分析

## 概要
基本的な改善は完了しましたが、さらに改善すべき点が残っています。

---

## 1. `_parse_pseudocode_conditions` の巨大ifチェーン (Critical)

**場所**: Lines 1425-1799 (約370行)

**問題**: 条件タイプマッピングが巨大なifチェーンで実装されている

```python
# 現在: 370行のifチェーン
if name == "COST_LEAD":
    ctype = ConditionType.SCORE_COMPARE
    params["type"] = "cost"
    ...
if name == "SCORE_LEAD":
    ctype = ConditionType.SCORE_COMPARE
    ...
# ... 100+ more if statements
```

**推奨修正**: 辞書ベースのマッピングに変換

```python
# 条件エイリアス定数を追加
CONDITION_ALIASES = {
    "COST_LEAD": ("SCORE_COMPARE", {"type": "cost", "target": "opponent", "comparison": "GT"}),
    "SCORE_LEAD": ("SCORE_COMPARE", {"type": "score", "comparison": "GT"}),
    "TYPE_MEMBER": ("TYPE_CHECK", {"card_type": "member"}),
    "TYPE_LIVE": ("TYPE_CHECK", {"card_type": "live"}),
    # ... 
}

# HAS_KEYWORDにフォールバックする条件のリスト
CONDITION_KEYWORD_FALLBACKS = {
    "MATCH_": "MATCH",
    "DID_ACTIVATE_": "DID_ACTIVATE",
    # ...
}
```

---

## 2. 重複コード: `ctype = ConditionType.HAS_KEYWORD` パターン

**場所**: Lines 1534-1537, 1547-1554, 1556-1569, 1617-1623, 1625-1627, 1629-1633, 1653-1655, 1657-1659, 1661-1663, 1671-1673, 1679-1681, 1713-1715

**問題**: 同じパターンが15回以上繰り返されている

```python
if name == "COUNT_PLAYED_THIS_TURN":
    ctype = ConditionType.HAS_KEYWORD
    params["keyword"] = "PLAYED_THIS_TURN"
```

**推奨修正**: 辞書で一元管理

```python
KEYWORD_CONDITIONS = {
    "COUNT_PLAYED_THIS_TURN": "PLAYED_THIS_TURN",
    "REVEALED_CONTAINS": "REVEALED_CONTAINS",
    "ZONE": "ZONE_CHECK",
    # ...
}

if name in KEYWORD_CONDITIONS:
    ctype = ConditionType.HAS_KEYWORD
    params["keyword"] = KEYWORD_CONDITIONS[name]
```

---

## 3. デッドコード

**場所**: Line 1631-1632

```python
ctype = ConditionType.HAS_KEYWORD
ctype = ConditionType.HAS_KEYWORD  # 重複
```

---

## 4. 正規表現の事前コンパイル

**場所**: 複数箇所

```python
# 現在: 毎回コンパイル
m = re.match(r"(\w+)(?:\s*\{(.*)\})?", name_part)

# 推奨: モジュールレベルでコンパイル
_CONDITION_PATTERN = re.compile(r"(\w+)(?:\s*\{(.*)\})?")
_EFFECT_PATTERN = re.compile(r"^([\w_]+)(?:\((.*?)\))?\s*(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$")
```

---

## 5. 型ヒントの不完全な適用

**場所**: 複数のメソッド

```python
# 現在
def _preprocess(self, text: str) -> str:  # OK
def _split_sentences(self, text: str) -> List[str]:  # OK
def _is_continuation(self, sentence: str, index: int) -> bool:  # OK

# 型ヒントが不足
def _apply_modifiers(self, ability: Ability, modifiers: Dict[str, Any]):  # -> None がない
def _extract_costs(self, cost_part: str) -> List[Cost]:  # OK
```

---

## 6. エラーハンドリングの不足

**場所**: 複数箇所

```python
# 現在: サイレントに失敗
try:
    val = int(val_str) if val_str else 0
except ValueError:
    val = 0  # ログなし

# 推奨: ログを追加
import logging
logger = logging.getLogger(__name__)

except ValueError:
    logger.debug(f"Non-integer value '{val_str}', defaulting to 0")
    val = 0
```

---

## 7. コメントの整理

**場所**: Lines 1526-1532

```python
# Map min to value for SCORE_COMPARE absolute check?
# Assuming SCORE_COMPARE supports absolute value if target is set?
# Actually logic.rs might compare vs opponent score if no value is set?
# If value IS set, it might compare vs value?
# I'll rely on value mapping logic.
pass  # 何もしない
```

**推奨**: 不要なコメントを削除するか、明確な意図を記述

---

## 8. StructuralLexerのさらなる活用

**場所**: [`_parse_pseudocode_effects()`](compiler/parser_v2.py:1801)

現在は `StructuralLexer.parse_effect()` が存在するが、`_parse_pseudocode_effects()` では使用されていない。

```python
# 現在: 手動正規表現
m = re.match(r"^([\w_]+)(?:\((.*?)\))?\s*(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$", p)

# 推奨: StructuralLexerを使用
structured = StructuralLexer.parse_effect(p)
name = structured.name
val = structured.value
params = structured.params
target_name = structured.target
```

---

## 優先度順の推奨対応

| 優先度 | 項目 | 工数 | 影響 |
|--------|------|------|------|
| High | 条件エイリアスの辞書化 | 中 | 保守性大幅向上 |
| High | 重複コード削除 | 低 | コード削減 |
| Medium | 正規表現の事前コンパイル | 低 | パフォーマンス |
| Medium | 型ヒント完全適用 | 低 | 品質 |
| Low | エラーログ追加 | 低 | デバッグ容易性 |
| Low | StructuralLexer活用拡大 | 中 | 設計一貫性 |

---

## 次のステップ

条件エイリアスの辞書化を実施しますか？
