import { State } from '../state.js';
import { Rendering } from '../ui_rendering.js';

export const PerformanceModal = {
    showLastPerformance: () => {
        const modal = document.getElementById('performance-modal');
        if (modal) modal.style.display = 'flex';
        if (Rendering && Rendering.renderPerformanceResult) {
            const latestTurn = State.performanceHistoryTurns && State.performanceHistoryTurns.length > 0
                ? Math.max(...State.performanceHistoryTurns)
                : -1;
            State.selectedPerfTurn = latestTurn;
            const dataToUse = latestTurn !== -1 ? State.performanceHistory[latestTurn] : State.lastPerformanceData;
            Rendering.renderPerformanceResult(dataToUse);
        }
    },

    showPerformanceForTurn: (turn) => {
        State.selectedPerfTurn = turn;
        const data = State.performanceHistory[turn];
        if (data && Rendering && Rendering.renderPerformanceResult) {
            Rendering.renderPerformanceResult(data);
        }
    },

    closePerformanceModal: () => {
        const modal = document.getElementById('performance-modal');
        if (modal) modal.style.display = 'none';
    }
};
