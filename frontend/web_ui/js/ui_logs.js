/**
 * UI Logs module
 * Handles rendering of Rule Log, Triggered Abilities, and Active Effects.
 */
import { State } from './state.js';
import { translations } from './translations_data.js';
import { Tooltips } from './ui_tooltips.js';

export const Logs = {
    renderRuleLog: (containerId = 'rule-log') => {
        const ruleLogEl = document.getElementById(containerId);
        if (!ruleLogEl) return;

        const state = State.data;
        const currentLang = State.currentLang;
        const showFriendlyAbilities = State.showFriendlyAbilities;
        const selectedTurn = State.selectedTurn || -1;
        const showingFullLog = State.showingFullLog;

        let logData = state.rule_log || [];

        // Apply filtering
        if (selectedTurn !== -1) {
            const turnStr = `[Turn ${selectedTurn}]`;
            logData = logData.filter(entry => entry.includes(turnStr));
        }

        ruleLogEl.innerHTML = '';

        const fragment = document.createDocumentFragment();
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
                // It's a grouped block
                const blockDiv = document.createElement('div');
                blockDiv.className = 'log-group-block';

                // Identify the "Header" (usually the first entry if it looks like a trigger)
                let headerEntry = group.entries[0];
                let detailEntries = group.entries.slice(1);

                // Create Header
                const headerDiv = document.createElement('div');
                headerDiv.className = 'log-entry ability group-header';
                headerDiv.innerHTML = Tooltips.enrichAbilityText(Logs.formatLogEntry(headerEntry, group.turnPrefix, currentLang, showFriendlyAbilities));
                blockDiv.appendChild(headerDiv);

                // Create container for details (nesting)
                if (detailEntries.length > 0) {
                    const detailsContainer = document.createElement('div');
                    detailsContainer.className = 'log-group-details';
                    detailEntries.forEach(detail => {
                        const detailDiv = document.createElement('div');
                        detailDiv.className = 'log-entry effect detail';
                        detailDiv.innerHTML = Tooltips.enrichAbilityText(Logs.formatLogEntry(detail, "", currentLang, showFriendlyAbilities));
                        detailsContainer.appendChild(detailDiv);
                    });
                    blockDiv.appendChild(detailsContainer);
                }
                fragment.appendChild(blockDiv);
            } else {
                // Standalone entry
                const div = document.createElement('div');
                div.className = 'log-entry';
                div.innerHTML = Tooltips.enrichAbilityText(Logs.formatLogEntry(group.body, group.turnPrefix, currentLang, showFriendlyAbilities));

                const entryUpper = group.entry.toUpperCase();
                if ((entryUpper.includes("---") && entryUpper.includes("PHASE")) || entryUpper.includes("[ACTIVE PHASE]")) div.classList.add('phase');
                else if (entryUpper.includes('PLAYS') || entryUpper.includes('MULLIGAN') || entryUpper.includes('SELECTED')) div.classList.add('action');
                else if (entryUpper.includes('EFFECT:') || entryUpper.includes('RULE')) div.classList.add('effect');
                else if (entryUpper.includes('SCORE') || entryUpper.includes('SUCCESS LIVE')) div.classList.add('score');
                else if (group.entry.includes('===')) div.classList.add('turn');

                fragment.appendChild(div);
            }
        });

        ruleLogEl.appendChild(fragment);
        if (!showingFullLog) ruleLogEl.scrollTop = ruleLogEl.scrollHeight;
    },

    formatLogEntry: (body, turnPrefix, currentLang, showFriendlyAbilities) => {
        let displayText = body;

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
                if (srcCard && srcCard.original_text) {
                    translatedEffect = srcCard.original_text;
                }
            }

            let displayCardName = cardName;
            if (currentLang === 'en' && window.NAME_MAP && window.NAME_MAP[cardName]) {
                displayCardName = window.NAME_MAP[cardName];
            }

            displayText = `${triggerLabel} ${displayCardName}: ${translatedEffect}`;
        }

        const mulliganMatch = body.match(/(Mulligan): (.*)/i);
        if (mulliganMatch) {
            const cardName = mulliganMatch[2].trim();
            let displayPhase = currentLang === 'jp' ? "マリガン" : "Mulligan";
            let displayCardName = cardName;
            if (currentLang === 'en' && window.NAME_MAP && window.NAME_MAP[cardName]) {
                displayCardName = window.NAME_MAP[cardName];
            }
            displayText = `${displayPhase}: ${displayCardName}`;
        }

        // Clean up internal tokens like HEART_BLUE
        displayText = displayText.replace(/HEART_RED/g, '❤️')
            .replace(/HEART_YELLOW/g, '💛')
            .replace(/HEART_GREEN/g, '💚')
            .replace(/HEART_BLUE/g, '💙')
            .replace(/HEART_PURPLE/g, '💜')
            .replace(/HEART_PINK/g, '💖')
            .replace(/HEART_WILD/g, '🤍');

        return (turnPrefix ? turnPrefix + " " : "") + displayText;
    },

    renderActiveAbilities: (containerId, abilities) => {
        const el = document.getElementById(containerId);
        if (!el || !abilities) return;
        el.innerHTML = abilities.map(a => `
            <div class="active-ability-tag" data-text="${a.text || a.description || ''}">
                ${Tooltips.enrichAbilityText(a.name || 'Ability')}
            </div>
        `).join('');
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
                <div class="effect-item ${e.type || ''}">
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
    }
};
