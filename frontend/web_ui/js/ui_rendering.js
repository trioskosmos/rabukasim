/**
 * UI Rendering Module
 * Handles all board, card, and performance result rendering.
 */
import { State } from './state.js';
import { CardRenderer } from './components/CardRenderer.js';
import { BoardRenderer } from './components/BoardRenderer.js';
import { ActionMenu } from './components/ActionMenu.js';

import { Phase, fixImg } from './constants.js';
import * as i18n from './i18n/index.js';
import { Tooltips } from './ui_tooltips.js';
import { InteractionAdapter } from './interaction_adapter.js';
import { Logs } from './ui_logs.js';
import { PerformanceRenderer } from './ui_performance.js';

// Cached DOM element references for performance
const DOM_CACHE = {
    turn: null,
    phase: null,
    score: null,
    headerEnergy: null,
    totalHearts: null,
    totalBlades: null,
    myHand: null,
    oppHand: null,
    myStage: null,
    oppStage: null,
    myLive: null,
    oppLive: null,
    myEnergy: null,
    oppEnergy: null,
    myDiscard: null,
    oppDiscard: null,
    mySuccess: null,
    oppSuccess: null,
    actions: null,
    ruleLog: null,
    activeAbilitiesList: null,
    activeAbilitiesPanel: null,
};

// Initialize DOM cache on first use
let domCacheInitialized = false;
function initDomCache() {
    if (domCacheInitialized) return;
    domCacheInitialized = true;
    for (const [key, id] of Object.entries({
        turn: 'turn',
        phase: 'phase',
        score: 'score',
        headerEnergy: 'header-energy',
        totalHearts: 'total-hearts-summary',
        totalBlades: 'total-blades-summary',
        myHand: 'my-hand',
        oppHand: 'opp-hand',
        myStage: 'my-stage',
        oppStage: 'opp-stage',
        myLive: 'my-live',
        oppLive: 'opp-live',
        myEnergy: 'my-energy',
        oppEnergy: 'opp-energy',
        myDiscard: 'my-discard-visual',
        oppDiscard: 'opp-discard-visual',
        mySuccess: 'my-success',
        oppSuccess: 'opp-success',
        actions: 'actions',
        ruleLog: 'rule-log',
        activeAbilitiesList: 'active-abilities-list',
        activeAbilitiesPanel: 'active-abilities-panel',
    })) {
        DOM_CACHE[key] = document.getElementById(id);
    }
}

