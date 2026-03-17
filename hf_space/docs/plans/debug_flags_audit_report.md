# Debug Flags Content Audit Report

## 概要
`id="debug-flags-content"` で表示されている flags と conditions を、[`data/metadata.json`](data/metadata.json) とバックエンドの Rust 構造体と比較して、欠けているフィールドを特定しました。

---

## data/metadata.json で定義されている Enums

### 1. Conditions (条件チェック) - 55種類
| Condition | Value | フロントエンド表示状態 |
|-----------|-------|----------------------|
| TURN_1 | 200 | ❌ 未表示 |
| HAS_MEMBER | 201 | ❌ 未表示 |
| HAS_COLOR | 202 | ❌ 未表示 |
| COUNT_STAGE | 203 | ❌ 未表示 |
| COUNT_HAND | 204 | ❌ 未表示 |
| COUNT_DISCARD | 205 | ❌ 未表示 |
| IS_CENTER | 206 | ❌ 未表示 |
| LIFE_LEAD | 207 | ❌ 未表示 |
| COUNT_GROUP | 208 | ❌ 未表示 |
| GROUP_FILTER | 209 | ❌ 未表示 |
| OPPONENT_HAS | 210 | ❌ 未表示 |
| SELF_IS_GROUP | 211 | ❌ 未表示 |
| MODAL_ANSWER | 212 | ❌ 未表示 |
| COUNT_ENERGY | 213 | ❌ 未表示 |
| HAS_LIVE_CARD | 214 | ❌ 未表示 |
| COST_CHECK | 215 | ❌ 未表示 |
| RARITY_CHECK | 216 | ❌ 未表示 |
| HAND_HAS_NO_LIVE | 217 | ❌ 未表示 |
| COUNT_SUCCESS_LIVE | 218 | ❌ 未表示 |
| OPPONENT_HAND_DIFF | 219 | ❌ 未表示 |
| SCORE_COMPARE | 220 | ❌ 未表示 |
| HAS_CHOICE | 221 | ❌ 未表示 |
| OPPONENT_CHOICE | 222 | ❌ 未表示 |
| COUNT_HEARTS | 223 | ❌ 未表示 |
| COUNT_BLADES | 224 | ❌ 未表示 |
| OPPONENT_ENERGY_DIFF | 225 | ❌ 未表示 |
| HAS_KEYWORD | 226 | ❌ 未表示 |
| DECK_REFRESHED | 227 | ❌ 未表示 |
| HAS_MOVED | 228 | ❌ 未表示 |
| HAND_INCREASED | 229 | ❌ 未表示 |
| COUNT_LIVE_ZONE | 230 | ❌ 未表示 |
| BATON | 231 | ❌ 未表示 |
| TYPE_CHECK | 232 | ❌ 未表示 |
| IS_IN_DISCARD | 233 | ❌ 未表示 |
| AREA_CHECK | 234 | ❌ 未表示 |
| COST_LEAD | 235 | ❌ 未表示 |
| SCORE_LEAD | 236 | ❌ 未表示 |
| HEART_LEAD | 237 | ❌ 未表示 |
| HAS_EXCESS_HEART | 238 | ❌ 未表示 |
| NOT_HAS_EXCESS_HEART | 239 | ❌ 未表示 |
| TOTAL_BLADES | 240 | ❌ 未表示 |
| COST_COMPARE | 241 | ❌ 未表示 |
| BLADE_COMPARE | 242 | ❌ 未表示 |
| HEART_COMPARE | 243 | ❌ 未表示 |
| OPPONENT_HAS_WAIT | 244 | ❌ 未表示 |
| IS_TAPPED | 245 | ❌ 未表示 |
| IS_ACTIVE | 246 | ❌ 未表示 |
| LIVE_PERFORMED | 247 | ❌ 未表示 |
| IS_PLAYER | 248 | ❌ 未表示 |
| IS_OPPONENT | 249 | ❌ 未表示 |
| COUNT_UNIQUE_COLORS | 250 | ❌ 未表示 |
| COUNT_ENERGY_EXACT | 301 | ❌ 未表示 |
| COUNT_BLADE_HEART_TYPES | 302 | ❌ 未表示 |
| OPPONENT_HAS_EXCESS_HEART | 303 | ❌ 未表示 |
| SCORE_TOTAL_CHECK | 304 | ❌ 未表示 |
| MAIN_PHASE | 305 | ❌ 未表示 |
| SELECT_MEMBER | 306 | ❌ 未表示 |
| SUCCESS_PILE_COUNT | 307 | ❌ 未表示 |
| IS_SELF_MOVE | 308 | ❌ 未表示 |
| DISCARDED_CARDS | 309 | ❌ 未表示 |
| YELL_REVEALED_UNIQUE_COLORS | 310 | ❌ 未表示 |
| SYNC_COST | 311 | ❌ 未表示 |
| SUM_VALUE | 312 | ❌ 未表示 |
| IS_WAIT | 313 | ❌ 未表示 |

