import { State } from '../state.js';
import { Network } from '../network.js';

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

    toggleLang: async () => {
        State.currentLang = State.currentLang === 'jp' ? 'en' : 'jp';
        localStorage.setItem('lovelive_lang', State.currentLang);

        // Ensure translations are loaded before updating UI
        const { loadTranslations } = await import('../i18n/index.js');
        await loadTranslations(State.currentLang);

        SettingsModal.updateLanguage();
    },

    toggleFriendlyAbilities: () => {
        State.showFriendlyAbilities = !State.showFriendlyAbilities;
        localStorage.setItem('lovelive_friendly_abilities', State.showFriendlyAbilities);
        SettingsModal.updateLanguage();
        if (window.render) window.render();
    },

    updateLanguage: () => {
        const translations = window.translations || (window.Translations ? {
            jp: window.currentTranslationsJP,
            en: window.currentTranslationsEN
        } : null);

        if (!translations || !translations[State.currentLang]) return;

        const t = translations[State.currentLang].ui || {};
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (t[key]) {
                if (key === 'friendly_abilities' || key === 'live_watch') {
                    const stateLabel = (key === 'friendly_abilities' ? State.showFriendlyAbilities : State.isLiveWatchOn) ? (t['on'] || 'ON') : (t['off'] || 'OFF');
                    el.textContent = `${t[key]}: ${stateLabel}`;
                } else {
                    el.textContent = t[key];
                }
            }
        });

        const btn = document.getElementById('lang-btn');
        if (btn) btn.textContent = State.currentLang === 'jp' ? 'English' : '日本語';

        if (State.data && window.render) window.render();
    },

    toggleDebugMode: async () => {
        const res = await Network.toggleDebugMode();
        if (res !== null) {
            const label = i18n.t('debug_mode');
            const subLabel = i18n.t('debug_bytecode_log');
            const stateLabel = res ? i18n.t('enabled') : i18n.t('disabled');
            alert(`${label} (${subLabel}): ${stateLabel}`);
        }
    }
};
