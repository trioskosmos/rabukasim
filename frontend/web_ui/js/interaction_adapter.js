/**
 * Interaction Adapter
 * Handles mapping of server Action IDs to UI targets and validating legal actions.
 */
import { State } from './state.js';

export const InteractionAdapter = {
    /**
     * Calculates which UI elements are valid targets for the current list of legal actions.
     * @param {Object} state The current game state
     * @returns {Object} Mapping of zone names to valid action IDs
     */
    get_valid_targets: (state) => {
        const valid = {
            myHand: {},
            oppHand: {},
            myStage: {},
            oppStage: {},
            myLive: {},
            oppLive: {},
            myEnergy: {},
            oppEnergy: {},
            discard: {},
            hasSelection: false
        };

        if (!state.legal_actions) return valid;

        state.legal_actions.forEach(a => {
            const m = a.metadata || {};
            const hIdx = a.hand_idx ?? m.hand_idx;
            const sIdx = a.slot_idx ?? m.slot_idx;
            const srcIdx = a.source_idx ?? m.source_idx;
            const eIdx = m.energy_idx;
            const tPlayer = m.target_player !== undefined ? m.target_player : State.perspectivePlayer;
            const isMe = (tPlayer === State.perspectivePlayer);

            if (hIdx !== undefined) {
                if (isMe) valid.myHand[hIdx] = a.id;
                else valid.oppHand[hIdx] = a.id;
            }

            if (sIdx !== undefined) {
                // Determine if it's a stage target or live target
                if (a.type !== 'PLAY' && a.type !== 'LIVE_SET' && m.category !== 'LIVE') {
                    if (isMe) valid.myStage[sIdx] = a.id;
                    else valid.oppStage[sIdx] = a.id;
                }
            }
            if (srcIdx !== undefined) {
                if (isMe) valid.myStage[srcIdx] = a.id;
                else valid.oppStage[srcIdx] = a.id;
            }

            if (a.type === 'LIVE_PERFORM' || m.category === 'LIVE') {
                const liveIdx = sIdx !== undefined ? sIdx : (a.id >= 600 && a.id < 610 ? a.id - 600 : (a.id >= 900 && a.id <= 902 ? a.id - 900 : undefined));
                if (liveIdx !== undefined) {
                    if (isMe) valid.myLive[liveIdx] = a.id;
                    else valid.oppLive[liveIdx] = a.id;
                }
            }

            if (a.type === 'SELECT_DISCARD' || m.from_discard || m.category === 'DISCARD') {
                valid.discard['all'] = a.id;
            }

            if (eIdx !== undefined) {
                if (isMe) valid.myEnergy[eIdx] = a.id;
                else valid.oppEnergy[eIdx] = a.id;
            }
        });

        const hasCardActions = (Object.keys(valid.myHand).length + Object.keys(valid.myStage).length + Object.keys(valid.myLive).length +
            Object.keys(valid.oppHand).length + Object.keys(valid.oppStage).length + Object.keys(valid.oppLive).length) > 0;
        valid.hasSelection = hasCardActions;

        if (state.pending_choice && state.pending_choice.options) {
            valid.hasSelection = true;
            valid.myHand = {}; valid.oppHand = {};
            valid.myStage = {}; valid.oppStage = {};
            valid.myLive = {}; valid.oppLive = {};
            valid.myEnergy = {}; valid.oppEnergy = {};

            state.pending_choice.options.forEach((opt, idx) => {
                const actionId = state.pending_choice.actions[idx];
                const tPlayer = opt.target_player !== undefined ? opt.target_player : State.perspectivePlayer;
                const isMe = (tPlayer === State.perspectivePlayer);

                if (opt.hand_idx !== undefined) { if (isMe) valid.myHand[opt.hand_idx] = actionId; else valid.oppHand[opt.hand_idx] = actionId; }
                if (opt.slot_idx !== undefined) { if (isMe) valid.myStage[opt.slot_idx] = actionId; else valid.oppStage[opt.slot_idx] = actionId; }
                if (opt.energy_idx !== undefined) { if (isMe) valid.myEnergy[opt.energy_idx] = actionId; else valid.oppEnergy[opt.energy_idx] = actionId; }
            });
        }

        return valid;
    }
};
