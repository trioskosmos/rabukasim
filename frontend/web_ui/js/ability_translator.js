/**
 * ability_translator.js - Legacy Facade for i18n module
 */

import { translateAbility as modularTranslate, NAME_MAP, loadTranslations } from './i18n/index.js';

// Re-expose to global window for legacy onclick handlers and direct access
window.translateAbility = modularTranslate;
window.NAME_MAP = NAME_MAP;
window.loadTranslations = loadTranslations;

// For backward compatibility with any code directly accessing window.Translations
// Note: This will only be populated AFTER loadTranslations is called.
Object.defineProperty(window, 'Translations', {
    get: () => {
        // This is a bit of a hack to support code that expects window.Translations.jp/en
        // But since we now load JSON dynamically, we might not have both.
        // We'll return an object that proxies to the modular state if possible.
        return {
            jp: window.currentTranslationsJP || {},
            en: window.currentTranslationsEN || {}
        };
    },
    configurable: true
});

export { modularTranslate as translateAbility, NAME_MAP };
export default modularTranslate;