**結論**: metadata.json で定義されている 55種類の conditions は、**すべて未表示**です。

---

### 2. Extra Constants (Flags) - 70+ 種類

#### Ability Flags (効果タイプフラグ)
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| FLAG_DRAW | 1 | ❌ 未表示 |
| FLAG_SEARCH | 2 | ❌ 未表示 |
| FLAG_RECOVER | 4 | ❌ 未表示 |
| FLAG_BUFF | 8 | ❌ 未表示 |
| FLAG_CHARGE | 16 | ❌ 未表示 |
| FLAG_TEMPO | 32 | ❌ 未表示 |
| FLAG_REDUCE | 64 | ❌ 未表示 |
| FLAG_BOOST | 128 | ❌ 未表示 |
| FLAG_TRANSFORM | 256 | ❌ 未表示 |
| FLAG_WIN_COND | 512 | ❌ 未表示 |
| FLAG_MOVE | 1024 | ❌ 未表示 |
| FLAG_TAP | 2048 | ❌ 未表示 |

#### Cost Flags
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| COST_FLAG_DISCARD | 1 | ❌ 未表示 |
| COST_FLAG_TAP | 2 | ❌ 未表示 |

#### Choice Flags
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| CHOICE_FLAG_LOOK | 1 | ❌ 未表示 |
| CHOICE_FLAG_DISCARD | 2 | ❌ 未表示 |
| CHOICE_FLAG_MODE | 4 | ❌ 未表示 |
| CHOICE_FLAG_COLOR | 8 | ❌ 未表示 |
| CHOICE_FLAG_ORDER | 16 | ❌ 未表示 |

#### Synergy Flags
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| SYN_FLAG_GROUP | 1 | ❌ 未表示 |
| SYN_FLAG_COLOR | 2 | ❌ 未表示 |
| SYN_FLAG_BATON | 4 | ❌ 未表示 |
| SYN_FLAG_CENTER | 8 | ❌ 未表示 |
| SYN_FLAG_LIFE_LEAD | 16 | ❌ 未表示 |

#### Filter Flags (一部抜粋)
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| FILTER_TYPE_MEMBER | 4 | ❌ 未表示 |
| FILTER_TYPE_LIVE | 8 | ❌ 未表示 |
| FILTER_GROUP_ENABLE | 16 | ❌ 未表示 |
| FILTER_TAPPED | 4096 | ❌ 未表示 |
| FILTER_HAS_BLADE_HEART | 8192 | ❌ 未表示 |
| FILTER_NOT_HAS_BLADE_HEART | 16384 | ❌ 未表示 |
| FILTER_UNIQUE_NAMES | 32768 | ❌ 未表示 |
| FILTER_UNIT_ENABLE | 65536 | ❌ 未表示 |
| FILTER_ZONE_STAGE | 9007199254740992 | ❌ 未表示 |
| FILTER_ZONE_DISCARD | 18014398509481984 | ❌ 未表示 |
| FILTER_ZONE_HAND | 36028797018963968 | ❌ 未表示 |
| FILTER_SETSUNA | 576460752303423488 | ❌ 未表示 |
| FILTER_IS_OPTIONAL | 2305843009213693952 | ❌ 未表示 |

