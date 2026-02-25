# 新しいアビリティに必要なオペコード調査レポート

## 概要

`cards_old.json` と `cards.json` を比較し、新しく追加された458枚のカードに含まれる新アビリティパターンを調査しました。その結果、現在のオペコード体系では対応できない可能性のある新しいメカニクスを特定しました。

## 調査結果サマリー

### 新しく追加されたカードセット
- **BP05シリーズ**: ブースターパックAnniversary2026
- **新スタートデッキ**: 蓮ノ空女学院スクールアイドルクラブ (HSSD01)、サンシャイン!! (SSD01)
- **新シリーズ**: 蓮ノ空、Liella!、虹ヶ咲の新カード

---

## 新しいオペコードが必要な可能性のあるメカニクス

### 1. 動的な枚数参照 (LOOK_DECK_DYNAMIC)

**アビリティ例:**
```
{{live_success.png|ライブ成功時}}手札を1枚控え室に置いてもよい：
自分のデッキの上から、自分のライブの合計スコアに2を足した数に等しい枚数見る。
その中からカードを1枚手札に加える。残りを控え室に置く。
```

**カード例:**
- PL!-bp5-001-AR (高坂穂乃果)
- PL!-bp5-001-P, PL!-bp5-001-SEC

**必要なオペコード:**
- `LOOK_DECK_DYNAMIC` (値が動的に計算される)
- パラメータ: `value_source: "live_score"`, `modifier: +2`

**現在の対応状況:** 
- `LOOK_DECK` (Opcode 14) は固定枚数のみ対応
- 動的な枚数計算には新しいオペコードまたはパラメータ拡張が必要

---

### 2. 動的エネルギーコスト (PAY_ENERGY_DYNAMIC)

**アビリティ例:**
```
{{kidou.png|起動}}{{turn1.png|ターン1回}}手札を1枚控え室に置く：
自分の控え室にあるライブカードを1枚選び、そのカードのスコアに等しい数の{{icon_energy.png|E}}を支払ってもよい。
そうした場合、そのライブカードを手札に加える。
```

**カード例:**
- PL!N-bp5-003-R (桜坂しずく)
- PL!N-bp5-003-AR, PL!N-bp5-003-P

**必要なオペコード:**
- `PAY_ENERGY_DYNAMIC` または `PAY_ENERGY` の拡張
- パラメータ: `value_source: "selected_card_score"`

**現在の対応状況:**
- `PAY_ENERGY` (Opcode 64) は固定コストのみ対応
- 選択したカードのスコアを参照する動的コストには対応していない

---

### 3. 繰り返し処理 (REPEAT_ABILITY)

**アビリティ例:**
```
{{live_start.png|ライブ開始時}}自分のデッキの一番上のカードを控え室に置いてもよい。
そうした場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る。
これにより控え室に置いたカードがライブカードの場合、このメンバーをウェイトにする。
自分はこの手順をさらに4回まで繰り返してもよい。
```

**カード例:**
- PL!SP-bp5-009-AR (鬼塚夏美)

**必要なオペコード:**
- `REPEAT_ABILITY` または `LOOP` 
- パラメータ: `max_repeats: 4`, `condition: "optional_continue"`

**現在の対応状況:**
- 繰り返し処理に対応するオペコードは存在しない
- 制御フローとして `JUMP` (Opcode 2) と `JUMP_IF_FALSE` (Opcode 3) があるが、ループ構造には対応していない

---

### 4. アクティブフェイズ制約 (SKIP_ACTIVATE_PHASE)

**アビリティ例:**
```
{{jyouji.png|常時}}このメンバーは自分のアクティブフェイズにアクティブにしない。
```

**カード例:**
- PL!N-bp5-006-AR (近江彼方)

**必要なオペコード:**
- `SKIP_ACTIVATE_PHASE` または `RESTRICTION` の拡張
- パラメータ: `phase: "active"`, `action: "skip_activate"`

**現在の対応状況:**
- `RESTRICTION` (Opcode 35) は存在するが、この特定の制約タイプには対応していない
- `PREVENT_ACTIVATE` (Opcode 82) はあるが、フェイズ固有の制約ではない

