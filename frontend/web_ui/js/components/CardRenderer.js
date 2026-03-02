import { State } from '../state.js';
import { Phase, fixImg as fixImgPath } from '../constants.js';
import * as i18n from '../i18n/index.js';
import { Tooltips } from '../ui_tooltips.js';

export const CardRenderer = {
    renderCards: (containerId, cards, clickable = false, mini = false, selectedIndices = [], validActionMap = {}, hasGlobalSelection = false) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        if (!cards) return;

        const state = State.data;
        cards.forEach((card, idx) => {
            const div = document.createElement('div');

            // Handle placeholders (null cards from engine tombstones)
            if (card === null) {
                div.className = 'card placeholder' + (mini ? ' card-mini' : '');
                div.style.visibility = 'hidden';
                div.style.pointerEvents = 'none';
                el.appendChild(div);
                return;
            }

            const isSelected = selectedIndices.includes(idx);

            // Validation Logic
            const actionId = validActionMap[idx];
            const isValid = actionId !== undefined;

            let highlightClass = '';
            if (isSelected) {
                highlightClass = (state.phase === Phase.MULLIGAN_P1 || state.phase === Phase.MULLIGAN_P2) ? ' mulligan-selected' : ' selected';
            }
            if (card.is_new) highlightClass += ' new-card';
            if (isValid) highlightClass += ' valid-target';

            const isHidden = card.hidden || card.id === -2;
            const isLive = card.type === 'live';

            let rotationClass = '';
            if (!isLive) {
                if (containerId.includes('live') || containerId.includes('success')) {
                    rotationClass = ' rotated-90';
                }
            }

            div.className = 'card' + (isHidden ? ' hidden' : '') +
                (isLive ? ' type-live' : '') +
                (mini ? ' card-mini' : '') + rotationClass + highlightClass;

            div.id = `${containerId}-card-${idx}`;

            Tooltips.attachCardData(div, card, isValid ? actionId : undefined);

            if (!isHidden) {
                let imgPath = card.img || card.img_path || '';
                const imgHtml = imgPath ? `<img src="${fixImgPath(imgPath)}" draggable="false" onerror="this.style.display='none'">` : '';
                div.innerHTML = `${imgHtml}${card.cost !== undefined ? `<span class="cost">${card.cost}</span>` : ''}<div class="name">${card.name || ''}</div>`;
            } else {
                div.classList.add('card-back');
                div.innerHTML = '';
            }

            if (clickable) {
                if (isValid || !hasGlobalSelection) {
                    div.style.cursor = 'pointer';
                    div.onclick = () => {
                        if (isValid && window.doAction) {
                            window.doAction(actionId);
                        } else if (window.playCard) {
                            window.playCard(idx);
                        }
                    };
                    if (isValid) {
                        div.onmouseenter = () => {
                            if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
                        };
                        div.onmouseleave = () => {
                            if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
                        };
                    }
                } else {
                    div.onclick = null;
                }
            }
            el.appendChild(div);
        });
    },

    renderStage: (containerId, stage, clickable, validActionMap = {}, hasGlobalSelection = false) => {
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const slot = stage[i];
            const area = document.createElement('div');
            area.className = 'member-area board-slot-container';

            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;

            let highlightClass = '';
            if (isValid) highlightClass += ' valid-target';

            const slotDiv = document.createElement('div');
            const isTapped = slot && typeof slot === 'object' && slot.tapped;
            slotDiv.className = 'member-slot' + (slot && slot !== -1 ? ' filled' : '') + (isTapped ? ' tapped' : '') + highlightClass;
            slotDiv.id = `${containerId}-slot-${i}`;

            if (slot && typeof slot === 'object' && slot.id !== undefined && slot.id !== -1) {
                let imgPath = slot.img || slot.img_path || '';
                let modifiersHtml = '';
                if (slot.modifiers && slot.modifiers.length > 0) {
                    modifiersHtml = `<div class="member-modifiers">${slot.modifiers.map(m => `<div class="modifier-tag ${m.type}">${m.label || (m.type === 'heart' ? '+' : m.value)}</div>`).join('')}</div>`;
                }

                slotDiv.innerHTML = imgPath ? `<img src="${fixImgPath(imgPath)}">${modifiersHtml}` : modifiersHtml;

                Tooltips.attachCardData(area, slot, isValid ? actionId : undefined);
                Tooltips.attachCardData(slotDiv, slot, isValid ? actionId : undefined);
            }

            area.appendChild(slotDiv);
            el.appendChild(area);

            if (clickable) {
                if (isValid || !hasGlobalSelection) {
                    area.onclick = () => {
                        if (isValid && window.doAction) {
                            window.doAction(actionId);
                        } else if (window.onStageSlotClick) {
                            window.onStageSlotClick(i);
                        }
                    };
                    slotDiv.onclick = area.onclick;
                    area.style.cursor = 'pointer';
                    if (isValid) {
                        area.onmouseenter = () => {
                            if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
                        };
                        area.onmouseleave = () => {
                            if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
                        };
                    }
                } else {
                    area.onclick = null;
                }
            }
        }
    },

    renderLiveZone: (containerId, liveCards, visible, validActionMap = {}, hasGlobalSelection = false) => {
        const state = State.data;
        const el = document.getElementById(containerId);
        if (!el) return;
        el.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const card = liveCards[i];

            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;
            let highlightClass = '';
            if (isValid) highlightClass += ' valid-target';

            const slot = document.createElement('div');
            const isLiveCard = card && card.type === 'live';

            slot.className = 'card card-mini' + (card ? (isLiveCard ? ' type-live' : '') : ' empty') + highlightClass;
            slot.id = `${containerId}-slot-${i}`;
            if (card && typeof card === 'object' && card.id !== undefined && card.id !== -1) {
                const isPerfLegal = card.is_perf_legal;
                const imgPath = card.img || card.img_path || '';
                slot.innerHTML = `
                    <div class="live-card-inner ${isPerfLegal ? 'perf-legal' : ''}">
                        ${imgPath ? `<img src="${fixImgPath(imgPath)}">` : ''}
                        <div class="cost">${card.score || (card.cost !== undefined ? card.cost : 0)}</div>
                        ${isPerfLegal ? '<div class="perf-badge">LIVE!</div>' : ''}
                    </div>
                `;
                const rawText = Tooltips.getEffectiveRawText(card);
                if (rawText) slot.setAttribute('data-text', rawText);
                slot.setAttribute('data-card-id', card.id);

                if (isValid) {
                    slot.style.cursor = 'pointer';
                    slot.onclick = () => { if (window.doAction) window.doAction(actionId); };
                    slot.onmouseenter = () => {
                        if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
                    };
                    slot.onmouseleave = () => {
                        if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
                    };
                } else if (isPerfLegal) {
                    const fallbackId = state.legal_actions?.find(a => (a.id === 600 + i || a.id === 900 + i || (a.metadata && a.metadata.slot_idx === i && a.metadata.category === 'LIVE')))?.id;
                    if (fallbackId !== undefined) {
                        slot.style.cursor = 'pointer';
                        slot.onclick = () => { if (window.doAction) window.doAction(fallbackId); };
                    } else {
                        slot.onclick = null;
                    }
                } else {
                    slot.onclick = null;
                }
            } else {
                slot.innerHTML = ``;
            }
            el.appendChild(slot);
        }
    },

    renderDiscardPile: (containerId, discard, playerIdx, validActionMap = {}, hasGlobalSelection = false, showModalCallback = null) => {
        const el = document.getElementById(containerId);
        if (!el) return;

        const actionId = validActionMap && validActionMap['all'];
        const isValid = actionId !== undefined;
        let highlightClass = isValid ? ' valid-target' : '';

        el.innerHTML = '';
        el.className = 'discard-pile-visual ' + highlightClass;

        if (!discard || discard.length === 0) {
            el.classList.add('empty');
            el.innerHTML = '<span style="opacity:0.3; font-size:0.8rem;">Discard</span>';
        } else {
            const showCount = Math.min(3, discard.length);
            for (let i = 0; i < showCount; i++) {
                const card = discard[discard.length - 1 - i];
                const div = document.createElement('div');
                div.className = 'card card-mini';
                div.innerHTML = `<img src="${fixImgPath(card.img || '')}">`;
                div.style.transform = `translate(${i * 2}px, ${i * 2}px)`;
                div.style.zIndex = 10 - i;

                if (card.id !== undefined) {
                    div.setAttribute('data-card-id', card.id);
                    const rawText = Tooltips.getEffectiveRawText(card);
                    if (rawText) div.setAttribute('data-text', rawText);
                }

                el.appendChild(div);
            }
        }

        if (isValid) {
            el.style.cursor = 'pointer';
            el.onclick = (e) => {
                e.stopPropagation();
                if (window.doAction) window.doAction(actionId);
            };
            el.onmouseenter = () => {
                if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
            };
            el.onmouseleave = () => {
                if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
            };
        } else if (!hasGlobalSelection && discard && discard.length > 0) {
            el.style.cursor = 'pointer';
            el.onclick = () => { if (showModalCallback) showModalCallback(playerIdx); };
        } else {
            el.onclick = null;
        }
    },

    renderLookedCards: (validActionMap = {}) => {
        const state = State.data;
        const panel = document.getElementById('looked-cards-panel');
        const content = document.getElementById('looked-cards-content');
        if (!panel || !content) return;

        const cards = state.looked_cards || [];
        if (cards.length === 0) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';

        let html = "";
        if (state.pending_choice && (state.pending_choice.title || state.pending_choice.text)) {
            const title = state.pending_choice.title || state.pending_choice.text;
            html += `<div class="looked-cards-header" style="width:100%; color: var(--accent-gold); font-size: 0.8rem; padding: 5px; margin-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.1); font-weight: bold;">${title}</div>`;
        }

        if (state.pending_choice && state.pending_choice.choose_count > 1) {
            const total = state.pending_choice.choose_count;
            const v_rem = state.pending_choice.v_remaining;
            const remaining = (v_rem === -1) ? total : (v_rem + 1);

            if (remaining > 1) {
                const label = i18n.t('pick_more', { count: remaining });
                html += `<div style="padding: 0 5px 8px 5px; font-size: 0.75rem; color: var(--accent-pink); font-style: italic;">${label}</div>`;
            } else {
                const label = i18n.t('pick_last');
                html += `<div style="padding: 0 5px 8px 5px; font-size: 0.75rem; color: var(--accent-green); font-style: italic;">${label}</div>`;
            }
        }

        content.innerHTML = '';
        cards.forEach((c, idx) => {
            if (c === null) {
                const placeholder = document.createElement('div');
                placeholder.className = 'looked-card-item placeholder';
                placeholder.style.visibility = 'hidden';
                placeholder.style.pointerEvents = 'none';
                content.appendChild(placeholder);
                return;
            }

            const aid = validActionMap[idx];
            const isClickable = (aid !== undefined && aid !== 0);

            const itemDiv = document.createElement('div');
            itemDiv.className = 'looked-card-item card card-mini' + (isClickable ? ' valid-target' : '');
            if (isClickable) {
                itemDiv.style.cursor = 'pointer';
                itemDiv.onclick = () => { if (window.doAction) window.doAction(aid); };
                itemDiv.onmouseenter = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(aid, true);
                };
                itemDiv.onmouseleave = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(aid, false);
                };
            }

            Tooltips.attachCardData(itemDiv, c, aid);

            itemDiv.innerHTML = `
                <img src="${fixImgPath(c.img)}" class="looked-card-img">
                <div class="looked-card-name">${c.name}</div>
            `;
            content.appendChild(itemDiv);
        });
    }
};
