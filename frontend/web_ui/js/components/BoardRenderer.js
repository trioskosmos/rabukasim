import { State } from '../state.js';
import { fixImg } from '../constants.js';
import { Tooltips } from '../ui_tooltips.js';
import { CardRenderer } from './CardRenderer.js';

export const BoardRenderer = {
    renderBoard: (state, p0, p1, validTargets, showDiscardModalCallback) => {
        CardRenderer.renderStage('my-stage', p0.stage, true, validTargets.myStage, validTargets.hasSelection);
        CardRenderer.renderStage('opp-stage', p1.stage, true, validTargets.oppStage, validTargets.hasSelection);
        CardRenderer.renderLiveZone('my-live', p0.live_zone, true, validTargets.myLive, validTargets.hasSelection);
        CardRenderer.renderLiveZone('opp-live', p1.live_zone, true, validTargets.oppLive, validTargets.hasSelection);
        BoardRenderer.renderEnergy('my-energy', p0.energy, true, validTargets.myEnergy, validTargets.hasSelection, state);
        BoardRenderer.renderEnergy('opp-energy', p1.energy, true, validTargets.oppEnergy, validTargets.hasSelection, state);


        CardRenderer.renderCards('my-success', p0.success_pile || p0.success_lives, true, true);
        CardRenderer.renderCards('opp-success', p1.success_pile || p1.success_lives, false, true);

        BoardRenderer.renderDeckCounts(p0, p1);
    },

    renderDeckCounts: (p0, p1) => {
        const updateCount = (id, count) => {
            const el = document.getElementById(id);
            if (el) el.textContent = count !== undefined ? count : 0;
        };

        updateCount('my-deck-count', p0.deck_count);
        updateCount('opp-deck-count', p1.deck_count);
        updateCount('my-energy-deck-count', p0.energy_deck_count);
        updateCount('opp-energy-deck-count', p1.energy_deck_count);
        updateCount('my-discard-count', p0.discard ? p0.discard.length : 0);
        updateCount('opp-discard-count', p1.discard ? p1.discard.length : 0);
    },

    renderEnergy: (containerId, energy, clickable = false, validActionMap = {}, hasGlobalSelection = false, state = null) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        if (!energy) return;

        energy.forEach((e, i) => {
            const div = document.createElement('div');

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

            if (e && e.card) {
                Tooltips.attachCardData(div, e.card, isValid ? actionId : undefined);
            } else if (isValid) {
                div.setAttribute('data-action-id', actionId);
            }

            if (clickable && isValid) {
                div.style.cursor = 'pointer';
                div.onclick = () => { if (window.doAction) window.doAction(actionId); };

                div.onmouseenter = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
                };
                div.onmouseleave = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
                };
            }

            el.appendChild(div);
        });
    }
};
