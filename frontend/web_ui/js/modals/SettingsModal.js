import { State } from '../state.js';

export const SettingsModal = {
    openSettingsModal: () => {
        const modal = document.getElementById('settings-modal');
        if (modal) modal.style.display = 'flex';
    },

    closeSettingsModal: () => {
        const modal = document.getElementById('settings-modal');
        if (modal) modal.style.display = 'none';
    },

    updateBoardScale: (val) => {
        const scale = parseFloat(val);
        document.documentElement.style.setProperty('--zoom-override', scale);
        const zoomValue = document.getElementById('zoom-value');
        if (zoomValue) zoomValue.textContent = scale.toFixed(2);
        localStorage.setItem('lovelive_board_scale', scale);

        const slider = document.getElementById('zoom-slider');
        if (slider && slider.value != val) slider.value = val;
    },

    toggleLang: () => {
        State.currentLang = State.currentLang === 'jp' ? 'en' : 'jp';
        SettingsModal.updateLanguage();
    },

    toggleFriendlyAbilities: () => {
        State.showFriendlyAbilities = !State.showFriendlyAbilities;
        localStorage.setItem('lovelive_friendly_abilities', State.showFriendlyAbilities);
        SettingsModal.updateLanguage();
        if (window.render) window.render();
    },

    updateLanguage: () => {
        if (!window.translations) return;
        const t = window.translations[State.currentLang];
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) {
                if (key === 'friendly_abilities') {
                    el.textContent = `${t[key]}: ${State.showFriendlyAbilities ? 'ON' : 'OFF'}`;
                } else {
                    el.textContent = t[key];
                }
            }
        });

        const btn = document.getElementById('lang-btn');
        if (btn) btn.textContent = State.currentLang === 'jp' ? 'English' : '日本語';

        if (State.data && window.render) window.render();
    }
};
