# オペコード実装監査レポート

## 概要

`data/metadata.json`で定義されたオペコード、条件、コストがRustエンジンで正しく実装されているかを監査しました。

## 1. 定義の同期状況

### ✅ 正常に同期されている項目

| カテゴリ | metadata.json | generated_constants.rs | 状態 |
|---------|---------------|------------------------|------|
| Opcodes | 62個 | 62個 | ✅ 完全一致 |
| Conditions | 50個 | 50個 | ✅ 完全一致 |
| Costs | 101個 | 101個 | ✅ 完全一致 |
| Triggers | 11個 | enums.rs | ✅ 完全一致 |
| Targets | 14個 | enums.rs | ✅ 完全一致 |
| Extra Constants | 22個 | 22個 | ✅ 完全一致 |

`generated_constants.rs`は`tools/sync_metadata.py`によって自動生成されており、`metadata.json`との同期は正しく維持されています。

---

## 2. オペコード実装状況

### ✅ 実装済みオペコード (56個)

#### 制御フロー (mod.rs)
| オペコード | 値 | 実装場所 |
|-----------|-----|---------|
| O_NOP | 0 | mod.rs:124 |
| O_RETURN | 1 | mod.rs:132 |
| O_JUMP | 2 | mod.rs:176 |
| O_JUMP_IF_FALSE | 3 | mod.rs:181 |
| O_SELECT_MODE | 30 | mod.rs:84-113 |

#### ドロー/ハンド (draw_hand.rs)
| オペコード | 値 | 実装状況 |
|-----------|-----|---------|
| O_DRAW | 10 | ✅ |
| O_DRAW_UNTIL | 66 | ✅ |
| O_ADD_TO_HAND | 44 | ✅ |

#### スコア/ハート (score_hearts.rs)
| オペコード | 値 | 実装状況 |
|-----------|-----|---------|
| O_ADD_BLADES | 11 | ✅ |
| O_ADD_HEARTS | 12 | ✅ |
| O_REDUCE_COST | 13 | ✅ |
| O_BOOST_SCORE | 16 | ✅ |
| O_BUFF_POWER | 18 | ✅ |
| O_SET_BLADES | 24 | ✅ |
| O_SET_HEARTS | 25 | ✅ |
| O_SET_SCORE | 37 | ✅ |
| O_TRANSFORM_COLOR | 39 | ✅ |
| O_REDUCE_HEART_REQ | 48 | ✅ |
| O_TRANSFORM_HEART | 73 | ✅ |
| O_INCREASE_HEART_COST | 61 | ✅ |

#### メンバー状態 (member_state.rs)
| オペコード | 値 | 実装状況 |
|-----------|-----|---------|
| O_ACTIVATE_MEMBER | 43 | ✅ |
| O_SET_TAPPED | 51 | ✅ |
| O_TAP_MEMBER | 53 | ✅ |
| O_TAP_OPPONENT | 32 | ✅ |
| O_MOVE_MEMBER | 20 | ✅ |
| O_FORMATION_CHANGE | 26 | ✅ (UNUSEDマーク付きだが実装済み) |
| O_PLACE_UNDER | 33 | ✅ |
| O_ADD_STAGE_ENERGY | 50 | ✅ |
| O_GRANT_ABILITY | 60 | ✅ |
| O_PLAY_MEMBER_FROM_HAND | 57 | ✅ |
| O_INCREASE_COST | 70 | ✅ |

#### エネルギー (energy.rs)
| オペコード | 値 | 実装状況 |
|-----------|-----|---------|
| O_ENERGY_CHARGE | 23 | ✅ |
| O_PAY_ENERGY | 64 | ✅ |
| O_ACTIVATE_ENERGY | 81 | ✅ |

#### デッキ/ゾーン (deck_zones.rs)
| オペコード | 値 | 実装状況 |
|-----------|-----|---------|
| O_LOOK_DECK | 14 | ✅ |
| O_RECOVER_LIVE | 15 | ✅ |
| O_RECOVER_MEMBER | 17 | ✅ |
| O_SWAP_CARDS | 21 | ✅ |
| O_SEARCH_DECK | 22 | ✅ (UNUSEDマーク付きだが実装済み) |
| O_ORDER_DECK | 28 | ✅ |
| O_MOVE_TO_DECK | 31 | ✅ |
| O_REVEAL_CARDS | 40 | ✅ |
| O_LOOK_AND_CHOOSE | 41 | ✅ |
| O_CHEER_REVEAL | 42 | ✅ |
| O_MOVE_TO_DISCARD | 58 | ✅ |
| O_REVEAL_UNTIL | 69 | ✅ |
| O_SWAP_ZONE | 38 | ✅ (UNUSEDマーク付きだが実装済み) |

