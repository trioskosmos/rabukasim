# Lean 32-bit Layout 改善計画

## 概要

このドキュメントは、ユーザーの提案に基づき、現在の「God Object」的な `a` (Attribute) ワードを整理し、4整数バイトコード構造 `[op, v, a, s]` を維持しながら、ビット競合を解消する計画です。

---

## 1. 現状の問題点

### 1.1 `a` ワードの過密パッキング

現在の `_pack_filter_attr` は以下を 32ビットに詰め込もうとしています:

| フィルタ種別 | 現在のビット位置 | 必要ビット数 |
|-------------|-----------------|-------------|
| Card Type | 2-3 | 2ビット |
| Group ID | 5-11 | **7ビット** (過剰) |
| Unit ID | 17-23 | **7ビット** (過剰) |
| Cost Filter | 24-30 | 7ビット |
| Color Filter | 24-30 | **競合!** |
| Tapped Flag | 12 | 1ビット |
| Blade Heart | 13-14 | 2ビット |
| Character IDs | 32-59 | **32ビット超過!** |

### 1.2 実際のゲーム要件

Love Live! カードゲームの実際の範囲:

| カテゴリ | 実際の数 | 必要ビット数 |
|---------|---------|-------------|
| Groups (μ's, Aqours, 等) | ~5 | **3ビット** (0-7) |
| Units (小队) | ~20 | **5ビット** (0-31) |
| Colors (Pink, Red, 等) | 7 | **3ビット** (0-7) |
| Cost | 0-11 | **4ビット** (0-15) |
| Character Names | ~50 | 別命令で処理 |

---

## 2. Lean 32-bit Layout 提案

### 2.1 新しいビットレイアウト

#### `op` (Int 1) - Opcode
```
変更なし: 命令コード (0-255)
```

#### `v` (Int 2) - Value/Counts + Color
```
┌─────────────────────────────────────────────────────────────────┐
│ Bits 0-15  : Count/Value (ドロー枚数、コスト値など)              │
│ Bits 16-21 : Color Mask (6ビット = 7色 + 予備)                  │
│ Bits 22-31 : 予備 (動的値フラグなど)                            │
└─────────────────────────────────────────────────────────────────┘
```

**変更点**: Color Filter を `a` から `v` に移動

#### `s` (Int 4) - Slot/Zones + Flags
```
┌─────────────────────────────────────────────────────────────────┐
│ Bits 0-7   : Target Slot (0-255)                               │
│ Bits 8-15  : Remainder/Destination Zone                        │
│ Bits 16-23 : Source Zone                                       │
│ Bit  24    : TARGET_OPPONENT フラグ                            │
│ Bit  25    : REVEAL_REMAINING フラグ                           │
│ Bits 26-31 : 予備                                              │
└─────────────────────────────────────────────────────────────────┘
```

**変更点**: システムフラグを上位ビットに集約

#### `a` (Int 3) - Attribute Filter (スリム化)
```
┌─────────────────────────────────────────────────────────────────┐
│ Bit  0     : IS_OPTIONAL (「～てもよい」)                       │
│ Bit  1     : DYNAMIC_VALUE (動的値フラグ)                       │
│ Bits 2-3   : Card Type (0=Any, 1=Member, 2=Live)               │
│ Bits 4-7   : Group ID (4ビット = 0-15グループ)                  │
│ Bits 8-12  : Unit ID (5ビット = 0-31ユニット)                   │
│ Bits 13-17 : Cost Threshold (5ビット = 0-31コスト)              │
│ Bit  18    : Cost Mode (0=GE, 1=LE)                            │
│ Bit  19    : Tapped Filter                                     │
│ Bit  20    : Has Blade Heart                                   │
│ Bit  21    : Not Has Blade Heart                               │
│ Bits 22-31 : 予備                                              │
└─────────────────────────────────────────────────────────────────┘
```

**変更点**:
- Group ID: 7ビット → 4ビット
- Unit ID: 7ビット → 5ビット
- Color Filter: 削除 (v に移動)
- Character IDs: 削除 (別命令で処理)

---

## 3. Character ID の処理方法

### 3.1 現在の問題

現在、Character ID を `a` のビット 32-59 にパックしようとしていますが、これは 32ビット整数では**即座に切り捨てられます**。

### 3.2 解決策: Assembly-Style Unrolling

「ちかという名前のピンクメンバーを捨て札から選ぶ」という効果がある場合:

**現在のアプローチ (失敗)**:
```
[OP_SELECT_MEMBER, 1, TYPE=Member|COLOR=Pink|CHAR=Chika, ZONE=Discard]
// ↑ CHAR=Chika は切り捨てられる!
```

**新しいアプローチ (成功)**:
```
[OP_FILTER_ZONE, ZONE=Discard, FILTER_TYPE=Member|COLOR=Pink, 0]
[OP_FILTER_CHARACTER, CHAR_ID=Chika, 0, 0]
[OP_PLAY_SELECTED, 1, 0, TARGET_SLOT]
```

### 3.3 新しい Opcode の必要性

| Opcode | 用途 |
|--------|------|
| `OP_FILTER_ZONE` | ゾーンからカードをフィルタリングして `looked_cards` に格納 |
| `OP_FILTER_CHARACTER` | `looked_cards` をさらにキャラクター名でフィルタリング |
| `OP_PLAY_SELECTED` | `looked_cards` のカードをプレイ |

**注意**: 既存の `OP_LOOK_AND_CHOOSE` と `OP_SELECT_CARDS` を拡張して、フィルタ連鎖をサポートすることも可能です。

---

## 4. 実装ステップ

### Phase 1: Color Filter の移動 (優先度: 高)

1. **Python コンパイラ更新**
   - `_pack_filter_attr` から Color Filter を削除
   - `_compile_single_effect` で Color を `v` のビット 16-21 にパック

2. **Rust インタープリタ更新**
   - `handle_look_and_choose`, `handle_select_cards` 等で `v` から Color を抽出

3. **テスト**
   - Color Filter を使用するカードのパリティテスト

### Phase 2: Group/Unit ID の縮小 (優先度: 中)

1. **ビット幅の変更**
   - Group ID: 7ビット → 4ビット
   - Unit ID: 7ビット → 5ビット

2. **マスク定数の更新**
   - `metadata.json` の `extra_constants` を更新
   - `sync_metadata.py` を再実行

### Phase 3: Character ID の分離 (優先度: 中)

1. **新しい Opcode の追加**
   - `OP_FILTER_CHARACTER` (または既存の拡張)

2. **コンパイラの更新**
   - Character ID を含む効果を複数命令に展開

---

## 5. 新しいビットレイアウトの詳細

### 5.1 `v` (Value) ワードの詳細

```python
def pack_value(count: int, color_mask: int = 0, flags: int = 0) -> int:
    """
    Pack value word:
    - Bits 0-15: Count/Value
    - Bits 16-21: Color Mask (bit 0=Pink, 1=Red, 2=Yellow, 3=Green, 4=Blue, 5=Purple, 6=Star)
    - Bits 22-31: Reserved
    """
    return (count & 0xFFFF) | ((color_mask & 0x3F) << 16)

def unpack_value(v: int) -> tuple[int, int]:
    """Unpack value word into (count, color_mask)"""
    count = v & 0xFFFF
    color_mask = (v >> 16) & 0x3F
    return count, color_mask
```

### 5.2 `a` (Attribute) ワードの詳細

```python
def pack_attr(
    is_optional: bool = False,
    is_dynamic: bool = False,
    card_type: int = 0,  # 0=Any, 1=Member, 2=Live
    group_id: int = 0,
    unit_id: int = 0,
    cost_threshold: int = 0,
    cost_is_le: bool = False,
    is_tapped: bool = False,
    has_blade_heart: bool = False,
    not_blade_heart: bool = False,
) -> int:
    """
    Pack attribute filter word (Lean Layout):
    - Bit 0: IS_OPTIONAL
    - Bit 1: DYNAMIC_VALUE
    - Bits 2-3: Card Type
    - Bits 4-7: Group ID (4 bits)
    - Bits 8-12: Unit ID (5 bits)
    - Bits 13-17: Cost Threshold (5 bits)
    - Bit 18: Cost Mode (0=GE, 1=LE)
    - Bit 19: Tapped Filter
    - Bit 20: Has Blade Heart
    - Bit 21: Not Has Blade Heart
    """
    attr = 0
    if is_optional: attr |= 1 << 0
    if is_dynamic: attr |= 1 << 1
    attr |= (card_type & 0x3) << 2
    attr |= (group_id & 0xF) << 4
    attr |= (unit_id & 0x1F) << 8
    attr |= (cost_threshold & 0x1F) << 13
    if cost_is_le: attr |= 1 << 18
    if is_tapped: attr |= 1 << 19
    if has_blade_heart: attr |= 1 << 20
    if not_blade_heart: attr |= 1 << 21
    return attr
```

### 5.3 `s` (Slot) ワードの詳細

```python
def pack_slot(
    target_slot: int,
    source_zone: int = 0,
    remainder_zone: int = 0,
    target_opponent: bool = False,
    reveal_remaining: bool = False,
) -> int:
    """
    Pack slot/zone word:
    - Bits 0-7: Target Slot
    - Bits 8-15: Remainder/Destination Zone
    - Bits 16-23: Source Zone
    - Bit 24: TARGET_OPPONENT flag
    - Bit 25: REVEAL_REMAINING flag
    """
    s = target_slot & 0xFF
    s |= (remainder_zone & 0xFF) << 8
    s |= (source_zone & 0xFF) << 16
    if target_opponent: s |= 1 << 24
    if reveal_remaining: s |= 1 << 25
    return s
```

---

## 6. 影響を受けるファイル

### 6.1 Python (Compiler)

| ファイル | 変更内容 |
|---------|---------|
| `engine/models/ability.py` | `_pack_filter_attr`, `_compile_single_effect` の更新 |
| `data/metadata.json` | `extra_constants` の更新 |

### 6.2 Rust (Interpreter)

| ファイル | 変更内容 |
|---------|---------|
| `engine_rust_src/src/core/generated_constants.rs` | 自動再生成 |
| `engine_rust_src/src/core/logic/filter.rs` | `CardFilter::from_packed` の更新 |
| `engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs` | `v` からの Color 抽出 |

### 6.3 Tests

| ファイル | 変更内容 |
|---------|---------|
| `engine_rust_src/src/parity_tests.rs` | 新しいレイアウトに対応 |
| `tools/verify/bytecode_decoder.py` | デコーダの更新 |

---

## 7. リスク評価

| リスク | 影響度 | 軽減策 |
|-------|-------|-------|
| 既存カードの破損 | 高 | 段階的移行、パリティテスト |
| Rust/Python 間の不整合 | 高 | 同時更新、自動テスト |
| Group ID 4ビット不足 | 低 | 現在5グループ、予備11枠 |

---

## 8. 次のステップ

1. **ユーザー確認**: この計画で進めてよいか確認
2. **Phase 1 実装**: Color Filter の移動
3. **パリティテスト**: 全カードのテスト実行
4. **Phase 2-3 実装**: Group/Unit 縮小、Character 分離

---

## 付録: 現在のビット使用状況の可視化

### 現在 (問題あり)
```
a (Attribute):
┌─────────────────────────────────────────────────────────────────┐
│ ?? ?? TTT GGGGGGG UUUUUUU CCCCCCC ?????? ?????? ?????? ?????? │
│     │   │       │       │       │
│     │   │       │       │       └─ Color (Cost と競合!)       │
│     │   │       │       └─ Cost Filter                        │
│     │   │       └─ Unit ID (7bit = 過剰)                      │
│     │   └─ Group ID (7bit = 過剰)                             │
│     └─ Type                                                  │
└─────────────────────────────────────────────────────────────────┘
ビット 32以上: Character IDs (切り捨てられる!)
```

### 提案 (Lean)
```
v (Value):
┌─────────────────────────────────────────────────────────────────┐
│ CCCCCCCCCCCCCCCC CCCCCC ?????? ?????? ?????? ?????? ?????? ??? │
│ │               │
│ │               └─ Color Mask (6bit = 7色)                    │
│ └─ Count/Value (16bit)                                       │
└─────────────────────────────────────────────────────────────────┘

a (Attribute):
┌─────────────────────────────────────────────────────────────────┐
│ OD TT GGGG UUUUU CCCCC M TB? ?????? ?????? ?????? ?????? ????? │
│ ││ │ │    │     │     │  │││
│ ││ │ │    │     │     │  ││└─ Not Blade Heart               │
│ ││ │ │    │     │     │  │└── Has Blade Heart               │
│ ││ │ │    │     │     │  └─── Tapped                        │
│ ││ │ │    │     │     └────── Cost Mode (GE/LE)             │
│ ││ │ │    │     └──────────── Cost Threshold (5bit)         │
│ ││ │ │    └────────────────── Unit ID (5bit)                │
│ ││ │ └─────────────────────── Group ID (4bit)               │
│ ││ └───────────────────────── Card Type (2bit)              │
│ │└─────────────────────────── Dynamic Value                  │
│ └──────────────────────────── Optional                       │
└─────────────────────────────────────────────────────────────────┘
```
