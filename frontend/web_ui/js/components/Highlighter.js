import { State } from '../state.js';
import { Tooltips } from '../ui_tooltips.js';

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
            '.hover-highlight', '.selected', '.mulligan-selected'
        ];
        document.querySelectorAll(selectors.join(', ')).forEach(el => {
            el.classList.remove(
                'highlight-source', 'highlight-target', 'highlight-target-opp',
                'valid-drop-target', 'drop-hover', 'highlight-hover',
                'hover-highlight', 'selected', 'mulligan-selected'
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
        const oppPrefix = (actingPlayer === perspectivePlayer ? 'opp' : 'my');

        const getPlayerPrefix = (targetId) => {
            if (targetId === undefined) return selfPrefix;
            return (targetId === perspectivePlayer ? 'my' : 'opp');
        };

        const m = a.metadata || {};
        const targetPlayer = m.target_player;
        const targetPrefix = getPlayerPrefix(targetPlayer);

        let specificHighlighted = false;

        if (a.type === 'PLAY' || (a.id >= 1000 && a.id <= 1599)) {
            const hIdx = a.hand_idx !== undefined ? a.hand_idx : (a.id >= 1000 && a.id <= 1599 ? Math.floor((a.id - 1000) / 10) : undefined);
            const sIdx = a.area_idx !== undefined ? a.area_idx : (a.id >= 1000 && a.id <= 1599 ? (a.id - 1000) % 10 : undefined);
            if (hIdx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${hIdx}`, 'highlight-source');
                specificHighlighted = true;
            }
            if (sIdx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-stage-slot-${sIdx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'LIVE_SET' || (a.id >= 400 && a.id <= 459)) {
            const hIdx = a.hand_idx !== undefined ? a.hand_idx : (a.id >= 400 && a.id <= 459 ? a.id - 400 : undefined);
            if (hIdx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${hIdx}`, 'highlight-source');
                specificHighlighted = true;
            }
            Highlighter.addHighlight(`${selfPrefix}-live`, 'highlight-target');
            specificHighlighted = true;
        } else if (a.type === 'ABILITY' || m.category === 'ABILITY' || (a.id >= 8300 && a.id <= 8599) || (a.id >= 1600 && a.id <= 2199) || (a.id >= 9300 && a.id <= 9999)) {
            if (a.location === 'discard' || m.location === 'discard' || (a.id >= 9300 && a.id <= 9999)) {
                Highlighter.addHighlight(`${selfPrefix}-discard`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.id >= 8300 && a.id <= 8599) {
                const sIdx = Math.floor((a.id - 8300) / 100);
                Highlighter.addHighlight(`${selfPrefix}-stage-slot-${sIdx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.id >= 1600 && a.id <= 2199) {
                const hIdx = Math.floor((a.id - 1600) / 10);
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${hIdx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.area_idx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-stage-slot-${a.area_idx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.slot_idx !== undefined) {
                Highlighter.addHighlight(`${targetPrefix}-stage-slot-${a.slot_idx}`, 'highlight-source');
                specificHighlighted = true;
            }
        } else if (a.type === 'CHOICE' || (a.id >= 2200 && a.id <= 2799) || (a.id >= 8600 && a.id <= 8899)) {
            const hIdx = a.hand_idx !== undefined ? a.hand_idx : (a.id >= 2200 && a.id <= 2799 ? Math.floor((a.id - 2200) / 10) : undefined);
            const sIdx = a.area_idx !== undefined ? a.area_idx : a.slot_idx !== undefined ? a.slot_idx : (a.id >= 8600 && a.id <= 8899 ? Math.floor((a.id - 8600) / 100) : undefined);
            if (hIdx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${hIdx}`, 'highlight-target');
                specificHighlighted = true;
            } else if (sIdx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-stage-slot-${sIdx}`, 'highlight-target');
                specificHighlighted = true;
            } else if (a.index !== undefined || a.id !== undefined) {
                Highlighter.addHighlight(`select-list-item-${a.index ?? a.id}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'MULLIGAN' || (a.id >= 300 && a.id <= 359)) {
            const hIdx = a.hand_idx !== undefined ? a.hand_idx : (a.id >= 300 && a.id <= 359 ? a.id - 300 : undefined);
            if (hIdx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${hIdx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_HAND' || (a.id >= 100 && a.id <= 159) || (a.id >= 500 && a.id <= 559) || (a.id >= 8200 && a.id <= 8259)) {
            let hIdx = a.hand_idx ?? m.hand_idx;
            if (hIdx === undefined) {
                if (a.id >= 100 && a.id <= 159) hIdx = a.id - 100;
                else if (a.id >= 500 && a.id <= 559) hIdx = a.id - 500;
                else if (a.id >= 8200 && a.id <= 8259) hIdx = a.id - 8200;
            }
            if (hIdx !== undefined) {
                const id = `${targetPrefix}-hand-card-${hIdx}`;
                Highlighter.addHighlight(id, 'highlight-source');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_STAGE' || (a.id >= 600 && a.id <= 602)) {
            const idx = a.slot_idx ?? a.area_idx ?? m.slot_idx ?? (a.id >= 600 && a.id <= 602 ? a.id - 600 : undefined);
            if (idx !== undefined) {
                Highlighter.addHighlight(`${targetPrefix}-stage-slot-${idx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_LIVE' || (a.id >= 900 && a.id <= 929)) {
            const idx = a.area_idx ?? a.slot_idx ?? (a.id >= 900 && a.id <= 929 ? a.id - 900 : undefined);
            if (idx !== undefined) {
                Highlighter.addHighlight(`${targetPrefix}-live-slot-${idx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.id >= 10000 && a.id <= 10999) {
            Highlighter.addHighlight(`${selfPrefix}-energy-slot-${a.id - 10000}`, 'highlight-target');
            specificHighlighted = true;
        }

        if (!specificHighlighted) {
            const aid = a.id;
            if (aid >= 600 && aid < 610) {
                const liveIdx = aid - 600;
                if (state.phase === 'LiveResult' || a.type === 'LIVE_PERFORM' || (a.metadata && a.metadata.category === 'LIVE')) {
                    Highlighter.addHighlight(`${selfPrefix}-live-slot-${liveIdx}`, 'highlight-target');
                } else {
                    Highlighter.addHighlight(`${oppPrefix}-stage-slot-${liveIdx}`, 'highlight-target');
                }
                specificHighlighted = true;
            } else if (a.type === 'SELECT_DISCARD' || (a.metadata && (a.metadata.from_discard || a.metadata.category === 'DISCARD'))) {
                Highlighter.addHighlight(`${selfPrefix}-discard-visual`, 'highlight-target');
                specificHighlighted = true;
            } else if (aid >= 300 && aid <= 399) {
                if (state.phase && state.phase.includes('Mulligan')) {
                    Highlighter.addHighlight(`${selfPrefix}-hand-card-${aid - 300}`, 'highlight-target');
                    specificHighlighted = true;
                }
            } else if (aid >= 400 && aid <= 499) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${aid - 400}`, 'highlight-source');
                Highlighter.addHighlight(`${selfPrefix}-live`, 'highlight-target');
                specificHighlighted = true;
            } else if (aid >= 500 && aid <= 509) {
                // Do nothing
            } else if (aid >= 8000 && aid <= 8999) {
                // Do nothing
            } else {
                const slotIdx = a.slot_idx !== undefined ? a.slot_idx : (a.index !== undefined ? a.index : a.choice_idx);
                if (slotIdx !== undefined && slotIdx !== -1) {
                    if (a.type === 'SELECT_LIVE' || (a.id >= 900 && a.id <= 902)) {
                        Highlighter.addHighlight(`${selfPrefix}-live-slot-${slotIdx}`, 'highlight-target');
                    } else {
                        Highlighter.addHighlight(`${selfPrefix}-stage-slot-${slotIdx}`, 'highlight-target');
                    }
                }
                if (a.hand_idx !== undefined && a.hand_idx !== -1) {
                    Highlighter.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-target');
                }
                if (a.area_idx !== undefined && a.area_idx !== -1) {
                    const id = a.type === 'LIVE_SET' ? `${selfPrefix}-live-slot-${a.area_idx}` : `${selfPrefix}-stage-slot-${a.area_idx}`;
                    Highlighter.addHighlight(id, 'highlight-target');
                }
            }
        }

        if (!specificHighlighted) {
            let srcCardId = a.source_card_id;
            if ((srcCardId === undefined || srcCardId === -1) && state.pending_choice) {
                srcCardId = state.pending_choice.source_card_id || state.pending_choice.card_id || (state.pending_choice.params ? state.pending_choice.params.source_card_id : -1);
            }

            if (srcCardId !== undefined && srcCardId !== -1) {
                Highlighter.highlightCardById(srcCardId, 'highlight-source');
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
        const perspectivePlayer = State.perspectivePlayer;
        const selfPrefix = (state.active_player === perspectivePlayer ? 'my' : 'opp');

        const area = choice.area !== undefined ? choice.area : (choice.params ? choice.params.area : undefined);
        if (area !== undefined) {
            Highlighter.addHighlight(`${selfPrefix}-stage-slot-${area}`, 'highlight-source');
            found = true;
        }

        const handIdx = choice.hand_idx !== undefined ? choice.hand_idx : (choice.params ? choice.params.hand_idx : undefined);
        if (handIdx !== undefined) {
            Highlighter.addHighlight(`${selfPrefix}-hand-card-${handIdx}`, 'highlight-source');
            found = true;
        }

        if (!found) {
            Highlighter.highlightCardById(srcId);
        }
    },

    highlightCardById: (srcId, className = 'highlight-source', firstOnly = true) => {
        const state = State.data;
        if (!state) return;

        const perspectivePlayer = State.perspectivePlayer;
        const playersMap = [
            { id: perspectivePlayer, prefix: 'my' },
            { id: 1 - perspectivePlayer, prefix: 'opp' }
        ];

        for (const pMap of playersMap) {
            const p = state.players[pMap.id];
            if (!p) continue;

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
            if (source === 'hand') {
                if (a.hand_idx === handIdx) {
                    if (a.type === 'PLAY' || a.type === 'FORMATION') {
                        if (a.area_idx !== undefined) validTargets.add(`my-stage-slot-${a.area_idx}`);
                        if (a.slot_idx !== undefined) validTargets.add(`my-stage-slot-${a.slot_idx}`);
                    }
                    if (a.type === 'LIVE_SET') {
                        if (a.slot_idx !== undefined) {
                            validTargets.add(`my-live-slot-${a.slot_idx}`);
                        } else {
                            for (let i = 0; i < 3; i++) validTargets.add(`my-live-slot-${i}`);
                        }
                    }
                }
                if ((a.hand_idx === handIdx || a.index === handIdx) &&
                    (a.type === 'SELECT_HAND' || (a.name && a.name.includes('Discard')))) {
                    validTargets.add('my-discard-visual');
                }
                if (a.hand_idx === handIdx && a.id >= 600 && a.id <= 602) {
                    validTargets.add(`opp-stage-slot-${a.id - 600}`);
                }
            } else if (source === 'stage') {
                const sourceSlot = index;
                if (a.id >= 600 && a.id <= 602) {
                    validTargets.add(`opp-stage-slot-${a.id - 600}`);
                }
                if ((a.type === 'FORMATION' || a.type === 'MOVE') &&
                    (a.source_idx === sourceSlot || a.prev_idx === sourceSlot)) {
                    if (a.area_idx !== undefined) validTargets.add(`my-stage-slot-${a.area_idx}`);
                    if (a.slot_idx !== undefined) validTargets.add(`my-stage-slot-${a.slot_idx}`);
                }
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
