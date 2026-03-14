/**
 * HeaderStats Component
 * Handles rendering of the game header (Turn, Phase, Energy, Scores, Hearts Summary).
 */
import * as i18n from '../i18n/index.js';
import { PerformanceRenderer } from './PerformanceRenderer.js';

export const HeaderStats = {
    cache: {
        turn: null,
        phase: null,
        score: null,
        energy: null,
        hearts: null,
        blades: null
    },

    init: () => {
        HeaderStats.cache.turn = document.getElementById('turn');
        HeaderStats.cache.phase = document.getElementById('phase');
        HeaderStats.cache.score = document.getElementById('score');
        HeaderStats.cache.energy = document.getElementById('header-energy');
        HeaderStats.cache.hearts = document.getElementById('total-hearts-summary');
        HeaderStats.cache.blades = document.getElementById('total-blades-summary');
    },

    render: (state, p0, getPhaseKey) => {
        if (!HeaderStats.cache.turn) HeaderStats.init();

        const phaseKey = getPhaseKey(state.phase);
        
        if (HeaderStats.cache.turn) HeaderStats.cache.turn.textContent = state.turn_number || state.turn || 1;
        if (HeaderStats.cache.phase) HeaderStats.cache.phase.textContent = i18n.t(phaseKey);

        if (HeaderStats.cache.score) {
            const p0Score = state.players[0].success_lives ? state.players[0].success_lives.length : 0;
            const p1Score = state.players[1].success_lives ? state.players[1].success_lives.length : 0;
            HeaderStats.cache.score.textContent = `${p0Score} - ${p1Score}`;
        }

        if (HeaderStats.cache.energy && p0) {
            HeaderStats.cache.energy.textContent = `${p0.energy_untapped || 0}/${p0.energy_count || 0}`;
        }

        if (HeaderStats.cache.hearts && p0) {
            const hearts = p0.total_hearts || [0, 0, 0, 0, 0, 0, 0];
            HeaderStats.cache.hearts.innerHTML = PerformanceRenderer.renderHeartsCompact(hearts);
        }

        if (HeaderStats.cache.blades && p0) {
            const bladesCount = p0.total_blades !== undefined ? p0.total_blades : 0;
            HeaderStats.cache.blades.innerHTML = `<span class="stat-item" title="Total Blades">
                <img src="img/texticon/icon_blade.png" class="heart-mini-icon">
                <span class="stat-value">${bladesCount}</span>
            </span>`;
        }
    }
};