---

### 5. 余剰ハート消費 (LOSE_EXCESS_HEARTS)

**アビリティ例:**
```
{{live_success.png|ライブ成功時}}自分が余剰ハートを3つ以上持っている場合、
それらをすべて失い、このカードのスコアを＋１する。
```

**カード例:**
- PL!N-bp5-025-L

**必要なオペコード:**
- `LOSE_EXCESS_HEARTS` 
- パラメータ: `min_count: 3`, `lose_all: true`

**現在の対応状況:**
- `HAS_EXCESS_HEART` 条件 (Condition 238) は存在
- 余剰ハートを能動的に消費する効果オペコードは存在しない

---

### 6. スコア減少効果 (REDUCE_SCORE)

**アビリティ例:**
```
{{live_success.png|ライブ成功時}}自分が余剰ハートを持たない場合、ライブの合計スコアを＋１する。
自分が余剰ハートを2つ以上持つ場合、ライブの合計スコアを－１する。
この効果ではライブの合計スコアは０未満にはならない。
```

**カード例:**
- PL!N-bp5-005-AR
- PL!S-bp5-005-AR

**必要なオペコード:**
- `REDUCE_SCORE` (負の値での `BOOST_SCORE` として実装可能)
- パラメータ: `min_value: 0`

**現在の対応状況:**
- `BOOST_SCORE` (Opcode 16) は正の値のみ想定
- 負の値での減少効果には対応していない可能性

---

### 7. エネルギー枚数の正確な条件 (COUNT_ENERGY_EXACT)

**アビリティ例:**
```
{{jyouji.png|常時}}自分のエネルギーがちょうど8枚あるかぎり、ライブの合計スコアを＋１する。
```

**カード例:**
- PL!S-bp5-006-AR
- PL!S-bp5-006-R

**必要な条件:**
- `COUNT_ENERGY_EXACT` 条件
- パラメータ: `exact_count: 8`

**現在の対応状況:**
- `COUNT_ENERGY` (Condition 213) は「以上」または「以下」の比較のみ
- 「ちょうど」の条件には対応していない

---

### 8. メンバーの下にエネルギーを置く (PLACE_ENERGY_UNDER_MEMBER)

**アビリティ例:**
```
{{kidou.png|起動}}{{turn1.png|ターン1回}}エネルギー置き場にあるエネルギー1枚をこのメンバーの下に置く：
カードを1枚引き、ライブ終了時まで、{{heart_01.png|heart01}}を得る。
```

**カード例:**
- PL!S-bp5-001-AR
- PL!S-bp5-001-R

**必要なオペコード:**
- `PLACE_ENERGY_UNDER_MEMBER` または `PLACE_UNDER` の拡張
- パラメータ: `source: "energy_zone"`, `target: "self"`

**現在の対応状況:**
- `PLACE_UNDER` (Opcode 33) は存在
- エネルギーカードをメンバーの下に置く具体的なパターンは確認必要

---

### 9. ブレードハートの種類カウント (COUNT_BLADE_HEART_TYPES)

**アビリティ例:**
```
{{jidou.png|自動}}{{turn1.png|ターン1回}}自分がエールしたとき、
エールにより公開された自分のカードが持つブレードハートの中に
[桃ブレード]、[赤ブレード]、[黄ブレード]、[緑ブレード]、[青ブレード]、[紫ブレード]、
{{icon_b_all.png|ALLブレード}}のうち、3種類以上ある場合、
ライブ終了時まで、{{heart_01.png|heart01}}を得る。
6種類以上ある場合、さらにライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを＋１する。」を得る。
```

**カード例:**
- PL!HS-bp5-007-AR
- PL!HS-bp5-007-R

**必要な条件:**
- `COUNT_BLADE_HEART_TYPES` 条件
- パラメータ: `min_types: 3` または `min_types: 6`

**現在の対応状況:**
- `COUNT_UNIQUE_COLORS` (Condition 250) は存在するが、ブレードハートの種類カウントには対応していない

---

