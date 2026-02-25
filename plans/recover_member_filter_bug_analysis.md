# RECOVER_MEMBER フィルターエンコーディングバグ分析

## 問題の概要

カード「大沢瑠璃乃 (PL!HS-bp2-005-P)」の登場時能力が、本来「みらくらぱーく！」のカードのみを回収すべきところ、非「みらくらぱーく！」カードも回収できてしまうバグが報告されました。

## 根本原因

[`engine/models/ability.py:1305-1350`](engine/models/ability.py:1305) のコードが、`if eff.effect_type == EffectType.META_RULE:` ブロックの中に誤ってネストされています。

```python
# line 1277
if eff.effect_type == EffectType.META_RULE:
    # ... META_RULE specific code ...
    
    # line 1305-1317: このコードは META_RULE ブロックの中にあるため、
    # RECOVER_MEMBER などの効果タイプでは実行されない
    if eff.effect_type in (
        EffectType.PLAY_MEMBER_FROM_HAND,
        EffectType.PLAY_MEMBER_FROM_DISCARD,
        EffectType.PLAY_LIVE_FROM_DISCARD,
        EffectType.RECOVER_MEMBER,
        EffectType.RECOVER_LIVE,
        EffectType.MOVE_TO_DISCARD,
        EffectType.SELECT_CARDS,
        EffectType.SELECT_MEMBER,
        EffectType.SELECT_LIVE,
        EffectType.REVEAL_UNTIL,
    ):
        attr = self._pack_filter_attr(eff)  # これが呼び出されない！
```

## バイトコード分析

### 正しいバイトコード（期待値）

`FILTER="UNIT_MIRAKURA"` (unit=15) の場合:
- Unit Filter Enable (bit 16): `0x10000`
- Unit ID 15 (bits 17-23): `15 << 17 = 0x1E0000`
- 合計: `0x10000 | 0x1E0000 = 0x1F0000 = 2031616`

### 実際のバイトコード

```json
"bytecode": [
    58, 1, 1, 0, 6,        // COST: MOVE_TO_DISCARD
    203, 1, 0, 0, 0,       // CONDITION: COUNT_STAGE
    17, 1, 0, 0, 458758,   // EFFECT: RECOVER_MEMBER (attr=0, slot=458758)
    1, 0, 0, 0, 0          // RETURN
]
```

- `attr = 0` (フィルターがエンコードされていない)
- `slot = 458758` (これは source zone encoding のみ)

## 影響を受けるカード

### 直接影響（RECOVER_MEMBER with UNIT filter）

| カード番号 | カード名 | フィルター |
|-----------|---------|-----------|
| PL!HS-bp2-005-P | 大沢瑠璃乃 | UNIT_MIRAKURA |
| PL!HS-bp2-005-P+ | 大沢瑠璃乃 | UNIT_MIRAKURA |
| PL!HS-bp2-005-R+ | 大沢瑠璃乃 | UNIT_MIRAKURA |
| PL!HS-bp2-005-SEC | 大沢瑠璃乃 | UNIT_MIRAKURA |
| PL!-pb1-030-L | Love Marginal | UNIT_BIBI |

### 間接的影響（他の効果タイプ）

以下の効果タイプも同様にフィルターがエンコードされない可能性があります：

- `PLAY_MEMBER_FROM_HAND`
- `PLAY_MEMBER_FROM_DISCARD`
- `PLAY_LIVE_FROM_DISCARD`
- `MOVE_TO_DISCARD`
- `SELECT_CARDS`
- `SELECT_MEMBER`
- `SELECT_LIVE`
- `REVEAL_UNTIL`

## 修正方法

[`engine/models/ability.py:1305-1350`](engine/models/ability.py:1305) のコードを `if eff.effect_type == EffectType.META_RULE:` ブロックの外に移動する必要があります。

### 修正前

```python
if eff.effect_type == EffectType.META_RULE:
    # ... META_RULE specific code ...
    
    if eff.effect_type in (...):  # 誤ったネスト
        attr = self._pack_filter_attr(eff)
```

### 修正後

```python
if eff.effect_type == EffectType.META_RULE:
    # ... META_RULE specific code ...

if eff.effect_type in (...):  # 正しいインデントレベル
    attr = self._pack_filter_attr(eff)
```

## 検証方法

1. 修正後にカードを再コンパイル
2. バイトコードの `attr` 値が正しくエンコードされていることを確認
3. シナリオテストで正しいフィルタリング動作を確認

## 影響を受ける効果タイプ一覧

以下の効果タイプがすべてこのバグの影響を受けます：

| 効果タイプ | 説明 | 影響を受けるカード数（推定） |
|-----------|------|---------------------------|
| RECOVER_MEMBER | 控え室からメンバー回収 | 5+ |
| RECOVER_LIVE | 控え室からライブ回収 | 少 |
| PLAY_MEMBER_FROM_HAND | 手札からメンバー登場 | 多 |
| PLAY_MEMBER_FROM_DISCARD | 控え室からメンバー登場 | 10+ |
| PLAY_LIVE_FROM_DISCARD | 控え室からライブ登場 | 少 |
| MOVE_TO_DISCARD | 控え室に移動 | 多 |
| SELECT_CARDS | カード選択 | 多 |
| SELECT_MEMBER | メンバー選択 | 50+ |
| SELECT_LIVE | ライブ選択 | 少 |
| REVEAL_UNTIL | 公開継続 | 少 |

