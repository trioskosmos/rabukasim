import { State } from '../state.js';
import { Phase } from '../constants.js';
import * as i18n from '../i18n/index.js';
import { Tooltips } from '../ui_tooltips.js';
import { ActionBases } from '../generated_constants.js';
import { DOMUtils } from '../utils/DOMUtils.js';
import { DOM_IDS, COLORS } from '../constants_dom.js';

export const ActionMenu = {
    renderActions: () => {
        const state = State.data;
        if (!state || state.game_over) return;

        const currentLang = State.currentLang;
        const perspectivePlayer = State.perspectivePlayer;

        // Clear both action containers
        DOMUtils.clear(DOM_IDS.CONTAINER_ACTIONS);
        DOMUtils.clear(DOM_IDS.CONTAINER_MOBILE_ACTION_BAR);

        // Get action container for appending elements
        const actionsDiv = DOMUtils.getElement(DOM_IDS.CONTAINER_ACTIONS);
        if (!actionsDiv) return;

        const getActionLabel = (a, isMini = false) => {
            if (a.id === 0 && state.pending_choice) {
                if (state.phase === Phase.MulliganP1 || state.phase === Phase.MulliganP2) {
                    return i18n.t('done') || (currentLang === 'jp' ? '完了' : 'Done');
                }
                return i18n.t('pass_no') || (currentLang === 'jp' ? 'パス / いいえ' : 'Pass / No');
            }
            const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;
            const heartIcon = `<img src="img/texticon/icon_heart.png" style="height:14px; vertical-align:middle; margin:0 2px;">`;

            let cost = a.metadata?.cost ?? a.cost ?? a.base_cost ?? null;
            const isBaton = (a.name && (a.name.includes('Baton') || a.name.includes('バトン')));
            let name = a.metadata?.name ?? a.name ?? "";

            if (name.match(/^Action\s+30\d$/) && a.metadata?.category !== 'ABILITY') {
                const liveIdx = parseInt(name.replace("Action 30", ""), 10);
                const liveCard = state?.live_zone && state.live_zone[liveIdx];
                if (liveCard && liveCard.name) {
                    name = liveCard.name;
                    return `<div class="action-title">${heartIcon} ${name}</div>`;
                }
            }

            name = name.replace(/[【\[].*?[】\]]/g, "").trim();

            if (!name || name.startsWith('Action ')) {
                if (a.id >= 580 && a.id < 590) {
                    const colorIdx = a.id - 580;
                    const colorKeys = ['PINK', 'RED', 'YELLOW', 'GREEN', 'BLUE', 'PURPLE'];
                    if (colorIdx < colorKeys.length) {
                        const colorKey = colorKeys[colorIdx];
                        const trans = currentLang === 'en' ? window.currentTranslationsEN : window.currentTranslationsJP;
                        name = trans?.params?.COLOR?.[colorKey] || colorKey;
                    }
                } else if (a.id >= 500 && a.id < 510) {
                    const modeIdx = a.id - 500;
                    const pc = state.pending_choice;
                    if (pc && pc.options_text && pc.options_text[modeIdx]) {
                        name = pc.options_text[modeIdx];
                    } else {
                        name = (currentLang === 'jp' ? "モード " : "Mode ") + modeIdx;
                    }
                } else if (a.id >= 600 && a.id <= 602) {
                    const slotIdx = a.id - 600;
                    const trans = i18n.getCurrentTranslations();
                    name = trans?.params?.AREA?.[slotIdx] || i18n.t('slot_n', { n: slotIdx });
                }
            }

            if (isMini) {
                if (a.type === 'PLAY') return `<span>${cost !== null ? cost : 0}</span>${isBaton ? ' [B]' : ''}`;
                if (a.type === 'MULLIGAN') {
                    const shortName = name.length > 10 ? name.substring(0, 10) + '…' : name;
                    return `<span style="font-size:0.65rem">${shortName || '?'}</span>`;
                }
                let label = `${energyIcon}${cost !== null ? cost : 0}`;
                if (isBaton) label += ' [B]';
                return Tooltips.enrichAbilityText(label);
            } else {
                let displayName = name;
                if (a.metadata?.secondary_slot_idx !== undefined && a.metadata?.areas_desc) {
                    displayName = (currentLang === 'jp')
                        ? a.metadata.areas_desc.replace(' & ', '＆')
                        : a.metadata.areas_desc;
                }

                // Translate the name if possible (especially for pseudo-English labels from the engine)
                if (window.translateAbility) {
                    displayName = window.translateAbility(displayName, currentLang);
                }

                displayName = Tooltips.enrichAbilityText(displayName);

                let label = `<div class="action-title" style="${(displayName.includes('&') || displayName.includes('＆')) ? 'font-size:0.85em;' : ''}">${displayName}</div>`;
                if (cost !== null) label += `<div class="action-cost">${energyIcon}${cost}</div>`;
                if (isBaton && a.metadata?.secondary_slot_idx === undefined) label += ' [B]';
                return label;
            }
        };

        const createActionButton = (a, isMini = false, extraClass = '') => {
            const btn = document.createElement('button');
            btn.className = `action-btn ${isMini ? 'mini' : ''} ${extraClass}`.trim();

            const sourceCard = a.source_card_id !== undefined ? Tooltips.findCardById(a.source_card_id) : null;
            Tooltips.attachCardData(btn, sourceCard, a.id);

            if (a.raw_text || a.text) btn.setAttribute('data-text', a.raw_text || a.text);

            btn.innerHTML = getActionLabel(a, isMini);
            btn.onclick = () => { if (window.doAction && a.id !== undefined) window.doAction(a.id); };

            btn.onmouseenter = () => {
                if (window.highlightActionTarget && a.id !== undefined) {
                    window.highlightActionTarget(a.id, true);
                }
            };
            btn.onmouseleave = () => {
                if (window.highlightActionTarget && a.id !== undefined) {
                    window.highlightActionTarget(a.id, false);
                }
            };

            return btn;
        };

        if (state.phase === Phase.RPS) {
            const rpsDiv = document.createElement('div');
            rpsDiv.className = 'rps-selector';
            rpsDiv.style.textAlign = 'center';
            rpsDiv.style.padding = '15px';
            rpsDiv.style.background = 'rgba(255, 255, 255, 0.05)';
            rpsDiv.style.borderRadius = '12px';
            rpsDiv.style.marginBottom = '20px';

            const title = i18n.t('choose_sign');
            rpsDiv.innerHTML = `<h3 style="margin-top:0; color:var(--accent-gold);">${title}</h3>`;

            const btnContainer = document.createElement('div');
            btnContainer.style.display = 'flex';
            btnContainer.style.flexDirection = 'column';
            btnContainer.style.alignItems = 'center';
            btnContainer.style.gap = '10px';

            const baseId = (perspectivePlayer === 1) ? ActionBases.RPS_P2 : ActionBases.RPS;
            const signs = [
                { id: baseId + 0, name: 'Rock', jp: 'グー' },
                { id: baseId + 1, name: 'Paper', jp: 'パー' },
                { id: baseId + 2, name: 'Scissors', jp: 'チョキ' }
            ];

            signs.forEach(sign => {
                const hasAction = state.legal_actions && state.legal_actions.some(a => a.id === sign.id);
                const a = { id: sign.id, name: currentLang === 'en' ? sign.name : sign.jp };
                const btn = createActionButton(a, false, 'rps-btn');
                btn.style.width = '120px';
                btn.style.opacity = hasAction ? '1' : '0.4';
                btn.style.pointerEvents = hasAction ? 'auto' : 'none';
                btnContainer.appendChild(btn);
            });

            rpsDiv.appendChild(btnContainer);
            actionsDiv.appendChild(rpsDiv);
            return;
        }

        if (state.pending_choice) {
            const choice = state.pending_choice;
            const choiceDiv = document.createElement('div');
            choiceDiv.className = 'pending-choice-indicator';

            const opcode = choice.opcode || (state.legal_actions && state.legal_actions[0] && state.legal_actions[0].opcode);
            let headerColor = 'var(--accent-gold)';
            if (opcode === 58) headerColor = '#ff4d4d';
            else if (opcode === 15 || opcode === 17 || opcode === 63 || opcode === 30) headerColor = '#4da6ff';
            else if (opcode === 45) headerColor = '#ffcc00';
            else if (opcode === 41 || opcode === 74) headerColor = '#9966ff';

            // JS keeps border-left color logic
            choiceDiv.style.borderLeft = `4px solid ${headerColor}`;

            // Rust serializer sends 'card_id', not 'source_card_id'
            const cardId = choice.card_id !== undefined ? choice.card_id : (choice.source_card_id !== undefined ? choice.source_card_id : -1);
            let cardName = choice.source_member;

            if (!cardName || cardName === 'Unknown Source' || cardName === 'Unknown Card' || cardName.startsWith('Card ')) {
                const resolvedCard = State.resolveCardData(cardId);
                if (resolvedCard && resolvedCard.name) {
                    cardName = resolvedCard.name;
                } else {
                    cardName = i18n.t('unknown_card');
                }
            }

            let headerText = cardName;
            if (cardId >= 0) {
                headerText += ` <span style="opacity:0.6; font-size:0.8em;">(ID: ${cardId})</span>`;
            }

            let content = `<div class="choice-header" style="color:${headerColor};">${headerText}</div>`;

            // Show the triggering ability text
            let abilityText = "";
            if (cardId >= 0) {
                const card = State.resolveCardData(cardId);
                const naturalText = Tooltips.extractRelevantAbility(card, choice.trigger_label, choice.ability_index);
                if (naturalText && !Tooltips.isGenericInstruction(naturalText)) {
                    abilityText = naturalText;
                }
            }

            // Fallback to server-provided source_ability (pseudocode) if no natural block found
            if (!abilityText || abilityText.length < 5) {
                const fallback = choice.source_ability || "";
                // If it's a generic choice (Pass/No), we really don't want to show the full pseudocode underneath it
                const isGenericChoice = Tooltips.isGenericInstruction(choice.choice_text);
                if (fallback && fallback.length > 5 && !Tooltips.isGenericInstruction(fallback) && !isGenericChoice) {
                    abilityText = fallback;
                }
            }

            if (abilityText && abilityText.length > 5 && !Tooltips.isGenericInstruction(abilityText)) {
                const blocks = Tooltips.splitAbilities ? Tooltips.splitAbilities(abilityText) : [abilityText];
                blocks.forEach(block => {
                    const enriched = Tooltips.enrichAbilityText(block);
                    content += `<div class="source-ability-text">${enriched}</div>`;
                });
            }


            choiceDiv.innerHTML = content;

            if (choice.choice_type === 29) { // REARRANGE_FORMATION
                const confirmBtn = document.createElement('button');
                confirmBtn.className = 'action-btn confirm';
                confirmBtn.style.width = '100%';
                confirmBtn.style.marginTop = '10px';
                confirmBtn.innerHTML = i18n.t('confirm_formation') || (State.currentLang === 'jp' ? 'フォーメーションを確定' : 'Confirm Formation');

                confirmBtn.onclick = () => {
                    const pIdx = State.perspectivePlayer;
                    const oldStage = State.rawData.players[pIdx].stage;
                    const newStage = state.players[pIdx].stage;

                    const perms = [
                        [0, 1, 2], [0, 2, 1], [1, 0, 2], [1, 2, 0], [2, 0, 1], [2, 1, 0]
                    ];
                    let permIdx = 0;
                    for (let i = 0; i < perms.length; i++) {
                        const p = perms[i];
                        if (newStage[0] === oldStage[p[0]] &&
                            newStage[1] === oldStage[p[1]] &&
                            newStage[2] === oldStage[p[2]]) {
                            permIdx = i;
                            break;
                        }
                    }
                    if (window.doAction) window.doAction(permIdx);
                };
                choiceDiv.appendChild(confirmBtn);
            } else if (choice.options && choice.options.length > 0) {
                const optContainer = document.createElement('div');
                optContainer.className = 'action-list choice-options-container';

                choice.options.forEach((opt, idx) => {
                    const optCardId = opt.card_id !== undefined ? opt.card_id : cardId;
                    const a = {
                        id: choice.actions[idx],
                        source_card_id: optCardId,
                        name: opt.name || opt.text || `Option ${idx + 1}`,
                        text: opt.text
                    };
                    const btn = createActionButton(a, false, 'confirm');
                    btn.style.width = '100%';
                    optContainer.appendChild(btn);
                });
                choiceDiv.appendChild(optContainer);
            }
            actionsDiv.appendChild(choiceDiv);
            return;
        }

        if (state.is_ai_thinking) {
            const aiDiv = document.createElement('div');
            aiDiv.className = 'ai-thinking-indicator';
            aiDiv.innerHTML = `<div style="font-weight:bold; color:#0096ff; padding:10px; border-left:4px solid #0096ff; background:rgba(0,150,255,0.1); border-radius:8px;">${state.ai_status || i18n.t('ai_thinking')}</div>`;
            actionsDiv.appendChild(aiDiv);
        }

        if (!state.legal_actions || state.legal_actions.length === 0) {
            actionsDiv.innerHTML = `<div class="no-actions">${i18n.t('wait')}</div>`;
            return;
        }

        const listDiv = document.createElement('div');
        listDiv.className = 'action-list';
        actionsDiv.appendChild(listDiv);

        const playActionsByHand = {};
        const mulliganActions = {};
        const abilityActions = [];
        const systemActions = [];
        const otherActions = [];

        state.legal_actions.forEach(a => {
            const category = a.category || a.type;
            const hIdx = a.hand_idx;
            const sIdx = a.slot_idx;

            // Normalize card_id → source_card_id (Rust sends card_id in metadata)
            if (a.source_card_id === undefined && a.card_id !== undefined) {
                a.source_card_id = a.card_id;
            }

            if (a.source_card_id === undefined) {
                if (hIdx !== undefined) {
                    const card = state.players[perspectivePlayer]?.hand[hIdx];
                    if (card) a.source_card_id = card.id;
                } else if (category === 'ABILITY' && sIdx !== undefined) {
                    const card = state.players[perspectivePlayer]?.stage[sIdx];
                    if (card) a.source_card_id = card.id;
                }
            }

            if (a.id === 0 || a.type === 'SYSTEM' || a.id < 10 || a.name?.includes('End') || a.name?.includes('終了')) {
                systemActions.push(a);
            } else if (category === 'PLAY' && hIdx !== undefined) {
                if (!playActionsByHand[hIdx]) playActionsByHand[hIdx] = [];
                playActionsByHand[hIdx].push(a);
            } else if (a.type === 'MULLIGAN' && hIdx !== undefined) {
                if (!mulliganActions[hIdx]) mulliganActions[hIdx] = [];
                mulliganActions[hIdx].push(a);
            } else if (category === 'ABILITY') {
                abilityActions.push(a);
            } else {
                otherActions.push(a);
            }
        });

        const addHeader = (text, color) => {
            const header = document.createElement('div');
            header.className = 'category-header';
            header.style.color = color || 'rgba(255,255,255,0.4)';
            header.innerText = text;
            listDiv.appendChild(header);
        };

        if (systemActions.length > 0) {
            addHeader(i18n.t('system'));
            systemActions.forEach(a => listDiv.appendChild(createActionButton(a, false, a.id === 0 ? 'confirm system' : 'system')));
        }

        if (abilityActions.length > 0) {
            addHeader(i18n.t('act_ability').toUpperCase(), '#9966ff');
            abilityActions.forEach(a => listDiv.appendChild(createActionButton(a)));
        }

        const perspectivePlayerHand = state.players[perspectivePlayer]?.hand || [];
        const allMulliganActions = Object.values(mulliganActions).flat();
        if (allMulliganActions.length > 0) {
            addHeader(i18n.t('mulligan').toUpperCase(), 'var(--accent-pink)');
            allMulliganActions.forEach(a => listDiv.appendChild(createActionButton(a)));
        }

        if (Object.keys(playActionsByHand).length > 0) {
            addHeader(i18n.t('event_play').toUpperCase(), 'var(--accent-gold)');
            Object.keys(playActionsByHand).sort((a, b) => parseInt(a) - parseInt(b)).forEach(hIdx => {
                const actions = playActionsByHand[hIdx];
                const firstA = actions[0];
                const groupDiv = document.createElement('div');
                groupDiv.className = 'action-group-card';

                const header = document.createElement('div');
                header.className = 'action-group-header';
                const energyIcon = `<img src="img/texticon/icon_energy.png" style="height:14px; vertical-align:middle; margin-left: 5px;">`;
                const displayCost = firstA.cost ?? firstA.base_cost ?? 0;
                let cleanName = (firstA.name ?? "").replace(/[【\[].*?[】\]]/g, "").replace(/\(.*?\)/g, "").trim();
                header.innerHTML = `<span>${cleanName}</span> <span class="header-base-cost">${energyIcon}${displayCost}</span>`;
                groupDiv.appendChild(header);

                const btnsDiv = document.createElement('div');
                btnsDiv.className = 'action-group-buttons grid-3';
                for (let slotIdx = 0; slotIdx < 3; slotIdx++) {
                    const a = actions.find(act => (act.slot_idx === slotIdx) && act.secondary_slot_idx === undefined);
                    if (a) {
                        btnsDiv.appendChild(createActionButton(a, true));
                    } else {
                        const spacer = document.createElement('div');
                        spacer.style.visibility = 'hidden';
                        spacer.style.minHeight = '36px';
                        btnsDiv.appendChild(spacer);
                    }
                }
                groupDiv.appendChild(btnsDiv);

                const doubleActions = actions.filter(act => act.secondary_slot_idx !== undefined);
                if (doubleActions.length > 0) {
                    const pairs = {};
                    doubleActions.forEach(a => {
                        const s1 = a.slot_idx;
                        const s2 = a.secondary_slot_idx;
                        const key = [s1, s2].sort().join('-');
                        if (!pairs[key]) pairs[key] = [];
                        pairs[key].push(a);
                    });

                    Object.values(pairs).forEach(pairActions => {
                        const doubleDiv = document.createElement('div');
                        doubleDiv.className = 'action-group-buttons double-baton-row grid-3';

                        const pairSlots = new Set();
                        pairActions.forEach(a => pairSlots.add(a.slot_idx));
                        pairActions.forEach(a => pairSlots.add(a.secondary_slot_idx));

                        for (let i = 0; i < 3; i++) {
                            const a = pairActions.find(act => act.slot_idx === i);
                            if (a) {
                                const btn = createActionButton(a, true, 'double-baton-btn');
                                btn.style.width = '100%';
                                doubleDiv.appendChild(btn);
                            } else if (pairSlots.has(i)) {
                                const spacer = document.createElement('div');
                                spacer.className = 'pair-spacer';
                                spacer.innerText = currentLang === 'jp' ? '間' : 'GAP';
                                doubleDiv.appendChild(spacer);
                            } else {
                                const spacer = document.createElement('div');
                                spacer.style.visibility = 'hidden';
                                doubleDiv.appendChild(spacer);
                            }
                        }
                        groupDiv.appendChild(doubleDiv);
                    });
                }
                listDiv.appendChild(groupDiv);
            });
        }

        if (otherActions.length > 0) {
            addHeader(i18n.t('actions').toUpperCase());
            otherActions.forEach(a => listDiv.appendChild(createActionButton(a)));
        }
    },

    renderGameOver: (state) => {
        const winnerName = state.winner === State.perspectivePlayer ? "YOU" : `Player ${state.winner + 1}`;
        const gameOverHTML = `
                <div class="game-over-banner">
                    <h2>GAME OVER</h2>
                    <div class="winner-announcement">Winner: ${winnerName}</div>
                    <button class="btn btn-primary" onclick="location.reload()">New Game</button>
                </div>
            `;
        DOMUtils.setHTML(DOM_IDS.CONTAINER_ACTIONS, gameOverHTML);
    }
};
