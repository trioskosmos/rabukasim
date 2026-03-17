# JavaScript リファクタリング評価レポート

## 概要

フロントエンドJavaScriptコードの分析を実施し、リファクタリングの必要性を評価しました。本レポートは**コード損失を防ぐ**ための詳細な移行手順を含みます。

---

## 分析対象ファイル

| ファイル | サイズ | 関数数 | 状態 |
|---------|--------|--------|------|
| `ui_rendering.js` | 80KB | 30+ | **要検討** |
| `ability_translator.js` | 53KB | 4 | **要検討** |
| `ui_tooltips.js` | 37KB | 複数 | 注意 |
| `wasm_adapter.js` | 15KB | クラス1 | 良好 |
| `state.js` | 3.5KB | 3 | 良好 |
| `network.js` | 中程度 | 複数 | 良好 |
| `main.js` | 298行 | 2 | 注意* |

---

## 🔒 安全なリファクタリング手順

### 事前準備（必須）

#### 1. バックアップ作成
```bash
# 作業開始前に必ずバックアップ
cp -r frontend/web_ui/js frontend/web_ui/js_backup_$(date +%Y%m%d)
```

#### 2. Git ブランチ作成
```bash
git checkout -b refactor/js-module-split
git add -A
git commit -m "chore: pre-refactor snapshot"
```

#### 3. 現在のエクスポート/インポート確認
各ファイルの依存関係を文書化：
```bash
# エクスポート一覧
grep -n "export " frontend/web_ui/js/*.js > exports_inventory.txt

# インポート一覧
grep -n "import " frontend/web_ui/js/*.js > imports_inventory.txt
```

---

## 詳細分析と移行計画

### 1. `ui_rendering.js` - 最優先リファクタリング候補

#### 現状の関数一覧（完全なインベントリ）

| 行番号 | 関数名 | 移行先モジュール |
|--------|--------|------------------|
| 11 | `render()` | index.js (統合エクスポート) |
| 20 | `renderHeaderStats()` | state_display.js |
| 61 | `get_valid_targets()` | targeting.js |
| 146 | `renderInternal()` | index.js |
| 216 | `getPhaseKey()` | state_display.js |
| 233 | `renderBoard()` | board.js |
| 252 | `renderDeckCounts()` | cards.js |
| 271 | `renderCards()` | cards.js |
| 364 | `renderStage()` | board.js |
| 420 | `renderEnergy()` | zones.js |
| 458 | `renderLiveZone()` | zones.js |
| 514 | `renderDiscardPile()` | zones.js |
| 557 | `renderActiveEffects()` | state_display.js |
| 662 | `renderRuleLog()` | state_display.js |
| 784 | `renderActiveAbilities()` | actions.js |
| 794 | `renderSelectionModal()` | modals.js |
| 801 | `renderGameOver()` | modals.js |
| 815 | `showDiscardModal()` | modals.js |
| 853 | `renderActions()` | actions.js |
| 1190 | `renderPerformanceGuide()` | performance.js |
| 1234 | `renderLookedCards()` | cards.js |
| 1292 | `renderPerformanceResult()` | performance.js |
| 1489 | `renderHeartProgress()` | hearts_blades.js |
| 1505 | `renderHeartsCompact()` | hearts_blades.js |
| 1520 | `renderBladeHeartsCompact()` | hearts_blades.js |
| 1524 | `renderBladesCompact()` | hearts_blades.js |
| 1534 | `renderTotalHeartsBreakdown()` | hearts_blades.js |
| 1538 | `renderModifiers()` | state_display.js |
| 1539 | `renderGameData()` | state_display.js |
| 1541 | `updateSettingsButtons()` | state_display.js |
| 1572 | `showPerfTab()` | performance.js |
| 1594 | `renderTurnHistory()` | performance.js |

#### 推奨される移行手順

**ステップ1: 新しいディレクトリ構造作成**
```
frontend/web_ui/js/rendering/
├── index.js           # 統合エクスポート
├── board.js           # renderBoard, renderStage
├── cards.js           # renderCards, renderDeckCounts, renderLookedCards
├── zones.js           # renderEnergy, renderLiveZone, renderDiscardPile
├── state_display.js   # renderHeaderStats, renderActiveEffects, renderRuleLog, etc.
├── actions.js         # renderActions, renderActiveAbilities
├── performance.js     # renderPerformanceGuide, renderPerformanceResult, etc.
├── hearts_blades.js   # renderHeartsCompact, renderBladesCompact, etc.
├── modals.js          # showDiscardModal, renderGameOver
└── targeting.js       # get_valid_targets
```

