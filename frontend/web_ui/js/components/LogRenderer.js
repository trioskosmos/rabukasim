import { State } from '../state.js';
import { translations } from '../translations_data.js';
import { Tooltips } from '../ui_tooltips.js';
import { LogFilter } from '../utils/LogFilter.js';
import { PerformanceMonitor } from '../utils/PerformanceMonitor.js';

const Phase = {
    RPS: 0, SETUP: 1, MULLIGAN_P1: 2, MULLIGAN_P2: 3,
    ACTIVE: 4, ENERGY: 5, DRAW: 6, MAIN: 7,
    LIVE_SET: 8, PERFORMANCE_P1: 9, PERFORMANCE_P2: 10, LIVE_RESULT: 11
};

export const LogRenderer = {
    renderRuleLog: (containerId = 'rule-log') => {
        const ruleLogEl = document.getElementById(containerId);
        if (!ruleLogEl) return;

        PerformanceMonitor.startPerfMeasure();

        const state = State.data;
        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;
        const selectedTurn = State.selectedTurn || -1;
        const showingFullLog = State.showingFullLog;
        const t = translations ? translations[currentLang] : {};

        ruleLogEl.innerHTML = '';
        const fragment = document.createDocumentFragment();

        // === SECTION 1: Active Effects ===
        const activeEffectsSection = LogRenderer.renderActiveEffectsSection(state, t);
        if (activeEffectsSection) {
            fragment.appendChild(activeEffectsSection);
        }

        // === SECTION 2: Turn History ===
        const turnHistorySection = LogRenderer.renderTurnHistorySection(state, t, selectedTurn);
        if (turnHistorySection) {
            fragment.appendChild(turnHistorySection);
        }

        // === SECTION 3: Rule Log ===
        const ruleLogSection = LogRenderer.renderRuleLogSection(state, currentLang, showFriendlyAbilities, selectedTurn);
        if (ruleLogSection) {
            fragment.appendChild(ruleLogSection);
        }

        ruleLogEl.appendChild(fragment);
        if (!showingFullLog) ruleLogEl.scrollTop = ruleLogEl.scrollHeight;

        PerformanceMonitor.endPerfMeasure();
    },

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

            if (p.cost_reduction && p.cost_reduction !== 0) {
                result.push({
                    player: playerLabel,
                    desc: `${t['cost_reduction'] || 'Cost Reduction'}: ${p.cost_reduction > 0 ? '-' : '+'}${Math.abs(p.cost_reduction)}`,
                    type: 'buff'
                });
            }

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

            const card = e.source_card_id !== undefined ? Tooltips.findCardById(e.source_card_id) : null;
            const container = document.createElement('div');
            container.className = 'active-effect-hover-container';
            container.style.display = 'contents';
            Tooltips.attachCardData(container, card);

            if (e.desc) container.setAttribute('data-text', e.desc);

            container.innerHTML = `<span class="player-badge p${State.perspectivePlayer}">${e.player}</span> ${e.desc}`;
            entry.appendChild(container);
            section.appendChild(entry);
        });

        PerformanceMonitor.recordEntryCount(effects.length);
        return section;
    },

    renderTurnHistorySection: (state, t, selectedTurn) => {
        const history = state.turn_history || state.turn_events || [];
        if (!history || history.length === 0) return null;

        const filteredHistory = LogFilter.applyFilters(history);

        if (filteredHistory.length === 0) return null;

        const section = document.createElement('div');
        section.className = 'log-section turn-history-section';

        const header = document.createElement('div');
        header.className = 'log-section-header';
        header.textContent = t['turn_history'] || 'ターン履歴';
        section.appendChild(header);

        filteredHistory.forEach(event => {
            const entry = LogRenderer.createTurnEventElement(event, t);
            section.appendChild(entry);
        });

        PerformanceMonitor.recordEntryCount(filteredHistory.length);
        return section;
    },

    createTurnEventElement: (event, t) => {
        const entry = document.createElement('div');
        const typeClass = event.event_type ? event.event_type.toLowerCase() : 'generic';
        entry.className = `log-entry turn-event ${typeClass}`;

        const playerLabel = event.player_id === State.perspectivePlayer
            ? (t['you'] || 'You')
            : (t['opponent'] || 'Opponent');

        const phaseKey = LogRenderer.getPhaseKey(event.phase);
        const phaseLabel = t[phaseKey] || event.phase;
        const eventIcon = LogRenderer.getEventIcon(event.event_type);

        entry.setAttribute('role', 'logentry');
        entry.setAttribute('aria-live', 'polite');
        entry.setAttribute('aria-label', `Turn ${event.turn}, ${phaseLabel}, ${playerLabel}: ${event.event_type} - ${event.description || ''}`);

        const card = event.card_id !== undefined ? Tooltips.findCardById(event.card_id) : null;
        let eventDesc = event.description || '';
        if ((event.event_type === 'TRIGGER' || event.event_type === 'EFFECT') && card && !State.showFriendlyAbilities) {
            const rawText = Tooltips.getEffectiveRawText(card);
            if (rawText) {
                eventDesc = rawText;
            }
        }

        const container = document.createElement('div');
        container.className = 'turn-event-hover-container';
        container.style.display = 'contents';
        Tooltips.attachCardData(container, card);

        if (eventDesc) container.setAttribute('data-text', eventDesc);
        if (event.card_name) container.setAttribute('data-card-name', event.card_name);

        const enrichedDesc = Tooltips.enrichAbilityText(eventDesc);

        container.innerHTML = `
            <span class="turn-badge" aria-label="Turn ${event.turn}">T${event.turn}</span>
            <span class="phase-badge" aria-label="Phase: ${phaseLabel}">${phaseLabel}</span>
            <span class="player-badge p${event.player_id}" aria-label="Player: ${playerLabel}">${playerLabel}</span>
            <span class="event-type" aria-label="Event type: ${event.event_type || 'Event'}">${eventIcon} ${event.event_type || 'Event'}</span>
            <span class="event-desc">${enrichedDesc}</span>
        `;
        entry.appendChild(container);

        return entry;
    },

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

    getEventIcon: (eventType) => {
        const icons = {
            'PLAY': '🃏', 'ACTIVATE': '⚡', 'TRIGGER': '🎯', 'EFFECT': '✨', 'RULE': '📜', 'YELL': '📣', 'PERFORMANCE': '🎤',
            'PHASE': '🔄', 'DRAW': '📥', 'SCORE': '📊', 'HEART': '💖', 'BATON': ' Baton', 'LIVE': '🎵'
        };
        return icons[eventType] || '•';
    },

    renderRuleLogSection: (state, currentLang, showFriendlyAbilities, selectedTurn) => {
        let logData = state.rule_log || [];

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
                const block = LogRenderer.createGroupedLogBlock(group, currentLang, showFriendlyAbilities);
                section.appendChild(block);
            } else {
                const entry = LogRenderer.createStandaloneLogEntry(group, currentLang, showFriendlyAbilities);
                section.appendChild(entry);
            }
        });

        PerformanceMonitor.recordEntryCount(groupedLogs.length);
        return section;
    },

    createGroupedLogBlock: (group, currentLang, showFriendlyAbilities) => {
        const blockDiv = document.createElement('div');
        blockDiv.className = 'log-group-block';

        let headerEntry = group.entries[0];
        let detailEntries = group.entries.slice(1);

        const headerDiv = document.createElement('div');
        headerDiv.className = 'log-entry ability group-header';

        const headerContent = LogRenderer.formatLogEntry(headerEntry, group.turnPrefix, currentLang, showFriendlyAbilities);
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
                const detailContent = LogRenderer.formatLogEntry(detail, "", currentLang, showFriendlyAbilities);
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

    createStandaloneLogEntry: (group, currentLang, showFriendlyAbilities) => {
        const div = document.createElement('div');
        div.className = 'log-entry';

        const bodyContent = LogRenderer.formatLogEntry(group.body, group.turnPrefix, currentLang, showFriendlyAbilities);
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

            if (p.cost_reduction && p.cost_reduction !== 0) {
                effects.push({ title: t['cost_reduction'] || 'Cost Reduction', desc: `${t['cost'] || 'Cost'} ${p.cost_reduction > 0 ? '-' : '+'}${Math.abs(p.cost_reduction)}`, duration: t['until_end_of_turn'] || 'Until End of Turn', type: 'buff' });
            }
            if (p.blade_buffs) {
                p.blade_buffs.forEach((val, idx) => {
                    if (val !== 0) {
                        effects.push({ title: `${t['slot'] || 'Slot'} ${idx + 1}: ${t['blade_buff'] || 'Blade Buff'}`, desc: `Appeal ${val > 0 ? '+' : ''}${val}`, duration: t['until_end_of_turn'] || 'Until End of Turn', type: val > 0 ? 'buff-blade' : 'debuff' });
                    }
                });
            }
            if (p.heart_buffs) {
                p.heart_buffs.forEach((hb, idx) => {
                    const colors = ['Smile', 'Pure', 'Cool', 'Green', 'Blue', 'Purple', 'Wildcard'];
                    let heartDesc = [];
                    if (hb && Array.isArray(hb)) {
                        hb.forEach((count, cIdx) => { if (count > 0) heartDesc.push(`${colors[cIdx] || cIdx} +${count}`); });
                    }
                    if (heartDesc.length > 0) {
                        effects.push({ title: `${t['slot'] || 'Slot'} ${idx + 1}: ${t['heart_buff'] || 'Heart Buff'}`, desc: heartDesc.join(', '), duration: t['until_end_of_turn'] || 'Until End of Turn', type: 'buff-heart' });
                    }
                });
            }
            if (p.prevent_baton_touch > 0) {
                effects.push({ title: t['restriction'] || 'Restriction', desc: t['cannot_baton_touch'] || 'Cannot Baton Touch', duration: t['until_end_of_turn'] || 'Until End of Turn', type: 'restriction' });
            }
            if (p.prevent_activate > 0) {
                effects.push({ title: t['restriction'] || 'Restriction', desc: t['cannot_activate_member'] || 'Cannot Activate Member Abilities', duration: t['until_end_of_turn'] || 'Until End of Turn', type: 'restriction' });
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

    updateLogDifferential: (containerId = 'rule-log') => {
        const ruleLogEl = document.getElementById(containerId);
        if (!ruleLogEl) return;

        const state = State.data;
        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;
        const t = translations ? translations[currentLang] : {};

        const currentLogCount = (state.rule_log || []).length;
        const currentHistoryCount = (state.turn_history || []).length;

        if (currentLogCount < PerformanceMonitor._lastLogCount || currentHistoryCount < PerformanceMonitor._lastHistoryCount) {
            PerformanceMonitor._lastLogCount = currentLogCount;
            PerformanceMonitor._lastHistoryCount = currentHistoryCount;
            LogRenderer.renderRuleLog(containerId);
            return;
        }

        const newLogEntries = state.rule_log.slice(PerformanceMonitor._lastLogCount);
        const newHistoryEntries = (state.turn_history || []).slice(PerformanceMonitor._lastHistoryCount);

        if (newLogEntries.length === 0 && newHistoryEntries.length === 0) return;

        if (newHistoryEntries.length > 0) {
            const turnHistorySection = ruleLogEl.querySelector('.turn-history-section');
            if (turnHistorySection) {
                newHistoryEntries.forEach(event => {
                    const filteredEvent = LogFilter.applyFilters([event])[0];
                    if (filteredEvent) {
                        const entry = LogRenderer.createTurnEventElement(event, t);
                        turnHistorySection.appendChild(entry);
                    }
                });
            }
        }

        if (newLogEntries.length > 0) {
            const ruleLogSection = ruleLogEl.querySelector('.rule-log-section');
            if (ruleLogSection) {
                newLogEntries.forEach(entry => {
                    const div = LogRenderer.createStandaloneLogEntry(
                        { entry, body: entry.replace(/^\[Turn \d+\]\s*/, ''), turnPrefix: '' },
                        currentLang,
                        showFriendlyAbilities
                    );
                    ruleLogSection.appendChild(div);
                });
            }
        }

        PerformanceMonitor._lastLogCount = currentLogCount;
        PerformanceMonitor._lastHistoryCount = currentHistoryCount;

        if (!State.showingFullLog) ruleLogEl.scrollTop = ruleLogEl.scrollHeight;
    }
};
