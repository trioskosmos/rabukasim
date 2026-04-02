/**
 * Interaction Adapter
 * Handles mapping of server Action IDs to UI targets and validating legal actions.
 */
import { State } from './state.js';
import { getActionMeta, getActionValue } from './interaction_meta.js';

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
            selection: {},
            hasSelection: false
        };

        if (!state.legal_actions) return valid;

        state.legal_actions.forEach(a => {
            const meta = getActionMeta(a);
            const sourceZone = getActionValue(a, 'source_zone');
            const sourceIndex = getActionValue(a, 'source_index', 'hand_idx', 'slot_idx', 'area_idx', 'energy_idx');
            const sourcePlayer = getActionValue(a, 'source_player', 'target_player');
            const targetZone = getActionValue(a, 'target_zone');
            const targetIndex = getActionValue(a, 'target_index', 'selection_index', 'hand_idx', 'slot_idx', 'area_idx', 'energy_idx');
            const targetPlayer = getActionValue(a, 'target_player', 'source_player');

            const sourceIsMe = (sourcePlayer ?? State.perspectivePlayer) === State.perspectivePlayer;
            const targetIsMe = (targetPlayer ?? State.perspectivePlayer) === State.perspectivePlayer;

            const addZone = (zone, index, isMe) => {
                if (index === undefined && zone !== 'live' && zone !== 'discard') {
                    return;
                }
                if (zone === 'hand') {
                    if (isMe) valid.myHand[index] = a.id;
                    else valid.oppHand[index] = a.id;
                } else if (zone === 'stage') {
                    if (isMe) valid.myStage[index] = a.id;
                    else valid.oppStage[index] = a.id;
                } else if (zone === 'live') {
                    if (isMe) valid.myLive[index ?? 'all'] = a.id;
                    else valid.oppLive[index ?? 'all'] = a.id;
                } else if (zone === 'energy') {
                    if (isMe) valid.myEnergy[index] = a.id;
                    else valid.oppEnergy[index] = a.id;
                } else if (zone === 'discard') {
                    valid.discard.all = a.id;
                } else if (zone === 'selection') {
                    valid.selection[index] = a.id;
                }
            };

            addZone(sourceZone, sourceIndex, sourceIsMe);
            addZone(targetZone, targetIndex, targetIsMe);

            if (meta.location === 'discard') {
                valid.discard.all = a.id;
            }
        });

            const hasCardActions = (Object.keys(valid.myHand).length + Object.keys(valid.myStage).length + Object.keys(valid.myLive).length +
                Object.keys(valid.oppHand).length + Object.keys(valid.oppStage).length + Object.keys(valid.oppLive).length +
                Object.keys(valid.myEnergy).length + Object.keys(valid.selection).length) > 0;
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