**ステップ2: 各モジュールの作成（例: board.js）**

```javascript
// frontend/web_ui/js/rendering/board.js
import { State } from '../state.js';
import { Rendering } from './index.js'; // 循環参照回避のため遅延インポート

export function renderBoard(state, p0, p1, validTargets = { stage: {}, discard: {}, hasSelection: false }) {
    // 元の ui_rendering.js から renderBoard 関数の内容をそのままコピー
    Rendering.renderStage('my-stage', p0.stage, true, validTargets.myStage, validTargets.hasSelection);
    // ... 残りのコード
}

export function renderStage(containerId, stage, clickable, validActionMap = {}, hasGlobalSelection = false) {
    // 元の ui_rendering.js から renderStage 関数の内容をそのままコピー
    // ...
}
```

**ステップ3: 統合エクスポート（index.js）**

```javascript
// frontend/web_ui/js/rendering/index.js
import { State } from '../state.js';
import { ICON_DATA_URIs } from '../assets_registry.js';
import { Tooltips } from '../ui_tooltips.js';

// 各モジュールからインポート
import * as Board from './board.js';
import * as Cards from './cards.js';
import * as Zones from './zones.js';
import * as StateDisplay from './state_display.js';
import * as Actions from './actions.js';
import * as Performance from './performance.js';
import * as HeartsBlades from './hearts_blades.js';
import * as Modals from './modals.js';
import * as Targeting from './targeting.js';

// 統合 Rendering オブジェクト（後方互換性維持）
export const Rendering = {
    render: () => { /* ... */ },
    renderInternal: () => { /* ... */ },

    // 各モジュールから再エクスポート
    ...Board,
    ...Cards,
    ...Zones,
    ...StateDisplay,
    ...Actions,
    ...Performance,
    ...HeartsBlades,
    ...Modals,
    ...Targeting
};

// 循環参照回避のため、必要な依存関係をグローバルに
window.Rendering = Rendering;
```

**ステップ4: 段階的移行**

```javascript
// 元の ui_rendering.js を残しつつ、新しいモジュールから再エクスポート
// frontend/web_ui/js/ui_rendering.js (移行期間中)

// 新しいモジュールから全てを再エクスポート
export { Rendering } from './rendering/index.js';

// 後方互換性のため window.Rendering も設定
import { Rendering } from './rendering/index.js';
window.Rendering = Rendering;
```

**ステップ5: 検証チェックリスト**

- [ ] 全ての関数が新しいモジュールにコピーされている
- [ ] 元のファイルと同じ行数のコードがある
- [ ] 全ての `import` 文が正しい
- [ ] `window.Rendering` が正しく設定されている
- [ ] `main.js` からの `import { Rendering }` が動作する
- [ ] ブラウザでUIが正しく描画される

---

### 2. `ability_translator.js` - データ分離

#### 現状の構造（完全なインベントリ）