## 具体的な影響例

### PLAY_MEMBER_FROM_DISCARD with FILTER

```
PL!-pb1-018-P+: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="COST_LE_2"}
PL!HS-bp1-002-P: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=4, COST_LE_15"}
PL!S-bp3-006-P: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=1, COST_EQ_TARGET_PLUS_2"}
PL!SP-bp4-004-P: PLAY_MEMBER_FROM_DISCARD(1) {FILTER="GROUP_ID=3, COST_LE=4"}
```

これらのカードは、本来フィルター条件を満たすカードのみを選択できるはずが、
フィルターがエンコードされていないため、任意のカードを選択できてしまいます。

### SELECT_MEMBER with FILTER

```
PL!N-bp3-011-P: SELECT_MEMBER(1) {TARGET="OPPONENT", FILTER="NOT_NAME=Mia"}
PL!N-pb1-003-P+: SELECT_MEMBER(1) {TARGET="PLAYER", FILTER="GROUP_ID=3"}
PL!S-bp3-006-P: SELECT_MEMBER(1) {TARGET="OTHER_MEMBER", FILTER="GROUP_ID=1"}
```

これらのカードも同様に、フィルターが機能せず、任意のメンバーを選択できてしまいます。

## 関連ファイル

- [`engine/models/ability.py`](engine/models/ability.py) - バイトコードコンパイラ
- [`engine/data/cards_compiled.json`](engine/data/cards_compiled.json) - コンパイル済みカードデータ
- [`data/manual_pseudocode.json`](data/manual_pseudocode.json) - 擬似コード定義

## 追加の問題

### 1. SELECT_MEMBER の重複処理

[`engine/models/ability.py`](engine/models/ability.py) で SELECT_MEMBER に対して `_pack_filter_attr` が2回呼び出される可能性があります：

- **lines 1003-1004**: `if eff.effect_type == EffectType.SELECT_MEMBER:`
- **lines 1104-1117**: `if eff.effect_type in (EffectType.SELECT_CARDS, EffectType.SELECT_MEMBER, EffectType.SELECT_LIVE):`

これは重複しており、最初の呼び出しが2番目の呼び出しで上書きされる可能性があります。

### 2. PLAY_MEMBER_FROM_HAND/DISCARD の重複処理

同様に、PLAY_MEMBER_FROM_HAND と PLAY_MEMBER_FROM_DISCARD も重複しています：

- **lines 1007-1008**: `if eff.effect_type in (EffectType.PLAY_MEMBER_FROM_HAND, EffectType.PLAY_MEMBER_FROM_DISCARD):`
- **lines 1305-1317** (META_RULE ブロック内): 同じ効果タイプが含まれている

### 3. PLAY_LIVE_FROM_DISCARD の重複処理

- **lines 1011-1012**: `if eff.effect_type == EffectType.PLAY_LIVE_FROM_DISCARD:`
- **lines 1305-1317** (META_RULE ブロック内): 同じ効果タイプが含まれている

## 修正の優先度

**緊急（高）** - このバグは多数のカードのゲームロジックに影響を与え、
プレイヤーが本来選択できないはずのカードを選択できる状態になっています。
ゲームの公平性と正確性に重大な影響を与えるため、早急な修正が必要です。

## 推奨される修正アプローチ

1. **lines 1305-1350 を META_RULE ブロックの外に移動**
2. **重複する処理を削除** - SELECT_MEMBER、PLAY_MEMBER_FROM_HAND/DISCARD、PLAY_LIVE_FROM_DISCARD は lines 1003-1012 で既に処理されているため、lines 1305-1317 からこれらを削除
3. **再コンパイル** - 修正後に全カードを再コンパイルしてバイトコードを更新

## コード修正の詳細

### 修正前（lines 1305-1317）
```python
if eff.effect_type in (
    EffectType.PLAY_MEMBER_FROM_HAND,      # 重複 - lines 1007-1008 で処理済み
    EffectType.PLAY_MEMBER_FROM_DISCARD,   # 重複 - lines 1007-1008 で処理済み
    EffectType.PLAY_LIVE_FROM_DISCARD,     # 重複 - lines 1011-1012 で処理済み
    EffectType.RECOVER_MEMBER,             # バグ - このブロック内では実行されない
    EffectType.RECOVER_LIVE,               # バグ - このブロック内では実行されない
    EffectType.MOVE_TO_DISCARD,            # バグ - このブロック内では実行されない
    EffectType.SELECT_CARDS,               # バグ - このブロック内では実行されない
    EffectType.SELECT_MEMBER,              # 重複 - lines 1003-1004 で処理済み
    EffectType.SELECT_LIVE,                # バグ - このブロック内では実行されない
    EffectType.REVEAL_UNTIL,               # バグ - このブロック内では実行されない
):
    attr = self._pack_filter_attr(eff)
```

### 修正後
```python
# META_RULE ブロックの外に移動
if eff.effect_type in (
    EffectType.RECOVER_MEMBER,
    EffectType.RECOVER_LIVE,
    EffectType.MOVE_TO_DISCARD,
    EffectType.SELECT_CARDS,
    EffectType.SELECT_LIVE,
    EffectType.REVEAL_UNTIL,
):
    attr = self._pack_filter_attr(eff)
    # ... 残りの処理
```
