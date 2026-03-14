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
        
        CardRenderer.renderDiscardPile('my-discard-visual', p0.discard || [], 0, validTargets.discard, validTargets.hasSelection, showDiscardModalCallback);
        CardRenderer.renderDiscardPile('opp-discard-visual', p1.discard || [], 1, validTargets.discard, validTargets.hasSelection, showDiscardModalCallback);

        BoardRenderer.renderEnergy('my-energy', p0.energy, true, validTargets.myEnergy, validTargets.hasSelection, state);
        BoardRenderer.renderEnergy('opp-energy', p1.energy, true, validTargets.oppEnergy, validTargets.hasSelection, state);

        const mySuccess = p0.success_pile || p0.success_lives || [];
        const oppSuccess = p1.success_pile || p1.success_lives || [];
        CardRenderer.renderCards('my-success', mySuccess, true, true);
        CardRenderer.renderCards('opp-success', oppSuccess, false, true);

        BoardRenderer.renderDeckCounts(p0, p1);
    },

    renderDeckCounts: (p0, p1) => {
        const updateCount = (id, count) => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = count !== undefined ? count : 0;
            } else {
                console.warn('[BoardRenderer] Element not found:', id);
            }
        };

        console.log('[BoardRenderer] renderDeckCounts - p0.hand:', p0?.hand, 'p0.energy:', p0?.energy);

        updateCount('my-deck-count', p0.deck_count);
        updateCount('opp-deck-count', p1.deck_count);
        updateCount('my-energy-deck-count', p0.energy_deck_count);
        updateCount('opp-energy-deck-count', p1.energy_deck_count);
        updateCount('my-discard-count', p0.discard ? p0.discard.length : 0);
        updateCount('opp-discard-count', p1.discard ? p1.discard.length : 0);

        // Update hand and energy counts
        updateCount('my-hand-count', p0.hand ? p0.hand.length : 0);
        updateCount('my-energy-count', p0.energy ? p0.energy.length : 0);
        updateCount('opp-hand-count', p1.hand ? p1.hand.length : 0);
        updateCount('opp-energy-count', p1.energy ? p1.energy.length : 0);
    },

    renderEnergy: (containerId, energy, clickable = false, validActionMap = {}, hasGlobalSelection = false, state = null) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        if (!energy) {
            el.innerHTML = '';
            return;
        }

        const existingPips = Array.from(el.children);
        const energyCount = energy.length;

        // Synchronize pip count
        while (el.children.length > energyCount) {
            el.removeChild(el.lastChild);
        }

        energy.forEach((e, i) => {
            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;
            const highlightClass = isValid ? ' valid-target' : '';
            const tappedClass = e.tapped ? ' tapped' : '';
            const existingPip = existingPips[i];

            let div;
            if (existingPip) {
                div = existingPip;
            } else {
                div = document.createElement('div');
                el.appendChild(div);
            }

            const newClassName = 'energy-pip' + tappedClass + highlightClass;
            if (div.className !== newClassName) div.className = newClassName;
            div.id = `${containerId}-slot-${i}`;

            let imgPath = e.img || e.img_path || 'img/texticon/icon_energy.png';
            const expectedInnerHtml = `
                <img src="${fixImg(imgPath)}" onerror="this.src='img/texticon/icon_energy.png'">
                <div class="energy-num">${i + 1}</div>
            `;
            
            if (div.innerHTML !== expectedInnerHtml) div.innerHTML = expectedInnerHtml;

            if (e && e.card) {
                Tooltips.attachCardData(div, e.card, isValid ? actionId : undefined);
            } else if (isValid) {
                DOMUtils.patchAttributes(div, { 'data-action-id': actionId });
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
            } else {
                div.style.cursor = '';
                div.onclick = null;
                div.onmouseenter = null;
                div.onmouseleave = null;
            }
        });
    }
};