## 既存オペコードで対応可能な新パターン

以下のパターンは既存のオペコードの組み合わせまたはパラメータ拡張で対応可能です：

### 1. スコア合計条件
- `SCORE_COMPARE` (Condition 220) で対応可能
- 「成功ライブカード置き場にあるカードのスコアの合計が６以上」などの条件

### 2. 余剰ハート条件
- `HAS_EXCESS_HEART` (Condition 238) と `NOT_HAS_EXCESS_HEART` (Condition 239) で対応可能

### 3. 相手の余剰ハート条件
- 新しい条件 `OPPONENT_HAS_EXCESS_HEART` が必要になる可能性

---

## 推奨される実装優先順位

### 高優先度
1. **LOOK_DECK_DYNAMIC** - 複数の新カードで使用
2. **PAY_ENERGY_DYNAMIC** - 新しいコスト支払いメカニクス
3. **REDUCE_SCORE** - スコア減少効果

### 中優先度
4. **REPEAT_ABILITY** - 複雑なループ処理
5. **LOSE_EXCESS_HEARTS** - 余剰ハート消費メカニクス
6. **COUNT_ENERGY_EXACT** - 正確な枚数条件

### 低優先度
7. **SKIP_ACTIVATE_PHASE** - 特定カードのみ使用
8. **COUNT_BLADE_HEART_TYPES** - 特定カードのみ使用

---

## 実装状況

### 追加済みオペコード (OPCODES)

| オペコード名 | 値 | 説明 |
|-------------|-----|------|
| `LOOK_DECK_DYNAMIC` | 91 | ライブスコアに基づく動的な枚数参照 |
| `REDUCE_SCORE` | 92 | スコア減少効果 |
| `REPEAT_ABILITY` | 93 | 手順の繰り返し処理 |
| `LOSE_EXCESS_HEARTS` | 94 | 余剰ハート消費 |
| `SKIP_ACTIVATE_PHASE` | 95 | アクティブフェイズ制約 |
| `PAY_ENERGY_DYNAMIC` | 96 | 選択カードのスコアに基づく動的エネルギーコスト |
| `PLACE_ENERGY_UNDER_MEMBER` | 97 | メンバーの下にエネルギーを置く |

### 追加済み条件 (CONDITIONS)

| 条件名 | 値 | 説明 |
|--------|-----|------|
| `COUNT_ENERGY_EXACT` | 301 | エネルギーがちょうどN枚 |
| `COUNT_BLADE_HEART_TYPES` | 302 | ブレードハートの種類カウント |
| `OPPONENT_HAS_EXCESS_HEART` | 303 | 相手の余剰ハート条件 |
| `SCORE_TOTAL_CHECK` | 304 | 成功ライブカード置き場のスコア合計条件 |

### 現在の使用状況

- **OPCODES**: 最大97 (制限256に対して余裕あり)
- **CONDITIONS**: 
  - 元の範囲: 200-249
  - 新しい範囲: 300-399 (将来的な拡張用に予約)
  - 現在使用: 301-304

### 更新したファイル

1. `engine/models/generated_metadata.py` - オペコードと条件の定義を追加
2. `compiler/main.py` - 有効なオペコードリストを更新
3. `compiler/patterns/effects.py` - 新しい効果パターンを追加
4. `compiler/patterns/conditions.py` - 新しい条件パターンを追加

---

## 次のステップ

1. ~~**オペコード定義の更新**: `engine/models/generated_metadata.py` に新しいオペコードを追加~~ ✅ 完了
2. ~~**コンパイラパターンの更新**: `compiler/patterns/effects.py` に新しいパターンを追加~~ ✅ 完了
3. **エンジン実装**: Rustエンジン側でのオペコード処理を実装
4. **テストケースの作成**: 新しいアビリティを持つカードのテストを作成

---

## 参照ファイル

- カードデータ: `data/cards.json`, `data/cards_old.json`
- 新カード情報: `data/new_cards_info.json`
- オペコード定義: `engine/models/generated_metadata.py`
- コンパイラパターン: `compiler/patterns/effects.py`
