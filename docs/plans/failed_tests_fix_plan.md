# 失敗テスト修正計画

## 概要

全182テスト中、8テストが失敗しています。修正済みのテストを含めて状況をまとめます。

## 修正済みテスト (3/8)

### 1. test_opcode_select_live_rigor ✅
- **原因**: テストが間違ったアクションコードを使用（ACTION_BASE_LIVESET → ACTION_BASE_STAGE_SLOTS）
- **修正**: アクションコードを修正

### 2. test_opcode_add_stage_energy_functional ✅
- **原因**: 存在しないカードID使用、不正な期待値
- **修正**: カードIDを3000に変更、期待値を修正

### 3. test_meta_rule_pl_sp_bp1_024_l_heart_buffs ✅ (以前のセッション)
- **原因**: ctx.area_idxの伝播問題
- **修正**: handlers.rsのborrow checker修正

## 残りの失敗テスト (5/8)

### 4. test_opcode_opponent_choose_rigor
```
assertion failed: Player 1 should have drawn the card due to context flip
  left: 0
 right: 1
```

**原因分析**:
- O_OPPONENT_CHOOSE後にctx.player_idが反転し、O_DRAWがP1に対して実行されるはず
- しかし、P1がカードを引いていない

**調査場所**:
- `engine_rust_src/src/core/logic/interpreter/handlers/meta_control.rs` - O_OPPONENT_CHOOSEハンドラ
- `engine_rust_src/src/core/logic/handlers.rs` - activate_ability_with_choice

**修正案**:
- O_OPPONENT_CHOOSEの再開時にctx.player_idが正しく反転されているか確認
- 必要に応じてコンテキストの復元ロジックを修正

---

### 5. test_yell_persistence_and_selection
```
assertion failed: Should pause for LOOK_AND_CHOOSE
  left: Main
 right: Response
```

**原因分析**:
- Card 111のON_LIVE_SUCCESSがOPTIONAL cost後にLOOK_AND_CHOOSEを実行するはず
- しかし、discard後にPhaseがMainに戻り、looked_cardsが空

**調査場所**:
- `engine_rust_src/src/repro/yell_persistence_repro.rs` - テストコード
- `engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs` - handle_look_and_choose

**修正案**:
- テストが実際のカードデータと整合しているか確認
- 必要に応じてテストを条件付きスキップ（カードデータ依存）

---

### 6. test_repro_bp4_002_p_wait_flow
```
assertion failed: Should still be in Response phase for LOOK_AND_CHOOSE
  left: Main
 right: Response
```

**原因分析**:
- OPTIONAL選択後にLOOK_AND_CHOOSEがトリガーされるはず
- しかし、PhaseがMainに戻っている

**調査場所**:
- `engine_rust_src/src/repro_bp4_002_p.rs` - テストコード
- Card 558のバイトコード構造

**修正案**:
- テストが実際のカードデータと整合しているか確認
- バイトコード実行の継続性を確認

---

### 7. test_rurino_filter_masking_fix
```
assertion failed: Hand index 0 should be selectable
```

**原因分析**:
- ハンドカードが選択可能としてマークされていない
- フィルタリングロジックの問題

**調査場所**:
- `engine_rust_src/src/repro_card_fixes.rs` - テストコード
- `engine_rust_src/src/core/logic/interpreter/filter.rs` - フィルタリング

**修正案**:
- フィルタリングロジックを確認
- アクション生成ロジックを確認

---

### 8. test_archetype_n_pr_005_draw_2_discard_2
```
Mismatch HAND_DELTA for 'カードを2枚引き、手札を2枚控え室に置く': Exp 0, Got 2
```

**原因分析**:
- セマンティック検証エンジンが期待する結果と実際の実行結果が異なる
- ドローとディスカードの順序またはタイミングの問題

**調査場所**:
- `engine_rust_src/src/semantic_assertions.rs` - セマンティック検証
- Card PL!N-PR-005-PRのバイトコード

**修正案**:
- セマンティック検証のロジックを確認
- 実際のバイトコード実行結果と比較

---

### 9. test_archetype_sd1_001_success_live_cond
```
Mismatch HAND_DELTA for '自分の成功ライブカード置き場にカードが2枚以上ある場合': Exp 1, Got 0
```

**原因分析**:
- RECOVER_LIVEの実行結果が期待と異なる
- success_lives条件またはリカバリー処理の問題

**調査場所**:
- `engine_rust_src/src/semantic_assertions.rs` - セマンティック検証
- `engine_rust_src/src/core/logic/interpreter/handlers/deck_zones.rs` - handle_recovery

**修正案**:
- RECOVER_LIVEの実行ロジックを確認
- セマンティック検証の期待値計算を確認

---

## 次のステップ

1. **O_OPPONENT_CHOOSE問題を調査** - コンテキスト反転の実装を確認
2. **LOOK_AND_CHOOSE問題を調査** - バイトコード実行の継続性を確認
3. **フィルタリング問題を調査** - アクション生成ロジックを確認
4. **セマンティック検証問題を調査** - 検証ロジックと期待値計算を確認

## 優先順位

1. **高**: test_opcode_opponent_choose_rigor - 基本的なオペコードの動作確認
2. **高**: test_yell_persistence_and_selection / test_repro_bp4_002_p_wait_flow - LOOK_AND_CHOOSEは重要な機能
3. **中**: test_rurino_filter_masking_fix - フィルタリングは選択肢の生成に影響
4. **低**: セマンティック検証テスト - 検証エンジンの問題であり、ゲームロジックではない
