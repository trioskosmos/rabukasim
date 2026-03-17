# PL!SP-bp1-026-L アビリティ発動問題 分析レポート

## 問題概要

カード「未来予報ハendelujah!」(PL!SP-bp1-026-L) のアビリティが発動しない問題を調査した。

## カード情報

- **カードID**: 519
- **カード名**: 未来予報ハendelujah!
- **日本語テキスト**:
  > ライブ開始時、自分の、ステージと控え室に名前の異なる『Liella!』のメンバーが5人以上いる場合、このカードを使用するためのコストはheart02×2, heart03×2, heart06×2になる。
  > (必要ハートを確認する時、エールで出たALLブレードは任意の色のハートとして扱う。)

## Manual Pseudocode

```pseudocode
TRIGGER: ON_LIVE_START
CONDITION: COUNT_CARDS(ZONE="STAGE_OR_DISCARD", FILTER="GROUP_ID=3, UNIQUE_NAMES", GE=5)
EFFECT: SET_HEART_REQ([2,2,3,3,6,6]) -> SELF
```

## 実際のバイトコード

```
[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]
```

**デコード結果**:
- `00: META_RULE | v=1, a=0, s=4`
- `05: RETURN | v=0, a=0, s=0`

## 問題の根本原因

### 1. バイトコードに条件チェックが含まれていない

Manual Pseudocodeには「ステージと控え室に名前の異なるLiella!メンバーが5人以上」という条件がありますが、実際のバイトコードにはこの条件チェックが含まれていません。

現在の `META_RULE` ハンドラー (`engine_rust_src/src/core/logic/interpreter/handlers/meta_control.rs:91-93`) は:
```rust
O_META_RULE => {
    if a == 0 { state.core.players[p_idx].cheer_mod_count = state.core.players[p_idx].cheer_mod_count.saturating_add(v as u16); }
},
```
これは `cheer_mod_count` を1増やすだけであり、条件チェックやハートコスト変更は行いません。

### 2. パーサーの制限

Manual Pseudocodeで記述されている形式:
- `COUNT_CARDS(ZONE="STAGE_OR_DISCARD", FILTER="GROUP_ID=3, UNIQUE_NAMES", GE=5)`
- `SET_HEART_REQ([2,2,3,3,6,6])`

これらの形式は現在のコンパイラで1. `COUNT_CARDS` が `CONDITION_AL正しく解析できません:
IASES` に未定義 → `ConditionType.NONE` として扱われる
2. `SET_HEART_REQ` が `EFFECT_ALIASES` に未定義 → `EffectType.META_RULE` として扱われる
3. 配列形式 `[2,2,3,3,6,6]` のパースが正しく行われない

## 修正オプション

### オプションA: コンパイラー拡張 (推奨)

**Pros**:
- 他の同様のカードにも適用可能
- メンテナンス性が高い

**Cons**:
- 実装に時間がかかる

**実装内容**:
1. `compiler/parser_v2.py` に以下を追加:
   - `COUNT_CARDS` → `GROUP_FILTER` へのマッピング
   - `SET_HEART_REQ` → `SET_HEART_COST` へのマッピング
   - 配列形式 `[2,2,3,3,6,6]` の特別処理
   - 複数ゾーン(STAGE_OR_DISCARD)対応

2. エンジン側に新しい条件タイプを追加 (必要な場合):
   - `ConditionType.COUNT_UNIQUE_NAMES`

3. エンジン側に新しい効果タイプを追加 (必要な場合):
   - `EffectType.SET_HEART_REQ`

### オプションB: 直接バイトコード生成 (シンプル)

**Pros**:
- 빠르게 구현 가능
- 即座に動作

**Cons**:
- 他のカードに適用困難

**実装内容**:
- `manual_pseudocode.json` のエントリを直接バイトコードに変換
- ただし、条件チェックのバイトコード生成は複雑

### オプションC: META_RULE で一元化 (暫定)

**Pros**:
- 既存の META_RULE インフラストラクチャを活用

**Cons**:
- 機能が限定的

**実装内容**:
- この能力を実装済みの他のカードと同じパターンに従う
- ただし、現在の META_RULE は条件チェックをサポートしていない

## 推奨アプローチ

**オプションA + エンジン拡張** を推奨します。

しかし、このカードの能力は**非常に特殊的**です:
1. 複数ゾーン(ステージ+控え室)でのカードカウント
2. メンバー名の重複排除(UNIQUE_NAMES)
3. グループフィルタリング(GROUP_ID=3 = Liella!)

現在のエンジンには、これらの機能を完全にサポートするopcodeが存在しません。

## 実装タスク

### タスク1: パーサー修正 (Code Mode)

- [ ] `compiler/parser_v2.py` の `CONDITION_ALIASES` に `COUNT_CARDS` 追加
- [ ] `compiler/parser_v2.py` の `EFFECT_ALIASES` に `SET_HEART_REQ` 追加
- [ ] 配列形式 `[2,2,3,3,6,6]` のパース処理追加

### タスク2: エンジン拡張 (Code Mode)

- [ ] `engine/models/ability.py` に `ConditionType.COUNT_UNIQUE_NAMES` 追加 (必要な場合)
- [ ] 対応するRust側ハンドラー実装
- [ ] `SET_HEART_REQ` 効果タイプのハンドラー実装

### タスク3: テスト (Code Mode)

- [ ] カード519のバイトコード再生成
- [ ] ユニットテスト作成
- [ ] 統合テストで確認

## リスクと考慮事項

1. **複雑さ**: このカードの能力は、現在サポートされていないいくつかの機能を必要とする
2. **優先度**: 他のカードや機能開発とのバランス
3. **後方互換性**: 既存のパーサーやエンジンへの影響

## 結論

この問題は、**パーサーの制限**と**エンジンの機能不足**の両方が原因です。

完全な修正には時間がかかりますが、まずパーサー側の基本的なマッピングを追加し、エンジンに新しいハンドルを実装することで対応可能です。

現在のバイトコード `[29, 1, 0, 0, 4, 1, 0, 0, 0, 0]` は条件チェックを省略しているため、能力が発動しません。