#### メタ制御 (meta_control.rs)
| オペコード | 値 | 実装状況 |
|-----------|-----|---------|
| O_NEGATE_EFFECT | 27 | ✅ |
| O_META_RULE | 29 | ✅ |
| O_BATON_TOUCH_MOD | 36 | ✅ |
| O_IMMUNITY | 19 | ✅ |
| O_RESTRICTION | 35 | ✅ |
| O_REDUCE_YELL_COUNT | 62 | ✅ |
| O_SELECT_MEMBER | 65 | ✅ |
| O_SELECT_PLAYER | 67 | ✅ |
| O_SELECT_LIVE | 68 | ✅ |
| O_COLOR_SELECT | 45 | ✅ |
| O_OPPONENT_CHOOSE | 75 | ✅ |
| O_TRIGGER_REMOTE | 47 | ✅ |
| O_REDUCE_LIVE_SET_LIMIT | 77 | ✅ |
| O_PREVENT_PLAY_TO_SLOT | 71 | ✅ |
| O_PREVENT_ACTIVATE | 82 | ✅ |
| O_PREVENT_BATON_TOUCH | 90 | ✅ |
| O_PREVENT_SET_TO_SUCCESS_PILE | 80 | ✅ |
| O_SWAP_AREA | 72 | ✅ |

---

### ⚠️ レガシー実装のみ（新ハンドラーに未移行）(3個)

以下のオペコードは`interpreter_legacy.rs`に実装がありますが、新しいハンドラーシステム(`handlers/`)には移行されていません：

| オペコード | 値 | 実装場所 | 説明 |
|-----------|-----|---------|------|
| **O_PLAY_MEMBER_FROM_DISCARD** | 63 | interpreter_legacy.rs:1582 | 捨て札からメンバーをプレイ |
| **O_PLAY_LIVE_FROM_DISCARD** | 76 | interpreter_legacy.rs:1582 | 捨て札からライブをプレイ |
| **O_SELECT_CARDS** | 74 | interpreter_legacy.rs:1719 | カード選択処理 |

#### 使用しているカード

**O_PLAY_MEMBER_FROM_DISCARD (63) を使用するカード:**
- カードID 103: `PL!-pb1-018-P＋` (矢澤にこ)
- カードID 163: `PL!HS-PR-022-PR`
- カードID 4263: `PL!HS-bp1-002-R`
- 他多数（`data/cards_compiled.json`で`"effect_type": 63`を検索）

**O_PLAY_LIVE_FROM_DISCARD (76) を使用するカード:**
- カードID 205: `PL!HS-bp2-018-N` (安養寺 姫芽)
- 他多数

**O_SELECT_CARDS (74) を使用するカード:**
- カードID 537: `PL!SP-bp2-011-P` (鬼塚冬毬)
- 効果: `SELECT_CARDS(2) {FROM="DISCARD", TYPE_LIVE, UNIQUE_NAMES} -> OPTIONS; OPPONENT_CHOOSE(OPTIONS) -> TARGET; ADD_TO_HAND(TARGET)`

---

### ⚪ UNUSEDマーク付き (実装なし、問題なし)

| オペコード | 値 | 状態 |
|-----------|-----|------|
| O_FLAVOR | 34 | 未実装 (意図的) |
| O_REPLACE_EFFECT | 46 | 未実装 (意図的) |
| O_ADD_CONTINUOUS | 52 | 未実装 (意図的) |
| O_SET_HEART_COST | 83 | 未実装 (意図的) |

---

## 3. 条件(Conditions)実装状況

### ✅ 実装済み (45個)

`conditions.rs`で実装済み:
- C_TURN_1, C_HAS_MEMBER, C_HAS_COLOR, C_COUNT_STAGE, C_COUNT_HAND, C_COUNT_DISCARD
- C_IS_CENTER, C_COUNT_GROUP, C_GROUP_FILTER, C_MODAL_ANSWER, C_COUNT_ENERGY
- C_HAS_LIVE_CARD, C_COST_CHECK, C_RARITY_CHECK, C_COUNT_SUCCESS_LIVE
- C_OPPONENT_HAND_DIFF, C_SCORE_COMPARE, C_COUNT_HEARTS, C_COUNT_BLADES
- C_OPPONENT_ENERGY_DIFF, C_HAS_KEYWORD, C_DECK_REFRESHED, C_BATON
- C_TYPE_CHECK, C_AREA_CHECK, C_COST_LEAD, C_SCORE_LEAD, C_HEART_LEAD
- C_HAS_EXCESS_HEART, C_NOT_HAS_EXCESS_HEART, C_TOTAL_BLADES
- C_COST_COMPARE, C_BLADE_COMPARE, C_HEART_COMPARE, C_OPPONENT_HAS_WAIT
- 他

### ❌ 未実装条件 (5個)

以下の条件は`generated_constants.rs`と`logging.rs`に定義がありますが、`conditions.rs`の`check_condition_opcode`関数に実装がありません：

