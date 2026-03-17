import { Phase } from './constants.js';

function getSelectedIndices(state, player, selectedHandIdx) {
    const isMulligan = state.phase === Phase.MULLIGAN_P1 || state.phase === Phase.MULLIGAN_P2;
    if (isMulligan) {
        return Array.from(player?.mulligan_selection || []);
    }
    return selectedHandIdx !== -1 ? [selectedHandIdx] : [];
}

function buildConfirmedActions(selectedIndices, validTargets) {
    const confirmedActions = {};
    selectedIndices.forEach((handIdx, internalIdx) => {
        if (validTargets.myHand[handIdx] !== undefined) {
            confirmedActions[internalIdx] = validTargets.myHand[handIdx];
        }
    });
    return confirmedActions;
}

function hasActiveEffects(state, p0, p1) {
    return Boolean(
        (state.triggered_abilities && state.triggered_abilities.length > 0) ||
        (p0?.blade_buffs && p0.blade_buffs.some(v => v !== 0)) ||
        (p0?.heart_buffs && p0.heart_buffs.some(hb => hb.some(v => v > 0))) ||
        (p1?.blade_buffs && p1.blade_buffs.some(v => v !== 0)) ||
        (p1?.heart_buffs && p1.heart_buffs.some(hb => hb.some(v => v > 0))) ||
        (p0?.cost_reduction ?? 0) !== 0 ||
        (p1?.cost_reduction ?? 0) !== 0 ||
        (p0?.prevent_baton_touch ?? 0) > 0 ||
        (p1?.prevent_baton_touch ?? 0) > 0
    );
}

export const ViewState = {
    buildRenderModel(state, uiState, validTargets) {
        const perspectivePlayer = uiState.hotseatMode && state.active_player !== undefined
            ? state.active_player
            : uiState.perspectivePlayer;

        const p0 = state.players[perspectivePlayer] || state.players[0];
        const p1 = state.players[1 - perspectivePlayer] || state.players[1];

        const isMulligan = state.phase === Phase.MULLIGAN_P1 || state.phase === Phase.MULLIGAN_P2;
        const selectedIndices = getSelectedIndices(state, p0, uiState.selectedHandIdx);
        const handFilter = (_, idx) => !isMulligan || !selectedIndices.some(s => Number(s) === Number(idx));
        const mulliganSelectedCards = isMulligan ? selectedIndices.map(idx => p0?.hand?.[idx]).filter(card => card !== null && card !== undefined) : [];
        const confirmedCards = isMulligan ? [] : selectedIndices.map(idx => p0?.hand?.[idx]).filter(card => card !== null && card !== undefined);

        const pendingChoice = state.pending_choice || null;
        const selectionCards = pendingChoice?.selection_cards || [];
        const selectionActions = selectionCards.map((_, idx) => validTargets.selection?.[idx]);

        return {
            perspectivePlayer,
            p0,
            p1,
            isMulligan,
            selectedIndices,
            handFilter,
            confirmedCards,
            mulliganSelectedCards,
            confirmedActions: buildConfirmedActions(selectedIndices, validTargets),
            showMulliganReturn: uiState.showMulliganReturn && uiState.lastMulliganCards.length > 0,
            mulliganReturnCards: uiState.lastMulliganCards,
            hasActiveEffects: hasActiveEffects(state, p0, p1),
            selectionModal: {
                isVisible: selectionCards.length > 0,
                cards: selectionCards,
                actions: selectionActions,
            },
        };
    },
};
