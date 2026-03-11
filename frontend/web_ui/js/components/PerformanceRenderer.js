/**
 * Performance Renderer Component
 * Handles rendering of performance results, heart progress, and performance guide.
 */
import { State } from '../state.js';
import { fixImg, Phase } from '../constants.js';
import * as i18n from '../i18n/index.js';
import { Tooltips } from '../ui_tooltips.js';

export const PerformanceRenderer = {
    renderHeartProgress: (filled, required) => {
        if (!required || !Array.isArray(required)) return '';
        const filledArr = (Array.isArray(filled) ? filled : []);
        let html = '<div class="heart-progress-row">';
        for (let i = 0; i < 7; i++) {
            const reqCount = required[i] || 0;
            const filledCount = filledArr[i] || 0;
            for (let j = 0; j < reqCount; j++) {
                const isFilled = j < filledCount;
                html += `<div class="heart-pip color-${i} ${isFilled ? 'filled' : 'empty'}"></div>`;
            }
        }
        html += '</div>';
        return html;
    },

    renderPerformanceGuide: () => {
        const state = State.data;
        const perspectivePlayer = State.perspectivePlayer;
        const p0 = state.players[perspectivePlayer] || state.players[0];
        const guide = p0.performance_guide;
        const panel = document.getElementById('perf-guide-panel');
        const contentEl = document.getElementById('perf-guide-content');
        if (!panel || !contentEl) return;

        if (!guide || !guide.lives || guide.lives.length === 0) {
            panel.style.display = 'none';
            return;
        }
        panel.style.display = 'block';

        let html = `<div class="perf-guide-header">
            <span>Blades: <b>${guide.total_blades}</b></span>
            <span>Hearts: ${PerformanceRenderer.renderHeartsCompact(guide.total_hearts)}</span>
        </div>`;

        guide.lives.forEach(l => {
            if (!l || typeof l !== 'object') return;
            const color = l.passed ? '#4f4' : '#f44';
            const imgPath = l.img || '';
            const imgHtml = imgPath ? `<img src="${fixImg(imgPath)}" class="perf-guide-img" style="border-color:${color}">` : '';

            let entryHtml = `<div class="perf-guide-entry" style="opacity: ${l.passed ? 1 : 0.7}" ${l.text ? `data-text="${l.text.replace(/"/g, '&quot;')}"` : ''} ${l.id !== undefined ? `data-card-id="${l.id}"` : ''}>
                ${imgHtml}
                <div class="perf-guide-info">
                    <div class="perf-guide-name">${l.name || 'Live'} <span class="perf-guide-score">(${l.score || 0}pts)</span></div>
                    <div class="perf-guide-pips">
                        ${PerformanceRenderer.renderHeartProgress(l.filled, l.required)}
                    </div>
                    ${!l.passed ? `<div class="perf-guide-reason">${l.reason || ''}</div>` : ''}
                </div>
                <div class="perf-guide-status" style="color:${color}">${l.passed ? '[OK]' : '[X]'}</div>
            </div>`;

            html += entryHtml;
        });

        contentEl.innerHTML = html;
    },

    renderPerformanceResult: (results = null) => {
        const modal = document.getElementById('performance-modal');
        const content = document.getElementById('performance-result-content');
        if (!modal || !content) return;

        let displayResults = results ||
            (State.data.performance_results && Object.keys(State.data.performance_results).length > 0 ? State.data.performance_results : State.data.last_performance_results);

        const currentLang = State.currentLang;

        if (!displayResults || Object.keys(displayResults).length === 0) {
            const label = i18n.t('no_perf_data');
            content.innerHTML = `<div style="text-align:center; padding: 20px; opacity:0.6;">${label}</div>`;
            return;
        }

        content.innerHTML = '';
        PerformanceRenderer.renderTurnHistory(); // Render history in background tab
        PerformanceRenderer.showPerfTab('result'); // Ensure we start on result tab

        let html = '';
        if (State.performanceHistoryTurns && State.performanceHistoryTurns.length > 1) {
            html += `<div class="perf-turn-nav">`;
            const turns = [...State.performanceHistoryTurns].sort((a, b) => a - b);
            turns.forEach((turn) => {
                const turnNum = parseInt(turn);
                const isLatest = turnNum === turns[turns.length - 1];
                let turnLabel = isLatest ? i18n.t('current_turn', { turn: turnNum }) : i18n.t('turn_label', { turn: turnNum });

                const isSelected = (State.selectedPerfTurn === turnNum) || (State.selectedPerfTurn === -1 && isLatest);
                const activeClass = isSelected ? 'active' : '';

                html += `<button class="perf-nav-btn ${activeClass}" onclick="window.showPerformanceForTurn(${turnNum})">
                            ${turnLabel}
                         </button>`;
            });
            html += `</div>`;
        }

        html += '<div class="perf-result-container">';
        [0, 1].forEach(pid => {
            const res = displayResults[pid];
            if (!res) return;

            const playerName = pid === State.perspectivePlayer ? i18n.t('you') : i18n.t('opponent');
            const statusLabel = res.success ? i18n.t('success') : i18n.t('failure');
            const statusClass = res.success ? 'success' : 'failure';

            html += `
                <div class="perf-player-box ${statusClass}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <h3 style="margin:0;">${playerName}: ${statusLabel}</h3>
                        <div style="text-align:right;">
                            <span style="font-size:0.75rem; opacity:0.6; text-transform:uppercase;">${i18n.t('judge_score') || 'Judge Score'}</span>
                            <div style="font-size:1.25rem; font-weight:bold; color:var(--accent-gold);">${res.total_score || 0}</div>
                        </div>
                    </div>
                    ${(res.breakdown && res.breakdown.scores && res.breakdown.scores.length > 0) ? `
                    <div class="perf-score-breakdown" style="background: rgba(0,0,0,0.2); padding: 8px; border-radius: 4px; margin-bottom: 10px; font-size: 0.85rem;">
                        ${res.breakdown.scores.map(s => `
                            <div class="perf-line" style="margin: 2px 0;">
                                <span style="opacity: 0.8;">${Tooltips.enrichAbilityText(s.source)}:</span>
                                <span class="value" style="color: var(--accent-gold);">+${s.value}</span>
                            </div>
                        `).join('')}
                    </div>
                    ` : ''}
                    <div class="perf-breakdown">
                        <div class="perf-section">
                            <h4>${i18n.t('target_lives')}</h4>
                            ${res.lives && res.lives.length > 0 ? res.lives.map((l, i) => {
                if (!l) return '';
                const filledSum = (l.filled || [0, 0, 0, 0, 0, 0, 0]).reduce((a, b) => a + b, 0);
                const reqSum = (l.required || [0, 0, 0, 0, 0, 0, 0]).reduce((a, b) => a + b, 0);

                // Get allocations for this specific live card
                const liveAllocations = (res.breakdown && res.breakdown.allocations)
                    ? res.breakdown.allocations.filter(a => a.target_idx === i)
                    : [];

                // Group by source to show compact list
                const sourceGroups = {};
                liveAllocations.forEach(a => {
                    const key = `${a.source_id}_${a.source_slot}`;
                    if (!sourceGroups[key]) {
                        sourceGroups[key] = { name: a.source_name, amount: 0, slot: a.source_slot, id: a.source_id };
                    }
                    sourceGroups[key].amount += a.amount;
                });

                return `
                                <div class="perf-line perf-live-card-row" style="flex-direction: column; align-items: flex-start; gap: 4px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; margin-bottom: 8px;" data-live-idx="${i}">
                                    <div style="display:flex; justify-content: space-between; width: 100%; align-items:center;">
                                        <div style="display:flex; align-items:center; gap:5px;">
                                            ${l.img ? `<img src="${fixImg(l.img)}" style="width:24px; border-radius:3px;">` : ''}
                                            <div style="display:flex; flex-direction:column;">
                                                <span style="font-weight:bold; font-size:0.9rem;">${l.name || 'Live'}</span>
                                                <span style="font-size:0.7rem; color:var(--accent-gold); opacity:0.9;">${i18n.t('score')}: <b>${l.score || 0}</b></span>
                                            </div>
                                        </div>
                                         <div style="display:flex; align-items:center; gap:10px;">
                                            ${Math.max(0, filledSum - reqSum) > 0 ? `<span style="font-size:0.75rem; color:var(--accent-gold);">${i18n.t('extra_hearts', { count: Math.max(0, filledSum - reqSum) })}</span>` : ''}
                                            <span style="color:${l.passed ? '#4f4' : '#f44'}; font-weight:bold; font-size:0.8rem;">${l.passed ? '[PASS]' : '[FAIL]'}</span>
                                        </div>
                                    </div>
                                    <div class="perf-heart-progress">
                                        ${PerformanceRenderer.renderHeartProgress(l.filled, l.required)}
                                    </div>
                                    
                                    <!-- Sum-style Alignment: Source vs Required -->
                                    <div class="perf-heart-sum-comparison" style="margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; display: flex; flex-direction: column; gap: 8px;">
                                        <div class="perf-sum-row drain" style="display: flex; align-items: center; gap: 10px; border-top: 2px solid rgba(255,255,255,0.1); padding-top: 8px; margin-top: 4px;">
                                            <span style="width: 70px; font-size: 0.7rem; opacity: 0.7; font-weight: bold; color: var(--accent-pink);">${i18n.t('sum_drain') || 'REQUIRED'}</span>
                                            <div class="perf-hearts-grid">
                                                ${PerformanceRenderer.renderHeartsGrid(l.required)}
                                            </div>
                                        </div>
                                        <div class="perf-sum-row source" style="display: flex; align-items: center; gap: 10px;">
                                            <span style="width: 70px; font-size: 0.7rem; opacity: 0.7; font-weight: bold; color: var(--accent-blue);">${i18n.t('sum_source') || 'SOURCES'}</span>
                                            <div class="perf-hearts-grid">
                                                ${PerformanceRenderer.renderHeartsGrid(l.filled)}
                                            </div>
                                        </div>
                                        
                                        ${l.spare && l.spare.some(v => v > 0) ? `
                                            <div class="perf-sum-row spare" style="display: flex; align-items: center; gap: 10px; border-top: 1px dashed rgba(255,255,255,0.1); padding-top: 8px;">
                                                <span style="width: 70px; font-size: 0.7rem; opacity: 0.7; font-weight: bold; color: var(--accent-gold);">${i18n.t('sum_spare') || 'SPARE'}</span>
                                                <div class="perf-spare-pile" title="${i18n.t('extra_hearts_title') || 'Spare Hearts (Excess)'}">
                                                    ${l.spare.map((count, idx) => {
                    const icon = idx === 6 ? 'img/texticon/icon_all.png' : `img/texticon/heart_0${idx + 1}.png`;
                    return Array(count).fill(0).map(() => `<img src="${icon}" class="heart-mini-icon spare-heart">`).join('');
                }).join('')}
                                                </div>
                                            </div>
                                        ` : ''}
                                    </div>

                                    ${Object.keys(sourceGroups).length > 0 ? `
                                    <div class="perf-live-sources" style="font-size: 0.70rem; opacity: 0.9; margin-top: 10px; display: flex; flex-direction: column; gap: 4px;">
                                        <div style="opacity: 0.6; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 2px; margin-bottom: 4px;">${i18n.t('source_breakdown') || 'Allocation Breakdown'}:</div>
                                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                            ${Object.values(sourceGroups).map(sg => {
                    const allocationsForSource = liveAllocations.filter(a => a.source_id == sg.id && a.source_slot == sg.slot);
                    const isBonus = allocationsForSource.some(a => a.is_bonus);
                    const isYell = allocationsForSource.some(a => a.source_type === 'yell');

                    // Get color counts for this specific source
                    const counts = [0, 0, 0, 0, 0, 0, 0];
                    allocationsForSource.forEach(a => {
                        if (a.color >= 0 && a.color < 7) counts[a.color] += a.amount;
                    });

                    return `
                                                    <span class="perf-source-tag ${isYell ? 'yell' : ''}"
                                                        data-source-id="${sg.id}"
                                                        data-source-slot="${sg.slot}"
                                                        data-card-id="${sg.id}"
                                                        ${sg.name ? `data-card-name="${sg.name.replace(/"/g, '&quot;')}"` : ''}>
                                                        <div style="display:flex; flex-direction:column; gap:2px;">
                                                            <div style="font-weight:bold;">${Tooltips.enrichAbilityText(sg.name)}</div>
                                                            ${allocationsForSource[0]?.ability_text ? `<div class="perf-ability-text" style="font-size:0.65rem; opacity:0.8; font-style:italic; line-height:1.1;">${Tooltips.enrichAbilityText(allocationsForSource[0].ability_text)}</div>` : ''}
                                                        </div>
                                                        <span class="perf-source-counts">${PerformanceRenderer.renderHeartsGrid(counts)}</span>
                                                    </span>
                                                `}).join('')}
                                        </div>
                                    </div>
                                    ` : ''}

                                </div>
                                `;
            }).join('') : 'None'}
                        </div>

                        <div class="perf-section">
                            <h4>${i18n.t('blades_breakdown', { total: res.yell_count || 0 })}</h4>
                            ${res.breakdown && res.breakdown.blades ? res.breakdown.blades.map(b => `
                                <div class="perf-line">
                                    <div style="display:flex; flex-direction:column; gap:2px;">
                                        <span style="font-weight:bold;">${Tooltips.enrichAbilityText(b.source)}</span>
                                        ${b.ability_text ? `<div class="perf-ability-text" style="font-size:0.65rem; opacity:0.8; font-style:italic;">${Tooltips.enrichAbilityText(b.ability_text)}</div>` : ''}
                                    </div>
                                    <span class="value">+${b.value}</span>
                                </div>
                            `).join('') : ''}
                            ${res.note_icons || res.volume_icons ? `
                                <div class="perf-line" style="border-top:1px dashed rgba(255,255,255,0.1); padding-top:2px;">
                                    <span>${i18n.t('notes')}</span>
                                    <span class="value">+${res.note_icons || res.volume_icons}</span>
                                </div>
                            ` : ''}
                        </div>

                        ${res.member_contributions && res.member_contributions.length > 0 ? `
                        <div class="perf-section">
                            <h4>${i18n.t('member_contrib')}</h4>
                            ${res.member_contributions.map(m => {
                if (!m) return '';
                return `
                                <div class="perf-member-contribution" data-member-id="${m.source_id}" data-member-slot="${m.slot}">
                                    ${m.img ? `<img src="${fixImg(m.img)}" class="perf-member-img">` : ''}
                                    <div class="perf-member-info">
                                        <div class="perf-member-name">${Tooltips.enrichAbilityText(m.source || "Member")}</div>
                                        <div class="perf-member-stats">
                                            <div class="contrib-row">
                                                ${PerformanceRenderer.renderHeartsCompact(m.base_hearts)}
                                                ${m.bonus_hearts && m.bonus_hearts.some(v => v > 0) ? `
                                                    <span class="perf-member-bonus-label" style="margin-left:5px;">+${PerformanceRenderer.renderHeartsCompact(m.bonus_hearts)}</span>
                                                    ${m.ability_heart_bonuses && m.ability_heart_bonuses.length > 0 ? `
                                                        <div class="perf-member-ability-details" style="margin-top:4px; padding-left:10px; border-left:2px solid rgba(255,255,255,0.1);">
                                                            ${m.ability_heart_bonuses.map(b => `
                                                                <div class="perf-bonus-source-line" style="font-size:0.65rem; margin-bottom:4px;">
                                                                    <div style="display:flex; align-items:center; gap:4px; font-weight:bold; opacity:0.9;">
                                                                        ${b.img ? `<img src="${fixImg(b.img)}" style="width:12px; height:12px; border-radius:2px;">` : ''}
                                                                        <span>${b.source}: +${b.amount} ${['Pink', 'Red', 'Yellow', 'Green', 'Blue', 'Purple', 'Any'][b.color] || ''}</span>
                                                                    </div>
                                                                    ${b.ability_text ? `<div class="perf-ability-text" style="opacity:0.8; font-style:italic; line-height:1.1;">${Tooltips.enrichAbilityText(b.ability_text)}</div>` : ''}
                                                                </div>
                                                            `).join('')}
                                                        </div>
                                                    ` : ''}
                                                ` : ''}
                                            </div>
                                            <div class="contrib-row">
                                                ${PerformanceRenderer.renderBladesCompact(m.base_blades)}
                                                ${m.bonus_blades > 0 ? `
                                                    <span class="perf-member-bonus-label" style="margin-left:5px;"> +${m.bonus_blades}</span>
                                                    ${m.ability_blade_bonuses && m.ability_blade_bonuses.length > 0 ? `
                                                        <div class="perf-member-ability-details" style="margin-top:4px; padding-left:10px; border-left:2px solid rgba(255,255,255,0.1);">
                                                            ${m.ability_blade_bonuses.map(b => `
                                                                <div class="perf-bonus-source-line" style="font-size:0.65rem; margin-bottom:4px;">
                                                                    <div style="display:flex; align-items:center; gap:4px; font-weight:bold; opacity:0.9;">
                                                                        ${b.img ? `<img src="${fixImg(b.img)}" style="width:12px; height:12px; border-radius:2px;">` : ''}
                                                                        <span>${b.source}: +${b.value}</span>
                                                                    </div>
                                                                    ${b.ability_text ? `<div class="perf-ability-text" style="opacity:0.8; font-style:italic; line-height:1.1;">${Tooltips.enrichAbilityText(b.ability_text)}</div>` : ''}
                                                                </div>
                                                            `).join('')}
                                                        </div>
                                                    ` : ''}
                                                ` : ''}
                                            </div>
                                              ${(m.base_notes > 0 || m.bonus_notes > 0) ? `<span>${i18n.t('notes')}: <b>${m.base_notes}${m.bonus_notes > 0 ? ` <span class="perf-member-bonus-label">(+${m.bonus_notes})</span>` : ''}</b></span>` : ''}
                                            ${m.draw_icons ? `<span>${i18n.t('cards_draw')}: <b>${m.draw_icons}</b></span>` : ''}

                                            ${(res.breakdown && res.breakdown.allocations) ? (() => {
                        const memberAllocations = res.breakdown.allocations.filter(a => a.source_id === m.source_id && a.source_slot === m.slot);
                        if (memberAllocations.length === 0) return '';

                        const targetGroups = {};
                        memberAllocations.forEach(a => {
                            if (!targetGroups[a.target_idx]) {
                                targetGroups[a.target_idx] = { name: a.target_name, amount: 0 };
                            }
                            targetGroups[a.target_idx].amount += a.amount;
                        });

                        return `
                                                <div class="perf-member-targets" style="margin-top: 4px; font-size: 0.7rem; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 4px;">
                                                    <span style="opacity: 0.6;">Contributed to:</span>
                                                    <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:2px;">
                                                        ${Object.entries(targetGroups).map(([idx, tg]) => {
                            const allocsForTarget = memberAllocations.filter(a => a.target_idx == idx);
                            const isBonus = allocsForTarget.some(a => a.is_bonus);
                            const isYell = allocsForTarget.some(a => a.source_type === 'yell');
                            let label = '';
                            if (isYell) label = '(Yell)';
                            else if (isBonus) label = '(Ability)';

                            return `
                                                            <span style="padding: 2px 4px; background: rgba(255,255,255,0.05); border-radius: 3px;"
                                                                data-target-idx="${idx}"
                                                                data-card-id="${res.lives[idx]?.id}"
                                                                ${res.lives[idx]?.name ? `data-card-name="${res.lives[idx].name.replace(/"/g, '&quot;')}"` : ''}>
                                                                ${Tooltips.enrichAbilityText(tg.name)} ${label} (+${tg.amount})
                                                            </span>
                                                        `}).join('')}
                                                    </div>
                                                </div>
                                                `;
                    })() : ''}

                                        </div>
                                    </div>
                                </div>
                            `;
            }).join('')}
                        </div>
                        ` : ''}

                        ${(res.breakdown && ((res.breakdown.requirements && res.breakdown.requirements.length > 0) || (res.breakdown.transforms && res.breakdown.transforms.length > 0) || (res.lives && res.lives.some(l => l.adjustments && l.adjustments.length > 0)))) ? `
                        <div class="perf-section">
                            <h4>${i18n.t('adjustments')}</h4>
                            ${res.breakdown.transforms ? res.breakdown.transforms.map(tr => `
                                <div class="perf-line" style="color: #aaf; font-size: 0.8rem; gap: 4px;">
                                    <span style="opacity:0.7;">${tr.source}:</span>
                                    <span>${tr.desc}</span>
                                </div>
                            `).join('') : ''}
                            ${res.lives && res.lives.some(l => l.adjustments && l.adjustments.length > 0) ? res.lives.map(l => {
                if (!l.adjustments) return '';
                return l.adjustments.map(adj => {
                    const colorNames = ['Pink', 'Red', 'Yellow', 'Green', 'Blue', 'Purple', 'Any'];
                    const colorName = colorNames[adj.color] || '??';
                    const icon = adj.color === 6 ? 'img/texticon/icon_all.png' : `img/texticon/heart_0${adj.color + 1}.png`;
                    const sign = adj.value > 0 ? '-' : '+';
                    const absValue = Math.abs(adj.value);
                    const adjTypeClass = adj.type || 'reduction';

                    return `
                        <div class="perf-line adjustment-line ${adjTypeClass}" style="font-size: 0.8rem; gap: 4px;">
                            <span style="opacity:0.7;">${l.name} (${adj.source}):</span>
                            <div style="display:flex; align-items:center; gap:2px;">
                                <img src="${icon}" class="heart-mini-icon">
                                <span class="value" style="color: inherit;">${sign}${absValue} Req</span>
                            </div>
                        </div>
                    `;
                }).join('');
            }).join('') : ''}
                        </div>
                        ` : ''}

                        ${res.triggered_abilities && res.triggered_abilities.length > 0 ? `
                        <div class="perf-section">
                            <h4>${i18n.t('activated_abilities', { defaultValue: 'Activated Abilities' })}</h4>
                            ${res.triggered_abilities.map(ta => `
                                <div class="perf-line" style="font-size: 0.8rem; gap: 4px; flex-direction: column; align-items: flex-start;">
                                    <div style="display:flex; align-items:center; gap:4px;">
                                        <span style="opacity:0.7; font-weight:bold;">${Tooltips.enrichAbilityText(ta.name)}:</span>
                                        <span>${Tooltips.enrichAbilityText(ta.card_name || 'Unknown Card')} (Ability ${ta.id + 1})</span>
                                    </div>
                                    ${ta.ability_text ? `<div class="perf-ability-text" style="font-size:0.75rem; opacity:0.8; font-style:italic; padding-left:10px;">${Tooltips.enrichAbilityText(ta.ability_text)}</div>` : ''}
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}

                        ${res.yell_cards && res.yell_cards.length > 0 ? `
                        <div class="perf-section">
                            <h4>${i18n.t('yelled_cards')} (${res.yell_cards.length} Total)</h4>
                            <div class="perf-yell-grid">
                                ${res.yell_cards.map(c => {
                if (!c) return '';
                const rawText = Tooltips.getEffectiveRawText(c);
                return `
                                        <div class="perf-yell-card" title="${c ? (c.name || 'Card') : 'Card'}" ${rawText ? `data-text="${rawText.replace(/"/g, '&quot;')}"` : ''} ${c && c.id !== undefined ? `data-card-id="${c.id}"` : ''}>
                                            ${c && c.img ? `<img src="${fixImg(c.img)}">` : ''}
                                            <div class="perf-card-icons">
                                                ${(c && c.blade_hearts && c.blade_hearts.some(v => v > 0)) ? c.blade_hearts.map((v, hIdx) => {
                    if (v <= 0) return '';
                    const icon = hIdx === 6 ? 'img/texticon/icon_all.png' : `img/texticon/heart_0${hIdx + 1}.png`;
                    return `<img src="${icon}" class="perf-mini-icon">`;
                }).join('') : ''}
                                                 ${(c && (c.note_icons > 0 || c.volume_icons > 0)) ? `<img src="img/texticon/icon_score.png" class="perf-mini-icon" title="${i18n.t('notes')}">` : ''}
                                                ${(c && c.draw_icons > 0) ? `<img src="img/texticon/icon_draw.png" class="perf-mini-icon" title="${i18n.t('cards_draw')}">` : ''}
                                            </div>
                                        </div>
                                    `;
            }).join('')}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
        PerformanceRenderer.attachAllocationFlashListeners(content);
    },

    attachAllocationFlashListeners: (container) => {
        const sourceTags = container.querySelectorAll('.perf-source-tag');
        const targetTags = container.querySelectorAll('.perf-member-targets span[data-target-idx]');
        const memberRows = container.querySelectorAll('.perf-member-contribution');
        const liveRows = container.querySelectorAll('.perf-live-card-row');

        const clearHighlights = () => {
            container.querySelectorAll('.perf-highlight-source, .perf-highlight-target').forEach(el => {
                el.classList.remove('perf-highlight-source', 'perf-highlight-target');
            });
        };

        const currentData = State.selectedPerfTurn !== -1 ? State.performanceHistory[State.selectedPerfTurn] : State.lastPerformanceData;
        const allocations = currentData?.breakdown?.allocations || [];

        sourceTags.forEach(tag => {
            tag.addEventListener('mouseenter', () => {
                const sid = tag.getAttribute('data-source-id');
                const sslot = tag.getAttribute('data-source-slot');
                const sourceMember = container.querySelector(`.perf-member-contribution[data-member-id="${sid}"][data-member-slot="${sslot}"]`);
                if (sourceMember) sourceMember.classList.add('perf-highlight-source');
                allocations.filter(a => a.source_id == sid && a.source_slot == sslot).forEach(a => {
                    const targetRow = container.querySelector(`.perf-live-card-row[data-live-idx="${a.target_idx}"]`);
                    if (targetRow) targetRow.classList.add('perf-highlight-target');
                });
            });
            tag.addEventListener('mouseleave', clearHighlights);
        });

        targetTags.forEach(tag => {
            tag.addEventListener('mouseenter', () => {
                const tidx = tag.getAttribute('data-target-idx');
                const targetRow = container.querySelector(`.perf-live-card-row[data-live-idx="${tidx}"]`);
                if (targetRow) targetRow.classList.add('perf-highlight-target');
                allocations.filter(a => a.target_idx == tidx).forEach(a => {
                    const sourceMember = container.querySelector(`.perf-member-contribution[data-member-id="${a.source_id}"][data-member-slot="${a.source_slot}"]`);
                    if (sourceMember) sourceMember.classList.add('perf-highlight-source');
                });
            });
            tag.addEventListener('mouseleave', clearHighlights);
        });

        memberRows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                const sid = row.getAttribute('data-member-id');
                const sslot = row.getAttribute('data-member-slot');
                row.classList.add('perf-highlight-source');
                allocations.filter(a => a.source_id == sid && a.source_slot == sslot).forEach(a => {
                    const targetRow = container.querySelector(`.perf-live-card-row[data-live-idx="${a.target_idx}"]`);
                    if (targetRow) targetRow.classList.add('perf-highlight-target');
                });
            });
            row.addEventListener('mouseleave', clearHighlights);
        });

        liveRows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                const tidx = row.getAttribute('data-live-idx');
                row.classList.add('perf-highlight-target');
                allocations.filter(a => a.target_idx == tidx).forEach(a => {
                    const sourceMember = container.querySelector(`.perf-member-contribution[data-member-id="${a.source_id}"][data-member-slot="${a.source_slot}"]`);
                    if (sourceMember) sourceMember.classList.add('perf-highlight-source');
                });
            });
            row.addEventListener('mouseleave', clearHighlights);
        });
    },

    renderHeartsCompact: (hearts) => {
        if (!hearts) return '';
        let html = '<div class="hearts-compact">';
        hearts.forEach((count, idx) => {
            if (count > 0) {
                const isAny = idx === 6;
                const colorClass = isAny ? 'color-any' : `color-${idx}`;
                const icon = isAny ? 'img/texticon/icon_all.png' : `img/texticon/heart_0${idx + 1}.png`;
                html += `<div class="heart-tag ${colorClass}"><img src="${icon}" class="heart-mini-icon"><span>${count}</span></div>`;
            }
        });
        html += '</div>';
        return (html === '<div class="hearts-compact"></div>') ? '-' : html;
    },

    renderBladesCompact: (blades) => {
        if (!blades || blades <= 0) return '';
        let html = '<div class="blades-compact">';
        for (let i = 0; i < blades; i++) {
            html += `<img src="img/texticon/icon_blade.png" class="heart-mini-icon">`;
        }
        html += '</div>';
        return html;
    },

    showPerfTab: (tab) => {
        const resultTab = document.getElementById('perf-tab-result');
        const historyTab = document.getElementById('perf-tab-history');
        const resultBtn = document.getElementById('tab-btn-result');
        const historyBtn = document.getElementById('tab-btn-history');

        if (!resultTab || !historyTab) return;

        if (tab === 'result') {
            resultTab.style.display = 'block';
            historyTab.style.display = 'none';
            if (resultBtn) resultBtn.classList.add('active');
            if (historyBtn) historyBtn.classList.remove('active');
        } else {
            resultTab.style.display = 'none';
            historyTab.style.display = 'block';
            if (resultBtn) resultBtn.classList.remove('active');
            if (historyBtn) historyBtn.classList.add('active');
            PerformanceRenderer.renderTurnHistory();
        }
    },

    renderTurnHistory: () => {
        const container = document.getElementById('performance-history-content');
        if (!container) return;

        const state = State.data;
        const history = state.turn_history || state.turn_events || [];

        if (history.length === 0) {
            const label = i18n.t('no_history');
            container.innerHTML = `<div style="text-align:center; padding:20px; opacity:0.6;">${label}</div>`;
            return;
        }

        let html = '';
        history.forEach((event) => {
            const phaseKey = PerformanceRenderer._getPhaseKey(event.phase);
            const playerLabel = event.player_id === State.perspectivePlayer ? i18n.t('you') : i18n.t('opponent');
            const typeClass = event.event_type ? event.event_type.toLowerCase() : 'generic';

            html += `
                <div class="turn-event-item ${typeClass}">
                    <div class="event-header">
                        <span>Turn ${event.turn} - <span class="event-phase-tag">${i18n.t(phaseKey)}</span></span>
                        <span>${playerLabel}</span>
                    </div>
                    <div class="event-source">${event.event_type || 'Event'}</div>
                    <div class="event-description">${event.description || ''}</div>
                </div>
            `;
        });
        container.innerHTML = html;
    },

    _getPhaseKey: (phase) => {
        const perspectivePlayer = State.perspectivePlayer;
        if (phase === Phase.RPS) return 'rps';
        if (phase === Phase.SETUP) return 'setup';
        if (phase === Phase.MULLIGAN_P1) return (perspectivePlayer === 0) ? 'mulligan_you' : 'mulligan_opp';
        if (phase === Phase.MULLIGAN_P2) return (perspectivePlayer === 1) ? 'mulligan_you' : 'mulligan_opp';
        if (phase === Phase.ACTIVE) return 'active';
        if (phase === Phase.ENERGY) return 'energy';
        if (phase === Phase.DRAW) return 'draw';
        if (phase === Phase.MAIN) return 'main';
        if (phase === Phase.LIVE_SET) return 'live_set';
        if (phase === Phase.PERFORMANCE_P1) return (perspectivePlayer === 0) ? 'perf_p1' : 'perf_p2';
        if (phase === Phase.PERFORMANCE_P2) return (perspectivePlayer === 1) ? 'perf_p1' : 'perf_p2';
        if (phase === Phase.LIVE_RESULT) return 'live_result';
        return 'wait';
    },
    renderHeartsGrid: (hearts) => {
        if (!hearts) return '';
        let html = '';
        // Always iterate 7 slots to keep them aligned
        for (let idx = 0; idx < 7; idx++) {
            const count = hearts[idx] || 0;
            const isAny = idx === 6;
            const colorClass = isAny ? 'color-any' : `color-${idx}`;
            const icon = isAny ? 'img/texticon/icon_all.png' : `img/texticon/heart_0${idx + 1}.png`;

            html += `
                <div class="heart-grid-cell ${count > 0 ? 'has-value' : 'empty'}">
                    <img src="${icon}" class="heart-mini-icon" style="opacity: ${count > 0 ? 1 : 0.15}">
                    <span class="count-value" style="visibility: ${count > 0 ? 'visible' : 'hidden'}">${count}</span>
                </div>`;
        }
        return html;
    },
};
