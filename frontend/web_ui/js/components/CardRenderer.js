import { State } from '../state.js';
import { Phase, fixImg as fixImgPath } from '../constants.js';
import * as i18n from '../i18n/index.js';
import { Tooltips } from '../ui_tooltips.js';
import { DOMUtils } from '../utils/DOMUtils.js';
import { DOM_IDS } from '../constants_dom.js';

export const CardRenderer = {
    /**
     * Maps engine card data to UI-specific properties (CSS classes, labels, etc.)
     */
    getCardViewModel: (card, options = {}) => {
        if (!card) return null;

        const state = State.data;
        const { isSelected, isValid, mini, containerId } = options;

        const isHidden = card.hidden || card.id === -2;
        const isLive = card.type === 'live' || card.type === 'ライブ' || card.score !== undefined;

        // 1. Determine CSS Classes
        const classNames = ['card'];
        if (isHidden) classNames.push('hidden');
        if (mini) classNames.push('card-mini');
        if (card.is_new) classNames.push('new-card');
        if (isLive) classNames.push('type-live');

        // Orientation Logic (Consolidated Matrix)
        const targetLandscape = isLive || (containerId && (
            containerId.includes('live') || 
            containerId.includes('success') || 
            containerId.includes('selection')
        ));
        const nativeLandscape = isLive;

        if (targetLandscape) {
            classNames.push('orientation-landscape');
        }
        
        // Image rotation is needed if native orientation doesn't match target orientation
        if (targetLandscape !== nativeLandscape) {
            classNames.push('rotate-img-90');
        }

        if (isSelected) {
            const isMulligan = (state.phase === Phase.MULLIGAN_P1 || state.phase === Phase.MULLIGAN_P2);
            classNames.push(isMulligan ? 'mulligan-selected' : 'selected');
        }
        if (isValid && containerId !== 'my-hand') classNames.push('valid-target');
        
        // Sticky class for view model: if we match current global hover, keep it
        const isCurrentlyHovered = options.actionId !== undefined && options.actionId === State.hoveredActionId;
        if (isCurrentlyHovered) {
            classNames.push('hover-highlight');
        }
        if (isHidden) classNames.push('card-back');

        // 2. Determine Display Name & Image
        let displayName = 'Card';
        let imgPath = '';

        if (!isHidden) {
            imgPath = card.img || card.img_path || '';
            displayName = i18n.translateCard(card).name || card.name || `[${i18n.translateCardType(card.type)}]` || 'Card';
        }

        return {
            classes: classNames.join(' '),
            displayName,
            imgPath: imgPath ? fixImgPath(imgPath) : '',
            cost: card.cost,
            isHidden,
            isValid,
            actionId: options.actionId
        };
    },

    /**
     * Creates a single card DOM element from a ViewModel
     */
    createCardDOM: (viewModel, cardData, onClick = null) => {
        const div = document.createElement('div');
        div.className = viewModel.classes;

        if (viewModel.actionId !== undefined || cardData.id !== undefined) {
            Tooltips.attachCardData(div, cardData, viewModel.actionId);
        }

        if (!viewModel.isHidden) {
            if (viewModel.imgPath) {
                const img = document.createElement('img');
                img.src = viewModel.imgPath;
                img.draggable = false;
                img.onerror = () => {
                    img.style.display = 'none';
                };
                div.appendChild(img);
            }

            if (viewModel.cost !== undefined) {
                const costSpan = document.createElement('span');
                costSpan.className = 'cost';
                costSpan.textContent = String(viewModel.cost);
                div.appendChild(costSpan);
            }

            const nameDiv = document.createElement('div');
            nameDiv.className = 'name';
            nameDiv.textContent = viewModel.displayName;

            if (cardData.card_no) {
                const cardNoDiv = document.createElement('div');
                cardNoDiv.className = 'card-no';
                cardNoDiv.textContent = cardData.card_no;
                nameDiv.appendChild(cardNoDiv);
            }

            div.appendChild(nameDiv);
        }

        if (onClick) {
            div.style.cursor = 'pointer';
            div.onclick = (e) => {
                e.stopPropagation();
                onClick(viewModel.actionId);
            };

            if (viewModel.isValid) {
                div.setAttribute('data-action-id', viewModel.actionId);
                div.onmouseenter = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(viewModel.actionId, true);
                };
                div.onmouseleave = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(viewModel.actionId, false);
                };
            }
        }

        return div;
    },

    /**
     * Updates an existing card DOM element with new ViewModel
     */
    updateCardDOM: (el, viewModel, cardData, onClick = null) => {
        DOMUtils.patchClasses(el, viewModel.classes);
        
        // Stickiness: Only apply if we have a match, but DON'T aggressively remove if actionId is briefly missing
        // or if it was already hovered (let CSS :hover handle local mouse, and highlightActionBtn handle remote)
        const isMatch = viewModel.actionId !== undefined && viewModel.actionId === State.hoveredActionId;
        if (isMatch) {
            el.classList.add('hover-highlight');
        } else if (viewModel.actionId !== undefined && State.hoveredActionId !== null) {
            // We are hovering a different action, so remove this one
            el.classList.remove('hover-highlight');
        }
        // Note: we don't remove if actionId is undefined to prevent flickering during transient states

        if (viewModel.actionId !== undefined || cardData.id !== undefined) {
            Tooltips.attachCardData(el, cardData, viewModel.actionId);
        }

        if (viewModel.isHidden) {
            el.innerHTML = '';
            el.classList.add('card-back');
        } else {
            const imgPath = viewModel.imgPath;
            const existingImg = el.querySelector('img');
            
            if (existingImg) {
                if (imgPath && existingImg.getAttribute('src') !== imgPath) {
                    existingImg.setAttribute('src', imgPath);
                    existingImg.style.display = '';
                } else if (!imgPath) {
                    existingImg.style.display = 'none';
                }
                existingImg.onerror = () => existingImg.style.display = 'none';
            } else if (imgPath) {
                const img = document.createElement('img');
                img.src = imgPath;
                img.draggable = false;
                img.onerror = () => img.style.display = 'none';
                el.prepend(img);
            }

            const existingCost = el.querySelector('.cost');
            const costText = viewModel.cost !== undefined ? String(viewModel.cost) : '';
            if (existingCost) {
                if (existingCost.textContent !== costText) existingCost.textContent = costText;
            } else if (costText !== '') {
                const costSpan = document.createElement('span');
                costSpan.className = 'cost';
                costSpan.textContent = costText;
                el.appendChild(costSpan);
            }

            const existingName = el.querySelector('.name');
            if (existingName) {
                const cardNoHtml = cardData.card_no ? `<div class="card-no">${cardData.card_no}</div>` : '';
                const expectedNameHtml = `${viewModel.displayName}${cardNoHtml}`;
                if (existingName.innerHTML !== expectedNameHtml) existingName.innerHTML = expectedNameHtml;
            } else {
                const nameDiv = document.createElement('div');
                nameDiv.className = 'name';
                const cardNoHtml = cardData.card_no ? `<div class="card-no">${cardData.card_no}</div>` : '';
                nameDiv.innerHTML = `${viewModel.displayName}${cardNoHtml}`;
                el.appendChild(nameDiv);
            }
        }

        el.style.cursor = onClick ? 'pointer' : '';
        el.onclick = onClick ? (e) => {
            e.stopPropagation();
            onClick(viewModel.actionId);
        } : null;

        if (onClick && viewModel.isValid) {
            el.setAttribute('data-action-id', viewModel.actionId);
            el.onmouseenter = () => {
                if (window.highlightActionBtn) window.highlightActionBtn(viewModel.actionId, true);
            };
            el.onmouseleave = () => {
                if (window.highlightActionBtn) window.highlightActionBtn(viewModel.actionId, false);
            };
        } else {
            el.removeAttribute('data-action-id');
            el.onmouseenter = null;
            el.onmouseleave = null;
        }

        return el;
    },

    renderCards: (containerId, cards, clickable = false, mini = false, selectedIndices = [], validActionMap = {}, hasGlobalSelection = false, filter = null) => {
        const el = DOMUtils.getElement(containerId);
        if (!el) return;
        if (!cards) {
            DOMUtils.clear(containerId);
            return;
        }

        const existingChildren = Array.from(el.children);
        const cardCount = cards.length;

        if (filter) {
            DOMUtils.clear(containerId);
        } else {
            // Synchronize children count
            while (el.children.length > cardCount) {
                el.removeChild(el.lastChild);
            }
        }

        cards.forEach((card, idx) => {
            if (filter && !filter(card, idx)) return;

            const isSelected = selectedIndices.includes(idx);
            const actionId = validActionMap[idx];
            const isValid = actionId !== undefined;
            const existingChild = filter ? null : existingChildren[idx];

            if (card === null) {
                if (existingChild && existingChild.classList.contains('placeholder')) {
                    existingChild.style.visibility = 'hidden';
                } else {
                    const placeholder = document.createElement('div');
                    placeholder.className = 'card placeholder' + (mini ? ' card-mini' : '');
                    placeholder.style.visibility = 'hidden';
                    if (existingChild) el.replaceChild(placeholder, existingChild);
                    else el.appendChild(placeholder);
                }
                return;
            }

            const viewModel = CardRenderer.getCardViewModel(card, {
                isSelected,
                isValid,
                mini,
                containerId,
                actionId
            });

            const onClick = clickable && (isValid || !hasGlobalSelection) ? (aid) => {
                if (isValid && window.doAction) {
                    window.doAction(aid);
                } else if (window.playCard) {
                    window.playCard(idx);
                }
            } : null;

            if (existingChild && !existingChild.classList.contains('placeholder')) {
                CardRenderer.updateCardDOM(existingChild, viewModel, card, onClick);
                existingChild.id = `${containerId}-card-${idx}`;
            } else {
                const cardEl = CardRenderer.createCardDOM(viewModel, card, onClick);
                cardEl.id = `${containerId}-card-${idx}`;
                if (existingChild) el.replaceChild(cardEl, existingChild);
                else el.appendChild(cardEl);
            }
        });
    },

    renderStage: (containerId, stage, clickable, validActionMap = {}, hasGlobalSelection = false) => {
        const el = DOMUtils.getElement(containerId);
        if (!el) return;

        const existingAreas = Array.from(el.children);
        
        for (let i = 0; i < 3; i++) {
            const slot = stage[i];
            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;
            const existingArea = existingAreas[i];

            let area, slotDiv;
            if (existingArea) {
                area = existingArea;
                slotDiv = area.querySelector('.member-slot');
            } else {
                area = document.createElement('div');
                area.className = 'member-area board-slot-container';
                slotDiv = document.createElement('div');
                area.appendChild(slotDiv);
                el.appendChild(area);
            }

            const isTapped = slot && typeof slot === 'object' && slot.tapped;
            const filledClass = (slot && slot !== -1 ? ' filled' : '');
            const tappedClass = isTapped ? ' tapped' : '';
            const validClass = isValid ? ' valid-target' : '';
            const hoverClass = (isValid && actionId === State.hoveredActionId) ? ' hover-highlight' : '';

            const newClassName = `member-slot${filledClass}${tappedClass}${validClass}${hoverClass}`;
            if (slotDiv.className !== newClassName) slotDiv.className = newClassName;
            slotDiv.id = `${containerId}-slot-${i}`;

            if (slot && typeof slot === 'object' && slot.id !== undefined && slot.id !== -1) {
                let imgPath = slot.img || slot.img_path || '';
                let modifiersHtml = '';
                if (slot.modifiers && slot.modifiers.length > 0) {
                    modifiersHtml = `<div class="member-modifiers">${slot.modifiers.map(m => `<div class="modifier-tag ${m.type}">${m.label || (m.type === 'heart' ? '+' : m.value)}</div>`).join('')}</div>`;
                }

                const expectedHtml = imgPath ? `<img src="${fixImgPath(imgPath)}">${modifiersHtml}` : modifiersHtml;
                if (slotDiv.innerHTML !== expectedHtml) slotDiv.innerHTML = expectedHtml;

                Tooltips.attachCardData(area, slot, isValid ? actionId : undefined);
                Tooltips.attachCardData(slotDiv, slot, isValid ? actionId : undefined);
                if (isValid) {
                    area.setAttribute('data-action-id', actionId);
                    slotDiv.setAttribute('data-action-id', actionId);
                } else {
                    area.removeAttribute('data-action-id');
                    slotDiv.removeAttribute('data-action-id');
                }
            } else {
                slotDiv.innerHTML = '';
                area.removeAttribute('data-action-id');
                slotDiv.removeAttribute('data-action-id');
            }

            if (clickable && (isValid || !hasGlobalSelection)) {
                const clickHandler = () => {
                    if (isValid && window.doAction) {
                        window.doAction(actionId);
                    } else if (window.onStageSlotClick) {
                        window.onStageSlotClick(i);
                    }
                };
                area.onclick = clickHandler;
                slotDiv.onclick = clickHandler;
                area.style.cursor = 'pointer';

                if (isValid) {
                    area.onmouseenter = () => {
                        if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
                    };
                    area.onmouseleave = () => {
                        if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
                    };
                } else {
                    area.onmouseenter = null;
                    area.onmouseleave = null;
                }
            } else {
                area.onclick = null;
                slotDiv.onclick = null;
                area.style.cursor = '';
                area.onmouseenter = null;
                area.onmouseleave = null;
            }
        }
    },

    renderLiveZone: (containerId, liveCards, visible, validActionMap = {}, hasGlobalSelection = false) => {
        const state = State.data;
        const el = DOMUtils.getElement(containerId);
        if (!el) return;

        const existingSlots = Array.from(el.children);

        for (let i = 0; i < 3; i++) {
            const card = liveCards[i];
            const actionId = validActionMap[i];
            const isValid = actionId !== undefined;
            const validClass = isValid ? ' valid-target' : '';
            const existingSlot = existingSlots[i];

            let slot;
            if (existingSlot) {
                slot = existingSlot;
            } else {
                slot = document.createElement('div');
                el.appendChild(slot);
            }

            const viewModel = CardRenderer.getCardViewModel(card, {
                isValid,
                containerId,
                actionId
            });
            
            let newClassName = viewModel ? viewModel.classes : (`card empty orientation-landscape${validClass}`);
            if (isValid && actionId === State.hoveredActionId) {
                newClassName += ' hover-highlight';
            }
            if (slot.className !== newClassName) slot.className = newClassName;
            slot.id = `${containerId}-slot-${i}`;

            if (card && typeof card === 'object' && card.id !== undefined && card.id !== -1) {
                const isPerfLegal = card.is_perf_legal;
                const imgPath = card.img || card.img_path || '';
                const expectedInnerHtml = `
                    <div class="live-card-inner">
                        ${imgPath ? `<img src="${fixImgPath(imgPath)}">` : ''}
                        <div class="cost">${card.score || (card.cost !== undefined ? card.cost : 0)}</div>
                        ${card.card_no ? `<div class="card-no">${card.card_no}</div>` : ''}
                    </div>
                `;
                
                if (slot.innerHTML !== expectedInnerHtml) slot.innerHTML = expectedInnerHtml;
                
                const rawText = Tooltips.getEffectiveRawText(card);
                if (rawText) DOMUtils.patchAttributes(slot, { 'data-text': rawText });
                DOMUtils.patchAttributes(slot, { 'data-card-id': card.id });
                if (isValid) slot.setAttribute('data-action-id', actionId);
                else slot.removeAttribute('data-action-id');

                if (isValid || isPerfLegal) {
                    const finalActionId = isValid ? actionId : state.legal_actions?.find(a => (a.id === 600 + i || a.id === 900 + i || (a.metadata && a.metadata.slot_idx === i && a.metadata.category === 'LIVE')))?.id;
                    
                    if (finalActionId !== undefined) {
                        slot.style.cursor = 'pointer';
                        slot.onclick = () => { if (window.doAction) window.doAction(finalActionId); };
                        
                        if (isValid) {
                            slot.onmouseenter = () => {
                                if (window.highlightActionBtn) window.highlightActionBtn(finalActionId, true);
                            };
                            slot.onmouseleave = () => {
                                if (window.highlightActionBtn) window.highlightActionBtn(finalActionId, false);
                            };
                        } else {
                            slot.onmouseenter = null;
                            slot.onmouseleave = null;
                        }
                    } else {
                        slot.onclick = null;
                        slot.style.cursor = '';
                        slot.onmouseenter = null;
                        slot.onmouseleave = null;
                    }
                } else {
                    slot.onclick = null;
                    slot.style.cursor = '';
                    slot.onmouseenter = null;
                    slot.onmouseleave = null;
                }
            } else {
                slot.innerHTML = '';
                slot.onclick = null;
                slot.style.cursor = '';
            }
        }
    },

    renderDiscardPile: (containerId, discard, playerIdx, validActionMap = {}, hasGlobalSelection = false, showModalCallback = null) => {
        const el = DOMUtils.getElement(containerId);
        if (!el) return;

        const actionId = validActionMap && validActionMap['all'];
        const isValid = actionId !== undefined;
        const hoverClass = (isValid && actionId === State.hoveredActionId) ? ' hover-highlight' : '';
        el.className = 'discard-pile-visual ' + (isValid ? 'valid-target' : '') + hoverClass;

        DOMUtils.clear(containerId);

        if (!discard || discard.length === 0) {
            el.classList.add('empty');
            DOMUtils.setHTML(containerId, `<span style="opacity:0.3; font-size:0.8rem;">${i18n.t('discard_pile')}</span>`);
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

        if (isValid || (!hasGlobalSelection && discard && discard.length > 0)) {
            el.style.cursor = 'pointer';
            el.onclick = (e) => {
                e.stopPropagation();
                if (isValid && window.doAction) {
                    window.doAction(actionId);
                } else if (!isValid && showModalCallback) {
                    showModalCallback(playerIdx);
                }
            };
            if (isValid) {
                el.onmouseenter = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(actionId, true);
                };
                el.onmouseleave = () => {
                    if (window.highlightActionBtn) window.highlightActionBtn(actionId, false);
                };
            }
        } else {
            el.onclick = null;
        }
    },

    renderLookedCards: (validActionMap = {}, overrideCards = null, overrideTitle = null) => {
        const state = State.data;
        const panel = DOMUtils.getElement(DOM_IDS.LOOKED_CARDS_PANEL);
        const content = DOMUtils.getElement(DOM_IDS.LOOKED_CARDS_CONTENT);
        if (!panel || !content) return;

        const pendingSelectionCards = state.pending_choice?.selection_cards || [];
        const cards = overrideCards || (pendingSelectionCards.length > 0 ? pendingSelectionCards : (state.looked_cards || []));
        if (cards.length === 0) {
            DOMUtils.setVisible(DOM_IDS.LOOKED_CARDS_PANEL, false);
            return;
        }
        DOMUtils.setVisible(DOM_IDS.LOOKED_CARDS_PANEL, true, 'flex');

        let headerHtml = "";
        if (overrideTitle) {
            headerHtml = `<div class="looked-cards-header">${overrideTitle}</div>`;
        } else if (state.pending_choice && (state.pending_choice.title || state.pending_choice.text)) {
            const title = state.pending_choice.title || state.pending_choice.text;
            headerHtml = `<div class="looked-cards-header">${title}</div>`;
        }

        if (state.pending_choice && state.pending_choice.choose_count > 1) {
            const total = state.pending_choice.choose_count;
            const v_rem = state.pending_choice.v_remaining;
            const remaining = (v_rem === -1) ? total : (v_rem + 1);
            const label = remaining > 1 ? i18n.t('pick_more', { count: remaining }) : i18n.t('pick_last');
            headerHtml += `<div class="looked-cards-subtitle">${label}</div>`;
        }

        DOMUtils.clear(DOM_IDS.LOOKED_CARDS_CONTENT);
        if (headerHtml) {
            const headerDiv = document.createElement('div');
            headerDiv.className = 'looked-cards-meta';
            headerDiv.innerHTML = headerHtml;
            content.appendChild(headerDiv);
        }

        cards.forEach((c, idx) => {
            if (c === null) {
                const placeholder = document.createElement('div');
                placeholder.className = 'looked-card-item placeholder';
                placeholder.style.visibility = 'hidden';
                content.appendChild(placeholder);
                return;
            }

            const selectionIdx = c?.selection_idx ?? idx;
            const aid = validActionMap[selectionIdx];
            const isClickable = (aid !== undefined && aid !== null && aid !== 0);

            const viewModel = CardRenderer.getCardViewModel(c, {
                mini: true,
                isValid: isClickable,
                containerId: DOM_IDS.LOOKED_CARDS_CONTENT,
                actionId: aid
            });

            const onClick = isClickable ? (actionId) => {
                if (window.doAction) window.doAction(actionId);
            } : null;

            const cardEl = CardRenderer.createCardDOM(viewModel, c, onClick);
            
            // Explicitly set class and ID for the item
            cardEl.classList.add('looked-card-item');
            cardEl.id = `looked-card-${selectionIdx}`;
            
            content.appendChild(cardEl);
        });
    }
};