export const Rendering = {
    render: () => {
        if (State.renderRequested) return;
        State.renderRequested = true;
        requestAnimationFrame(() => {
            initDomCache();
            Rendering.renderInternal();
            State.renderRequested = false;
        });
    },

    renderHeaderStats: (state, p0, p1, t) => {
        // RPS, Setup, etc. phase names
        let phaseKey = Rendering.getPhaseKey(state.phase);

        if (DOM_CACHE.turn) DOM_CACHE.turn.textContent = state.turn_number || state.turn || 1;
        if (DOM_CACHE.phase) DOM_CACHE.phase.textContent = i18n.t(phaseKey);

        if (DOM_CACHE.score) {
            const p0Score = state.players[0].success_lives ? state.players[0].success_lives.length : 0;
            const p1Score = state.players[1].success_lives ? state.players[1].success_lives.length : 0;
            DOM_CACHE.score.textContent = `${p0Score} - ${p1Score}`;
        }

        // Energy and Hearts
        if (DOM_CACHE.headerEnergy && p0) {
            DOM_CACHE.headerEnergy.textContent = `${p0.energy_untapped || 0}/${p0.energy_count || 0}`;
        }

        // Hearts summary
        if (DOM_CACHE.totalHearts && p0) {
            const hearts = p0.total_hearts || [0, 0, 0, 0, 0, 0, 0];
            DOM_CACHE.totalHearts.innerHTML = Rendering.renderHeartsCompact(hearts);
        }

        // Blades summary
        if (DOM_CACHE.totalBlades && p0) {
            const bladesCount = p0.total_blades !== undefined ? p0.total_blades : 0;
            DOM_CACHE.totalBlades.innerHTML = `<span class="stat-item" title="Total Blades">
                <img src="img/texticon/icon_blade.png" class="heart-mini-icon">
                <span class="stat-value">${bladesCount}</span>
             </span>`;
        }
    },

    get_valid_targets: InteractionAdapter.get_valid_targets,

    renderInternal: () => {
        const state = State.data;
        if (!state || !state.players) return;

        const perspectivePlayer = State.perspectivePlayer;
        const currentLang = State.currentLang;
        const t = i18n.getCurrentTranslations();

        // --- Proactive Pre-loading ---
        const assetsToLoad = [];
        state.players.forEach(p => {
            if (p.hand) p.hand.forEach(c => { if (c && c.img) assetsToLoad.push(fixImg(c.img)); });
            if (p.stage) p.stage.forEach(c => { if (c && c.img) assetsToLoad.push(fixImg(c.img)); });
        });
        if (state.legal_actions) {
            state.legal_actions.forEach(a => { if (a && a.img) assetsToLoad.push(fixImg(a.img)); });
        }

        const assetsHash = assetsToLoad.join('|');
        if (State.lastAssetsHash !== assetsHash) {
            if (window.preloadAssets) window.preloadAssets(assetsToLoad);
            State.lastAssetsHash = assetsHash;
        }

        if (State.hotseatMode && state.active_player !== undefined) {
            State.perspectivePlayer = state.active_player;
        }

        const p0 = state.players[State.perspectivePlayer] || state.players[0];
        const p1 = state.players[1 - State.perspectivePlayer] || state.players[1];

        if (p0) state.looked_cards = p0.looked_cards || [];
        if (!p0 || !p1) return;

        // Calculate Valid Targets for Highlighting
        const validTargets = Rendering.get_valid_targets(state);

        // Update UI Headers, Stats, etc. (Logic moved from main.js)
        Rendering.renderHeaderStats(state, p0, p1, t);
        Rendering.renderBoard(state, p0, p1, validTargets);

        let selectedIndices = [];
        if (state.phase === Phase.MULLIGAN_P1 || state.phase === Phase.MULLIGAN_P2) {
            selectedIndices = Array.from(p0.mulligan_selection || []);
        } else {
            if (State.selectedHandIdx !== -1) selectedIndices = [State.selectedHandIdx];
        }

        Rendering.renderCards('my-hand', p0.hand, true, false, selectedIndices, validTargets.myHand, validTargets.hasSelection);
        Rendering.renderCards('opp-hand', p1.hand, false, true, [], validTargets.oppHand, validTargets.hasSelection);
        Rendering.renderPerformanceGuide();
        Rendering.renderLookedCards(validTargets.selection);
        Rendering.renderSelectionModal();
        Rendering.renderRuleLog();
        Rendering.renderActiveEffects(state);
        Rendering.renderActiveEffects(state);
        // Toggle the panel visibility based on content
        const abPanel = document.getElementById('active-abilities-panel');
        const hasContent = (state.triggered_abilities && state.triggered_abilities.length > 0) ||
            (p0.blade_buffs && p0.blade_buffs.some(v => v !== 0)) ||
            (p0.heart_buffs && p0.heart_buffs.some(hb => hb.some(v => v > 0))) ||
            (p1.blade_buffs && p1.blade_buffs.some(v => v !== 0)) ||
            (p1.heart_buffs && p1.heart_buffs.some(hb => hb.some(v => v > 0))) ||
            (p0.cost_reduction !== 0) || (p1.cost_reduction !== 0) ||
            (p0.prevent_baton_touch > 0) || (p1.prevent_baton_touch > 0);

        if (abPanel) abPanel.style.display = hasContent ? 'block' : 'none';
        if (state.game_over) {
            Rendering.renderGameOver(state);
        } else {
            Rendering.renderActions();
        }

        Tooltips.highlightPendingSource();
        Rendering.updateSettingsButtons();
    },

    getPhaseKey: (phase) => {
        const perspectivePlayer = State.perspectivePlayer;
        if (phase === Phase.RPS) return 'rps';
        if (phase === Phase.SETUP) return 'setup';
        if (phase === Phase.MULLIGAN_P1) return (perspectivePlayer === 0) ? 'mulligan_you' : 'mulligan_opp';
        if (phase === Phase.MULLIGAN_P2) return (perspectivePlayer === 1) ? 'mulligan_you' : 'mulligan_opp';
        if (phase === Phase.ACTIVE) return 'active';
        if (phase === Phase.ENERGY) return 'energy';
        if (phase === Phase.DRAW) return 'draw';
        if (phase === Phase.MAIN) return 'main';
        if (phase === Phase.LIVE_SET) return 'live_set';
        if (phase === Phase.PERFORMANCE_P1) return (perspectivePlayer === 0) ? 'perf_p1' : 'perf_p2';
        if (phase === Phase.PERFORMANCE_P2) return (perspectivePlayer === 1) ? 'perf_p1' : 'perf_p2';
        if (phase === Phase.LIVE_RESULT) return 'live_result';
        return 'wait';
    },


    renderBoard: (state, p0, p1, validTargets = { stage: {}, discard: {}, hasSelection: false }) => {
        BoardRenderer.renderBoard(state, p0, p1, validTargets, Rendering.showDiscardModal);
    },

    renderDeckCounts: (p0, p1) => {
        BoardRenderer.renderDeckCounts(p0, p1);
    },

    renderCards: (containerId, cards, clickable = false, mini = false, selectedIndices = [], validActionMap = {}, hasGlobalSelection = false) => {
        CardRenderer.renderCards(containerId, cards, clickable, mini, selectedIndices, validActionMap, hasGlobalSelection);
    },

    renderStage: (containerId, stage, clickable, validActionMap = {}, hasGlobalSelection = false) => {
        CardRenderer.renderStage(containerId, stage, clickable, validActionMap, hasGlobalSelection);
    },

    renderEnergy: (containerId, energy, clickable = false, validActionMap = {}, hasGlobalSelection = false) => {
        BoardRenderer.renderEnergy(containerId, energy, clickable, validActionMap, hasGlobalSelection, State.data);
    },

    renderLiveZone: (containerId, liveCards, visible, validActionMap = {}, hasGlobalSelection = false) => {
        CardRenderer.renderLiveZone(containerId, liveCards, visible, validActionMap, hasGlobalSelection);
    },

    renderDiscardPile: (containerId, discard, playerIdx, validActionMap = {}, hasGlobalSelection = false) => {
        CardRenderer.renderDiscardPile(containerId, discard, playerIdx, validActionMap, hasGlobalSelection, Rendering.showDiscardModal);
    },

    renderActiveEffects: (state, p0, p1) => Logs.renderActiveEffects(state, p0, p1),

    renderRuleLog: (containerId = 'rule-log') => Logs.renderRuleLog(containerId),



    renderActiveAbilities: (containerId, abilities) => Logs.renderActiveAbilities(containerId, abilities),

    renderSelectionModal: () => {
        // Disabled as per user request - all selections are now in the sidebar
        const modal = document.getElementById('selection-modal');
        if (modal) modal.style.display = 'none';
        return;
    },

    renderGameOver: (state) => {
        ActionMenu.renderGameOver(state);
    },

    showDiscardModal: (playerIdx) => {
        console.log("[Rendering] showDiscardModal triggered for player:", playerIdx);
        const state = State.data;
        if (!state || !state.players) return;

        const player = state.players[playerIdx];
        const discard = player.discard || [];

        const modal = document.getElementById('discard-modal');
        const title = document.getElementById('discard-modal-title');
        const container = document.getElementById('discard-modal-cards');

        const isMe = playerIdx === State.perspectivePlayer;
        const count = discard.length;
        title.textContent = isMe ? i18n.t('your_discard_title', { count }) : i18n.t('opp_discard_title', { count });
        container.innerHTML = '';

        if (discard.length === 0) {
            container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; opacity: 0.5; padding: 40px;">${i18n.t('no_cards_discard')}</div>`;
        } else {
            discard.forEach((card) => {
                if (!card) return;
                const div = document.createElement('div');
                div.className = 'card';
                let imgPath = card.img || card.img_path || '';
                div.innerHTML = `<img src="${fixImg(imgPath)}">`;
                const rawText = Tooltips.getEffectiveRawText(card);
                if (rawText) div.setAttribute('data-text', rawText);
                if (card.id !== undefined) div.setAttribute('data-card-id', card.id);
                container.appendChild(div);
            });
        }
        modal.style.display = 'flex';
    },

    showZoneViewer: (playerIdx) => {
        console.log("[Rendering] showZoneViewer triggered for player:", playerIdx);
        const state = State.data;
        if (!state || !state.players) return;

        const player = state.players[playerIdx];
        const modal = document.getElementById('discard-modal'); // Reusing discard modal for now
        const title = document.getElementById('discard-modal-title');
        const container = document.getElementById('discard-modal-cards');

        const isMe = playerIdx === State.perspectivePlayer;
        title.textContent = isMe ? i18n.t('your_viewer_title') : i18n.t('opp_viewer_title');
        container.innerHTML = '';
        container.className = 'zone-viewer-grid'; // Use a different grid if needed

        const addSection = (label, cards, isDeck = false) => {
            if (!cards || cards.length === 0) return;

            const section = document.createElement('div');
            section.className = 'zone-viewer-section';
            section.innerHTML = `<h3>${label} (${cards.length})</h3>`;

            const grid = document.createElement('div');
            grid.className = 'selection-grid';

            // For deck, we want "input order". Since we don't have the original deck,
            // we sort by card ID as a stable substitute for now, or use alphabetic.
            let sortedCards = [...cards];
            if (isDeck) {
                sortedCards.sort((a, b) => (a.id || 0) - (b.id || 0));
            }

            sortedCards.forEach(card => {
                if (!card) return;
                const div = document.createElement('div');
                div.className = 'card card-mini';
                const imgPath = card.img || card.img_path || '';
                div.innerHTML = `<img src="${fixImg(imgPath)}" onerror="this.src='img/texticon/icon_energy.png'">`;

                Tooltips.attachCardData(div, card);
                grid.appendChild(div);
            });

            section.appendChild(grid);
            container.appendChild(section);
        };

        const addEmptySection = (label) => {
            const section = document.createElement('div');
            section.className = 'zone-viewer-section';
            section.innerHTML = `<h3>${label} (0)</h3><div style="opacity:0.5; padding:10px;">${i18n.t('no_cards_zone')}</div>`;
            container.appendChild(section);
        };

        // Deck Sections
        const deck = player.deck_cards || player.deck || player.full_deck || [];
        const energyDeck = player.energy_deck_cards || player.energy_deck || [];

        if (deck.length > 0) addSection(i18n.t('member_deck_rem'), deck, true);
        else addEmptySection(i18n.t('member_deck_rem'));

        if (energyDeck.length > 0) addSection(i18n.t('energy_deck_rem'), energyDeck, true);
        else addEmptySection(i18n.t('energy_deck_rem'));

        addSection(i18n.t('hand'), player.hand);
        addSection(i18n.t('stage'), player.stage);
        addSection(i18n.t('energy'), player.energy ? player.energy.map(e => e.card || e) : []);
        addSection(i18n.t('success_zone'), player.success_lives || player.success_pile);
        addSection(i18n.t('discard_pile'), player.discard);

        modal.style.display = 'flex';
    },

    renderActions: () => {
        ActionMenu.renderActions();
    },

    renderPerformanceGuide: () => PerformanceRenderer.renderPerformanceGuide(Rendering.renderHeartProgress),

    renderSelectionModal: () => {
        const state = State.data;
        const panel = document.getElementById('selection-modal');
        const content = document.getElementById('selection-content');
        if (!panel || !content || !state.pending_choice) return;

        const cards = state.pending_choice.selection_cards || [];
        if (cards.length === 0) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';

        content.innerHTML = cards.map((c, idx) => {
            const div = document.createElement('div');
            div.className = 'selection-card-item card';
            Tooltips.attachCardData(div, c);
            const imgPath = c.img || c.img_path || '';
            div.innerHTML = `<img src="${fixImg(imgPath)}" class="selection-card-img"><div class="selection-card-name">${c.name}</div>`;
            return div.outerHTML;
        }).join('');
    },

    renderRuleLog: () => Logs.renderRuleLog('rule-log'),

    renderActiveEffects: (state) => Logs.renderActiveEffects(state),

    renderActiveAbilities: (containerId, abilities) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = abilities.map(a => {
            const card = Tooltips.findCardById(a.source_card_id);
            const name = card ? card.name : i18n.t('card');
            const dataText = a.description || (card ? Tooltips.getEffectiveRawText(card) : '');

            return `<div class="active-ability-item" data-card-id="${a.source_card_id}" data-text="${dataText.replace(/"/g, '&quot;')}">
                <span class="ability-source">${name}:</span> ${a.description}
            </div>`;
        }).join('');
    },

    renderLookedCards: (selectionTargets = {}) => {
        CardRenderer.renderLookedCards(selectionTargets);
    },

    renderPerformanceResult: (results = null) => PerformanceRenderer.renderPerformanceResult(results),
    renderHeartProgress: (filled, required) => PerformanceRenderer.renderHeartProgress(filled, required),

    renderHeartsCompact: (hearts) => PerformanceRenderer.renderHeartsCompact(hearts),
    renderBladeHeartsCompact: (hearts) => PerformanceRenderer.renderHeartsCompact(hearts),
    renderBladesCompact: (blades) => PerformanceRenderer.renderBladesCompact(blades),
    renderTotalHeartsBreakdown: (hearts) => PerformanceRenderer.renderHeartsCompact(hearts),

    renderModifiers: () => { /* Placeholder for future implementation */ },
    renderGameData: () => { /* Placeholder for future implementation */ },

    updateSettingsButtons: () => {
        const liveWatchBtn = document.getElementById('live-watch-btn');
        if (liveWatchBtn) {
            const label = i18n.t('live_watch');
            const stateLabel = State.isLiveWatchOn ? i18n.t('on') : i18n.t('off');
            liveWatchBtn.textContent = `${label}: ${stateLabel}`;
        }

        const hotseatBtn = document.getElementById('pvp-btn');
        if (hotseatBtn) {
            const label = i18n.t('shared_screen');
            const stateLabel = State.hotseatMode ? i18n.t('on') : i18n.t('off');
            hotseatBtn.textContent = `${label}: ${stateLabel}`;
        }

        const perspectiveBtn = document.getElementById('switch-btn');
        if (perspectiveBtn) {
            const label = i18n.t('view_persp');
            perspectiveBtn.textContent = `${label}: P${State.perspectivePlayer + 1}`;
        }

        const friendlyBtn = document.getElementById('friendly-abilities-btn');
        if (friendlyBtn) {
            const label = i18n.t('friendly_abilities');
            const stateLabel = State.showFriendlyAbilities ? i18n.t('on') : i18n.t('off');
            friendlyBtn.textContent = `${label}: ${stateLabel}`;
        }

        const langBtn = document.getElementById('lang-btn');
        if (langBtn) {
            langBtn.textContent = State.currentLang === 'jp' ? 'English' : '日本語';
        }
    },

    showPerfTab: (tab) => PerformanceRenderer.showPerfTab(tab),

    renderTurnHistory: () => PerformanceRenderer.renderTurnHistory(Rendering.getPhaseKey)
};

// Global Highlighting Logic for Bidirectional Linkage
window.highlightActionBtn = (actionId, active) => {
    const btns = document.querySelectorAll(`.action-btn[data-action-id="${actionId}"]`);
    btns.forEach(btn => {
        if (active) btn.classList.add('hover-highlight');
        else btn.classList.remove('hover-highlight');
    });
};

window.highlightActionTarget = (actionId, active) => {
    const targets = document.querySelectorAll(`[data-action-id="${actionId}"]:not(.action-btn)`);
    targets.forEach(target => {
        if (active) target.classList.add('hover-highlight');
        else target.classList.remove('hover-highlight');
    });
};
