# Cost/Color ビット競合修正計画

## 問題の概要

64bit `a` ワード内で、Cost Filter と Color Filter が同じビット領域 (bits 24-30) を使用しており、両方が同時に設定されるとデータが破損します。

## 現在のビットレイアウト

```
Bit 24:     Cost Enable / Color Mask bit 0  ← 競合!
Bit 25-29:  Cost Threshold / Color Mask bits 1-5  ← 競合!
Bit 30:     Cost LE Mode / Color Mask bit 6  ← 競合!
Bit 31:     Color Enable
```

### 現在の定数値

```json
// metadata.json より
"FILTER_COLOR_ENABLE": 2147483648,   // 0x80000000 = bit 31
"FILTER_COLOR_SHIFT": 24,             // bits 24-30
"FILTER_COST_ENABLE": 16777216,       // 0x01000000 = bit 24
"FILTER_COST_SHIFT": 25,              // bits 25-29
"FILTER_COST_LE": 1073741824          // 0x40000000 = bit 30
```

## 64ビット全体の使用状況

```
Bit 0-1:    未使用
Bit 2-3:    Card Type
Bit 4:      Group Enable
Bit 5-11:   Group ID (7bit)
Bit 12:     Tapped Filter
Bit 13:     Has Blade Heart
Bit 14:     Not Blade Heart
Bit 15:     Unique Names
Bit 16:     Unit Enable
Bit 17-23:  Unit ID (7bit)
Bit 24:     Cost Enable
Bit 25-29:  Cost Threshold (5bit)
Bit 30:     Cost LE Mode
Bit 31:     Color Enable (現在)
Bit 32-38:  Character ID 1 (7bit)
Bit 39-41:  未使用
Bit 42:     Character Enable
Bit 43-49:  Character ID 2 (7bit)
Bit 50-56:  Character ID 3 (7bit)
Bit 57-59:  Special ID (3bit)
Bit 60-63:  未使用 (4bit)
```

## 修正案: Color Filter を bits 60-63 に移動

Color Filter を最上位の未使用領域 (bits 60-63) に移動し、Cost Filter との競合を解消します。

### 新しいビットレイアウト

```
=== Cost Filter (変更なし) ===
Bit 24:     Cost Enable
Bit 25-29:  Cost Threshold (0-31)
Bit 30:     Cost LE Mode (0=GE, 1=LE)

=== Color Filter (移動) ===
Bit 60:     Color Enable (新規)
Bit 61-63:  Color Mask (3bit = 8色、現在7色で十分)
```

### 新しい定数値

```json
{
    "FILTER_COLOR_ENABLE": 1152921504606846976,  // 0x1000000000000000 = bit 60
    "FILTER_COLOR_SHIFT": 61,                     // bits 61-63
    "FILTER_COLOR_MASK": 7                        // 0x07 (3bit mask)
}
```

### 重複チェック

| 領域 | Cost | Color | 重複 |
|------|------|-------|------|
| Bit 24 | Enable | - | なし |
| Bit 25-29 | Threshold | - | なし |
| Bit 30 | LE Mode | - | なし |
| Bit 60 | - | Enable | なし |
| Bit 61-63 | - | Mask | なし |

**確認: 重複なし**

## 修正が必要なファイル

### 1. `data/metadata.json`

```diff
- "FILTER_COLOR_ENABLE": 2147483648,
- "FILTER_COLOR_SHIFT": 24,
+ "FILTER_COLOR_ENABLE": 1152921504606846976,
+ "FILTER_COLOR_SHIFT": 61,
```

### 2. `engine_rust_src/src/core/generated_constants.rs`

sync_metadata.py により自動生成されるが、念のため確認:

```rust
pub const FILTER_COLOR_ENABLE: u64 = 0x1000000000000000; // bit 60
pub const FILTER_COLOR_SHIFT: usize = 61;
```

### 3. `engine_rust_src/src/core/logic/filter.rs`

```diff
// Color mask (bits 61-66, enabled by bit 60)
- if (filter_attr & FILTER_COLOR_ENABLE as u64) != 0 {
-     filter.color_mask = ((filter_attr >> FILTER_COLOR_SHIFT) & 0x7F) as u8;
- }
+ if (filter_attr & FILTER_COLOR_ENABLE) != 0 {
+     filter.color_mask = ((filter_attr >> FILTER_COLOR_SHIFT) & 0x7F) as u8;
+ }
```

```diff
// to_attr()
- if self.color_mask != 0 {
-     attr |= FILTER_COLOR_ENABLE as u64;
-     attr |= (self.color_mask as u64) << FILTER_COLOR_SHIFT;
- }
+ if self.color_mask != 0 {
+     attr |= FILTER_COLOR_ENABLE;
+     attr |= (self.color_mask as u64) << FILTER_COLOR_SHIFT;
+ }
```

### 4. `engine/models/ability.py`

```diff
# Color Filter (Bits 61-66, Enabled by Bit 60)
- attr |= (color_mask & 0x7F) << 24
- attr |= 1 << 31  # Enable bit
+ attr |= (color_mask & 0x7F) << 61
+ attr |= 1 << 60  # Enable bit (bit 60)
```

## テスト計画

### 1. ユニットテスト

```rust
#[test]
fn test_cost_and_color_no_collision() {
    let mut filter = CardFilter::default();
    filter.cost_filter = Some((5, false)); // Cost GE 5
    filter.color_mask = 0x03; // SMILE + PURE

    let attr = filter.to_attr();
    let parsed = CardFilter::from_attr(attr);

    assert_eq!(filter.cost_filter, parsed.cost_filter);
    assert_eq!(filter.color_mask, parsed.color_mask);
}
```

### 2. 回帰テスト

既存のテストがすべてパスすることを確認:
- `cargo test` (Rust)
- `pytest` (Python)

## 影響範囲

### 影響を受ける機能

1. **カードフィルタリング** - Color Filter を使用するすべての処理
2. **Look and Choose** - 色でフィルタリングする選択肢
3. **Select Member** - 色条件付きメンバー選択

### 影響を受けない機能

1. **Cost Filter** - ビット位置が変更なし
2. **Group/Unit Filter** - 関連なし
3. **Character Filter** - 関連なし

## 実装順序

1. **metadata.json を更新**
2. **sync_metadata.py を実行** → generated_constants.rs 更新
3. **filter.rs のロジックを確認** (定数は自動更新されるが、キャスト等を確認)
4. **ability.py を手動更新**
5. **テスト実行**
6. **必要に応じてデバッグ**

## リスク評価

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| 既存カードの色フィルターが動作しない | 高 | 高 | 全カードのテスト実行 |
| GPU シェーダーでのビット演算エラー | 中 | 高 | WGSL 側の定数も更新 |
| Python-Rust 間のパリティ崩れ | 中 | 高 | パリティテスト実行 |

## 将来の拡張性

この修正により、以下のビットが利用可能になります:

- **Bits 39-41**: レアリティフィルター (3bit)
- **Bits 0-1**: 将来の拡張用 (2bit)
- **Bit 67**: Color Filter 拡張用 (1bit)

## 結論

Color Filter を bits 60-66 に移動することで、Cost Filter との競合を完全に解消できます。これは 5x32 フォーマットの利点を最大限に活かす修正であり、将来の拡張性も確保されます。
