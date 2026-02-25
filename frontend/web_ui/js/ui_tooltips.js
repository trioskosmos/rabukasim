/**
 * UI Tooltips & Highlighting Module
 * Handles contextual tooltips, ability text enrichment, and visual highlights for actions.
 */
import { State } from './state.js';
import { Rendering } from './ui_rendering.js';
import { ICON_DATA_URIs } from './assets_registry.js';

let tooltipTimeout = null;
let tooltipHideTimeout = null;
let currentTooltipTarget = null;
let currentTooltipSidebarTarget = null;

// Pre-compiled regex patterns for performance
const REGEX_HTML_TAG = /<[^>]+>/g;
const REGEX_CURLY_TAG = /{{(.*?)\|(.*?)}}/g;
const REGEX_COLORS = /(ピンク|レッド|赤|イエロー|黄|グリーン|緑|ブルー|青|パープル|紫|オール|Pink|Red|Yellow|Green|Blue|Purple|All)/g;
const REGEX_MECHANICS = /(ハート|ピース|エナジー|ボルテージ|勧誘|Hearts|Blades|Energy|Voltage|Scout|Yell|RUSH|LIVE|LIVE!|Appeal|HEART|DREAM)/g;
const REGEX_SUCCESS = /(SUCCESS|成功)/g;
const REGEX_FAILURE = /(FAILURE|失敗)/g;
const REGEX_CARD_NUM = /(PL![\w-]+)/g;
const REGEX_NEWLINE = /\\n/g;

// Pre-built zone regex
const ZONE_LIST = ['控え室', 'メンバー置場', 'ライブ置場', 'エナジー置場', '待機室', '手札', 'デッキ', '山札', 'Discard', 'Stage', 'Live Zone', 'Hand', 'Deck', 'Performance'];
const REGEX_ZONES = new RegExp(`(${ZONE_LIST.join('|')})`, 'g');

// Pre-built icon map with pre-compiled regexes
const ICON_MAP = {
    '登場時': { path: 'toujyou.png', regex: /【登場時】/g },
    '[Play]': { path: 'toujyou.png', regex: /\[Play\]/g },
    'Play': { path: 'toujyou.png', regex: /【Play】/g },
    '自動': { path: 'jidou.png', regex: /【自動】/g },
    '[Auto]': { path: 'jidou.png', regex: /\[Auto\]/g },
    'Auto': { path: 'jidou.png', regex: /【Auto】/g },
    '永続': { path: 'jyouji.png', regex: /【永続】/g },
    '[Always]': { path: 'jyouji.png', regex: /\[Always\]/g },
    'Always': { path: 'jyouji.png', regex: /【Always】/g },
    '起動': { path: 'kidou.png', regex: /【起動】/g },
    '[Act]': { path: 'kidou.png', regex: /\[Act\]/g },
    'Act': { path: 'kidou.png', regex: /【Act】/g },
    'ターン1': { path: 'turn1.png', regex: /【ターン1】/g },
    'Turn 1': { path: 'turn1.png', regex: /【Turn 1】/g },
    '[Turn 1]': { path: 'turn1.png', regex: /\[Turn 1\]/g },
    'ライブスタート': { path: 'live_start.png', regex: /【ライブスタート】/g },
    'LIVE START': { path: 'live_start.png', regex: /【LIVE START】/g },
    '[Start]': { path: 'live_start.png', regex: /\[Start\]/g },
    'ピンク': { path: 'color_pink.png', regex: /【ピンク】/g },
    'Pink': { path: 'color_pink.png', regex: /【Pink】/g },
    'レッド': { path: 'color_red.png', regex: /【レッド】/g },
    '赤': { path: 'color_red.png', regex: /【赤】/g },
    'Red': { path: 'color_red.png', regex: /【Red】/g },
    'イエロー': { path: 'color_yellow.png', regex: /【イエロー】/g },
    '黄': { path: 'color_yellow.png', regex: /【黄】/g },
    'Yellow': { path: 'color_yellow.png', regex: /【Yellow】/g },
    'グリーン': { path: 'color_green.png', regex: /【グリーン】/g },
    '緑': { path: 'color_green.png', regex: /【緑】/g },
    'Green': { path: 'color_green.png', regex: /【Green】/g },
    'ブルー': { path: 'color_blue.png', regex: /【ブルー】/g },
    '青': { path: 'color_blue.png', regex: /【青】/g },
    'Blue': { path: 'color_blue.png', regex: /【Blue】/g },
    'パープル': { path: 'color_purple.png', regex: /【パープル】/g },
    '紫': { path: 'color_purple.png', regex: /【紫】/g },
    'Purple': { path: 'color_purple.png', regex: /【Purple】/g },
    'オール': { path: 'icon_all.png', regex: /【オール】/g },
    'All': { path: 'icon_all.png', regex: /【All】/g },
    'ライブ開始時': { path: 'live_start.png', regex: /【ライブ開始時】/g },
    '成功時': { path: 'live_success.png', regex: /【成功時】/g },
    'ライブ成功時': { path: 'live_success.png', regex: /【ライブ成功時】/g },
    'LIVE SUCCESS': { path: 'live_success.png', regex: /【LIVE SUCCESS】/g },
    '[Success]': { path: 'live_success.png', regex: /\[Success\]/g },
    'エネ': { path: 'icon_energy.png', regex: /【エネ】/g },
    'Energy': { path: 'icon_energy.png', regex: /【Energy】/g },
    'エネルギー': { path: 'icon_energy.png', regex: /【エネルギー】/g },
    'ハート': { path: 'heart_01.png', regex: /【ハート】/g },
    'Hearts': { path: 'heart_01.png', regex: /【Hearts】/g },
    'ピース': { path: 'heart_01.png', regex: /【ピース】/g },
    'ピンクハート': { path: 'heart_00.png', regex: /【ピンクハート】/g },
    'Pink Hearts': { path: 'heart_00.png', regex: /【Pink Hearts】/g },
    'レッドハート': { path: 'heart_01.png', regex: /【レッドハート】/g },
    'Red Hearts': { path: 'heart_01.png', regex: /【Red Hearts】/g },
    'イエローハート': { path: 'heart_02.png', regex: /【イエローハート】/g },
    'Yellow Hearts': { path: 'heart_02.png', regex: /【Yellow Hearts】/g },
    'グリーンハート': { path: 'heart_03.png', regex: /【グリーンハート】/g },
    'Green Hearts': { path: 'heart_03.png', regex: /【Green Hearts】/g },
    'ブルーハート': { path: 'heart_04.png', regex: /【ブルーハート】/g },
    'Blue Hearts': { path: 'heart_04.png', regex: /【Blue Hearts】/g },
    'パープルハート': { path: 'heart_05.png', regex: /【パープルハート】/g },
    'Purple Hearts': { path: 'heart_05.png', regex: /【Purple Hearts】/g },
    '全色ハート': { path: 'heart_06.png', regex: /【全色ハート】/g },
    'All Color Hearts': { path: 'heart_06.png', regex: /【All Color Hearts】/g },
    'ブレード': { path: 'icon_blade.png', regex: /【ブレード】/g },
    'Blade': { path: 'icon_blade.png', regex: /【Blade】/g },
    'Blades': { path: 'icon_blade.png', regex: /【Blades】/g },
    '開始時': { path: 'live_start.png', regex: /【開始時】/g },
};


