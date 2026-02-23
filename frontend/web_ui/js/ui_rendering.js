/**
 * UI Rendering Module
 * Handles all board, card, and performance result rendering.
 */
import { State } from './state.js';
import { Phase, fixImg } from './constants.js';
import { translations } from './translations_data.js';
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
        if (DOM_CACHE.phase) DOM_CACHE.phase.textContent = t[phaseKey] || state.phase;

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
        const t = translations[currentLang];

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
        Rendering.renderLiveZone('my-live', p0.live_zone, p0.live_zone_revealed, validTargets.myLive, validTargets.hasSelection);
        Rendering.renderPerformanceGuide();
        Rendering.renderLookedCards();
        Rendering.renderSelectionModal();
        Rendering.renderRuleLog();
        Rendering.renderActiveEffects(state, p0, p1, t);
        Rendering.renderActiveAbilities('active-abilities-list', state.triggered_abilities || []);
        // Toggle the panel visibility based on content
        const abPanel = document.getElementById('active-abilities-panel');
        if (abPanel) abPanel.style.display = (state.triggered_abilities && state.triggered_abilities.length > 0) ? 'block' : 'none';
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
        Rendering.renderStage('my-stage', p0.stage, true, validTargets.myStage, validTargets.hasSelection);
        Rendering.renderStage('opp-stage', p1.stage, true, validTargets.oppStage, validTargets.hasSelection);
        Rendering.renderLiveZone('my-live', p0.live_zone, true, validTargets.myLive, validTargets.hasSelection);
        Rendering.renderLiveZone('opp-live', p1.live_zone, true, validTargets.oppLive, validTargets.hasSelection);
        Rendering.renderEnergy('my-energy', p0.energy, true, validTargets.myEnergy, validTargets.hasSelection);
        Rendering.renderEnergy('opp-energy', p1.energy, true, validTargets.oppEnergy, validTargets.hasSelection);

        // Discard Pile (Visual Mini-Card)
        Rendering.renderDiscardPile('my-discard-visual', p0.discard, 0, validTargets.discard, validTargets.hasSelection);
        Rendering.renderDiscardPile('opp-discard-visual', p1.discard, 1);

        // Success Piles (Mini, Portrait)
        Rendering.renderCards('my-success', p0.success_pile || p0.success_lives, true, true);
        Rendering.renderCards('opp-success', p1.success_pile || p1.success_lives, false, true);

        Rendering.renderDeckCounts(p0, p1);
    },

    renderDeckCounts: (p0, p1) => {
        const updateCount = (id, count) => {
            const el = document.getElementById(id);
            if (el) el.textContent = count !== undefined ? count : 0;
        };

        // Main Decks
        updateCount('my-deck-count', p0.deck_count);
        updateCount('opp-deck-count', p1.deck_count);

        // Energy Decks
        updateCount('my-energy-deck-count', p0.energy_deck_count);
        updateCount('opp-energy-deck-count', p1.energy_deck_count);

        // Discard Counts
        updateCount('my-discard-count', p0.discard ? p0.discard.length : 0);
        updateCount('opp-discard-count', p1.discard ? p1.discard.length : 0);
    },

    renderCards: (containerId, cards, clickable = false, mini = false, selectedIndices = [], validActionMap = {}, hasGlobalSelection = false) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        if (!cards) return;

        const state = State.data;
        cards.forEach((card, idx) => {
            const div = document.createElement('div');

            // Handle placeholders (null cards from engine tombstones)
            if (card === null) {
                div.className = 'card placeholder' + (mini ? ' card-mini' : '');
                div.style.visibility = 'hidden';
                div.style.pointerEvents = 'none';
                el.appendChild(div);
                return;
            }

            const isSelected = selectedIndices.includes(idx);

            // Validation Logic
            const actionId = validActionMap[idx];
            const isValid = actionId !== undefined;

            let highlightClass = '';
            if (isSelected) {
                highlightClass = (state.phase === Phase.MULLIGAN_P1 || state.phase === Phase.MULLIGAN_P2) ? ' mulligan-selected' : ' selected';
            }
            if (card.is_new) highlightClass += ' new-card';
            if (isValid) highlightClass += ' valid-target';

            const isHidden = card.hidden || card.id === -2;
            const isLive = card.type === 'live';

            // Apply rotation logic based on zone context and card type
            let rotationClass = '';
            if (isLive) {
                // Live Cards (Naturally Landscape)
                if (containerId.includes('hand')) {
                    // Stay horizontal in hand, or we could rotate to portrait. 
                    // User requested Hand cards stop overlapping, and "already in correct orientation" for live zone.
                    // For hand, we keep them native (landscape) but sized to fit.
                }
            } else {
                // Member Cards (Naturally Portrait)
                if (containerId.includes('live') || containerId.includes('success')) {
                    // Member entering Landscape zone rotates 90deg to Lay Down
                    rotationClass = ' rotated-90';
                }
            }

            div.className = 'card' + (isHidden ? ' hidden' : '') +
                (isLive ? ' type-live' : '') +
                (mini ? ' card-mini' : '') + rotationClass + highlightClass;

            div.id = `${containerId}-card-${idx}`;
            div.setAttribute('data-card-id', card.id);

            if (!isHidden) {
                let imgPath = card.img || card.img_path || '';
                const imgHtml = imgPath ? `<img src="${fixImg(imgPath)}" draggable="false" onerror="this.style.display='none'">` : '';

                div.innerHTML = `${imgHtml}${card.cost !== undefined ? `<span class="cost">${card.cost}</span>` : ''}<div class="name">${card.name || ''}</div>`;
            } else {
                div.classList.add('card-back');
                div.innerHTML = ''; // Ensure no "undefined" text
            }

            if (clickable) {
                if (isValid || !hasGlobalSelection) {
                    div.style.cursor = 'pointer';
                    div.onclick = () => {
                        if (isValid && window.doAction) {
                            window.doAction(actionId);
                        } else if (window.playCard) {
                            window.playCard(idx);
                        }
                    };
                } else {
                    div.onclick = null;
                }
            }
            el.appendChild(div);

            if (!card.hidden) {
                const rawText = Tooltips.getEffectiveRawText(card);
                if (rawText) div.setAttribute('data-text', rawText);
                if (card.id !== undefined) div.setAttribute('data-card-id', card.id);
            }
        });
    },

    renderStage: (containerId, stage, clickable, validActionMap = {}, hasGlobalSelection = false) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const slot = stage[i];
            const area = document.createElement('div');
            area.className = 'member-area board-slot-container';

            // Validation
            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;

            let highlightClass = '';
            if (isValid) highlightClass += ' valid-target';

            const slotDiv = document.createElement('div');
            const isTapped = slot && typeof slot === 'object' && slot.tapped;
            slotDiv.className = 'member-slot' + (slot && slot !== -1 ? ' filled' : '') + (isTapped ? ' tapped' : '') + highlightClass;
            slotDiv.id = `${containerId}-slot-${i}`;

            if (slot && typeof slot === 'object' && slot.id !== undefined && slot.id !== -1) {
                let imgPath = slot.img || slot.img_path || '';
                let modifiersHtml = '';
                if (slot.modifiers && slot.modifiers.length > 0) {
                    modifiersHtml = `<div class="member-modifiers">${slot.modifiers.map(m => `<div class="modifier-tag ${m.type}">${m.label || (m.type === 'heart' ? '+' : m.value)}</div>`).join('')}</div>`;
                }

                slotDiv.innerHTML = imgPath ? `<img src="${fixImg(imgPath)}">${modifiersHtml}` : modifiersHtml;

                const rawText = Tooltips.getEffectiveRawText(slot);
                if (rawText) {
                    slotDiv.setAttribute('data-text', rawText);
                    area.setAttribute('data-text', rawText);
                }
                slotDiv.setAttribute('data-card-id', slot.id);
                area.setAttribute('data-card-id', slot.id);
            }

            area.appendChild(slotDiv);
            el.appendChild(area);

            if (clickable) {
                if (isValid || !hasGlobalSelection) {
                    area.onclick = () => {
                        if (isValid && window.doAction) {
                            window.doAction(actionId);
                        } else if (window.onStageSlotClick) {
                            window.onStageSlotClick(i);
                        }
                    };
                    // Also clickable on slotDiv just in case
                    slotDiv.onclick = area.onclick;
                    area.style.cursor = 'pointer';
                } else {
                    area.onclick = null;
                }
            }
        }
    },

    renderEnergy: (containerId, energy, clickable = false, validActionMap = {}, hasGlobalSelection = false) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        if (!energy) return;

        energy.forEach((e, i) => {
            const div = document.createElement('div');

            // Validation
            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;
            let highlightClass = isValid ? ' valid-target' : '';

            div.className = 'energy-pip' + (e.tapped ? ' tapped' : '') + highlightClass;
            div.id = `${containerId}-slot-${i}`;

            let imgPath = e.img || e.img_path || 'img/texticon/icon_energy.png';
            div.innerHTML = `
                <img src="${fixImg(imgPath)}" onerror="this.src='img/texticon/icon_energy.png'">
                <div class="energy-num">${i + 1}</div>
            `;

            if (e.card) {
                const rawText = Tooltips.getEffectiveRawText(e.card);
                if (rawText) div.setAttribute('data-text', rawText);
                div.setAttribute('data-card-id', e.card.id);
            }

            if (clickable && isValid) {
                div.style.cursor = 'pointer';
                div.onclick = () => { if (window.doAction) window.doAction(actionId); };
            }

            el.appendChild(div);
        });
    },

    renderLiveZone: (containerId, liveCards, visible, validActionMap = {}, hasGlobalSelection = false) => {
        const state = State.data;
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const card = liveCards[i];

            // Validation
            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;
            let highlightClass = '';
            if (isValid) highlightClass += ' valid-target';

            const slot = document.createElement('div');
            const isLiveCard = card && card.type === 'live';

            slot.className = 'card card-mini' + (card ? (isLiveCard ? ' type-live' : '') : ' empty') + highlightClass;
            slot.id = `${containerId}-slot-${i}`;
            if (card && typeof card === 'object' && card.id !== undefined && card.id !== -1) {
                const isPerfLegal = card.is_perf_legal;
                const imgPath = card.img || card.img_path || '';
                slot.innerHTML = `
                    <div class="live-card-inner ${isPerfLegal ? 'perf-legal' : ''}">
                        ${imgPath ? `<img src="${fixImg(imgPath)}">` : ''}
                        <div class="cost">${card.score || (card.cost !== undefined ? card.cost : 0)}</div>
                        ${isPerfLegal ? '<div class="perf-badge">LIVE!</div>' : ''}
                    </div>
                `;
                const rawText = Tooltips.getEffectiveRawText(card);
                if (rawText) slot.setAttribute('data-text', rawText);
                slot.setAttribute('data-card-id', card.id);

                if (isValid) {
                    slot.style.cursor = 'pointer';
                    slot.onclick = () => { if (window.doAction) window.doAction(actionId); };
                } else if (isPerfLegal) {
                    // Fallback highlight for performance selection if validActionMap didn't catch it
                    // Search for 600+ or 900+ IDs in the top-level legal_actions for this card
                    const fallbackId = state.legal_actions.find(a => (a.id === 600 + i || a.id === 900 + i || (a.metadata && a.metadata.slot_idx === i && a.metadata.category === 'LIVE')))?.id;
                    if (fallbackId !== undefined) {
                        slot.style.cursor = 'pointer';
                        slot.onclick = () => { if (window.doAction) window.doAction(fallbackId); };
                    } else {
                        slot.onclick = null;
                    }
                } else {
                    slot.onclick = null;
                }
            } else {
                slot.innerHTML = ``;
            }
            el.appendChild(slot);
        }
    },

    renderDiscardPile: (containerId, discard, playerIdx, validActionMap = {}, hasGlobalSelection = false) => {
        const el = document.getElementById(containerId);
        if (!el) return;

        // Validation for the PILE itself
        const actionId = validActionMap && validActionMap['all'];
        const isValid = actionId !== undefined;
        let highlightClass = isValid ? ' valid-target' : '';

        el.innerHTML = '';
        el.className = 'discard-pile-visual ' + highlightClass;

        if (!discard || discard.length === 0) {
            el.classList.add('empty');
            el.innerHTML = '<span style="opacity:0.3; font-size:0.8rem;">Discard</span>';
        } else {
            // Show up to 3 cards in a stack (Visual representation)
            const showCount = Math.min(3, discard.length);
            for (let i = 0; i < showCount; i++) {
                const card = discard[discard.length - 1 - i];
                const div = document.createElement('div');
                div.className = 'card card-mini';
                div.innerHTML = `<img src="${fixImg(card.img || '')}">`;
                div.style.transform = `translate(${i * 2}px, ${i * 2}px)`;
                div.style.zIndex = 10 - i;

                // Add tooltip metadata to mini-cards
                if (card.id !== undefined) {
                    div.setAttribute('data-card-id', card.id);
                    const rawText = Tooltips.getEffectiveRawText(card);
                    if (rawText) div.setAttribute('data-text', rawText);
                }

                el.appendChild(div);
            }
        }

        if (isValid) {
            el.style.cursor = 'pointer';
            el.onclick = (e) => {
                e.stopPropagation();
                if (window.doAction) window.doAction(actionId);
            };
        } else if (!hasGlobalSelection && discard && discard.length > 0) {
            el.style.cursor = 'pointer';
            el.onclick = () => Rendering.showDiscardModal(playerIdx);
        } else {
            el.onclick = null;
        }
    },

    renderActiveEffects: (state, p0, p1, t) => Logs.renderActiveEffects(state, p0, p1, t),

    renderRuleLog: (containerId = 'rule-log') => Logs.renderRuleLog(containerId),

    renderActiveAbilities: (containerId, abilities) => Logs.renderActiveAbilities(containerId, abilities),

    renderSelectionModal: () => {
        // Disabled as per user request - all selections are now in the sidebar
        const modal = document.getElementById('selection-modal');
        if (modal) modal.style.display = 'none';
        return;
    },

    renderGameOver: (state) => {
        const actionsDiv = document.getElementById('actions');
        if (actionsDiv) {
            const winnerName = state.winner === State.perspectivePlayer ? "YOU" : `Player ${state.winner + 1}`;
            actionsDiv.innerHTML = `
                <div class="game-over-banner">
                    <h2>GAME OVER</h2>
                    <div class="winner-announcement">Winner: ${winnerName}</div>
                    <button class="btn btn-primary" onclick="location.reload()">New Game</button>
                </div>
            `;
        }
    },

    showDiscardModal: (playerIdx) => {
        console.log("[Rendering] showDiscardModal triggered for player:", playerIdx);
        const state = State.data;
        if (!state || !state.players) {
            console.error("[Rendering] showDiscardModal: No state data found!");
            return;
        }
        const player = state.players[playerIdx];
        console.log("[Rendering] player discard length:", player.discard ? player.discard.length : 0);
        const discard = player.discard || [];

        const modal = document.getElementById('discard-modal');
        const title = document.getElementById('discard-modal-title');
        const container = document.getElementById('discard-modal-cards');

        if (!modal || !container) return;

        title.textContent = (playerIdx === State.perspectivePlayer ? "Your" : "Opponent's") + " Discard Pile (" + discard.length + ")";
        container.innerHTML = '';

        if (discard.length === 0) {
            container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; opacity: 0.5; padding: 40px;">No cards in discard pile.</div>';
        } else {
            discard.forEach((card, idx) => {
                if (!card) return; // Added null check
                const div = document.createElement('div');
                div.className = 'card'; // Original class name
                let imgPath = card.img || card.img_path || '';
                div.innerHTML = `<img src="${fixImg(imgPath)}">`;

                // Add tooltip metadata
                const rawText = Tooltips.getEffectiveRawText(card);
                if (rawText) div.setAttribute('data-text', rawText);
                if (card.id !== undefined) div.setAttribute('data-card-id', card.id);

                container.appendChild(div);
            });
        }

        modal.style.display = 'flex';
    },

    renderActions: () => {
        const state = State.data;
        const actionsDiv = document.getElementById('actions');
        if (!state || !actionsDiv || state.game_over) return;

        const currentLang = State.currentLang;
        const t = translations[currentLang];
        const perspectivePlayer = State.perspectivePlayer;
        const mobileActionBar = document.getElementById('mobile-action-bar');

        if (mobileActionBar) mobileActionBar.innerHTML = '';
        actionsDiv.innerHTML = '';

        // Helper for consistent action labels
        const getActionLabel = (a, isMini = false) => {
            if (a.id === 0 && state.pending_choice) {
                if (state.phase === Phase.MulliganP1 || state.phase === Phase.MulliganP2) {
                    return currentLang === 'jp' ? '完了' : 'Done';
                }
                return currentLang === 'jp' ? 'パス / いいえ' : 'Pass / No';
            }
            const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;
            const heartIcon = `<img src="img/texticon/icon_heart.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;

            let cost = a.metadata?.cost ?? a.cost ?? a.base_cost ?? null;
            const isBaton = (a.name && (a.name.includes('Baton') || a.name.includes('バトン')));
            let name = a.metadata?.name ?? a.name ?? "";


            // User Request: If name is "Action 30X", try to resolve the card name
            // But ONLY if it's not an ability-related action (which might share ID indices)
            if (name.match(/^Action\s+30\d$/) && a.metadata?.category !== 'ABILITY') {
                const liveIdx = parseInt(name.replace("Action 30", ""), 10);
                const state = State.data;
                const liveCard = state?.live_zone && state.live_zone[liveIdx];
                if (liveCard && liveCard.name) {
                    name = liveCard.name;
                    // Add heart icon for live cards
                    return `<div class="action-title">${heartIcon} ${name}</div>`;
                }
            }

            // Clean name: remove verbose bracketed prefixes
            name = name.replace(/[【\[].*?[】\]]/g, "").trim();

            if (isMini) {
                // For PLAY actions, show just the cost number
                if (a.type === 'PLAY') return `<span>${cost !== null ? cost : 0}</span>${isBaton ? ' [B]' : ''}`;
                // For MULLIGAN, show the card name (truncated if needed)
                if (a.type === 'MULLIGAN') {
                    const shortName = name.length > 10 ? name.substring(0, 10) + '…' : name;
                    return `<span style="font-size:0.65rem">${shortName || '?'}</span>`;
                }
                // Default mini: energy + cost
                let label = `${energyIcon}${cost !== null ? cost : 0}`;
                if (isBaton) label += ' [B]';
                return Tooltips.enrichAbilityText(label);
            } else {
                let displayName = name;
                if (a.metadata?.secondary_slot_idx !== undefined && a.metadata?.areas_desc) {
                    displayName = (currentLang === 'jp')
                        ? a.metadata.areas_desc.replace(' & ', '＆')
                        : a.metadata.areas_desc;
                }

                // Enrich the name with icons/highlights
                displayName = Tooltips.enrichAbilityText(displayName);

                let label = `<div class="action-title" style="${(displayName.includes('&') || displayName.includes('＆')) ? 'font-size:0.85em;' : ''}">${displayName}</div>`;
                if (cost !== null) label += `<div class="action-cost">${energyIcon}${cost}</div>`;
                if (isBaton && a.metadata?.secondary_slot_idx === undefined) label += ' [B]';
                return label;
            }
        };

        const getHighlightTargets = (a) => {
            const state = State.data;
            if (!state) return [];
            const m = a.metadata || {};
            const hIdx = a.hand_idx ?? m.hand_idx;
            const sIdx = a.slot_idx ?? m.slot_idx;
            const srcIdx = a.source_idx ?? m.source_idx;
            const targetSlotIdx = m.target_slot_idx ?? m.secondary_slot_idx;
            const tPlayer = m.target_player !== undefined ? m.target_player : perspectivePlayer;
            const isMe = (tPlayer === perspectivePlayer);
            const playerKey = isMe ? 'p0' : 'p1';

            const targets = [];
            if (hIdx !== undefined) targets.push(`${playerKey}-hand-card-${hIdx}`);
            if (sIdx !== undefined) {
                if (a.type !== 'PLAY' && a.type !== 'LIVE_SET' && m.category !== 'LIVE') {
                    targets.push(`${playerKey}-stage-slot-${sIdx}`);
                }
            }
            if (srcIdx !== undefined) targets.push(`${playerKey}-stage-slot-${srcIdx}`);
            if (targetSlotIdx !== undefined) targets.push(`${playerKey}-stage-slot-${targetSlotIdx}`);
            if (a.type === 'LIVE_PERFORM' || m.category === 'LIVE') {
                const liveIdx = sIdx !== undefined ? sIdx : (a.id >= 600 && a.id < 610 ? a.id - 600 : (a.id >= 900 && a.id <= 902 ? a.id - 900 : undefined));
                if (liveIdx !== undefined) targets.push(`${playerKey}-live-zone-slot-${liveIdx}`);
            }
            return targets;
        };


        // Unified Button Creator to reduce repeated code
        const createActionButton = (a, isMini = false, extraClass = '') => {
            const btn = document.createElement('button');
            btn.className = `action-btn ${isMini ? 'mini' : ''} ${extraClass}`.trim();
            if (a.id !== undefined) btn.setAttribute('data-action-id', a.id);

            // Standardized Tooltip Data: Always try to attach source_card_id for tooltips
            if (a.source_card_id !== undefined) {
                btn.setAttribute('data-card-id', a.source_card_id);
            }

            if (a.raw_text || a.text) btn.dataset.text = a.raw_text || a.text;
            btn.innerHTML = getActionLabel(a, isMini);
            btn.onclick = () => { if (window.doAction && a.id !== undefined) window.doAction(a.id); };

            // Hover Highlighting
            btn.onmouseenter = () => {
                const targets = getHighlightTargets(a);
                targets.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.classList.add('action-highlight');
                });
            };
            btn.onmouseleave = () => {
                const targets = getHighlightTargets(a);
                targets.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.classList.remove('action-highlight');
                });
            };

            return btn;
        };


        // RPS Phase Handler
        if (state.phase === Phase.RPS) {
            const rpsDiv = document.createElement('div');
            rpsDiv.className = 'rps-selector';
            rpsDiv.style.textAlign = 'center';
            rpsDiv.style.padding = '15px';
            rpsDiv.style.background = 'rgba(255, 255, 255, 0.05)';
            rpsDiv.style.borderRadius = '12px';
            rpsDiv.style.marginBottom = '20px';

            const title = currentLang === 'en' ? 'Choose Your Sign' : '手を選んでください';
            rpsDiv.innerHTML = `<h3 style="margin-top:0; color:var(--accent-gold);">${title}</h3>`;

            const btnContainer = document.createElement('div');
            btnContainer.style.display = 'flex';
            btnContainer.style.flexDirection = 'column';
            btnContainer.style.alignItems = 'center';
            btnContainer.style.gap = '10px';

            const baseId = (perspectivePlayer === 1) ? 11000 : 10000;
            const signs = [
                { id: baseId + 0, name: 'Rock', jp: 'グー' },
                { id: baseId + 1, name: 'Paper', jp: 'パー' },
                { id: baseId + 2, name: 'Scissors', jp: 'チョキ' }
            ];

            signs.forEach(sign => {
                const hasAction = state.legal_actions && state.legal_actions.some(a => a.id === sign.id);
                const a = { id: sign.id, name: currentLang === 'en' ? sign.name : sign.jp };
                const btn = createActionButton(a, false, 'rps-btn');
                btn.style.width = '120px';
                btn.style.opacity = hasAction ? '1' : '0.4';
                btn.style.pointerEvents = hasAction ? 'auto' : 'none';
                btnContainer.appendChild(btn);
            });

            rpsDiv.appendChild(btnContainer);
            actionsDiv.appendChild(rpsDiv);
            return;
        }

        // Choice Indicator & Inline Selection
        if (state.pending_choice) {
            const choice = state.pending_choice;
            const choiceDiv = document.createElement('div');
            choiceDiv.className = 'pending-choice-indicator';

            const opcode = choice.opcode || (state.legal_actions && state.legal_actions[0] && state.legal_actions[0].metadata && state.legal_actions[0].metadata.opcode);
            let headerColor = 'var(--accent-gold)';
            if (opcode === 58) headerColor = '#ff4d4d';
            else if (opcode === 15 || opcode === 17 || opcode === 63) headerColor = '#4da6ff';
            else if (opcode === 45) headerColor = '#ffcc00';
            else if (opcode === 41 || opcode === 74) headerColor = '#9966ff';

            choiceDiv.style.marginBottom = '15px';
            choiceDiv.style.padding = '12px';
            choiceDiv.style.background = 'rgba(255,255,255,0.05)';
            choiceDiv.style.borderRadius = '10px';
            choiceDiv.style.borderLeft = `4px solid ${headerColor}`;

            const title = choice.title || choice.description || (currentLang === 'jp' ? '選択してください' : 'Please Select');
            let content = `<div style="font-weight:bold; color:${headerColor}; margin-bottom: 10px; font-size: 1.1rem;">${title}</div>`;
            if (choice.text && choice.text !== title) {
                content += `<div style="font-size: 0.9rem; margin-bottom: 10px; opacity: 0.8; line-height: 1.4;">${choice.text}</div>`;
            }
            choiceDiv.innerHTML = content;

            if (choice.options && choice.options.length > 0) {
                const optContainer = document.createElement('div');
                optContainer.className = 'action-list';
                optContainer.style.maxHeight = '300px';
                optContainer.style.overflowY = 'auto';

                choice.options.forEach((opt, idx) => {
                    const a = {
                        id: choice.actions[idx],
                        source_card_id: choice.source_card_id, // Pass source card to options for tooltips
                        name: opt.name || opt.text || `Option ${idx + 1}`,
                        text: opt.text
                    };
                    const btn = createActionButton(a, false, 'confirm');
                    btn.style.width = '100%';
                    optContainer.appendChild(btn);
                });
                choiceDiv.appendChild(optContainer);
            }
            actionsDiv.appendChild(choiceDiv);
            return;
        }

        if (state.is_ai_thinking) {
            const aiDiv = document.createElement('div');
            aiDiv.className = 'ai-thinking-indicator';
            aiDiv.innerHTML = `<div style="font-weight:bold; color:#0096ff; padding:10px; border-left:4px solid #0096ff; background:rgba(0,150,255,0.1); border-radius:8px;">${state.ai_status || 'AI is thinking...'}</div>`;
            actionsDiv.appendChild(aiDiv);
        }

        if (!state.legal_actions || state.legal_actions.length === 0) {
            actionsDiv.innerHTML = `<div class="no-actions">${t['wait'] || 'Waiting...'}</div>`;
            return;
        }

        const listDiv = document.createElement('div');
        listDiv.className = 'action-list';
        actionsDiv.appendChild(listDiv);

        // Grouping Actions — ONLY positional for MULLIGAN and PLAY
        const playActionsByHand = {};
        const mulliganActions = {};
        const abilityActions = [];
        const systemActions = [];
        const otherActions = [];

        state.legal_actions.forEach(a => {
            const category = a.metadata?.category || a.type;
            const hIdx = a.metadata?.hand_idx ?? a.hand_idx;
            const sIdx = a.metadata?.slot_idx ?? a.slot_idx;

            // Resolve source_card_id for tooltips if missing
            if (a.source_card_id === undefined) {
                if (hIdx !== undefined) {
                    const card = state.players[perspectivePlayer]?.hand[hIdx];
                    if (card) a.source_card_id = card.id;
                } else if (category === 'ABILITY' && sIdx !== undefined) {
                    const card = state.players[perspectivePlayer]?.stage[sIdx];
                    if (card) a.source_card_id = card.id;
                }
            }

            if (a.id === 0 || a.type === 'SYSTEM' || a.id < 10 || a.name?.includes('End') || a.name?.includes('終了')) {
                systemActions.push(a);
            } else if (category === 'PLAY' && hIdx !== undefined) {
                if (!playActionsByHand[hIdx]) playActionsByHand[hIdx] = [];
                playActionsByHand[hIdx].push(a);
            } else if (a.type === 'MULLIGAN' && hIdx !== undefined) {
                if (!mulliganActions[hIdx]) mulliganActions[hIdx] = [];
                mulliganActions[hIdx].push(a);
            } else if (category === 'ABILITY') {
                abilityActions.push(a);
            } else {
                otherActions.push(a);
            }
        });

        const addHeader = (text, color) => {
            const header = document.createElement('div');
            header.className = 'category-header';
            header.style.color = color || 'rgba(255,255,255,0.4)';
            header.innerText = text;
            listDiv.appendChild(header);
        };

        // 1. SYSTEM (Pass, Confirm)
        if (systemActions.length > 0) {
            addHeader(currentLang === 'jp' ? 'システム' : 'SYSTEM');
            systemActions.forEach(a => listDiv.appendChild(createActionButton(a, false, a.id === 0 ? 'confirm system' : 'system')));
        }

        // 2. ABILITIES
        if (abilityActions.length > 0) {
            addHeader(currentLang === 'jp' ? 'アビリティ' : 'ABILITIES', '#9966ff');
            abilityActions.forEach(a => listDiv.appendChild(createActionButton(a)));
        }

        // 3. MULLIGAN (Hand Grid with stable positions)
        const perspectivePlayerHand = state.players[perspectivePlayer]?.hand || [];
        if (Object.keys(mulliganActions).length > 0) {
            addHeader(currentLang === 'jp' ? 'マリガン' : 'MULLIGAN', 'var(--accent-pink)');

            perspectivePlayerHand.forEach((_, idx) => {
                const actions = mulliganActions[idx] || [];
                if (actions.length > 0) {
                    actions.forEach(a => listDiv.appendChild(createActionButton(a)));
                } else {
                    // Invisible placeholder keeps layout stable
                    const spacer = document.createElement('button');
                    spacer.className = 'action-btn';
                    spacer.style.visibility = 'hidden';
                    listDiv.appendChild(spacer);
                }
            });
        }

        // 4. PLAY MEMBER (Grouped by hand card, 3-slot sub-grid)
        if (Object.keys(playActionsByHand).length > 0) {
            addHeader(currentLang === 'jp' ? 'メンバー登場' : 'PLAY MEMBER', 'var(--accent-gold)');
            Object.keys(playActionsByHand).sort((a, b) => parseInt(a) - parseInt(b)).forEach(hIdx => {
                const actions = playActionsByHand[hIdx];
                const firstA = actions[0];
                const groupDiv = document.createElement('div');
                groupDiv.className = 'action-group-card';

                const header = document.createElement('div');
                header.className = 'action-group-header';
                const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin-left: 5px;">`;
                const displayCost = firstA.metadata?.cost ?? firstA.cost ?? firstA.base_cost ?? 0;
                let cleanName = (firstA.metadata?.name ?? firstA.name ?? "").replace(/[【\[].*?[】\]]/g, "").replace(/\(.*?\)/g, "").trim();
                header.innerHTML = `<span>${cleanName}</span> <span class="header-base-cost">${energyIcon}${displayCost}</span>`;
                groupDiv.appendChild(header);

                const btnsDiv = document.createElement('div');
                btnsDiv.className = 'action-group-buttons grid-3';
                for (let slotIdx = 0; slotIdx < 3; slotIdx++) {
                    const a = actions.find(act => (act.slot_idx === slotIdx || act.metadata?.slot_idx === slotIdx) && act.metadata?.secondary_slot_idx === undefined);
                    if (a) {
                        btnsDiv.appendChild(createActionButton(a, true));
                    } else {
                        const spacer = document.createElement('div');
                        spacer.style.visibility = 'hidden';
                        spacer.style.minHeight = '36px';
                        btnsDiv.appendChild(spacer);
                    }
                }
                groupDiv.appendChild(btnsDiv);

                const doubleActions = actions.filter(act => act.metadata?.secondary_slot_idx !== undefined);
                if (doubleActions.length > 0) {
                    // Group double actions by unique pair (sorted indices)
                    const pairs = {};
                    doubleActions.forEach(a => {
                        const s1 = a.metadata.slot_idx;
                        const s2 = a.metadata.secondary_slot_idx;
                        const key = [s1, s2].sort().join('-');
                        if (!pairs[key]) pairs[key] = [];
                        pairs[key].push(a);
                    });

                    Object.values(pairs).forEach(pairActions => {
                        const doubleDiv = document.createElement('div');
                        doubleDiv.className = 'action-group-buttons double-baton-row grid-3';

                        // Show buttons in their actual target columns
                        const pairSlots = new Set();
                        pairActions.forEach(a => pairSlots.add(a.metadata.slot_idx));
                        pairActions.forEach(a => pairSlots.add(a.metadata.secondary_slot_idx));

                        for (let i = 0; i < 3; i++) {
                            const a = pairActions.find(act => act.metadata.slot_idx === i);
                            if (a) {
                                const btn = createActionButton(a, true, 'double-baton-btn');
                                btn.style.width = '100%';
                                doubleDiv.appendChild(btn);
                            } else if (pairSlots.has(i)) {
                                // Slot is part of the pair but this specific action doesn't target it
                                // (e.g. the other half of the pair's choice)
                                const spacer = document.createElement('div');
                                spacer.className = 'pair-spacer';
                                spacer.innerText = currentLang === 'jp' ? '間' : 'GAP';
                                doubleDiv.appendChild(spacer);
                            } else {
                                // Slot is not part of this pair at all
                                const spacer = document.createElement('div');
                                spacer.style.visibility = 'hidden';
                                doubleDiv.appendChild(spacer);
                            }
                        }
                        groupDiv.appendChild(doubleDiv);
                    });
                }

                listDiv.appendChild(groupDiv);
            });
        }

        // 5. OTHER ACTIONS (Choices, Selects, Responses — full-size buttons)
        if (otherActions.length > 0) {
            addHeader(currentLang === 'jp' ? 'アクション' : 'ACTIONS');
            otherActions.forEach(a => listDiv.appendChild(createActionButton(a)));
        }
    },

    renderPerformanceGuide: () => PerformanceRenderer.renderPerformanceGuide(Rendering.renderHeartProgress),

    renderLookedCards: () => {
        const state = State.data;
        const panel = document.getElementById('looked-cards-panel');
        const content = document.getElementById('looked-cards-content');
        if (!panel || !content) return;

        const cards = state.looked_cards || [];
        if (cards.length === 0) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';

        let html = "";
        if (state.pending_choice && (state.pending_choice.title || state.pending_choice.text)) {
            const title = state.pending_choice.title || state.pending_choice.text;
            html += `<div class="looked-cards-header" style="width:100%; color: var(--accent-gold); font-size: 0.8rem; padding: 5px; margin-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.1); font-weight: bold;">${title}</div>`;
        }

        if (state.pending_choice && state.pending_choice.choose_count > 1) {
            const total = state.pending_choice.choose_count;
            const v_rem = state.pending_choice.v_remaining;
            const remaining = (v_rem === -1) ? total : (v_rem + 1);
            const t = translations ? translations[State.currentLang] : null;

            if (remaining > 1) {
                const label = t ? (t['pick_more'] || `Pick ${remaining} more cards`).replace('{count}', remaining) : `Pick ${remaining} more cards`;
                html += `<div style="padding: 0 5px 8px 5px; font-size: 0.75rem; color: var(--accent-pink); font-style: italic;">${label}</div>`;
            } else {
                const label = t ? (t['pick_last'] || 'Pick the last card') : 'Pick the last card';
                html += `<div style="padding: 0 5px 8px 5px; font-size: 0.75rem; color: var(--accent-green); font-style: italic;">${label}</div>`;
            }
        }

        html += cards.map((c, idx) => {
            if (c === null) {
                return `<div class="looked-card-item placeholder" style="visibility: hidden; pointer-events: none;"></div>`;
            }
            const tooltip = Tooltips.getEffectiveAbilityText(c);
            const aid = (state.pending_choice && state.pending_choice.actions && state.pending_choice.actions.length > idx)
                ? state.pending_choice.actions[idx]
                : undefined;

            // Only make clickable if action ID is valid
            const isClickable = (aid !== undefined && aid !== 0);
            const clickHandler = isClickable ? `if(window.doAction) window.doAction(${aid})` : '';
            const cursorStyle = isClickable ? 'cursor: pointer;' : '';
            const rawText = Tooltips.getEffectiveRawText(c);

            return `
                <div class="looked-card-item card" 
                    ${isClickable ? `onclick="${clickHandler}"` : ''} 
                    style="${cursorStyle}" 
                    data-card-id="${c.id}" 
                    data-text="${rawText.replace(/"/g, '&quot;')}"
                    ${aid !== undefined ? `data-action-id="${aid}"` : ''}>
                    <img src="${fixImg(c.img)}" class="looked-card-img">
                    <div class="looked-card-name">${c.name}</div>
                </div>
            `;
        }).join('');
        content.innerHTML = html;
    },

    renderPerformanceResult: (results = null) => PerformanceRenderer.renderPerformanceResult(results, Rendering.renderHeartProgress),

    renderHeartProgress: (filled, required) => {
        if (!required || !Array.isArray(required)) return '';
        const filledArr = (Array.isArray(filled) ? filled : []);
        let html = '<div class="heart-progress-row">';
        for (let i = 0; i < 7; i++) {
            const reqCount = required[i] || 0;
            const filledCount = filledArr[i] || 0;
            for (let j = 0; j < reqCount; j++) {
                const isFilled = j < filledCount;
                html += `<div class="heart-pip color-${i} ${isFilled ? 'filled' : 'empty'}"></div>`;
            }
        }
        html += '</div>';
        return html;
    },

    renderHeartsCompact: (hearts) => PerformanceRenderer.renderHeartsCompact(hearts),
    renderBladeHeartsCompact: (hearts) => PerformanceRenderer.renderHeartsCompact(hearts),
    renderBladesCompact: (blades) => PerformanceRenderer.renderBladesCompact(blades),
    renderTotalHeartsBreakdown: (hearts) => PerformanceRenderer.renderHeartsCompact(hearts),

    renderModifiers: () => { /* Placeholder for future implementation */ },
    renderGameData: () => { /* Placeholder for future implementation */ },

    updateSettingsButtons: () => {
        const t = (window.translations && State.currentLang) ? window.translations[State.currentLang] : null;

        const liveWatchBtn = document.getElementById('live-watch-btn');
        if (liveWatchBtn) {
            const label = t ? (t['live_watch'] || 'Live Watch') : 'Live Watch';
            liveWatchBtn.textContent = `${label}: ${State.isLiveWatchOn ? 'ON' : 'OFF'}`;
        }

        const hotseatBtn = document.getElementById('pvp-btn');
        if (hotseatBtn) {
            hotseatBtn.textContent = `Shared Screen: ${State.hotseatMode ? 'ON' : 'OFF'}`;
        }

        const perspectiveBtn = document.getElementById('switch-btn');
        if (perspectiveBtn) {
            perspectiveBtn.textContent = `View: P${State.perspectivePlayer + 1}`;
        }

        const friendlyBtn = document.getElementById('friendly-abilities-btn');
        if (friendlyBtn) {
            const label = t ? (t['friendly_abilities'] || 'Friendly Abilities') : 'Friendly Abilities';
            friendlyBtn.textContent = `${label}: ${State.showFriendlyAbilities ? 'ON' : 'OFF'}`;
        }

        const langBtn = document.getElementById('lang-btn');
        if (langBtn) {
            langBtn.textContent = State.currentLang === 'jp' ? 'English' : '日本語';
        }
    },

    showPerfTab: (tab) => PerformanceRenderer.showPerfTab(tab),

    renderTurnHistory: () => PerformanceRenderer.renderTurnHistory(Rendering.getPhaseKey)
};

