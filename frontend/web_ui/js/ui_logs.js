/**
 * UI Logs module
 * Handles rendering of Rule Log, Triggered Abilities, and Active Effects.
 * 
 * UNIFIED LOG SYSTEM:
 * This module provides a unified view combining:
 * 1. Active Effects (適用中の効果) - Current buffs/debuffs
 * 2. Turn History (ターン履歴) - Structured event data from turn_history
 * 3. Rule Log (ルールログ) - Text-based game log from rule_log
 */
import { State } from './state.js';
import { translations } from './translations_data.js';
import { Tooltips } from './ui_tooltips.js';

// Phase enum mapping (must match Rust backend)
const Phase = {
    RPS: 0, SETUP: 1, MULLIGAN_P1: 2, MULLIGAN_P2: 3,
    ACTIVE: 4, ENERGY: 5, DRAW: 6, MAIN: 7,
    LIVE_SET: 8, PERFORMANCE_P1: 9, PERFORMANCE_P2: 10, LIVE_RESULT: 11
};

export const Logs = {
    /**
     * Render unified log panel with Active Effects, Turn History, and Rule Log.
     * @param {string} containerId - Container element ID (default: 'rule-log')
     */
    renderRuleLog: (containerId = 'rule-log') => {
        const ruleLogEl = document.getElementById(containerId);
        if (!ruleLogEl) return;

        const state = State.data;
        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;
        const selectedTurn = State.selectedTurn || -1;
        const showingFullLog = State.showingFullLog;
        const t = translations ? translations[currentLang] : {};

        ruleLogEl.innerHTML = '';
        const fragment = document.createDocumentFragment();

        // === SECTION 1: Active Effects (適用中の効果) ===
        const activeEffectsSection = Logs.renderActiveEffectsSection(state, t);
        if (activeEffectsSection) {
            fragment.appendChild(activeEffectsSection);
        }

        // === SECTION 2: Turn History (ターン履歴) ===
        const turnHistorySection = Logs.renderTurnHistorySection(state, t, selectedTurn);
        if (turnHistorySection) {
            fragment.appendChild(turnHistorySection);
        }

        // === SECTION 3: Rule Log (ルールログ) ===
        const ruleLogSection = Logs.renderRuleLogSection(state, currentLang, showFriendlyAbilities, selectedTurn);
        if (ruleLogSection) {
            fragment.appendChild(ruleLogSection);
        }

        ruleLogEl.appendChild(fragment);
        if (!showingFullLog) ruleLogEl.scrollTop = ruleLogEl.scrollHeight;
    },

    /**
     * Render Active Effects section
     */
    renderActiveEffectsSection: (state, t) => {
        if (!state || !state.players) return null;

        const p0 = state.players[0];
        const p1 = state.players[1];
        let effects = [];

        const collectEffects = (p, pIdx) => {
            if (!p) return [];
            const isMe = pIdx === State.perspectivePlayer;
            const playerLabel = isMe ? (t['you'] || 'You') : (t['opponent'] || 'Opponent');
            let result = [];

            // Cost Reduction
            if (p.cost_reduction && p.cost_reduction !== 0) {
                result.push({
                    player: playerLabel,
                    desc: `${t['cost_reduction'] || 'Cost Reduction'}: ${p.cost_reduction > 0 ? '-' : '+'}${Math.abs(p.cost_reduction)}`,
                    type: 'buff'
                });
            }

            // Blade Buffs
            if (p.blade_buffs) {
                p.blade_buffs.forEach((val, idx) => {
                    if (val !== 0) {
                        result.push({
                            player: playerLabel,
                            desc: `${t['slot'] || 'Slot'} ${idx + 1}: Appeal ${val > 0 ? '+' : ''}${val}`,
                            type: val > 0 ? 'buff-blade' : 'debuff'
                        });
                    }
                });
            }

            // Heart Buffs
            if (p.heart_buffs) {
                const colors = ['Smile', 'Pure', 'Cool', 'Green', 'Blue', 'Purple', 'Wildcard'];
                p.heart_buffs.forEach((hb, idx) => {
                    if (hb && Array.isArray(hb)) {
                        let heartDesc = hb.map((count, cIdx) => count > 0 ? `${colors[cIdx]} +${count}` : null).filter(Boolean);
                        if (heartDesc.length > 0) {
                            result.push({
                                player: playerLabel,
                                desc: `${t['slot'] || 'Slot'} ${idx + 1}: ${heartDesc.join(', ')}`,
                                type: 'buff-heart'
                            });
                        }
                    }
                });
            }

            // Restrictions
            if (p.prevent_baton_touch > 0) {
                result.push({
                    player: playerLabel,
                    desc: t['cannot_baton_touch'] || 'Cannot Baton Touch',
                    type: 'restriction'
                });
            }
            if (p.prevent_activate > 0) {
                result.push({
                    player: playerLabel,
                    desc: t['cannot_activate_member'] || 'Cannot Activate Member Abilities',
                    type: 'restriction'
                });
            }

            return result;
        };

        effects = [...collectEffects(p0, State.perspectivePlayer), ...collectEffects(p1, 1 - State.perspectivePlayer)];

        if (effects.length === 0) return null;

        const section = document.createElement('div');
        section.className = 'log-section active-effects-section';

        const header = document.createElement('div');
        header.className = 'log-section-header';
        header.textContent = t['active_effects'] || '適用中の効果';
        section.appendChild(header);

        effects.forEach(e => {
            const entry = document.createElement('div');
            entry.className = `log-entry active-effect ${e.type || ''}`;
            const cardIdAttr = e.source_card_id !== undefined ? `data-card-id="${e.source_card_id}"` : '';
            const dataTextAttr = e.desc ? `data-text="${e.desc.replace(/"/g, '&quot;')}"` : '';
            entry.innerHTML = `<div class="active-effect-hover-container" ${cardIdAttr} ${dataTextAttr} style="display: contents;">
                <span class="player-badge p${State.perspectivePlayer}">${e.player}</span> ${e.desc}
            </div>`;
            section.appendChild(entry);
        });

        return section;
    },

    /**
     * Render Turn History section from structured turn_history data
     */
    renderTurnHistorySection: (state, t, selectedTurn) => {
        const history = state.turn_history || state.turn_events || [];
        if (!history || history.length === 0) return null;

        // Filter by selected turn
        const filteredHistory = selectedTurn !== -1
            ? history.filter(e => e.turn === selectedTurn)
            : history;

        if (filteredHistory.length === 0) return null;

        const section = document.createElement('div');
        section.className = 'log-section turn-history-section';

        const header = document.createElement('div');
        header.className = 'log-section-header';
        header.textContent = t['turn_history'] || 'ターン履歴';
        section.appendChild(header);

        filteredHistory.forEach(event => {
            const entry = Logs.createTurnEventElement(event, t);
            section.appendChild(entry);
        });

        return section;
    },

    /**
     * Create a single turn event element
     */
    createTurnEventElement: (event, t) => {
        const entry = document.createElement('div');
        const typeClass = event.event_type ? event.event_type.toLowerCase() : 'generic';
        entry.className = `log-entry turn-event ${typeClass}`;

        const playerLabel = event.player_id === State.perspectivePlayer
            ? (t['you'] || 'You')
            : (t['opponent'] || 'Opponent');

        const phaseKey = Logs.getPhaseKey(event.phase);
        const phaseLabel = t[phaseKey] || event.phase;
        const eventIcon = Logs.getEventIcon(event.event_type);

        // Accessibility: Add ARIA attributes
        entry.setAttribute('role', 'logentry');
        entry.setAttribute('aria-live', 'polite');
        entry.setAttribute('aria-label', `Turn ${event.turn}, ${phaseLabel}, ${playerLabel}: ${event.event_type} - ${event.description || ''}`);

        const cardIdAttr = event.card_id !== undefined ? `data-card-id="${event.card_id}"` : '';
        const cardNameAttr = event.card_name ? `data-card-name="${event.card_name}"` : '';
        const dataTextAttr = event.description ? `data-text="${event.description.replace(/"/g, '&quot;')}"` : '';

        entry.innerHTML = `
            <div class="turn-event-hover-container" ${cardIdAttr} ${cardNameAttr} ${dataTextAttr} style="display: contents;">
                <span class="turn-badge" aria-label="Turn ${event.turn}">T${event.turn}</span>
                <span class="phase-badge" aria-label="Phase: ${phaseLabel}">${phaseLabel}</span>
                <span class="player-badge p${event.player_id}" aria-label="Player: ${playerLabel}">${playerLabel}</span>
                <span class="event-type" aria-label="Event type: ${event.event_type || 'Event'}">${eventIcon} ${event.event_type || 'Event'}</span>
                <span class="event-desc">${event.description || ''}</span>
            </div>
        `;

        return entry;
    },

    /**
     * Get phase key for translation lookup
     */
    getPhaseKey: (phase) => {
        const perspectivePlayer = State.perspectivePlayer;
        switch (phase) {
            case Phase.RPS: return 'rps';
            case Phase.SETUP: return 'setup';
            case Phase.MULLIGAN_P1: return perspectivePlayer === 0 ? 'mulligan_you' : 'mulligan_opp';
            case Phase.MULLIGAN_P2: return perspectivePlayer === 1 ? 'mulligan_you' : 'mulligan_opp';
            case Phase.ACTIVE: return 'active';
            case Phase.ENERGY: return 'energy';
            case Phase.DRAW: return 'draw';
            case Phase.MAIN: return 'main';
            case Phase.LIVE_SET: return 'live_set';
            case Phase.PERFORMANCE_P1: return perspectivePlayer === 0 ? 'perf_p1' : 'perf_p2';
            case Phase.PERFORMANCE_P2: return perspectivePlayer === 1 ? 'perf_p1' : 'perf_p2';
            case Phase.LIVE_RESULT: return 'live_result';
            default: return String(phase);
        }
    },

    /**
     * Get icon for event type
     */
    getEventIcon: (eventType) => {
        const icons = {
            'PLAY': '🃏',
            'ACTIVATE': '⚡',
            'TRIGGER': '🎯',
            'EFFECT': '✨',
            'RULE': '📜',
            'YELL': '📣',
            'PERFORMANCE': '🎤',
            // New event types (Phase 2)
            'PHASE': '🔄',
            'DRAW': '📥',
            'SCORE': '📊',
            'HEART': '💖',
            'BATON': ' Baton',
            'LIVE': '🎵'
        };
        return icons[eventType] || '•';
    },

    /**
     * Render Rule Log section (text-based log)
     */
    renderRuleLogSection: (state, currentLang, showFriendlyAbilities, selectedTurn) => {
        let logData = state.rule_log || [];

        // Apply filtering
        if (selectedTurn !== -1) {
            const turnStr = `[Turn ${selectedTurn}]`;
            logData = logData.filter(entry => entry.includes(turnStr));
        }

        if (logData.length === 0) return null;

        const section = document.createElement('div');
        section.className = 'log-section rule-log-section';

        const header = document.createElement('div');
        header.className = 'log-section-header';
        header.textContent = currentLang === 'jp' ? 'ルールログ' : 'Rule Log';
        section.appendChild(header);

        let groupedLogs = [];
        let currentGroup = null;

        logData.forEach((entry) => {
            // Parse Execution ID: [Turn X] [ID: Y] Body OR [Turn X] Body
            const idMatch = entry.match(/\[Turn \d+\] \[ID: (\d+)\] (.*)/);
            const executionId = idMatch ? idMatch[1] : null;
            const body = idMatch ? idMatch[2] : entry.replace(/^\[Turn \d+\]\s*/, '');
            const turnMatch = entry.match(/^\[Turn \d+\]/);
            const turnPrefix = turnMatch ? turnMatch[0] : "";

            if (executionId) {
                if (!currentGroup || currentGroup.id !== executionId) {
                    currentGroup = { id: executionId, entries: [], turnPrefix };
                    groupedLogs.push(currentGroup);
                }
                currentGroup.entries.push(body);
            } else {
                currentGroup = null;
                groupedLogs.push({ entry, body, turnPrefix });
            }
        });

        groupedLogs.forEach(group => {
            if (group.entries) {
                const block = Logs.createGroupedLogBlock(group, currentLang, showFriendlyAbilities);
                section.appendChild(block);
            } else {
                const entry = Logs.createStandaloneLogEntry(group, currentLang, showFriendlyAbilities);
                section.appendChild(entry);
            }
        });

        return section;
    },

    /**
     * Create grouped log block (for ability execution groups)
     */
    createGroupedLogBlock: (group, currentLang, showFriendlyAbilities) => {
        const blockDiv = document.createElement('div');
        blockDiv.className = 'log-group-block';

        let headerEntry = group.entries[0];
        let detailEntries = group.entries.slice(1);

        const headerDiv = document.createElement('div');
        headerDiv.className = 'log-entry ability group-header';

        const headerContent = Logs.formatLogEntry(headerEntry, group.turnPrefix, currentLang, showFriendlyAbilities);
        const enrichedHeader = Tooltips.enrichAbilityText(headerContent);

        headerDiv.innerHTML = `
            <div class="log-entry-icon"></div>
            <div class="log-entry-content">${enrichedHeader}</div>
            <div class="log-group-toggle">▼</div>
        `;

        blockDiv.appendChild(headerDiv);

        if (detailEntries.length > 0) {
            const detailsContainer = document.createElement('div');
            detailsContainer.className = 'log-group-details';

            detailEntries.forEach(detail => {
                const detailDiv = document.createElement('div');
                detailDiv.className = 'log-entry effect detail';

                const detailContent = Logs.formatLogEntry(detail, "", currentLang, showFriendlyAbilities);
                const enrichedDetail = Tooltips.enrichAbilityText(detailContent);

                detailDiv.innerHTML = `
                    <div class="log-entry-icon"></div>
                    <div class="log-entry-content">${enrichedDetail}</div>
                `;
                detailsContainer.appendChild(detailDiv);
            });
            blockDiv.appendChild(detailsContainer);

            headerDiv.onclick = () => {
                const isCollapsed = detailsContainer.classList.toggle('collapsed');
                blockDiv.classList.toggle('open', !isCollapsed);
            };
        }

        return blockDiv;
    },

    /**
     * Create standalone log entry
     */
    createStandaloneLogEntry: (group, currentLang, showFriendlyAbilities) => {
        const div = document.createElement('div');
        div.className = 'log-entry';

        const bodyContent = Logs.formatLogEntry(group.body, group.turnPrefix, currentLang, showFriendlyAbilities);
        const enrichedBody = Tooltips.enrichAbilityText(bodyContent);

        const entryUpper = group.entry.toUpperCase();

        if ((entryUpper.includes("---") && entryUpper.includes("PHASE")) || entryUpper.includes("[ACTIVE PHASE]")) {
            div.classList.add('phase');
        } else if (entryUpper.includes('PLAYS') || entryUpper.includes('MULLIGAN') || entryUpper.includes('SELECTED')) {
            div.classList.add('action');
        } else if (entryUpper.includes('EFFECT:') || entryUpper.includes('RULE')) {
            div.classList.add('effect');
        } else if (entryUpper.includes('SCORE') || entryUpper.includes('SUCCESS LIVE')) {
            div.classList.add('score');
        } else if (group.entry.includes('===')) {
            div.classList.add('turn');
        }

        div.innerHTML = `
            <div class="log-entry-icon"></div>
            <div class="log-entry-content">${enrichedBody}</div>
        `;

        return div;
    },

    formatLogEntry: (body, turnPrefix, currentLang, showFriendlyAbilities) => {
        let displayText = body;
        let playerTag = "";

        // Identify player context from body
        if (body.startsWith("P1 ") || body.startsWith("[P1]")) {
            playerTag = `<span class="log-p-badge p1">P1</span>`;
            displayText = displayText.replace(/^\[?P1\]?\s?/, '');
        } else if (body.startsWith("P2 ") || body.startsWith("[P2]")) {
            playerTag = `<span class="log-p-badge p2">P2</span>`;
            displayText = displayText.replace(/^\[?P2\]?\s?/, '');
        }

        const abilityMatch = body.match(/\[TRIGGER:(\d+)\](.*?): (.*)/);
        const rustAbilityMatch = body.match(/(\[Rule .*?\]|\[Activated\]|\[Turn Start\]|\[Turn End\]|\[Triggered\])(.*?): (.*)/);

        if (abilityMatch || rustAbilityMatch) {
            const match = abilityMatch || rustAbilityMatch;
            let triggerLabel = "";
            let cardName = "";
            let pseudocode = "";

            if (abilityMatch) {
                const triggerId = parseInt(match[1]);
                cardName = match[2].trim();
                pseudocode = match[3].trim();
                triggerLabel = `[${triggerId}]`;
                if (translations[currentLang]?.triggers?.[triggerId]) {
                    triggerLabel = translations[currentLang].triggers[triggerId];
                }
            } else {
                triggerLabel = match[1].trim();
                cardName = match[2].trim();
                pseudocode = match[3].trim();
            }

            let translatedEffect = pseudocode;
            const shouldTranslate = (currentLang === 'en' || showFriendlyAbilities);

            if (shouldTranslate && window.translateAbility) {
                translatedEffect = window.translateAbility("EFFECT: " + pseudocode, currentLang);
                translatedEffect = translatedEffect.replace(/^.*?: /, '').replace(/^→ /, '');
            } else if (currentLang === 'jp' && !showFriendlyAbilities) {
                const srcCard = State.resolveCardDataByName(cardName);
                if (srcCard && (srcCard.original_text || srcCard.ability)) {
                    translatedEffect = srcCard.original_text || srcCard.ability;
                }
            }

            let displayCardName = cardName;
            if (currentLang === 'en' && window.NAME_MAP && window.NAME_MAP[cardName]) {
                displayCardName = window.NAME_MAP[cardName];
            }

            displayText = `${triggerLabel} <strong>${displayCardName}</strong>: ${translatedEffect}`;
        }

        const mulliganMatch = body.match(/(Mulligan): (.*)/i);
        if (mulliganMatch) {
            const cardName = mulliganMatch[2].trim();
            let displayPhase = currentLang === 'jp' ? "マリガン" : "Mulligan";
            let displayCardName = cardName;
            if (currentLang === 'en' && window.NAME_MAP && window.NAME_MAP[cardName]) {
                displayCardName = window.NAME_MAP[cardName];
            }
            displayText = `${displayPhase}: <strong>${displayCardName}</strong>`;
        }

        // Clean up internal tokens like HEART_BLUE
        displayText = displayText.replace(/HEART_RED/g, '[Red]')
            .replace(/HEART_YELLOW/g, '[Yellow]')
            .replace(/HEART_GREEN/g, '[Green]')
            .replace(/HEART_BLUE/g, '[Blue]')
            .replace(/HEART_PURPLE/g, '[Purple]')
            .replace(/HEART_PINK/g, '[Pink]')
            .replace(/HEART_WILD/g, '[Wild]');

        return (turnPrefix ? `<span class="log-turn-prefix">${turnPrefix}</span> ` : "") + playerTag + displayText;
    },

    renderActiveAbilities: (containerId, abilities) => {
        const el = document.getElementById(containerId);
        if (!el || !abilities) return;
        el.innerHTML = abilities.map(a => {
            const cardIdAttr = a.source_card_id !== undefined ? `data-card-id="${a.source_card_id}"` : '';
            const dataTextAttr = a.text || a.description ? `data-text="${a.text || a.description}"` : '';
            return `
                <div class="active-ability-tag" ${cardIdAttr} ${dataTextAttr}>
                    ${Tooltips.enrichAbilityText(a.name || 'Ability')}
                </div>
            `;
        }).join('');
    },

    renderActiveEffects: (state, p0, p1, t) => {
        const container = document.getElementById('active-effects-list');
        if (!container) return;

        let html = '';

        const renderPlayerEffects = (p, pIdx) => {
            if (!p) return '';
            let effects = [];
            const isMe = pIdx === State.perspectivePlayer;
            const badgeClass = isMe ? 'badge-p1' : 'badge-p2';
            const badgeLabel = isMe ? (t['you'] || 'You') : (t['opponent'] || 'Opponent');

            // Cost Reduction
            if (p.cost_reduction && p.cost_reduction !== 0) {
                effects.push({
                    title: t['cost_reduction'] || 'Cost Reduction',
                    desc: `${t['cost'] || 'Cost'} ${p.cost_reduction > 0 ? '-' : '+'}${Math.abs(p.cost_reduction)}`,
                    duration: t['until_end_of_turn'] || 'Until End of Turn',
                    type: 'buff'
                });
            }

            // Blade Buffs
            if (p.blade_buffs) {
                p.blade_buffs.forEach((val, idx) => {
                    if (val !== 0) {
                        effects.push({
                            title: `${t['slot'] || 'Slot'} ${idx + 1}: ${t['blade_buff'] || 'Blade Buff'}`,
                            desc: `Appeal ${val > 0 ? '+' : ''}${val}`,
                            duration: t['until_end_of_turn'] || 'Until End of Turn',
                            type: val > 0 ? 'buff-blade' : 'debuff'
                        });
                    }
                });
            }

            // Heart Buffs
            if (p.heart_buffs) {
                p.heart_buffs.forEach((hb, idx) => {
                    const colors = ['Smile', 'Pure', 'Cool', 'Green', 'Blue', 'Purple', 'Wildcard'];
                    let heartDesc = [];
                    if (hb && Array.isArray(hb)) {
                        hb.forEach((count, cIdx) => {
                            if (count > 0) {
                                heartDesc.push(`${colors[cIdx] || cIdx} +${count}`);
                            }
                        });
                    }
                    if (heartDesc.length > 0) {
                        effects.push({
                            title: `${t['slot'] || 'Slot'} ${idx + 1}: ${t['heart_buff'] || 'Heart Buff'}`,
                            desc: heartDesc.join(', '),
                            duration: t['until_end_of_turn'] || 'Until End of Turn',
                            type: 'buff-heart'
                        });
                    }
                });
            }

            // Game Restrictions
            if (p.prevent_baton_touch > 0) {
                effects.push({
                    title: t['restriction'] || 'Restriction',
                    desc: t['cannot_baton_touch'] || 'Cannot Baton Touch',
                    duration: t['until_end_of_turn'] || 'Until End of Turn',
                    type: 'restriction'
                });
            }
            if (p.prevent_activate > 0) {
                effects.push({
                    title: t['restriction'] || 'Restriction',
                    desc: t['cannot_activate_member'] || 'Cannot Activate Member Abilities',
                    duration: t['until_end_of_turn'] || 'Until End of Turn',
                    type: 'restriction'
                });
            }

            if (effects.length === 0) return '';

            let pStats = `<div class="effect-player-badge ${badgeClass}">${badgeLabel}</div>`;
            return pStats + effects.map(e => `
                <div class="effect-item ${e.type || ''}" ${e.desc ? `data-text="${e.desc.replace(/"/g, '&quot;')}"` : ''} ${e.source_card_id !== undefined ? `data-card-id="${e.source_card_id}"` : ''}>
                    <div class="effect-title-row">
                        <span class="effect-title">${e.title}</span>
                        <span class="effect-duration">${e.duration}</span>
                    </div>
                    <div class="effect-desc">${e.desc}</div>
                </div>
            `).join('');
        };

        html += renderPlayerEffects(p0, State.perspectivePlayer);
        html += renderPlayerEffects(p1, 1 - State.perspectivePlayer);

        if (!html) {
            container.innerHTML = `<div style="font-size: 0.75rem; color: var(--text-dim); text-align: center; padding: 10px;">${t['no_active_effects'] || 'No active effects'}</div>`;
        } else {
            container.innerHTML = html;
        }
    },

    // ========================================
    // FILTER FUNCTIONALITY
    // ========================================

    /**
     * Filter state for log entries
     */
    filterState: {
        eventTypes: new Set(['PLAY', 'ACTIVATE', 'TRIGGER', 'EFFECT', 'RULE', 'YELL', 'PERFORMANCE']),
        players: new Set([0, 1]),
        searchText: '',
        selectedTurn: -1
    },

    /**
     * Apply filters to events
     * @param {Array} events - Array of events to filter
     * @returns {Array} Filtered events
     */
    applyFilters: (events) => {
        const filters = Logs.filterState;
        return events.filter(e => {
            // Event type filter
            if (!filters.eventTypes.has(e.event_type)) return false;
            // Player filter
            if (!filters.players.has(e.player_id)) return false;
            // Turn filter
            if (filters.selectedTurn !== -1 && e.turn !== filters.selectedTurn) return false;
            // Search text filter
            if (filters.searchText && !e.description.toLowerCase().includes(filters.searchText.toLowerCase())) return false;
            return true;
        });
    },

    /**
     * Toggle event type filter
     * @param {string} eventType - Event type to toggle
     */
    toggleEventType: (eventType) => {
        if (Logs.filterState.eventTypes.has(eventType)) {
            Logs.filterState.eventTypes.delete(eventType);
        } else {
            Logs.filterState.eventTypes.add(eventType);
        }
        Logs.renderRuleLog();
    },

    /**
     * Toggle player filter
     * @param {number} playerId - Player ID to toggle (0 or 1)
     */
    togglePlayer: (playerId) => {
        if (Logs.filterState.players.has(playerId)) {
            Logs.filterState.players.delete(playerId);
        } else {
            Logs.filterState.players.add(playerId);
        }
        Logs.renderRuleLog();
    },

    /**
     * Set search text filter
     * @param {string} text - Search text
     */
    setSearchText: (text) => {
        Logs.filterState.searchText = text;
        Logs.renderRuleLog();
    },

    /**
     * Set turn filter
     * @param {number} turn - Turn number (-1 for all)
     */
    setTurnFilter: (turn) => {
        Logs.filterState.selectedTurn = turn;
        Logs.renderRuleLog();
    },

    /**
     * Reset all filters
     */
    resetFilters: () => {
        Logs.filterState = {
            eventTypes: new Set(['PLAY', 'ACTIVATE', 'TRIGGER', 'EFFECT', 'RULE', 'YELL', 'PERFORMANCE']),
            players: new Set([0, 1]),
            searchText: '',
            selectedTurn: -1
        };
        Logs.renderRuleLog();
    },

    /**
     * Render filter controls UI
     * @param {HTMLElement} container - Container element
     * @param {Object} t - Translations object
     */
    renderFilterControls: (container, t) => {
        const filterDiv = document.createElement('div');
        filterDiv.className = 'log-filter-controls';

        // Event type checkboxes
        const eventTypes = ['PLAY', 'ACTIVATE', 'TRIGGER', 'EFFECT', 'RULE', 'YELL'];
        const eventTypeHtml = eventTypes.map(type => {
            const checked = Logs.filterState.eventTypes.has(type) ? 'checked' : '';
            const label = t[`event_${type.toLowerCase()}`] || type;
            return `<label class="filter-checkbox">
                <input type="checkbox" value="${type}" ${checked} onchange="Logs.toggleEventType('${type}')">
                ${label}
            </label>`;
        }).join('');

        filterDiv.innerHTML = `
            <div class="filter-row">
                <input type="text" class="log-search-input" 
                    placeholder="${t['search_placeholder'] || 'Search...'}"
                    value="${Logs.filterState.searchText}"
                    oninput="Logs.setSearchText(this.value)">
            </div>
            <div class="filter-row event-type-filters">
                ${eventTypeHtml}
            </div>
        `;

        container.appendChild(filterDiv);
    },

    // ========================================
    // DIFFERENTIAL UPDATE FUNCTIONALITY
    // ========================================

    /**
     * Last rendered log count for differential updates
     */
    _lastLogCount: 0,
    _lastHistoryCount: 0,

    /**
     * Update log with differential rendering (append only new entries)
     * @param {string} containerId - Container element ID
     */
    updateLogDifferential: (containerId = 'rule-log') => {
        const ruleLogEl = document.getElementById(containerId);
        if (!ruleLogEl) return;

        const state = State.data;
        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;
        const t = translations ? translations[currentLang] : {};

        // Check if we need full re-render
        const currentLogCount = (state.rule_log || []).length;
        const currentHistoryCount = (state.turn_history || []).length;

        // If counts decreased (reset), do full render
        if (currentLogCount < Logs._lastLogCount || currentHistoryCount < Logs._lastHistoryCount) {
            Logs._lastLogCount = currentLogCount;
            Logs._lastHistoryCount = currentHistoryCount;
            Logs.renderRuleLog(containerId);
            return;
        }

        // Append new entries only
        const newLogEntries = state.rule_log.slice(Logs._lastLogCount);
        const newHistoryEntries = state.turn_history.slice(Logs._lastHistoryCount);

        if (newLogEntries.length === 0 && newHistoryEntries.length === 0) {
            return; // No new entries
        }

        const fragment = document.createDocumentFragment();

        // Append new turn history entries
        if (newHistoryEntries.length > 0) {
            const turnHistorySection = ruleLogEl.querySelector('.turn-history-section');
            if (turnHistorySection) {
                newHistoryEntries.forEach(event => {
                    const filteredEvent = Logs.applyFilters([event])[0];
                    if (filteredEvent) {
                        const entry = Logs.createTurnEventElement(event, t);
                        turnHistorySection.appendChild(entry);
                    }
                });
            }
        }

        // Append new rule log entries
        if (newLogEntries.length > 0) {
            const ruleLogSection = ruleLogEl.querySelector('.rule-log-section');
            if (ruleLogSection) {
                newLogEntries.forEach(entry => {
                    const div = Logs.createStandaloneLogEntry(
                        { entry, body: entry.replace(/^\[Turn \d+\]\s*/, ''), turnPrefix: '' },
                        currentLang,
                        showFriendlyAbilities
                    );
                    ruleLogSection.appendChild(div);
                });
            }
        }

        Logs._lastLogCount = currentLogCount;
        Logs._lastHistoryCount = currentHistoryCount;

        if (!State.showingFullLog) {
            ruleLogEl.scrollTop = ruleLogEl.scrollHeight;
        }
    },

    // ========================================
    // PERFORMANCE MONITORING (Phase 3)
    // ========================================

    /**
     * Performance metrics for monitoring
     */
    _perfMetrics: {
        renderTime: 0,
        entryCount: 0,
        filterTime: 0,
        lastRenderTimestamp: 0
    },

    /**
     * Start performance measurement
     */
    startPerfMeasure: () => {
        Logs._perfMetrics.renderTime = performance.now();
        Logs._perfMetrics.entryCount = 0;
        return Logs._perfMetrics.renderTime;
    },

    /**
     * End performance measurement and return duration
     */
    endPerfMeasure: (startMark) => {
        const duration = performance.now() - startMark;
        Logs._perfMetrics.renderTime = duration;
        return duration;
    },

    /**
     * Record entry count
     */
    recordEntryCount: (count) => {
        Logs._perfMetrics.entryCount += count;
    },

    /**
     * Get performance report
     */
    getPerfReport: () => {
        return {
            renderTime: Logs._perfMetrics.renderTime,
            entryCount: Logs._perfMetrics.entryCount,
            filterTime: Logs._perfMetrics.filterTime,
            avgRenderTime: Logs._perfMetrics.entryCount > 0
                ? Logs._perfMetrics.renderTime / Logs._perfMetrics.entryCount
                : 0
        };
    },

    /**
     * Check performance and log warning if slow
     */
    checkPerformance: (threshold = 100) => {
        const report = Logs.getPerfReport();
        if (report.renderTime > threshold) {
            console.warn(`[Log Performance] Render took ${report.renderTime.toFixed(2)}ms (threshold: ${threshold}ms)`);
            return true;
        }
        return false;
    }
};