| 行番号 | 要素 | 種別 | 移行先 |
|--------|------|------|--------|
| 12-18 | `COMMON_NAMES` | データ | i18n/names.js |
| 20-24 | `NAME_MAP` | データ（自動生成） | i18n/names.js |
| 26-78 | `Translations.jp` | データ | i18n/locales/jp/*.json |
| 79-231 | `Translations.en` | データ | i18n/locales/en/*.json |
| 232 | `parseParams()` | 関数 | i18n/translator.js |
| 248 | `translatePart()` | 関数 | i18n/translator.js |
| 348 | `translateHeuristic()` | 関数 | i18n/translator.js |
| 373 | `translateAbility()` | 関数 | i18n/translator.js |

#### 推奨される移行手順

**ステップ1: ディレクトリ構造作成**
```
frontend/web_ui/js/i18n/
├── index.js              # エクスポート統合
├── translator.js         # 翻訳ロジック（4関数）
├── names.js              # COMMON_NAMES, NAME_MAP
└── locales/
    ├── jp.json           # 日本語翻訳データ
    └── en.json           # 英語翻訳データ
```

**ステップ2: データ抽出（locales/jp.json）**

```json
{
  "triggers": {
    "ON_PLAY": "【登場時】",
    "ON_LIVE_START": "【ライブ開始時】",
    ...
  },
  "opcodes": {
    "ENERGY": "【エネ】{value}獲得",
    ...
  },
  "params": { ... },
  "misc": { ... }
}
```

**ステップ3: 翻訳ロジック移行（translator.js）**

```javascript
// frontend/web_ui/js/i18n/translator.js
import { COMMON_NAMES, NAME_MAP } from './names.js';

// 翻訳データを動的ロード
let translations = {};

export async function loadTranslations(lang = 'jp') {
    if (!translations[lang]) {
        const response = await fetch(`./js/i18n/locales/${lang}.json`);
        translations[lang] = await response.json();
    }
    return translations[lang];
}

export function parseParams(paramStr) {
    // 元の関数をそのままコピー
}

export function translatePart(part, t, lang, allParams, consumedKeys) {
    // 元の関数をそのままコピー
}

export function translateHeuristic(text) {
    // 元の関数をそのままコピー
}

export function translateAbility(rawText, lang = 'jp') {
    // 元の関数をそのままコピー
}
```

**ステップ4: 後方互換性維持**

```javascript
// frontend/web_ui/js/ability_translator.js (移行期間中)
// 新しいモジュールから再エクスポート
export { translateAbility, parseParams, translatePart, translateHeuristic } from './i18n/translator.js';
export { COMMON_NAMES, NAME_MAP } from './i18n/names.js';
```

---

### 3. `main.js` - グローバル関数整理

#### 現状の window.* 代入一覧

```javascript
// main.js 内の全ての window.* 代入を文書化
window.doAction = Network.doAction;
window.selectCard = selectCard;
window.selectStageCard = selectStageCard;
window.selectEnergyCard = selectEnergyCard;
window.selectLiveCard = selectLiveCard;
window.selectDiscardCard = selectDiscardCard;
window.confirmSelection = confirmSelection;
window.cancelSelection = cancelSelection;
window.toggleSidebar = toggleSidebar;
window.switchBoard = switchBoard;
window.showDeckModal = Modals.showDeckModal;
window.closeDeckModal = Modals.closeDeckModal;
window.showSettingsModal = Modals.showSettingsModal;
window.closeSettingsModal = Modals.closeSettingsModal;
window.showSetupModal = Modals.showSetupModal;
window.closeSetupModal = Modals.closeSetupModal;
window.startGame = startGame;
window.startOfflineGame = startOfflineGame;
window.startReplay = startReplay;
window.toggleHotseat = toggleHotseat;
window.loadDeckPreset = Modals.loadDeckPreset;
window.setLang = setLang;
window.toggleFriendlyAbilities = toggleFriendlyAbilities;
window.toggleFullLog = toggleFullLog;
window.selectTurn = selectTurn;
window.selectPerfTurn = selectPerfTurn;
window.showPerfTab = Rendering.showPerfTab;
window.closePerformanceModal = closePerformanceModal;
window.closeDiscardModal = closeDiscardModal;
window.closeLookedCards = closeLookedCards;
window.closeRuleLog = closeRuleLog;
window.closeReplayModal = closeReplayModal;
window.downloadReplay = downloadReplay;
window.uploadReplayFile = uploadReplayFile;
```

#### 推奨される移行手順

**ステップ1: 専用ブリッジファイル作成**

```javascript
// frontend/web_ui/js/global_bridge.js
import { Network } from './network.js';
import { Rendering } from './rendering/index.js';
import { Modals } from './ui_modals.js';
import { Replay } from './replay_system.js';
// ... その他のインポート

// グローバル関数を一箇所に集約
export function setupGlobals() {
    // Network
    window.doAction = Network.doAction;

    // Selection
    window.selectCard = selectCard;
    window.selectStageCard = selectStageCard;
    // ... 他の選択関数

    // Modals
    window.showDeckModal = Modals.showDeckModal;
    // ... 他のモーダル関数

    // ... 残りの関数
}
```

**ステップ2: main.js で呼び出し**

```javascript
// frontend/web_ui/js/main.js
import { setupGlobals } from './global_bridge.js';

// 初期化時に呼び出し
export async function initialize() {
    setupGlobals();
    // ... 残りの初期化
}
```

---

## 🔍 検証手順

### 自動検証スクリプト

```bash
#!/bin/bash
# verify_refactor.sh

echo "=== 関数数チェック ==="
echo "元の ui_rendering.js 関数数:"
grep -c "^\s\+\w\+:\s*(" frontend/web_ui/js_backup/js/ui_rendering.js

echo "新しいモジュールの関数数合計:"
find frontend/web_ui/js/rendering -name "*.js" -exec grep -c "^\s*export function\|^\s*export const.*=.*(" {} \; | awk '{s+=$1} END {print s}'

echo "=== エクスポート整合性チェック ==="
# 元のエクスポートと新しいエクスポートを比較
diff <(grep "export " frontend/web_ui/js_backup/js/ui_rendering.js) \
     <(grep "export " frontend/web_ui/js/rendering/index.js)

echo "=== インポート整合性チェック ==="
# main.js でのインポートが動作するか確認
node -e "import('./frontend/web_ui/js/main.js').then(() => console.log('OK')).catch(e => console.error(e))"
```

### 手動検証チェックリスト

#### UI描画テスト
- [ ] ゲームボードが正しく描画される
- [ ] カードが正しく表示される
- [ ] エネルギーエリアが正しく描画される
- [ ] ライブゾーンが正しく描画される
- [ ] 控え室が正しく描画される
- [ ] アクションボタンが正しく表示される
- [ ] パフォーマンス結果が正しく表示される
- [ ] ハート/ブレードが正しく表示される

#### 機能テスト
- [ ] カード選択が動作する
- [ ] アクション実行が動作する
- [ ] モーダル表示/非表示が動作する
- [ ] 言語切替が動作する
- [ ] リプレイ機能が動作する

#### 翻訳テスト
- [ ] 日本語翻訳が正しく表示される
- [ ] 英語翻訳が正しく表示される
- [ ] 能力テキストが正しく変換される

---

## 📋 移行完了チェックリスト

### ファイル単位

#### ui_rendering.js → rendering/
- [ ] 全30+関数がコピーされている
- [ ] 行数が一致している（±許容範囲）
- [ ] import文が正しい
- [ ] 循環参照がない
- [ ] window.Rendering が設定されている

#### ability_translator.js → i18n/
- [ ] COMMON_NAMES がコピーされている
- [ ] NAME_MAP がコピーされている
- [ ] Translations.jp が JSON に変換されている
- [ ] Translations.en が JSON に変換されている
- [ ] 4つの翻訳関数がコピーされている
- [ ] 動的ロードが動作する

#### main.js → global_bridge.js
- [ ] 全 window.* 代入が移動されている
- [ ] setupGlobals() が正しく動作する
- [ ] HTML onclick ハンドラが動作する

### 統合テスト

- [ ] `npm run build` が成功する
- [ ] `npm run dev` でアプリが起動する
- [ ] 全UIコンポーネントが描画される
- [ ] 全ユーザー操作が動作する
- [ ] エラーログに異常がない

---

## 優先度付き推奨事項

### 高優先度

1. **`ui_rendering.js` の分割**
   - 影響: 大
   - リスク: 中（テスト必須）
   - **上記の段階的移行手順に従うこと**

### 中優先度

2. **`ability_translator.js` のデータ分離**
   - 影響: 中
   - リスク: 低
   - JSONファイルへの変換は機械的に可能

### 低優先度

3. **`main.js` グローバル関数の整理**
   - 影響: 小〜中
   - リスク: 中（HTML修正が必要な場合あり）

---

## 結論

**リファクタリングは推奨されますが、以下の安全策を講じること：**

1. ✅ 必ずバックアップを作成
2. ✅ Git ブランチで作業
3. ✅ 関数単位で段階的に移行
4. ✅ 各ステップで動作確認
5. ✅ 後方互換性を維持（再エクスポート）
6. ✅ 最終的に元ファイルを削除前に全テスト実施

この手順に従えば、コード損失のリスクを最小限に抑えながらリファクタリングを実行できます。
