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
        document.querySelectorAll('.highlight-source, .highlight-target, .highlight-target-opp, .valid-drop-target, .drop-hover, .highlight-hover').forEach(el => {
            el.classList.remove('highlight-source', 'highlight-target', 'highlight-target-opp', 'valid-drop-target', 'drop-hover', 'highlight-hover');
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

        if (a.type === 'PLAY') {
            if (a.hand_idx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-source');
                specificHighlighted = true;
            }
            if (a.area_idx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-stage-slot-${a.area_idx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'LIVE_SET') {
            if (a.hand_idx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-source');
                specificHighlighted = true;
            }
            Highlighter.addHighlight(`${selfPrefix}-live`, 'highlight-target');
            specificHighlighted = true;
        } else if (a.type === 'ABILITY' || (a.metadata && a.metadata.category === 'ABILITY')) {
            if (a.location === 'discard' || (a.metadata && a.metadata.location === 'discard')) {
                Highlighter.addHighlight(`${selfPrefix}-discard`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.area_idx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-stage-slot-${a.area_idx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.slot_idx !== undefined) {
                Highlighter.addHighlight(`${targetPrefix}-stage-slot-${a.slot_idx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.source_card_id !== undefined && a.source_card_id !== -1) {
                Highlighter.highlightCardById(a.source_card_id);
                specificHighlighted = true;
            }
        } else if (a.type === 'MULLIGAN') {
            if (a.hand_idx !== undefined) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_HAND') {
            const hIdx = a.hand_idx ?? m.hand_idx;
            if (hIdx !== undefined) {
                const id = `${targetPrefix}-hand-card-${hIdx}`;
                Highlighter.addHighlight(id, 'highlight-source');
                specificHighlighted = true;
                const card = document.getElementById(id);
                if (card && card.dataset.text) {
                    Tooltips.showTooltip(card, { clientX: card.getBoundingClientRect().right + 10, clientY: card.getBoundingClientRect().top });
                }
            }
        } else if (a.type === 'SELECT_STAGE' || a.type === 'SELECT_MEMBER') {
            const idx = a.slot_idx ?? a.area_idx ?? m.slot_idx;
            if (idx !== undefined) {
                const id = `${targetPrefix}-stage-slot-${idx}`;
                Highlighter.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
                const slot = document.getElementById(id);
                if (slot && slot.dataset.text) {
                    Tooltips.showTooltip(slot, { clientX: slot.getBoundingClientRect().right + 10, clientY: slot.getBoundingClientRect().top });
                }
            }
        } else if (a.type === 'SELECT' || a.type === 'TARGET_OPPONENT' || m.category === 'CHOICE' || m.category === 'SELECT') {
            if (a.type === 'TARGET_OPPONENT' || (state.pending_choice && state.pending_choice.type === 'TARGET_OPPONENT_MEMBER') || m.opcode === 32) {
                const idx = a.index ?? a.slot_idx ?? m.slot_idx;
                if (idx !== undefined) {
                    const prefix = (a.type === 'TARGET_OPPONENT' || m.opcode === 32) ? oppPrefix : targetPrefix;
                    const id = `${prefix}-stage-slot-${idx}`;
                    Highlighter.addHighlight(id, 'highlight-target');
                    specificHighlighted = true;
                }
            } else if (m.hand_idx !== undefined) {
                const id = `${targetPrefix}-hand-card-${m.hand_idx}`;
                Highlighter.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            } else if (m.slot_idx !== undefined) {
                const id = `${targetPrefix}-stage-slot-${m.slot_idx}`;
                Highlighter.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            } else if (m.energy_idx !== undefined) {
                const id = `${targetPrefix}-energy-slot-${m.energy_idx}`;
                Highlighter.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            } else {
                Highlighter.addHighlight(`select-list-item-${a.index ?? a.id}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_DISCARD' || m.category === 'DISCARD') {
            Highlighter.addHighlight(`${targetPrefix}-discard`, 'highlight-target');
            specificHighlighted = true;
        } else if (a.type === 'COLOR' || (a.id >= 580 && a.id <= 586)) {
            specificHighlighted = true;
        } else if (a.type === 'SELECT_LIVE' || a.type === 'LIVE_PERFORM' || (a.id >= 900 && a.id <= 902) || m.category === 'LIVE') {
            const idx = (a.area_idx !== undefined) ? a.area_idx : (a.slot_idx !== undefined ? a.slot_idx : (a.id >= 900 && a.id <= 902 ? a.id - 900 : (a.id >= 600 && a.id <= 602 ? a.id - 600 : -1)));
            if (idx !== -1) {
                const id = `${targetPrefix}-live-slot-${idx}`;
                Highlighter.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'FORMATION' || a.type === 'MOVE') {
            if (a.src_idx !== undefined || a.source_idx !== undefined || a.prev_idx !== undefined) {
                const idx = a.src_idx !== undefined ? a.src_idx : (a.source_idx !== undefined ? a.source_idx : a.prev_idx);
                Highlighter.addHighlight(`${targetPrefix}-stage-slot-${idx}`, 'highlight-source');
            }
            if (a.dst_idx !== undefined || a.area_idx !== undefined || a.slot_idx !== undefined) {
                const idx = a.dst_idx !== undefined ? a.dst_idx : (a.area_idx !== undefined ? a.area_idx : a.slot_idx);
                Highlighter.addHighlight(`${targetPrefix}-stage-slot-${idx}`, 'highlight-target');
            }
            specificHighlighted = true;
        }

        if (!specificHighlighted) {
            const aid = a.id;
            if (aid >= 600 && aid <= 602) {
                const prefix = (state.phase === 'LiveResult' ? selfPrefix : oppPrefix);
                const targetId = state.phase === 'LiveResult' ? `${prefix}-live-slot-${aid - 600}` : `${prefix}-stage-slot-${aid - 600}`;
                Highlighter.addHighlight(targetId, 'highlight-target');
            } else if (aid >= 300 && aid <= 399) {
                if (state.phase && state.phase.includes('Mulligan')) {
                    Highlighter.addHighlight(`${selfPrefix}-hand-card-${aid - 300}`, 'highlight-target');
                }
            } else if (aid >= 400 && aid <= 499) {
                Highlighter.addHighlight(`${selfPrefix}-hand-card-${aid - 400}`, 'highlight-source');
                Highlighter.addHighlight(`${selfPrefix}-live`, 'highlight-target');
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
                srcCardId = state.pending_choice.source_card_id || (state.pending_choice.params ? state.pending_choice.params.source_card_id : -1);
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
        const srcId = choice.source_card_id || (choice.params ? choice.params.source_card_id : -1);

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
                Highlighter.addHighlight(`${pMap.prefix}-discard`, className);
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
                    validTargets.add('my-discard');
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
