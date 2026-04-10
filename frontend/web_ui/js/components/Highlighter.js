import { State } from '../state.js';
import { Tooltips } from '../ui_tooltips.js';
import { getActionMeta, getActionTargetElementIds, getActionValue, getPlayerPrefix, zoneElementId } from '../interaction_meta.js';

export const Highlighter = {
    addHighlight: (idOrEl, className) => {
        const el = typeof idOrEl === 'string' ? document.getElementById(idOrEl) : idOrEl;
        if (el) {
            el.classList.add(className);
            if (el.closest && el.closest('.card-area.hand')) {
                el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        }
    },

    clearHighlights: () => {
        const selectors = [
            '.highlight-source', '.highlight-target', '.highlight-target-opp',
            '.valid-drop-target', '.drop-hover', '.highlight-hover',
            // NOTE: 'hover-highlight' is intentionally NOT cleared here
            // It's managed by window.highlightActionBtn for persistent hover state
            '.selected', '.mulligan-selected'
        ];
        document.querySelectorAll(selectors.join(', ')).forEach(el => {
            el.classList.remove(
                'highlight-source', 'highlight-target', 'highlight-target-opp',
                'valid-drop-target', 'drop-hover', 'highlight-hover',
                // 'hover-highlight' is NOT removed - managed by window.highlightActionBtn
                'selected', 'mulligan-selected'
            );
        });
    },

    highlightTargetsForAction: (action) => {
        if (!action) return;
        Highlighter.highlightAction(action);
    },

    highlightAction: (a) => {
        const state = State.data;
        if (!state) return;
        Highlighter.clearHighlights();

        const perspectivePlayer = State.perspectivePlayer;
        const actingPlayer = state.current_player ?? state.active_player;
        const selfPrefix = (actingPlayer === perspectivePlayer ? 'my' : 'opp');
        const meta = getActionMeta(a);
        const sourceZone = getActionValue(a, 'source_zone');
        const sourceIndex = getActionValue(a, 'source_index', 'hand_idx', 'slot_idx', 'area_idx', 'energy_idx', 'selection_index');
        const targetZone = getActionValue(a, 'target_zone');
        const targetIndex = getActionValue(a, 'target_index', 'selection_index', 'hand_idx', 'slot_idx', 'area_idx', 'energy_idx');
        const sourcePlayer = getActionValue(a, 'source_player');
        const targetPlayer = getActionValue(a, 'target_player');

        let specificHighlighted = false;

        const sourcePrefix = getPlayerPrefix(sourcePlayer, perspectivePlayer, selfPrefix);
        const targetPrefix = getPlayerPrefix(targetPlayer, perspectivePlayer, selfPrefix);

        const sourceEl = zoneElementId(sourcePrefix, sourceZone, sourceIndex);
        if (sourceEl) {
            Highlighter.addHighlight(sourceEl, 'highlight-source');
            specificHighlighted = true;
        }

        const targetEl = zoneElementId(targetPrefix, targetZone, targetIndex);
        if (targetEl) {
            Highlighter.addHighlight(targetEl, 'highlight-target');
            specificHighlighted = true;
        }

        if (!specificHighlighted && meta.location === 'discard') {
            Highlighter.addHighlight(`${sourcePrefix}-discard-visual`, 'highlight-source');
            specificHighlighted = true;
        }

        // Special handling for mulligan actions (IDs 300-359)
        // Mulligan action IDs map directly to hand index: hand_idx = actionId - 300
        if (!specificHighlighted && a.id >= 300 && a.id <= 359) {
            const handIdx = a.id - 300;
            const mulliganEl = zoneElementId(sourcePrefix, 'hand', handIdx);
            if (mulliganEl) {
                Highlighter.addHighlight(mulliganEl, 'highlight-source');
                specificHighlighted = true;
            }
        }

        // Only fall back to card ID search if we have no zone/index info at all
        // This prevents highlighting the wrong card when there are duplicate IDs
        if (!specificHighlighted && sourceZone === undefined && sourceIndex === undefined) {
            let srcCardId = getActionValue(a, 'source_card_id');
            if ((srcCardId === undefined || srcCardId === -1) && state.pending_choice) {
                srcCardId = state.pending_choice.source_card_id || state.pending_choice.card_id || (state.pending_choice.params ? state.pending_choice.params.source_card_id : -1);
            }

            if (srcCardId !== undefined && srcCardId !== -1) {
                // Pass source zone/index as preferred parameters to handle duplicate IDs correctly
                Highlighter.highlightCardById(srcCardId, 'highlight-source', true, sourceZone, sourceIndex, sourcePrefix);
            }
        }
    },

    highlightPendingSource: () => {
        const state = State.data;
        if (!state || !state.pending_choice) return;
        const choice = state.pending_choice;
        const srcId = choice.source_card_id || choice.card_id || (choice.params ? choice.params.source_card_id : -1);

        if (srcId === undefined || srcId === -1) return;

        let found = false;
        let foundZone = null;
        let foundIndex = null;
        const perspectivePlayer = State.perspectivePlayer;
        const selfPrefix = getPlayerPrefix(choice.source_player, perspectivePlayer, (state.active_player === perspectivePlayer ? 'my' : 'opp'));

        const area = choice.source_area !== undefined ? choice.source_area : (choice.area !== undefined ? choice.area : (choice.params ? choice.params.area : undefined));
        if (area !== undefined) {
            Highlighter.addHighlight(`${selfPrefix}-stage-slot-${area}`, 'highlight-source');
            found = true;
            foundZone = 'stage';
            foundIndex = area;
        }

        const handIdx = choice.hand_idx !== undefined ? choice.hand_idx : (choice.params ? choice.params.hand_idx : undefined);
        if (handIdx !== undefined) {
            Highlighter.addHighlight(`${selfPrefix}-hand-card-${handIdx}`, 'highlight-source');
            found = true;
            foundZone = 'hand';
            foundIndex = handIdx;
        }

        if (!found) {
            Highlighter.highlightCardById(srcId, 'highlight-source', true, null, null, selfPrefix);
        }
    },

    highlightCardById: (srcId, className = 'highlight-source', firstOnly = true, preferredZone = null, preferredIndex = null, preferredPrefix = 'my') => {
        const state = State.data;
        if (!state) return;

        const perspectivePlayer = State.perspectivePlayer;
        const playersMap = [
            { id: perspectivePlayer, prefix: 'my' },
            { id: 1 - perspectivePlayer, prefix: 'opp' }
        ];

        // If we have a preferred zone and index, try that first
        if (preferredZone && preferredIndex !== null) {
            const preferredEl = zoneElementId(preferredPrefix, preferredZone, preferredIndex);
            if (preferredEl) {
                // Verify the card at this position matches the expected ID
                const p = state.players[playersMap.find(pm => pm.prefix === preferredPrefix)?.id ?? perspectivePlayer];
                let cardAtPos = null;
                if (preferredZone === 'hand' && p?.hand) {
                    cardAtPos = p.hand[preferredIndex];
                } else if (preferredZone === 'stage' && p?.stage) {
                    cardAtPos = p.stage[preferredIndex];
                } else if (preferredZone === 'live' && p?.live_zone) {
                    cardAtPos = p.live_zone[preferredIndex];
                } else if (preferredZone === 'energy' && p?.energy) {
                    cardAtPos = p.energy[preferredIndex]?.card;
                }
                const cidAtPos = cardAtPos ? (cardAtPos.id ?? cardAtPos) : -1;
                if (cidAtPos === srcId || cidAtPos === (srcId & 0x1FFFFF)) { // Check both raw and masked ID
                    Highlighter.addHighlight(preferredEl, className);
                    return;
                }
            }
        }

        for (const pMap of playersMap) {
            const p = state.players[pMap.id];
            if (!p) continue;

            // Check preferred zone first if specified (but no specific index)
            if (preferredZone === 'hand' && p.hand) {
                for (let idx = 0; idx < p.hand.length; idx++) {
                    const card = p.hand[idx];
                    const cid = card ? card.id : -1;
                    if (cid === srcId) {
                        Highlighter.addHighlight(`${pMap.prefix}-hand-card-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            } else if (preferredZone !== 'hand') {
                // Only search hand if not already searched as preferred zone
                if (p.hand) {
                    for (let idx = 0; idx < p.hand.length; idx++) {
                        const card = p.hand[idx];
                        const cid = card ? card.id : -1;
                        if (cid === srcId) {
                            Highlighter.addHighlight(`${pMap.prefix}-hand-card-${idx}`, className);
                            if (firstOnly) return;
                        }
                    }
                }
            }

            if (p.stage) {
                for (let idx = 0; idx < p.stage.length; idx++) {
                    const card = p.stage[idx];
                    const cid = card ? card.id : -1;
                    if (cid === srcId) {
                        Highlighter.addHighlight(`${pMap.prefix}-stage-slot-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
            if (p.live_zone) {
                for (let idx = 0; idx < p.live_zone.length; idx++) {
                    const cardObj = p.live_zone[idx];
                    const cid = cardObj ? cardObj.id : -1;
                    if (cid === srcId) {
                        Highlighter.addHighlight(`${pMap.prefix}-live-slot-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
            if (p.discard && p.discard.some(c => (typeof c === 'object' ? c.id === srcId : c === srcId))) {
                Highlighter.addHighlight(`${pMap.prefix}-discard-visual`, className);
                if (firstOnly) return;
            }
            if (p.energy) {
                for (let idx = 0; idx < p.energy.length; idx++) {
                    const e = p.energy[idx];
                    const cid = (e && e.card) ? e.card.id : -1;
                    if (cid === srcId) {
                        Highlighter.addHighlight(`${pMap.prefix}-energy-slot-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
        }
    },

    highlightValidZones: (source, index) => {
        const state = State.data;
        if (!state || !state.legal_actions) return;

        const validTargets = new Set();
        const handIdx = index;

        state.legal_actions.forEach(a => {
            if (source === 'hand' || source === 'stage') {
                getActionTargetElementIds(a, source, index).forEach(id => validTargets.add(id));
            } else if (source === 'discard') {
                if (a.discard_idx === index || a.index === index) {
                    if (a.type === 'SELECT_DISCARD' || a.type === 'SELECT_CARD') {
                        validTargets.add('my-hand');
                    }
                    if (a.type === 'PLAY_MEMBER_FROM_DISCARD') {
                        if (a.area_idx !== undefined) validTargets.add(`my-stage-slot-${a.area_idx}`);
                    }
                }
            } else if (source === 'deck') {
                const Phase = { DRAW: 'DRAW' };
                if (a.id === 2 || (a.id === 0 && state.phase === Phase.DRAW)) {
                    validTargets.add('my-hand');
                }
            }
        });

        validTargets.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.add('valid-drop-target');
                if (id.includes('slot-')) {
                    const container = el.closest('.board-slot-container');
                    if (container) container.classList.add('valid-drop-target');
                }
            }
        });
    },

    highlightStageCard: (areaIdx) => {
        Highlighter.clearHighlights();
        Highlighter.addHighlight(`my-stage-slot-${areaIdx}`, 'highlight-source');
    }
};
