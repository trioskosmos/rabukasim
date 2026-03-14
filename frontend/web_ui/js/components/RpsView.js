import { ActionButtons } from './ActionButtons.js';
import { ActionBases } from '../generated_constants.js';
import * as i18n from '../i18n/index.js';

export const RpsView = {
    render: (state, perspectivePlayer, container) => {
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
            { id: baseId + 0, name: i18n.t('rock') },
            { id: baseId + 1, name: i18n.t('paper') },
            { id: baseId + 2, name: i18n.t('scissors') }
        ];

        signs.forEach(sign => {
            const hasAction = state.legal_actions && state.legal_actions.some(a => a.id === sign.id);
            const a = { id: sign.id, name: sign.name };
            const btn = ActionButtons.createActionButton(a, false, 'rps-btn', state);
            btn.style.width = '120px';
            btn.style.opacity = hasAction ? '1' : '0.4';
            btn.style.pointerEvents = hasAction ? 'auto' : 'none';
            btnContainer.appendChild(btn);
        });

        rpsDiv.appendChild(btnContainer);
        container.appendChild(rpsDiv);
    }
};
