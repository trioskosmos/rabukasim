/**
 * UI Tooltips & Highlighting facade
 * Delegates to TextEnricher and Highlighter for backward compatibility.
 */
import { State } from './state.js';
import { TextEnricher } from './utils/TextEnricher.js';
import { Highlighter } from './components/Highlighter.js';

let tooltipTimeout = null;
let tooltipHideTimeout = null;
let currentTooltipTarget = null;

export const Tooltips = {
    findCardById: (cardId) => State.resolveCardData(cardId),

    attachCardData: (el, cardOrId, actionId = undefined) => {
        if (!el || !cardOrId) return;

        let card = typeof cardOrId === 'object' ? cardOrId : Tooltips.findCardById(cardOrId);
        if (!card && typeof cardOrId === 'string' && cardOrId.includes('ID:')) {
            const idMatch = cardOrId.match(/ID: (\d+)/);
            if (idMatch) card = Tooltips.findCardById(parseInt(idMatch[1]));
        }

        if (!card) {
            if (actionId !== undefined && actionId !== 0) el.setAttribute('data-action-id', actionId);
            return;
        }

        const cid = card.id !== undefined ? card.id : card.card_id;
        if (cid !== undefined && cid !== -1) el.setAttribute('data-card-id', cid);
        if (card.name) el.setAttribute('data-card-name', card.name);

        // Always attach card text - ability text is public knowledge from master data
        const rawText = TextEnricher.getEffectiveRawText(card);
        if (rawText) el.setAttribute('data-text', rawText);

        if (actionId !== undefined && actionId !== 0) el.setAttribute('data-action-id', actionId);
    },

    showTooltip: (target, e, forceTarget = null, useSidebar = false, explicitText = null) => {
        const effectiveTarget = forceTarget || target;
        const dataSource = effectiveTarget.closest('[data-card-id],[data-action-id],[data-text]') || effectiveTarget;

        const descPanel = document.getElementById('card-desc-panel');
        const descContent = document.getElementById('card-desc-content');
        const descTitle = document.getElementById('card-desc-title');

        if (currentTooltipTarget && currentTooltipTarget !== dataSource) {
            currentTooltipTarget.classList.remove('highlight-hover');
        }
        currentTooltipTarget = dataSource;
        dataSource.classList.add('highlight-hover');

        const state = State.data;
        const perspectivePlayer = State.perspectivePlayer;
        let cardObj = null;
        let actionObj = null;

        const actionId = dataSource.dataset.actionId;
        const cardId = dataSource.dataset.cardId;

        if (actionId !== undefined && state && state.legal_actions) {
            actionObj = state.legal_actions.find(a => a.id === parseInt(actionId));
            if (actionObj) {
                Highlighter.highlightTargetsForAction(actionObj);
                const p = state.players[perspectivePlayer];
                if (p) {
                    if (actionObj.hand_idx !== undefined && p.hand) cardObj = p.hand[actionObj.hand_idx];
                    else if (actionObj.area_idx !== undefined && p.stage) cardObj = p.stage[actionObj.area_idx];
                    else if (actionObj.slot_idx !== undefined && p.stage) cardObj = p.stage[actionObj.slot_idx];
                    else if (actionObj.live_idx !== undefined && p.live_zone) cardObj = p.live_zone[actionObj.live_idx];
                    else if (actionObj.energy_idx !== undefined && p.energy) {
                        const energySlot = p.energy[actionObj.energy_idx];
                        if (energySlot && energySlot.card) cardObj = energySlot.card;
                    }
                }
                if (!cardObj && actionObj.source_card_id !== undefined && actionObj.source_card_id !== -1) {
                    cardObj = Tooltips.findCardById(actionObj.source_card_id);
                }
            }
        }

        if (!cardObj && cardId !== undefined) {
            cardObj = Tooltips.findCardById(parseInt(cardId));
        }

        if (!cardObj && dataSource.dataset.cardName) {
            cardObj = State.resolveCardDataByName(dataSource.dataset.cardName);
        }

        if (cardObj && cardObj.id !== undefined && cardObj.id >= 0) {
            const master = Tooltips.findCardById(cardObj.id);
            if (master) cardObj = master;
        }

        const dText = dataSource.dataset.text;
        // Always get card text - hidden flag should only hide instance-specific data,
        // not the card's ability which is public knowledge from master data
        const cardText = cardObj ? TextEnricher.getEffectiveRawText(cardObj) : "";
        let finalText = "";

        // Selection Priority Logic:
        // 1. If we have master index text and dText is generic or identical, use master text (more likely to be enriched)
        if (cardText && (!dText || TextEnricher.isGenericInstruction(dText) || dText === cardText)) {
            finalText = cardText;
        }
        // 2. If dText is rich and unique (e.g. action-specific info), use it
        else if (dText && !TextEnricher.isGenericInstruction(dText)) {
            finalText = dText;
        }

        // Action enrichment: If we have an action object, try to get even better text (e.g. translated or card-specific)
        if (actionObj) {
            const actionRichText = TextEnricher.getEffectiveActionText(actionObj);
            const rawActionRichText = actionRichText.replace(/<[^>]+>/g, "").trim(); // Stripped version for comparison

            if (rawActionRichText && !TextEnricher.isGenericInstruction(rawActionRichText)) {
                // If it's substantially better than current finalText, use it
                // We store the already enriched text to avoid double enrichment later
                finalText = actionRichText;
            }
        }

        // 3. Fallback to any available text
        if (!finalText) {
            finalText = cardText || dText || "";
        }

        if (!finalText) {
            descPanel.style.display = 'none';
            return;
        }

        const cardIdLabel = (cardObj && cardObj.id !== undefined && cardObj.id >= 0) ? ` <span style="opacity:0.6; font-size:0.8em;">(ID: ${cardObj.id})</span>` : "";
        const titleText = (cardObj && cardObj.name) ? cardObj.name + cardIdLabel : (dataSource.dataset.cardName || "Card Detail");

        if (descTitle) {
            descTitle.innerHTML = titleText;
            descTitle.style.display = titleText ? 'block' : 'none';
            // Match pending-choice-indicator header style
            descTitle.style.fontSize = '1.1rem';
            descTitle.style.borderBottom = 'none';
            descTitle.style.marginBottom = '10px';
        }

        const enrichedText = TextEnricher.enrichAbilityText(finalText);
        descContent.innerHTML = enrichedText;
        descContent.dataset.rawText = finalText;
        descPanel.style.display = 'flex';
        descPanel.style.borderLeft = '4px solid var(--accent-pink)'; // Match pending-choice-indicator accent
        descPanel.style.padding = '12px';
        descPanel.style.background = 'rgba(255,255,255,0.05)';

        if (tooltipHideTimeout) {
            clearTimeout(tooltipHideTimeout);
            tooltipHideTimeout = null;
        }

        const floatingTooltip = document.getElementById('floating-tooltip');
        if (floatingTooltip) {
            floatingTooltip.style.display = 'none';
            floatingTooltip.style.opacity = '0';
        }
    },

    hideTooltip: (immediate = false) => {
        clearTimeout(tooltipTimeout);
        tooltipTimeout = null;

        const hideAction = () => {
            tooltipHideTimeout = null;
            if (currentTooltipTarget) {
                currentTooltipTarget.classList.remove('highlight-hover');
            }
            currentTooltipTarget = null;
            Highlighter.clearHighlights();
        };

        if (immediate) {
            clearTimeout(tooltipHideTimeout);
            hideAction();
            return;
        }

        if (tooltipHideTimeout) return;
        tooltipHideTimeout = setTimeout(hideAction, 100);
    },

    // Proxies for backwards compatibility
    enrichAbilityText: (text) => TextEnricher.enrichAbilityText(text),
    getEffectiveAbilityText: (card) => TextEnricher.getEffectiveAbilityText(card),
    getEffectiveRawText: (card) => TextEnricher.getEffectiveRawText(card),
    isGenericInstruction: (text) => TextEnricher.isGenericInstruction(text),
    isRichAbility: (text) => TextEnricher.isRichAbility(text),
    getEffectiveActionText: (action) => TextEnricher.getEffectiveActionText(action),
    getActionTags: (action, vertical) => TextEnricher.getActionTags(action, vertical),

    addHighlight: (id, cls) => Highlighter.addHighlight(id, cls),
    clearHighlights: () => Highlighter.clearHighlights(),
    highlightAction: (a) => Highlighter.highlightAction(a),
    highlightPendingSource: () => Highlighter.highlightPendingSource(),
    highlightCardById: (src, cls, first) => Highlighter.highlightCardById(src, cls, first),
    highlightValidZones: (src, idx) => Highlighter.highlightValidZones(src, idx),
    highlightStageCard: (idx) => Highlighter.highlightStageCard(idx),
    highlightTargetsForAction: (act) => Highlighter.highlightTargetsForAction(act)
};

