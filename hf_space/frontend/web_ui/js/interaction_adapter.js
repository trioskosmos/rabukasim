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
                const m = a.metadata || a; // Some layers pass metadata flat
                const hIdx = a.hand_idx !== undefined ? a.hand_idx : m.hand_idx;
                const sIdx = a.slot_idx !== undefined ? a.slot_idx : m.slot_idx;
                const eIdx = a.energy_idx !== undefined ? a.energy_idx : m.energy_idx;
                const tPlayer = m.target_player !== undefined ? m.target_player : State.perspectivePlayer;
                const isMe = (tPlayer === State.perspectivePlayer);

                // Hand Index Handling (Mulligan, LiveSet, Play, SelectHand, HandAbility)
                if (hIdx !== undefined) {
                    if (isMe) valid.myHand[hIdx] = a.id;
                    else valid.oppHand[hIdx] = a.id;
                } else {
                    // Fallbacks for known ranges
                    if (a.id >= 300 && a.id <= 359) { // Mulligan
                        if (isMe) valid.myHand[a.id - 300] = a.id;
                    } else if (a.id >= 400 && a.id <= 459) { // LiveSet
                        if (isMe) valid.myHand[a.id - 400] = a.id;
                    } else if (a.id >= 1000 && a.id <= 1599) { // Play Member
                        const fIdx = Math.floor((a.id - 1000) / 10);
                        if (isMe) valid.myHand[fIdx] = a.id;
                    } else if (a.id >= 1600 && a.id <= 2199) { // Hand Ability
                        const fIdx = Math.floor((a.id - 1600) / 10);
                        if (isMe) valid.myHand[fIdx] = a.id;
                    } else if (a.id >= 8200 && a.id <= 8259) { // Select Hand
                        if (isMe) valid.myHand[a.id - 8200] = a.id;
                    }
                }

                // Stage Index Handling (Stage Ability, Stage Select)
                if (sIdx !== undefined) {
                    if (m.category === 'LIVE' || a.type === 'LIVE_SET') {
                        if (isMe) valid.myLive[sIdx] = a.id;
                        else valid.oppLive[sIdx] = a.id;
                    } else {
                        if (isMe) valid.myStage[sIdx] = a.id;
                        else valid.oppStage[sIdx] = a.id;
                    }
                } else {
                    // Fallbacks for Stage
                    if (a.id >= 8300 && a.id <= 8599) { // Stage Ability
                        const fIdx = Math.floor((a.id - 8300) / 100);
                        if (isMe) valid.myStage[fIdx] = a.id;
                    } else if (a.id >= 1000 && a.id <= 1599) { // Play Member (Slot target)
                        const fIdx = (a.id - 1000) % 10;
                        if (isMe) valid.myStage[fIdx] = a.id;
                    } else if (a.id >= 600 && a.id <= 602) { // Select Stage
                        if (isMe) valid.myStage[a.id - 600] = a.id;
                    }
                }

                // Live Zone Index Handling
                if (a.id >= 900 && a.id <= 929) { // Performance / Select Live
                    const fIdx = a.id - 900;
                    if (isMe) valid.myLive[fIdx] = a.id;
                }

                // Energy Index Handling
                if (eIdx !== undefined) {
                    if (isMe) valid.myEnergy[eIdx] = a.id;
                    else valid.oppEnergy[eIdx] = a.id;
                } else if (a.id >= 2200 && a.id <= 2799) { // Choice related to hand
                    const handIdx = Math.floor((a.id - 2200) / 10);
                    if (isMe) valid.myHand[handIdx] = a.id;
                } else if (a.id >= 8600 && a.id <= 8899) { // Choice related to stage/area
                    const areaIdx = Math.floor((a.id - 8600) / 100);
                    if (isMe) valid.myStage[areaIdx] = a.id; // Assuming it maps to myStage for now
                } else if (a.id >= 10000 && a.id <= 10999) {
                    if (isMe) valid.myEnergy[a.id - 10000] = a.id;
                }

                // Discard
                if (a.type === 'SELECT_DISCARD' || m.from_discard || (a.id >= 9300 && a.id <= 9999)) {
                    valid.discard['all'] = a.id;
                }
            });

            const hasCardActions = (Object.keys(valid.myHand).length + Object.keys(valid.myStage).length + Object.keys(valid.myLive).length +
                Object.keys(valid.oppHand).length + Object.keys(valid.oppStage).length + Object.keys(valid.oppLive).length +
                Object.keys(valid.myEnergy).length) > 0;
            valid.hasSelection = hasCardActions;

            // Handle pending choice options
            if (state.pending_choice && state.pending_choice.params && state.pending_choice.params.cards) {
                // If we have a list of cards to choose from, we might want to highlight them in hand/discard/etc.
                // But usually this is handled by a separate modal.
            }

        if (state.pending_choice && state.pending_choice.options) {
            // ... (existing logic)
        }

        // Special Mode: Rearrange Formation (Manual Interaction)
        if (state.pending_choice && state.pending_choice.choice_type === 29) {
            valid.myStage = { 0: true, 1: true, 2: true };
            valid.hasSelection = true;
        }

        return valid;
    }
};
