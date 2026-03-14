# テストカバレッジ改善計画

## 現状分析

### 1. Rustテストスイート実行結果
- **成功**: 225テスト
- **失敗**: 0テスト
- **無視**: 1テスト（`test_gpu_integration` - GPU統合テスト）

### 2. セマンティック監査（Ability Verification Skill）
- **現在のパス率**: 87.1%（710/815能力）
- **目標**: 100%
- **前回記録**: 78.3%（638/815）→ 8.8%改善

#### 失敗カテゴリ分析（残り105能力）

| カテゴリ | カード数 | 割合 | 根本原因 |
|:---|:---:|:---:|:---|
| Infinite Loop | ~6 | 6% | インタープリータの無限ループ検出 |
| Condition Not Met | ~50 | 48% | 合成ボード状態が条件を満たしていない |
| Score Delta Zero | ~30 | 29% | Constant能力/Liveコンテキストの問題 |
| Optional Not Resolved | ~10 | 10% | インタラクション解決の未処理 |
| Other | ~9 | 7% | その他の問題 |

### 3. テスト厳密性レベル（Opcode Rigor Audit）

| レベル | 名称 | 説明 | 例 |
|:---:|:---|:---|:---|
| 1 | Property Check | 値の変更を検証 | `coverage_gap_tests` |
| 2 | Parity Check | 実装間の比較 | `semantic_assertions` |
| 3 | Functional Behavior | フロー、フェーズ遷移、インタラクションスタック | `opcode_missing_tests`, `repro_card_fixes` |

### 4. Q&Aルール検証マトリックス
- **総項目数**: 206+
- **検証済み**: Q16-Q66の大部分
- **未検証**: カード固有のルール多数

---

## テストギャップ

### ギャップ1: セマンティック監査の失敗（177能力）
**最優先**: カテゴリ1と2で全体の63%を占める

#### 修正アプローチ:
1. `setup_oracle_environment`を拡張して両プレイヤーの状態を設定
2. Liveフェーズコンテキストを正しく設定
3. Constant能力の条件フィルタを事前設定

### ギャップ2: GPUパリティテスト
- `test_gpu_integration`が無視されている
- CPU-GPU間のビットレベルパリティ未検証

#### 修正アプローチ:
1. `test_gpu_parity_suite.rs`のシナリオを拡充
2. WGSLシェーダーとRustインタープリータの同期確認

### ギャップ3: Level 3テストの不足
多くのオペコードがLevel 1（プロパティチェック）のみ

#### 修正アプローチ:
1. インタラクションサイクルテストを追加
2. エッジケース境界テストを追加
3. エフェクトリップルテストを追加

---

## 改善計画

### フェーズ1: セマンティック監査パス率向上（目標: 90%+）

#### タスク1.1: Oracle環境の拡張
- [ ] `setup_oracle_environment`に対戦相手カード追加
- [ ] Liveフェーズコンテキスト設定
- [ ] バトンタッチフラグ設定

#### タスク1.2: インタラクション解決の改善
- [ ] `SELECT_HAND_DISCARD`の自動解決
- [ ] `OPTIONAL`インタラクションの処理
- [ ] 起動能力のコスト前払い

#### タスク1.3: Oracle正規表現の修正
- [ ] 条件値と効果量の区別
- [ ] 複雑な日本語テキストの解析

### フェーズ2: テスト厳密性向上

#### タスク2.1: Level 3テスト追加
- [ ] O_SELECT_MEMBERのインタラクションサイクル
- [ ] O_LOOK_AND_CHOOSEのエッジケース
- [ ] O_MODIFY_SCORE_RULEのエフェクトリップル

#### タスク2.2: GPUパリティテスト有効化
- [ ] test_gpu_integrationの修正
- [ ] パリティチェックシナリオ追加

### フェーズ3: Q&Aルール検証拡充

#### タスク3.1: 未検証ルールのテスト化
- [ ] Q70-Q100のカード固有ルール
- [ ] エッジケースルールの検証

---

## スキルファイル同期

`.agent/skills`フォルダの内容をKilocodeと同期する方法：

### オプションA: シンボリックリンク作成
```bash
# Windows（管理者権限必要）
mklink /D .kilocode\skills .agent\skills
```

### オプションB: コピー
```bash
# Windows
xcopy /E /I /Y .agent\skills .kilocode\skills
```

### オプションC: 設定ファイルで参照
`.kilocode/config.json`にスキルパスを追加

---

## 次のステップ

1. **即時**: セマンティック監査の失敗カテゴリ1（Condition Not Met）の修正
2. **短期**: Oracle環境拡張とインタラクション解決改善
3. **中期**: Level 3テスト追加とGPUパリティ有効化
4. **継続**: Q&Aルール検証の拡充

---

## メトリクス目標

| 指標 | 現在 | 目標 |
|:---|:---:|:---:|
| セマンティック監査パス率 | 87.1% | 95%+ |
| Level 3テストカバレッジ | ~30% | 60%+ |
| Q&Aルール検証率 | ~40% | 80%+ |
| GPUパリティテスト | 無効 | 有効 |

---

## スキルファイル同期完了

`.agent/skills`の内容を`.kilocode/skills`にコピーしました（25ファイル）。

### 同期されたスキル一覧:
- `ability_verification/` - 能力検証フレームワーク
- `alphazero_training/` - AlphaZeroトレーニング
- `board_layout_rules/` - ボードレイアウトルール
- `card_id_auditor/` - カードID監査
- `card_id_mapping/` - カードIDマッピング
- `frontend_sync/` - フロントエンド同期
- `future_implementations/` - 将来の実装計画
- `gpu_parity_standards/` - GPUパリティ標準
- `opcode_management/` - オペコード管理
- `opcode_rigor_audit/` - オペコード厳密性監査
- `pseudocode_guidelines/` - 擬似コードガイドライン
- `qa_rule_verification/` - Q&Aルール検証
- `rich_rule_log_guide/` - リッチルールログガイド
- `robust_editor/` - 堅牢エディタ
- `rust_compiler/` - Rustコンパイラ
- `rust_extension_management/` - Rust拡張管理
- `rust_test_explorer/` - Rustテストエクスプローラー
- `semantic_testing/` - セマンティックテスト
- `unified_card_search/` - 統一カード検索
