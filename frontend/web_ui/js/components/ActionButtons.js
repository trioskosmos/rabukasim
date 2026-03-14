import { State } from '../state.js';
import * as i18n from '../i18n/index.js';
import { Tooltips } from '../ui_tooltips.js';
import { Phase } from '../constants.js';

export const ActionButtons = {
    getActionLabel: (a, isMini = false, state) => {
        const currentLang = State.currentLang;
        if (a.id === 0 && state.pending_choice) {
            if (state.phase === Phase.MulliganP1 || state.phase === Phase.MulliganP2) {
                return i18n.t('done');
            }
            return i18n.t('pass_no');
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
                    const trans = i18n.getCurrentTranslations();
                    name = trans?.params?.COLOR?.[colorKey] || colorKey;
                }
            } else if (a.id >= 500 && a.id < 510) {
                const modeIdx = a.id - 500;
                const pc = state.pending_choice;
                if (pc && pc.options_text && pc.options_text[modeIdx]) {
                    name = pc.options_text[modeIdx];
                } else {
                    name = i18n.t('mode_n', { n: modeIdx });
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

            if (window.translateAbility) {
                displayName = window.translateAbility(displayName, currentLang);
            }

            displayName = Tooltips.enrichAbilityText(displayName);

            let label = `<div class="action-title" style="${(displayName.includes('&') || displayName.includes('＆')) ? 'font-size:0.85em;' : ''}">${displayName}</div>`;
            if (cost !== null) label += `<div class="action-cost">${energyIcon}${cost}</div>`;
            if (isBaton && a.metadata?.secondary_slot_idx === undefined) label += ' [B]';
            return label;
        }
    },

    createActionButton: (a, isMini = false, extraClass = '', state) => {
        const btn = document.createElement('button');
        btn.className = `action-btn ${isMini ? 'mini' : ''} ${extraClass}`.trim();

        const sourceCard = a.source_card_id !== undefined ? Tooltips.findCardById(a.source_card_id) : null;
        Tooltips.attachCardData(btn, sourceCard, a.id);

        if (a.raw_text || a.text) btn.setAttribute('data-text', a.raw_text || a.text);

        btn.innerHTML = ActionButtons.getActionLabel(a, isMini, state);
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
    }
};