// Global Event Listeners for Tooltips
if (typeof document !== 'undefined') {
    document.body.addEventListener('mouseover', (e) => {
        const selector = '.card, .member-slot, .member-area, .board-slot-container, .energy-pip, .modifier-line, .action-btn, .action-group, .btn, .active-ability-tag, .perf-guide-entry, .perf-yell-card, .log-entry, .turn-event-item, .active-effect, .turn-event-hover-container, .active-effect-hover-container';
        const target = e.target.closest(selector);

        if (target) {
            if (tooltipHideTimeout) {
                clearTimeout(tooltipHideTimeout);
                tooltipHideTimeout = null;
            }
            Tooltips.showTooltip(target, e, null, false);
        } else {
            Tooltips.hideTooltip();
        }
    });

    document.body.addEventListener('mouseout', (e) => {
        const selector = '.card, .member-slot, .member-area, .board-slot-container, .energy-pip, .modifier-line, .action-btn, .action-group, .btn, .active-ability-tag, .perf-guide-entry, .perf-yell-card, .log-entry, .turn-event-item, .active-effect';
        const target = e.target.closest(selector);
        if (target) {
            const nextTarget = e.relatedTarget ? e.relatedTarget.closest(selector) : null;
            if (!nextTarget) {
                Tooltips.hideTooltip();
            }
        }
    });

    window.addEventListener('scroll', () => Tooltips.hideTooltip(true), { passive: true });
    window.addEventListener('click', () => Tooltips.hideTooltip(true));
}
