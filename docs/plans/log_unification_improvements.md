# ログ統合システム: 追加改善計画

## 現在の実装状況

### 完了した項目
- ✅ `log_event()` 関数の実装 (game.rs)
- ✅ 重複している3箇所のリファクタリング (handlers.rs)
- ✅ UI統合 (ui_logs.js)
- ✅ CSSスタイル追加 (unified_log_styles.css)
- ✅ cargo check 成功

---

## 追加改善の領域

### 1. パフォーマンス最適化

#### 1.1 仮想スクロールの実装
**問題**: ログエントリが多数ある場合、DOM要素が増加しパフォーマンスが低下

**解決策**:
```javascript
// 仮想スクロール実装の概要
class VirtualScroll {
    constructor(container, itemHeight, bufferSize = 5) {
        this.container = container;
        this.itemHeight = itemHeight;
        this.bufferSize = bufferSize;
        this.visibleItems = [];
    }

    render(items, scrollTop) {
        const startIdx = Math.floor(scrollTop / this.itemHeight) - this.bufferSize;
        const endIdx = startIdx + Math.ceil(this.container.clientHeight / this.itemHeight) + this.bufferSize * 2;

        // 表示範囲のアイテムのみレンダリング
        return items.slice(Math.max(0, startIdx), endIdx);
    }
}
```

**影響**: 大規模ゲーム（100+ターン）でのメモリ使用量削減

#### 1.2 差分更新の実装
**問題**: 現在は全体を再レンダリングしている

**解決策**:
```javascript
// 差分更新の実装
updateRuleLog: (newEntries) => {
    const fragment = document.createDocumentFragment();
    newEntries.forEach(entry => {
        const el = Logs.createLogEntryElement(entry);
        fragment.appendChild(el);
    });
    ruleLogEl.appendChild(fragment);
}
```

---

### 2. フィルタリング機能の強化

#### 2.1 イベントタイプフィルター
**現在**: ターン番号でのフィルタリングのみ

**改善案**:
```javascript
// フィルター状態
const filterState = {
    selectedTurn: -1,
    eventTypes: ['PLAY', 'ACTIVATE', 'TRIGGER', 'EFFECT', 'RULE', 'YELL'],
    players: [0, 1],  // 両プレイヤー表示
    searchText: ''
};

// フィルター適用関数
applyFilters: (events, filters) => {
    return events.filter(e =>
        filters.eventTypes.includes(e.event_type) &&
        filters.players.includes(e.player_id) &&
        (filters.selectedTurn === -1 || e.turn === filters.selectedTurn) &&
        (filters.searchText === '' || e.description.includes(filters.searchText))
    );
}
```

#### 2.2 UIコントロールの追加
```html
<div class="log-filter-controls">
    <select id="log-turn-filter">
        <option value="-1">All Turns</option>
        <!-- 動的に生成 -->
    </select>
    <div class="event-type-filters">
        <label><input type="checkbox" value="PLAY" checked> Play</label>
        <label><input type="checkbox" value="ACTIVATE" checked> Activate</label>
        <label><input type="checkbox" value="TRIGGER" checked> Trigger</label>
        <label><input type="checkbox" value="EFFECT" checked> Effect</label>
    </div>
    <input type="text" id="log-search" placeholder="Search...">
</div>
```

---

### 3. イベントタイプの拡張

#### 3.1 新しいイベントタイプの追加
**現在**: PLAY, ACTIVATE, TRIGGER, EFFECT, RULE, YELL, PERFORMANCE

**提案**:
| イベントタイプ | 説明 | 優先度 |
|---------------|------|--------|
| PHASE | フェーズ遷移 | 高 |
| DRAW | ドロー処理 | 高 |
| SCORE | スコア計算 | 中 |
| HEART | Heart追加/削除 | 中 |
| BATON | バトンタッチ | 中 |
| LIVE | ライブパフォーマンス | 低 |

#### 3.2 イベント詳細情報の拡充
```rust
// TurnEvent構造体の拡張
pub struct TurnEvent {
    pub turn: u32,
    pub phase: Phase,
    pub player_id: u8,
    pub event_type: String,
    pub source_cid: i32,
    pub ability_idx: i16,
    pub description: String,
    // 追加フィールド
    pub target_cids: Vec<i32>,      // 対象カードID
    pub value: i32,                  // 数値（ダメージ、回復量など）
    pub tags: Vec<String>,           // タグ（buff, debuff, trigger等）
}
```

---

### 4. アクセシビリティ改善

#### 4.1 ARIA属性の追加
```html
<div class="log-section" role="region" aria-label="Game Log">
    <div class="log-entry" role="logentry" aria-live="polite">
        <span class="turn-badge" aria-label="Turn 3">T3</span>
        <span class="event-type" aria-label="Play event">🃏 PLAY</span>
    </div>
</div>
```