#### Keyword Flags
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| KEYWORD_ACTIVATED_ENERGY_BY_GROUP | 4611686018427387904 | ❌ 未表示 |
| KEYWORD_ACTIVATED_MEMBER_BY_GROUP | 9223372036854775808 | ❌ 未表示 |
| KEYWORD_PLAYED_THIS_TURN | 17592186044416 | ❌ 未表示 |
| KEYWORD_YELL_COUNT | 35184372088832 | ❌ 未表示 |
| KEYWORD_HAS_LIVE_SET | 70368744177664 | ❌ 未表示 |

#### Target/Behavior Flags
| Flag | Value | フロントエンド表示状態 |
|------|-------|----------------------|
| FLAG_TARGET_OPPONENT | 16777216 | ❌ 未表示 |
| FLAG_CAPTURE_VALUE | 33554432 | ❌ 未表示 |
| FLAG_EMPTY_SLOT_ONLY | 67108864 | ❌ 未表示 |
| FLAG_IS_WAIT | 134217728 | ❌ 未表示 |
| FLAG_REVEAL_UNTIL_IS_LIVE | 33554432 | ❌ 未表示 |
| DYNAMIC_VALUE | 1152921504606846976 | ❌ 未表示 |

#### Area/Zone Constants
| Constant | Value | フロントエンド表示状態 |
|----------|-------|----------------------|
| AREA_LEFT | 1 | ❌ 未表示 |
| AREA_CENTER | 2 | ❌ 未表示 |
| AREA_RIGHT | 3 | ❌ 未表示 |
| ZONE_MASK_STAGE | 4 | ❌ 未表示 |
| ZONE_MASK_HAND | 6 | ❌ 未表示 |
| ZONE_MASK_DISCARD | 7 | ❌ 未表示 |
| ZONE_LOOKED_CARDS | 90 | ❌ 未表示 |

---

## フロントエンドで現在表示されている項目 (DebugModal.js)

### システムレベル (GameState)
| 項目名 | バックエンドフィールド | 状態 |
|--------|----------------------|------|
| Phase | `phase` | ✅ 表示中 |
| Turn | `turn` | ✅ 表示中 |
| Active | `current_player` | ✅ 表示中 |
| Queue | `trigger_queue.len()` | ✅ 表示中 (推定) |
| RPS | `rps_choices` | ✅ 表示中 |
| Winner | `winner` | ✅ 表示中 |
| FirstPl | `first_player` | ✅ 表示中 |
| TrigDepth | `trigger_depth` | ✅ 表示中 |
| InteractDepth | `interaction_stack.len()` | ✅ 表示中 (推定) |
| LiveResPend | `live_result_selection_pending` | ✅ 表示中 |
| NeedsDeck | `needs_deck` | ⚠️ 未確認 |
| Spectators | `spectators` | ⚠️ 未確認 |

