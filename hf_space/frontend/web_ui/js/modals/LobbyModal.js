import { validator } from '../components/DeckValidator.js';
import { ModalManager } from '../utils/ModalManager.js';
import { DOM_IDS } from '../constants_dom.js';

export const LobbyModal = {
    openLobby: () => {
        ModalManager.show(DOM_IDS.MODAL_ROOM);
        validator.init();
        if (window.fetchPublicRooms) window.fetchPublicRooms();

        const input = document.getElementById('pjoin-deck-paste');
        if (input) {
            input.addEventListener('input', () => LobbyModal.validateInline());
        }
    },

    validateInline: () => {
        const input = document.getElementById('pjoin-deck-paste');
        const preview = document.getElementById('pjoin-deck-preview');
        if (!input || !preview) return;

        const results = validator.validateDeckString(input.value);
        validator.renderPreview(results, preview);
    },

    closeLobby: () => {
        ModalManager.hide(DOM_IDS.MODAL_ROOM);
    }
};