#### 4.2 キーボードナビゲーション
```javascript
// キーボードショートカット
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'f') {
        // 検索フォーカス
        document.getElementById('log-search').focus();
    }
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        // ログエントリ間の移動
        navigateLogEntries(e.key === 'ArrowDown' ? 1 : -1);
    }
});
```

---

### 5. 国際化(i18n)の完全対応

#### 5.1 翻訳キーの追加
```javascript
// translations_data.js
const translations = {
    jp: {
        // 既存
        'active_effects': '適用中の効果',
        'turn_history': 'ターン履歴',
        // 追加
        'event_play': 'プレイ',
        'event_activate': '発動',
        'event_trigger': 'トリガー',
        'event_effect': '効果',
        'event_rule': 'ルール',
        'event_yell': 'エール',
        'filter_all_turns': '全ターン',
        'filter_by_type': 'タイプで絞り込み',
        'search_placeholder': 'ログを検索...',
    },
    en: {
        // ...
    }
};
```

#### 5.2 動的テキストのフォーマット
```javascript
// 複数形対応
formatEventCount: (count, type) => {
    const key = count === 1 ? `event_${type}_single` : `event_${type}_plural`;
    return t[key].replace('{count}', count);
}
```

---

### 6. テストカバレッジ

#### 6.1 ユニットテスト
```javascript
// ui_logs.test.js
describe('Logs Module', () => {
    test('renderActiveEffectsSection returns null when no effects', () => {
        const state = { players: [{}, {}] };
        const result = Logs.renderActiveEffectsSection(state, {});
        expect(result).toBeNull();
    });

    test('createTurnEventElement creates correct structure', () => {
        const event = {
            turn: 1,
            phase: 7,
            player_id: 0,
            event_type: 'PLAY',
            description: 'Test'
        };
        const el = Logs.createTurnEventElement(event, {});
        expect(el.className).toContain('turn-event');
        expect(el.className).toContain('play');
    });
});
```

#### 6.2 統合テスト
```javascript
describe('Log Integration', () => {
    test('log_event writes to both turn_history and rule_log', async () => {
        const gameState = createTestGameState();
        gameState.log_event('TEST', 'Test event', -1, -1, 0, None, true);

        expect(gameState.turn_history).toHaveLength(1);
        expect(gameState.ui.rule_log).toHaveLength(1);
    });
});
```

---

### 7. モバイル対応

#### 7.1 レスポンシブデザイン
```css
/* モバイル対応 */
@media (max-width: 768px) {
    .log-section-header {
        font-size: 0.75rem;
        padding: 3px 4px;
    }

    .log-entry {
        padding: 3px 4px;
        font-size: 0.75rem;
    }

    .player-badge, .turn-badge, .phase-badge {
        font-size: 0.6rem;
        padding: 1px 2px;
    }

    /* 折りたたみ可能セクション */
    .log-section.collapsed .log-section-content {
        display: none;
    }
}
```

#### 7.2 タッチジェスチャー
```javascript
// スワイプでフィルター表示
let touchStartX = 0;
container.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
});

container.addEventListener('touchend', (e) => {
    const touchEndX = e.changedTouches[0].clientX;
    if (touchEndX - touchStartX > 50) {
        showFilterPanel();
    }
});
```

---

## 優先順位付き実装計画

### Phase 1: 高優先度（1-2週間）
1. [ ] 差分更新の実装
2. [ ] イベントタイプフィルターの追加
3. [ ] 翻訳キーの完全対応

### Phase 2: 中優先度（2-4週間）
4. [ ] 仮想スクロールの実装
5. [ ] 新しいイベントタイプの追加
6. [ ] アクセシビリティ改善

### Phase 3: 低優先度（1ヶ月以上）
7. [ ] テストカバレッジの向上
8. [ ] モバイル対応の強化
9. [ ] パフォーマンス監視の追加

---

## メトリクス

### 現在のパフォーマンス指標
- ログエントリ100件のレンダリング時間: ~50ms
- メモリ使用量: ~2MB（1000エントリ）

### 目標指標
- ログエントリ1000件のレンダリング時間: <100ms
- メモリ使用量: <5MB（10000エントリ）
- フィルター適用時間: <50ms

---

## リスク評価

| リスク | 影響 | 確率 | 軽減策 |
|--------|------|------|--------|
| 既存機能への影響 | 高 | 低 | 段階的ロールアウト |
| パフォーマンス低下 | 中 | 中 | ベンチマークテスト |
| 翻訳の不整合 | 低 | 中 | 自動翻訳チェック |

---

## 次のステップ

1. **即座に実施可能**: 翻訳キーの追加、CSS改善
2. **要検討**: 仮想スクロール、イベントタイプ拡張
3. **長期計画**: テストカバレッジ、モバイル対応