### プレイヤーレベル (PlayerState)
| 項目名 | バックエンドフィールド | 状態 |
|--------|----------------------|------|
| Energy | `energy_zone.len()` / `energy_count` | ✅ 表示中 |
| Hand | `hand.len()` | ✅ 表示中 |
| Deck | `deck.len()` | ✅ 表示中 |
| Discard | `discard.len()` | ✅ 表示中 |
| EnergyDeck | `energy_deck.len()` | ✅ 表示中 |
| SuccessLives | `success_lives.len()` | ✅ 表示中 |
| LiveZone | `live_zone` (非 -1 カウント) | ✅ 表示中 |
| YellCards | `yell_cards.len()` | ✅ 表示中 |
| Exile | `exile.len()` | ✅ 表示中 |
| LiveDeck | `live_deck.len()` | ✅ 表示中 |
| CostReduction | `cost_reduction` | ✅ 表示中 |
| BatonCount | `baton_touch_count` / `baton_touch_limit` | ✅ 表示中 |
| PrevActivate | `prevent_activate` | ✅ 表示中 |
| PrevBaton | `prevent_baton_touch` | ✅ 表示中 |
| PrevSuccess | `prevent_success_pile_set` | ✅ 表示中 |
| PrevPlaySlotMask | `prevent_play_to_slot_mask` | ✅ 表示中 |
| SkipNextAct | `skip_next_activate` | ✅ 表示中 |
| LiveScoreBonus | `live_score_bonus` | ✅ 表示中 |
| YellReduction | `yell_count_reduction` | ✅ 表示中 |
| CheerMod | `cheer_mod_count` | ✅ 表示中 |
| PlayCount | `play_count_this_turn` | ✅ 表示中 |
| HandIncrTurn | `hand_increased_this_turn` | ✅ 表示中 |
| DiscardedTurn | `discarded_this_turn` | ✅ 表示中 |
| TurnVolume | `current_turn_notes` | ✅ 表示中 |
| ExcessHearts | `excess_hearts` | ✅ 表示中 |
| FlagsBits | `flags` | ✅ 表示中 (16進数のみ) |
| PlayedGrpMask | `played_group_mask` | ✅ 表示中 |
| ActEnergyGrp | `activated_energy_group_mask` | ✅ 表示中 |
| ActMemberGrp | `activated_member_group_mask` | ✅ 表示中 |
| ColorXforms | `color_transforms.len()` | ✅ 表示中 |
| NegatedTrigs | `negated_triggers.len()` | ✅ 表示中 |
| GrantedAbs | `granted_abilities.len()` | ✅ 表示中 |
| UsedAbs | `used_abilities.len()` | ✅ 表示中 |
| Restrictions | `restrictions` | ✅ 表示中 |
| MullSelection | `mulligan_selection` | ✅ 表示中 |
| ObtSuccess | `obtained_success_live` | ✅ 表示中 |
| LvRevealed | `live_zone_revealed` | ✅ 表示中 |
| BladeBuffs | `blade_buffs[slot]` | ✅ 表示中 |
| HeartBuffs | `heart_buffs[slot]` | ✅ 表示中 |
| CostMod | `slot_cost_modifiers[slot]` | ✅ 表示中 |
| StgEnergy | `stage_energy_count[slot]` | ✅ 表示中 |
| Reductions | `heart_req_reductions` | ✅ 条件付き表示 |
| Additions | `heart_req_additions` | ✅ 条件付き表示 |

---

## 欠けているフィールド（未表示）

### 🔴 CRITICAL: metadata.json Conditions (55種類)
**すべて未表示** - アビリティ条件評価のデバッグに必須:
- `TURN_1`, `HAS_MEMBER`, `HAS_COLOR`, `COUNT_STAGE`, `COUNT_HAND`, etc.
- `IS_TAPPED`, `IS_ACTIVE`, `IS_WAIT`, `LIVE_PERFORMED`
- `SCORE_COMPARE`, `COST_COMPARE`, `BLADE_COMPARE`, `HEART_COMPARE`
- `DECK_REFRESHED`, `HAS_MOVED`, `HAND_INCREASED`

### 🔴 HIGH Priority（デバッグに重要）
#### PlayerState Fields
| フィールド | 型 | 説明 |
|-----------|-----|------|
| `tapped_energy_mask` | `u64` | Energy Zone のタップ状態（ビットマスク） |
| `cost_modifiers` | `Vec<(Condition, i32)>` | コスト修正の詳細条件 |
| `stage_energy` | `[SmallVec<[i32; 4]>; 3]` | ステージスロット下のエネルギーカード |

#### GameState Fields
| フィールド | 型 | 説明 |
|-----------|-----|------|
| `score_req_list` | `Vec<u8>` | スコア要求リスト |
| `score_req_player` | `i8` | スコア要求プレイヤー |