// Pre-built icon replacement strings
const ICON_REPLACEMENTS = {};
for (const [key, data] of Object.entries(ICON_MAP)) {
    let style = 'height: 1.1em; vertical-align: middle;';
    if (data.path.includes('live_start') || data.path.includes('live_success')) {
        style += ' min-width: 3.5em;';
    } else if (data.path.includes('all')) {
        style += ' min-width: 2em;';
    }

    // Construct local path fallback
    let src = data.path.includes('/') ? `img/${data.path}` : `img/texticon/${data.path}`;

    // Check registry for data URI by filename (iconKey)
    const iconKey = data.path.replace('.png', '');
    if (typeof ICON_DATA_URIs !== 'undefined' && ICON_DATA_URIs[iconKey]) {
        src = ICON_DATA_URIs[iconKey];
    }

    ICON_REPLACEMENTS[key] = {
        regex: data.regex,
        replacement: `<span class="icon-wrapper"><img src="${src}" alt="${key}" style="${style}" onerror="this.style.visibility='hidden'"></span>`
    };
}


export const Tooltips = {
    /**
     * Replaces bracketed icons [Auto] and {{icon|alt}} with actual <img> tags.
     * Optimized with pre-compiled regex patterns.
     */
    enrichAbilityText: (text) => {
        if (!text) return "";

        // Keep a list of masked segments to restore later
        const placeholders = [];

        // 1. First, mask all existing HTML tags to prevent text-based highlighting from matching inside them
        text = text.replace(REGEX_HTML_TAG, (match) => {
            const id = `__TAG_${placeholders.length}__`;
            placeholders.push(match);
            return id;
        });

        // 2. Hide curly-brace tags {{...}} to prevent highlighting matching into alt text
        text = text.replace(REGEX_CURLY_TAG, (match) => {
            const id = `__PH_${placeholders.length}__`;
            placeholders.push(match);
            return id;
        });

        // 3. Apply text-based highlighting only on the unmasked text

        // Colors (SIC Attributes)
        text = text.replace(REGEX_COLORS, match => {
            const m = match.toLowerCase();
            let cls = 'hl-keyword';
            if (m.includes('pink') || m.includes('red') || m === 'ピンク' || m === 'レッド' || m === '赤') cls = 'hl-heart';
            if (m.includes('yellow') || m.includes('green') || m === 'イエロー' || m === '黄' || m === 'グリーン' || m === '緑') cls = 'hl-energy';
            if (m.includes('blue') || m.includes('purple') || m === 'ブルー' || m === '青' || m === 'パープル' || m === '紫') cls = 'hl-blade';
            return `<span class="${cls}">${match}</span>`;
        });

        // Zones (Discard, Stage, Live Zone)
        text = text.replace(REGEX_ZONES, '<span class="hl-zone">$1</span>');

        // Mechanics (Hearts, Blades, Energy, Yell)
        text = text.replace(REGEX_MECHANICS, '<span class="hl-keyword">$1</span>');

        // Success/Failure
        text = text.replace(REGEX_SUCCESS, '<span class="hl-success">$1</span>');
        text = text.replace(REGEX_FAILURE, '<span class="hl-failure">$1</span>');

        // Card Numbers (e.g., PL!HS-PR-010-PR)
        text = text.replace(REGEX_CARD_NUM, '<span class="hl-card">$1</span>');

        // 4. Restore ALL placeholders in reverse order to handle nesting if any occurred (though unlikely here)
        for (let i = placeholders.length - 1; i >= 0; i--) {
            text = text.replace(`__TAG_${i}__`, placeholders[i]);
            text = text.replace(`__PH_${i}__`, placeholders[i]);
        }

        // 5. Now insert icons using pre-built replacements
        for (const data of Object.values(ICON_REPLACEMENTS)) {
            // Reset regex lastIndex for global regex reuse
            data.regex.lastIndex = 0;
            text = text.replace(data.regex, data.replacement);
        }

        // --- Complex Replacement for {{icon|alt}} syntax ---
        text = text.replace(REGEX_CURLY_TAG, (match, img, alt) => {
            let src = "img/" + img;
            if (img.endsWith('.png') && !img.includes('/')) {
                src = "img/texticon/" + img;
            }
            let style = "height: 1.1em; vertical-align: middle;";
            if (img.includes('live_start') || img.includes('live_success')) {
                style += ' min-width: 3.2em;'; // Slightly tighter
            }
            const iconKey = img.replace('.png', '');
            if (typeof ICON_DATA_URIs !== 'undefined' && ICON_DATA_URIs[iconKey]) {
                src = ICON_DATA_URIs[iconKey];
            }
            // Use icon-wrapper for better spacing control
            return `<span class="icon-wrapper"><img src="${src}" alt="${alt}" style="${style}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';"><span style="display:none;">${alt}</span></span>`;
        });
        text = text.replace(REGEX_NEWLINE, '<br>');

        return text;
    },

    /**
     * Determines which ability text to show based on settings and language.
     */
    /**
     * Translates and enriches ability text for display.
     */
    getEffectiveAbilityText: (card) => {
        const raw = Tooltips.getEffectiveRawText(card);
        return Tooltips.enrichAbilityText(raw);
    },

    /**
     * Translates ability text based on settings and language, without HTML enrichment.
     */
    getEffectiveRawText: (card) => {
        if (!card) return "";
        const lang = State.currentLang;

        // Priority 1: Direct fields on the provided object
        let text = lang === 'en' ? (card.original_text_en || card.original_text) : card.original_text;

        // Priority 2: Fallback to card index lookup if the provided object is "thin" (common for STAGE members)
        if (!text && card.id !== undefined) {
            const indexed = Tooltips.findCardById(card.id);
            if (indexed && indexed !== card) {
                text = lang === 'en' ? (indexed.original_text_en || indexed.original_text) : indexed.original_text;
            }
        }

        // Priority 3: Last ditch fields
        if (!text) text = card.ability || card.original_text || "";

        return text;
    },

    /**
     * Identifies system strings that should not be displayed in the card-desc-panel.
     */
    isGenericInstruction: (text) => {
        if (!text) return true;
        const genericPatterns = [
            /戻して引き直します/,
            /引き直します/,
            /何もしない/,
            /次へ進みます/,
            /終了します/,
            /を確定して/,
            /キャンセルします/,
            /^Confirm$/i,
            /^Pass$/i,
            /^Skip$/i,
            /^Decline$/i,
            /^No$/i,
            /^Yes$/i
        ];
        return genericPatterns.some(p => p.test(text));
    },

    /**
     * Identifies text that appears to be a rich ability description or summary.
     */
    isRichAbility: (text) => {
        if (!text) return false;
        // Trust if it has icon markers, trigger brackets, or meaningful length
        return text.includes('{{') || text.includes('【') || text.includes('[') || text.length > 25;
    },

    /**
     * Helper to find a card object in the current game state by its unique ID.
     * Delegates to State.resolveCardData for consistency and deduplication.
     */
    findCardById: (cardId) => {
        return State.resolveCardData(cardId);
    },

    showTooltip: (target, e, forceTarget = null, useSidebar = false, explicitText = null) => {
        const effectiveTarget = forceTarget || target;
        // Robustly find the data source (handles hovering children like icons)
        const dataSource = effectiveTarget.closest('[data-card-id],[data-action-id],[data-text]') || effectiveTarget;

        const descPanel = document.getElementById('card-desc-panel');
        const descContent = document.getElementById('card-desc-content');
        const descTitle = document.getElementById('card-desc-title');

        // 1. HIGHLIGHT MANAGEMENT
        if (currentTooltipTarget && currentTooltipTarget !== dataSource) {
            currentTooltipTarget.classList.remove('highlight-hover');
        }
        currentTooltipTarget = dataSource;
        dataSource.classList.add('highlight-hover');

        // 2. DATA RESOLUTION
        const state = State.data;
        const perspectivePlayer = State.perspectivePlayer;
        let cardObj = null;
        let actionObj = null;

        // Resolve via Action OR Card ID
        const actionId = dataSource.dataset.actionId;
        const cardId = dataSource.dataset.cardId;

        if (actionId !== undefined && state && state.legal_actions) {
            actionObj = state.legal_actions.find(a => a.id === parseInt(actionId));
            if (actionObj) {
                Tooltips.highlightAction(actionObj);
                const p = state.players[perspectivePlayer];
                // Priority 1: Index-based lookup for your own cards (most specific)
                if (p) {
                    if (actionObj.hand_idx !== undefined && p.hand) cardObj = p.hand[actionObj.hand_idx];
                    else if (actionObj.area_idx !== undefined && p.stage) cardObj = p.stage[actionObj.area_idx];
                    else if (actionObj.slot_idx !== undefined && p.stage) cardObj = p.stage[actionObj.slot_idx];
                    // Also check live_zone and energy for action-based lookups
                    else if (actionObj.live_idx !== undefined && p.live_zone) cardObj = p.live_zone[actionObj.live_idx];
                    else if (actionObj.energy_idx !== undefined && p.energy) {
                        const energySlot = p.energy[actionObj.energy_idx];
                        if (energySlot && energySlot.card) cardObj = energySlot.card;
                    }
                }
                // Priority 2: source_card_id (fallback when no position info)
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

        // --- MASTER DATA RECONCILIATION ---
        // If we found a cardObj, immediately try to get the "richest" version from the index
        if (cardObj && cardObj.id !== undefined && cardObj.id >= 0) {
            const master = Tooltips.findCardById(cardObj.id);
            if (master) cardObj = master;
        }

        // --- RESOLVE FINAL DISPLAY TEXT ---
        const dText = dataSource.dataset.text;
        let cardText = (cardObj && !cardObj.hidden) ? Tooltips.getEffectiveRawText(cardObj) : "";
        let finalText = "";

        // PRIORITY RESOLUTION (Top-Down):
        // 1. Contextual summary from element attribute is preferred for actions
        if (dText && !Tooltips.isGenericInstruction(dText)) {
            finalText = dText;
        }
        // 2. Fallback to master card ability text
        else if (cardText) {
            finalText = cardText;
        }
        // 3. Absolute fallback: even if generic, show it if no cardObj is present (unlikely)
        else if (dText && !cardObj) {
            finalText = dText;
        }

        // Resilience: We ONLY hide if we have absolutely NO text to show.
        // Even if cardObj is missing/placeholder, we show the panel if we have text.
        if (!finalText) {
            descPanel.style.display = 'none';
            return;
        }

        // IDENTITY RESOLUTION: Always set title from card identity if available
        const titleText = (cardObj && cardObj.name) ? cardObj.name : (dataSource.dataset.cardName || "Card Detail");

        if (descTitle) {
            descTitle.innerHTML = titleText;
            descTitle.style.display = titleText ? 'block' : 'none';
        }

        const enrichedText = Tooltips.enrichAbilityText(finalText);
        descContent.innerHTML = enrichedText;
        descContent.dataset.rawText = finalText;
        descPanel.style.display = 'flex';

        // Success: we clear any "stale" hiding logic
        if (tooltipHideTimeout) {
            clearTimeout(tooltipHideTimeout);
            tooltipHideTimeout = null;
        }

        // 4. FLOATING TOOLTIP REMOVAL (Cleanup)
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

            // Remove highlight from previous target
            if (currentTooltipTarget) {
                currentTooltipTarget.classList.remove('highlight-hover');
            }
            currentTooltipTarget = null;

            // CRITICAL: We NO LONGER hide the card-desc-panel on mouseout.
            // It persists until a new card is hovered or the page is refreshed.
            // This fixes the "only sometimes comes up" issue by preventing it from disappearing 
            // when the mouse moves between cards or into "dead space" between elements.
            Tooltips.clearHighlights();
        };

        if (immediate) {
            clearTimeout(tooltipHideTimeout);
            hideAction();
            return;
        }

        if (tooltipHideTimeout) return;
        tooltipHideTimeout = setTimeout(hideAction, 100);
    },

    addHighlight: (idOrEl, className) => {
        const el = typeof idOrEl === 'string' ? document.getElementById(idOrEl) : idOrEl;
        if (el) {
            el.classList.add(className);
            if (el.closest && el.closest('.card-area.hand')) {
                el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        }
    },

    clearHighlights: () => {
        document.querySelectorAll('.highlight-source, .highlight-target, .highlight-target-opp, .valid-drop-target, .drop-hover, .highlight-hover').forEach(el => {
            el.classList.remove('highlight-source', 'highlight-target', 'highlight-target-opp', 'valid-drop-target', 'drop-hover', 'highlight-hover');
        });
    },

    highlightAction: (a) => {
        const state = State.data;
        if (!state) return;
        Tooltips.clearHighlights();

        const perspectivePlayer = State.perspectivePlayer;
        const actingPlayer = state.current_player ?? state.active_player;
        const selfPrefix = (actingPlayer === perspectivePlayer ? 'my' : 'opp');
        const oppPrefix = (actingPlayer === perspectivePlayer ? 'opp' : 'my');

        // Helper to get prefix for a target player
        const getPlayerPrefix = (targetId) => {
            if (targetId === undefined) return selfPrefix;
            return (targetId === perspectivePlayer ? 'my' : 'opp');
        };

        const m = a.metadata || {};
        const targetPlayer = m.target_player;
        const targetPrefix = getPlayerPrefix(targetPlayer);

        let specificHighlighted = false;

        if (a.type === 'PLAY') {
            if (a.hand_idx !== undefined) {
                Tooltips.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-source');
                specificHighlighted = true;
            }
            if (a.area_idx !== undefined) {
                Tooltips.addHighlight(`${selfPrefix}-stage-slot-${a.area_idx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'LIVE_SET') {
            if (a.hand_idx !== undefined) {
                Tooltips.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-source');
                specificHighlighted = true;
            }
            Tooltips.addHighlight(`${selfPrefix}-live`, 'highlight-target');
            specificHighlighted = true;
        } else if (a.type === 'ABILITY' || (a.metadata && a.metadata.category === 'ABILITY')) {
            if (a.location === 'discard' || (a.metadata && a.metadata.location === 'discard')) {
                Tooltips.addHighlight(`${selfPrefix}-discard`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.area_idx !== undefined) {
                Tooltips.addHighlight(`${selfPrefix}-stage-slot-${a.area_idx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.slot_idx !== undefined) {
                Tooltips.addHighlight(`${targetPrefix}-stage-slot-${a.slot_idx}`, 'highlight-source');
                specificHighlighted = true;
            } else if (a.source_card_id !== undefined && a.source_card_id !== -1) {
                // Find and highlight by ID if indices aren't available
                Tooltips.highlightCardById(a.source_card_id);
                specificHighlighted = true;
            }
        } else if (a.type === 'MULLIGAN') {
            if (a.hand_idx !== undefined) {
                Tooltips.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_HAND') {
            const hIdx = a.hand_idx ?? m.hand_idx;
            if (hIdx !== undefined) {
                const id = `${targetPrefix}-hand-card-${hIdx}`;
                Tooltips.addHighlight(id, 'highlight-source');
                specificHighlighted = true;
                const card = document.getElementById(id);
                if (card && card.dataset.text) {
                    Tooltips.showTooltip(card, { clientX: card.getBoundingClientRect().right + 10, clientY: card.getBoundingClientRect().top });
                }
            }
        } else if (a.type === 'SELECT_STAGE' || a.type === 'SELECT_MEMBER') {
            const idx = a.slot_idx ?? a.area_idx ?? m.slot_idx;
            if (idx !== undefined) {
                const id = `${targetPrefix}-stage-slot-${idx}`;
                Tooltips.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
                const slot = document.getElementById(id);
                if (slot && slot.dataset.text) {
                    Tooltips.showTooltip(slot, { clientX: slot.getBoundingClientRect().right + 10, clientY: slot.getBoundingClientRect().top });
                }
            }
        } else if (a.type === 'SELECT' || a.type === 'TARGET_OPPONENT' || m.category === 'CHOICE' || m.category === 'SELECT') {
            if (a.type === 'TARGET_OPPONENT' || (state.pending_choice && state.pending_choice.type === 'TARGET_OPPONENT_MEMBER') || m.opcode === 32) { // O_TAP_OPPONENT = 32
                const idx = a.index ?? a.slot_idx ?? m.slot_idx;
                if (idx !== undefined) {
                    const prefix = (a.type === 'TARGET_OPPONENT' || m.opcode === 32) ? oppPrefix : targetPrefix;
                    const id = `${prefix}-stage-slot-${idx}`;
                    Tooltips.addHighlight(id, 'highlight-target');
                    specificHighlighted = true;
                }
            } else if (m.hand_idx !== undefined) {
                const id = `${targetPrefix}-hand-card-${m.hand_idx}`;
                Tooltips.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            } else if (m.slot_idx !== undefined) {
                const id = `${targetPrefix}-stage-slot-${m.slot_idx}`;
                Tooltips.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            } else if (m.energy_idx !== undefined) {
                const id = `${targetPrefix}-energy-slot-${m.energy_idx}`;
                Tooltips.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            } else {
                Tooltips.addHighlight(`select-list-item-${a.index ?? a.id}`, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'SELECT_DISCARD' || m.category === 'DISCARD') {
            Tooltips.addHighlight(`${targetPrefix}-discard`, 'highlight-target');
            specificHighlighted = true;
        } else if (a.type === 'COLOR' || (a.id >= 580 && a.id <= 586)) {
            // Visual aids for color select
            specificHighlighted = true;
        } else if (a.type === 'SELECT_LIVE' || a.type === 'LIVE_PERFORM' || (a.id >= 900 && a.id <= 902) || m.category === 'LIVE') {
            const idx = (a.area_idx !== undefined) ? a.area_idx : (a.slot_idx !== undefined ? a.slot_idx : (a.id >= 900 && a.id <= 902 ? a.id - 900 : (a.id >= 600 && a.id <= 602 ? a.id - 600 : -1)));
            if (idx !== -1) {
                const id = `${targetPrefix}-live-slot-${idx}`;
                Tooltips.addHighlight(id, 'highlight-target');
                specificHighlighted = true;
            }
        } else if (a.type === 'FORMATION' || a.type === 'MOVE') {
            if (a.src_idx !== undefined || a.source_idx !== undefined || a.prev_idx !== undefined) {
                const idx = a.src_idx !== undefined ? a.src_idx : (a.source_idx !== undefined ? a.source_idx : a.prev_idx);
                Tooltips.addHighlight(`${targetPrefix}-stage-slot-${idx}`, 'highlight-source');
            }
            if (a.dst_idx !== undefined || a.area_idx !== undefined || a.slot_idx !== undefined) {
                const idx = a.dst_idx !== undefined ? a.dst_idx : (a.area_idx !== undefined ? a.area_idx : a.slot_idx);
                Tooltips.addHighlight(`${targetPrefix}-stage-slot-${idx}`, 'highlight-target');
            }
            specificHighlighted = true;
        }

        // --- CATCH-ALL FOR ALL ACTION IDs ---
        // If not specific highlighted, but we have common indices, try to highlight them as target
        if (!specificHighlighted) {
            // Check for explicit ID ranges if metadata is missing
            const aid = a.id;
            if (aid >= 600 && aid <= 602) { // Stage/Live Slot selection
                const prefix = (state.phase === 'LiveResult' ? selfPrefix : oppPrefix); // Typically targets opponent in Response
                const targetId = state.phase === 'LiveResult' ? `${prefix}-live-slot-${aid - 600}` : `${prefix}-stage-slot-${aid - 600}`;
                Tooltips.addHighlight(targetId, 'highlight-target');
            } else if (aid >= 300 && aid <= 399) { // Mulligan (only applies in Mulligan phase or if type is explicitly MULLIGAN)
                if (state.phase && state.phase.includes('Mulligan')) {
                    Tooltips.addHighlight(`${selfPrefix}-hand-card-${aid - 300}`, 'highlight-target');
                }
            } else if (aid >= 400 && aid <= 499) { // Live Set
                Tooltips.addHighlight(`${selfPrefix}-hand-card-${aid - 400}`, 'highlight-source');
                Tooltips.addHighlight(`${selfPrefix}-live`, 'highlight-target');
            } else if (aid >= 500 && aid <= 509) { // SELECT_MODE
                // Intentionally do nothing. Mode choices are abstract and don't target hand cards.
            } else if (aid >= 8000 && aid <= 8999) { // LOOK_AND_CHOOSE or generic choice
                // For LOOK_AND_CHOOSE, the UI element often has data-action-id matching this, 
                // but the card itself might be in the looked-cards panel.
                // It is abstract in terms of board state highlighting.
            } else {
                const slotIdx = a.slot_idx !== undefined ? a.slot_idx : (a.index !== undefined ? a.index : a.choice_idx);
                if (slotIdx !== undefined && slotIdx !== -1) {
                    if (a.type === 'SELECT_LIVE' || (a.id >= 900 && a.id <= 902)) {
                        Tooltips.addHighlight(`${selfPrefix}-live-slot-${slotIdx}`, 'highlight-target');
                    } else {
                        Tooltips.addHighlight(`${selfPrefix}-stage-slot-${slotIdx}`, 'highlight-target');
                    }
                }
                if (a.hand_idx !== undefined && a.hand_idx !== -1) {
                    Tooltips.addHighlight(`${selfPrefix}-hand-card-${a.hand_idx}`, 'highlight-target');
                }
                if (a.area_idx !== undefined && a.area_idx !== -1) {
                    const id = a.type === 'LIVE_SET' ? `${selfPrefix}-live-slot-${a.area_idx}` : `${selfPrefix}-stage-slot-${a.area_idx}`;
                    Tooltips.addHighlight(id, 'highlight-target');
                }
            }
        }

        // Only highlight by source_card_id if not already specifically highlighted by position
        // This prevents highlighting ALL cards with the same ID when we already found the specific one
        if (!specificHighlighted) {
            let srcCardId = a.source_card_id;
            // If action has no source but we're in a pending choice, the choice might have the source
            if ((srcCardId === undefined || srcCardId === -1) && state.pending_choice) {
                srcCardId = state.pending_choice.source_card_id || (state.pending_choice.params ? state.pending_choice.params.source_card_id : -1);
            }

            if (srcCardId !== undefined && srcCardId !== -1) {
                Tooltips.highlightCardById(srcCardId, 'highlight-source');
            }
        }
    },

    highlightPendingSource: () => {
        const state = State.data;
        if (!state || !state.pending_choice) return;
        const choice = state.pending_choice;
        const srcId = choice.source_card_id || (choice.params ? choice.params.source_card_id : -1);

        if (srcId === undefined || srcId === -1) return;

        let found = false;
        const perspectivePlayer = State.perspectivePlayer;
        const selfPrefix = (state.active_player === perspectivePlayer ? 'my' : 'opp');

        const area = choice.area !== undefined ? choice.area : (choice.params ? choice.params.area : undefined);
        if (area !== undefined) {
            Tooltips.addHighlight(`${selfPrefix}-stage-slot-${area}`, 'highlight-source');
            found = true;
        }

        const handIdx = choice.hand_idx !== undefined ? choice.hand_idx : (choice.params ? choice.params.hand_idx : undefined);
        if (handIdx !== undefined) {
            Tooltips.addHighlight(`${selfPrefix}-hand-card-${handIdx}`, 'highlight-source');
            found = true;
        }

        if (!found) {
            Tooltips.highlightCardById(srcId);
        }
    },

    highlightCardById: (srcId, className = 'highlight-source', firstOnly = true) => {
        const state = State.data;
        if (!state) return;

        const perspectivePlayer = State.perspectivePlayer;
        const playersMap = [
            { id: perspectivePlayer, prefix: 'my' },
            { id: 1 - perspectivePlayer, prefix: 'opp' }
        ];

        for (const pMap of playersMap) {
            const p = state.players[pMap.id];
            if (!p) continue;

            // Check stage
            if (p.stage) {
                for (let idx = 0; idx < p.stage.length; idx++) {
                    const card = p.stage[idx];
                    const cid = card ? card.id : -1;
                    if (cid === srcId) {
                        Tooltips.addHighlight(`${pMap.prefix}-stage-slot-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
            // Check hand
            if (p.hand) {
                for (let idx = 0; idx < p.hand.length; idx++) {
                    const card = p.hand[idx];
                    const cid = card ? card.id : -1;
                    if (cid === srcId) {
                        Tooltips.addHighlight(`${pMap.prefix}-hand-card-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
            // Check live_zone
            if (p.live_zone) {
                for (let idx = 0; idx < p.live_zone.length; idx++) {
                    const cardObj = p.live_zone[idx];
                    const cid = cardObj ? cardObj.id : -1;
                    if (cid === srcId) {
                        Tooltips.addHighlight(`${pMap.prefix}-live-slot-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
            // Check discard
            if (p.discard && p.discard.some(c => (typeof c === 'object' ? c.id === srcId : c === srcId))) {
                Tooltips.addHighlight(`${pMap.prefix}-discard`, className);
                if (firstOnly) return;
            }
            // Check energy
            if (p.energy) {
                for (let idx = 0; idx < p.energy.length; idx++) {
                    const e = p.energy[idx];
                    const cid = (e && e.card) ? e.card.id : -1;
                    if (cid === srcId) {
                        Tooltips.addHighlight(`${pMap.prefix}-energy-slot-${idx}`, className);
                        if (firstOnly) return;
                    }
                }
            }
        }
    },

    highlightValidZones: (source, index) => {
        const state = State.data;
        if (!state || !state.legal_actions) return;

        const validTargets = new Set();
        const handIdx = index;

        state.legal_actions.forEach(a => {
            if (source === 'hand') {
                if (a.hand_idx === handIdx) {
                    if (a.type === 'PLAY' || a.type === 'FORMATION') {
                        if (a.area_idx !== undefined) validTargets.add(`my-stage-slot-${a.area_idx}`);
                        if (a.slot_idx !== undefined) validTargets.add(`my-stage-slot-${a.slot_idx}`);
                    }
                    if (a.type === 'LIVE_SET') {
                        if (a.slot_idx !== undefined) {
                            validTargets.add(`my-live-slot-${a.slot_idx}`);
                        } else {
                            for (let i = 0; i < 3; i++) validTargets.add(`my-live-slot-${i}`);
                        }
                    }
                }
                if ((a.hand_idx === handIdx || a.index === handIdx) &&
                    (a.type === 'SELECT_HAND' || (a.name && a.name.includes('Discard')))) {
                    validTargets.add('my-discard');
                }
                if (a.hand_idx === handIdx && a.id >= 600 && a.id <= 602) {
                    validTargets.add(`opp-stage-slot-${a.id - 600}`);
                }
            } else if (source === 'stage') {
                const sourceSlot = index;
                if (a.id >= 600 && a.id <= 602) {
                    validTargets.add(`opp-stage-slot-${a.id - 600}`);
                }
                if ((a.type === 'FORMATION' || a.type === 'MOVE') &&
                    (a.source_idx === sourceSlot || a.prev_idx === sourceSlot)) {
                    if (a.area_idx !== undefined) validTargets.add(`my-stage-slot-${a.area_idx}`);
                    if (a.slot_idx !== undefined) validTargets.add(`my-stage-slot-${a.slot_idx}`);
                }
            } else if (source === 'discard') {
                if (a.discard_idx === index || a.index === index) {
                    if (a.type === 'SELECT_DISCARD' || a.type === 'SELECT_CARD') {
                        validTargets.add('my-hand');
                    }
                    if (a.type === 'PLAY_MEMBER_FROM_DISCARD') {
                        if (a.area_idx !== undefined) validTargets.add(`my-stage-slot-${a.area_idx}`);
                    }
                }
            } else if (source === 'deck') {
                const Phase = { DRAW: 'DRAW' }; // Fallback
                if (a.id === 2 || (a.id === 0 && state.phase === Phase.DRAW)) {
                    validTargets.add('my-hand');
                }
            }
        });

        validTargets.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.add('valid-drop-target');
                if (id.includes('slot-')) {
                    const container = el.closest('.board-slot-container');
                    if (container) container.classList.add('valid-drop-target');
                }
            }
        });
    },

    highlightStageCard: (areaIdx) => {
        Tooltips.clearHighlights();
        Tooltips.addHighlight(`my-stage-slot-${areaIdx}`, 'highlight-source');
    },

    getEffectiveActionText: (action) => {
        if (!action) return "";
        const rawText = action.raw_text || action.text || "";

        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;

        // Special handling: if it's an action with a source card, use the standardized card text resolution logic
        // for consistency, unless it's a generic action without a specific source card text.
        if (action.source_card_id !== undefined && action.source_card_id !== -1) {
            const srcCard = State.resolveCardData(action.source_card_id);
            if (srcCard && (srcCard.text || srcCard.ability_text || srcCard.original_text || srcCard.ability)) {
                return Tooltips.enrichAbilityText(Tooltips.getEffectiveRawText(srcCard));
            }
        }

        let effectiveText = rawText;
        if ((currentLang === 'en' || showFriendlyAbilities) && window.translateAbility) {
            effectiveText = window.translateAbility(rawText, currentLang);
        } else if (currentLang === 'jp') {
            const srcCard = State.resolveCardData(action.source_card_id);
            if (srcCard && (srcCard.original_text || srcCard.ability)) {
                effectiveText = srcCard.original_text || srcCard.ability;
            } else if (window.translateAbility) {
                effectiveText = window.translateAbility(rawText, 'jp');
            }
        }

        // Apply icon enrichment
        let text = Tooltips.enrichAbilityText(effectiveText);

        // Final cleanup: strip technical prefixes if they persist in the summary
        text = text.replace(/TRIGGER:\s*/g, '');
        text = text.replace(/\[TRIGGER\]\s*/g, '');

        return text;
    },

    getActionTags: (action, vertical = false) => {
        if (!action || !action.triggers) return "";
        const tags = [];
        if (action.triggers.includes(1)) tags.push(`<img src="img/texticon/toujyou.png" alt="[登場時]" style="height:14px; vertical-align:middle;">`);
        if (action.triggers.includes(2)) tags.push(`<img src="img/texticon/live_kaishi.png" alt="[開始時]" style="height:14px; vertical-align:middle;">`);
        if (action.triggers.includes(7)) tags.push(`<img src="img/texticon/kidou.png" alt="[起動]" style="height:14px; vertical-align:middle;">`);
        if (action.triggers.includes(6)) tags.push(`<img src="img/texticon/jyouji.png" alt="[常時]" style="height:14px; vertical-align:middle;">`);

        if (tags.length === 0) return "";
        if (vertical) {
            return `<div style="display:flex; flex-direction:column; align-items:center; gap:1px; margin-left:4px;">${tags.join('')}</div>`;
        }
        return `<div style="display:flex; gap:3px; margin-top:2px;">${tags.join('')}</div>`;
    }
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