| 条件 | 値 | 説明 | ログ出力のみ |
|------|-----|------|-------------|
| **C_IS_TAPPED** | 245 | タップ状態チェック | ✅ logging.rs:78 |
| **C_IS_ACTIVE** | 246 | アクティブ状態チェック | ✅ logging.rs:79 |
| **C_LIVE_PERFORMED** | 247 | ライブ実行済みチェック | ✅ logging.rs:80 |
| **C_IS_PLAYER** | 248 | プレイヤー判定 | ✅ logging.rs:81 |
| **C_IS_OPPONENT** | 249 | 対戦相手判定 | ✅ logging.rs:82 |

これらの条件は`conditions.rs`のmatch文でデフォルトケース(`_ => false`)にフォールスルーし、常に`false`を返します。

---

## 4. コスト(Costs)実装状況

### ✅ 実装済み

`costs.rs`で主要なコストタイプは実装済み:
- COST_ENERGY, COST_TAP_SELF, COST_DISCARD_HAND, COST_RETURN_HAND
- COST_SACRIFICE_SELF, COST_REVEAL_HAND, COST_SACRIFICE_UNDER
- COST_DISCARD_ENERGY, COST_TAP_MEMBER, COST_TAP_ENERGY
- COST_RETURN_MEMBER_TO_DECK, COST_RETURN_DISCARD_TO_DECK
- 他多数

---

## 5. 発見された問題点

### 🔴 重要な問題

1. **未実装オペコードが存在**
   - `O_PLAY_MEMBER_FROM_DISCARD (63)` - 一部カードで使用される可能性
   - `O_PLAY_LIVE_FROM_DISCARD (76)` - 一部カードで使用される可能性
   - これらは`interpreter_legacy.rs`には実装があるが、新しいハンドラー構造には移行されていない

2. **未実装条件が存在**
   - `C_IS_TAPPED`, `C_IS_ACTIVE`, `C_LIVE_PERFORMED`, `C_IS_PLAYER`, `C_IS_OPPONENT`
   - これらは条件チェック(200-255)の範囲で、`conditions.rs`のmatch文でデフォルト`false`を返す

### 🟡 中程度の問題

3. **UNUSEDマークの不一致**
   - `O_SEARCH_DECK`, `O_FORMATION_CHANGE`, `O_SWAP_ZONE`は`[UNUSED]`マークがあるが実際は実装済み
   - metadata.jsonの`unused`リストと実装状況が一致していない

4. **重複実装**
   - `O_REDUCE_YELL_COUNT`が`meta_control.rs`と`score_hearts.rs`の両方で処理されている

---

## 6. 推奨アクション

### 即時対応が必要

1. **未実装オペコードの追加**
   ```rust
   // member_state.rs または deck_zones.rs に追加
   O_PLAY_MEMBER_FROM_DISCARD => { /* 実装 */ }
   O_PLAY_LIVE_FROM_DISCARD => { /* 実装 */ }
   O_SELECT_CARDS => { /* 実装 */ }
   ```

2. **未実装条件の追加**
   ```rust
   // conditions.rs に追加
   C_IS_TAPPED => player.is_tapped(ctx.area_idx as usize),
   C_IS_ACTIVE => !player.is_tapped(ctx.area_idx as usize),
   C_LIVE_PERFORMED => player.live_performed_this_turn,
   C_IS_PLAYER => ctx.player_id == state.current_player as u8,
   C_IS_OPPONENT => ctx.player_id != state.current_player as u8,
   ```

### 整理対応

3. **metadata.jsonの`unused`リスト更新**
   - 実装済みの`O_SEARCH_DECK`, `O_FORMATION_CHANGE`, `O_SWAP_ZONE`を削除

4. **重複実装の解消**
   - `O_REDUCE_YELL_COUNT`を一箇所に集約

---

## 7. アーキテクチャ評価

### ✅ 良い点

- ハンドラーが機能別に適切に分割されている
- `generated_constants.rs`の自動生成により同期が保たれている
- `HandlerResult`による一貫したフロー制御
- 条件チェックとオペコード実行の分離

### 改善推奨

- コンパイル時のオペコード網羅チェックの追加
- 未実装オペコードのログ出力または警告

---

## 結論

**実装状況:**
- **オペコード**: 59/62個が新ハンドラーで実装済み、3個はレガシー実装のみ
- **条件**: 45/50個が実装済み、5個は未実装（常にfalseを返す）

**重要な発見:**
1. 3つのオペコードは`interpreter_legacy.rs`に実装があるため、レガシーパスを使用すれば動作します
2. しかし、新しいハンドラーシステムへの移行が不完全です
3. 5つの条件は定義されているものの、実際には機能せず常にfalseを返します

**推奨アクション:**
1. レガシー実装を新ハンドラーに移行（`deck_zones.rs`または`member_state.rs`に追加）
2. 未実装条件を`conditions.rs`に追加