### 🟡 MEDIUM Priority
#### PlayerState Fields
| フィールド | 型 | 説明 |
|-----------|-----|------|
| `used_abilities` | `SmallVec<[u32; 16]>` | 使用済みアビリティの詳細リスト |
| `live_score_bonus_logs` | `SmallVec<[(i32, i32); 4]>` | スコアボーナスログ |
| `blade_buff_logs` | `SmallVec<[(i32, i16, u8); 4]>` | ブレードバフログ |
| `heart_buff_logs` | `SmallVec<[(i32, i32, u8, u8); 4]>` | ハートバフログ |
| `color_transforms` | `SmallVec<[(i32, u8, u8); 4]>` | カラー変換の詳細 |
| `perf_triggered_abilities` | `Vec<(i32, i16, TriggerType)>` | パフォーマンス中に発動したアビリティ |

#### GameState Fields
| フィールド | 型 | 説明 |
|-----------|-----|------|
| `prev_phase` | `Phase` | 前のフェーズ |
| `prev_card_id` | `i32` | 前に使用されたカードID |
| `live_set_pending_draws` | `[u8; 2]` | Live Set 待機ドロー |
| `live_result_triggers_done` | `bool` | Live Result トリガー完了 |
| `live_start_triggers_done` | `bool` | Live Start トリガー完了 |

### 🟢 LOW Priority
- 各種処理済みマスク (`*_processed_mask`)
- 各種ログフィールド (`*_logs`)
- `turn_history`, `hand_added_turn`, `looked_cards`

---

## Flags ビットフィールド (`flags: u32`) の詳細

バックエンドコメントによると:
```rust
pub flags: u32, // [cannot_live:1, deck_refreshed:1, immunity:1, tapped_m_0..3:3, moved_m_0..3:3, live_revealed_0..3:3]
```

フロントエンドでは現在 `FlagsBits` として16進数で表示のみ。
**個別ビットの展開表示を追加することを推奨**:
| ビット | 名前 | 説明 |
|--------|------|------|
| 0 | `cannot_live` | Live不可フラグ |
| 1 | `deck_refreshed` | デッキリフレッシュ済み |
| 2 | `immunity` | 免疫状態 |
| 3-5 | `tapped_m_0/1/2` | メンバータップ状態 |
| 6-8 | `moved_m_0/1/2` | メンバー移動状態 |
| 9-11 | `live_revealed_0/1/2` | Live公開状態 |

---

## 推奨追加項目（優先順）

### Phase 1: CRITICAL (即座に追加すべき)
1. **metadata.json の conditions 一覧表示** - 現在評価中の条件を確認できるように
2. **`tapped_energy_mask`** - Energy Zone のタップ状態を可視化
3. **`cost_modifiers`** - コスト修正の詳細
4. **`stage_energy`** - ステージ下のエネルギーカード

### Phase 2: HIGH Priority
5. **`score_req_list` / `score_req_player`** - スコア要求システム
6. **`flags` ビット展開** - 個別ビットの表示

### Phase 3: MEDIUM Priority
7. `used_abilities` - どのアビリティが使用済みか
8. `*_logs` 系 - バフ/ボーナスの履歴
9. `prev_phase`, `prev_card_id` - 前の状態

---

## 実装ノート

追加時の参考: フロントエンドの [`DebugModal.js`](frontend/web_ui/js/modals/DebugModal.js:232) で `_flag` ヘルパー関数を使用:

```javascript
${F('FieldName', p.field_name ?? default_value)}
```

複雑なデータ構造（配列や Vec）は `JSON.stringify()` を使用:

```javascript
${F('CostModifiers', JSON.stringify(p.cost_modifiers || []))}
```

---

*Source: data/metadata.json, engine_rust_src/src/core/logic/player.rs, engine_rust_src/src/core/logic/state.rs*
*Generated by Architect mode audit*
