import { validator } from '../components/DeckValidator.js';

export const LobbyModal = {
    openLobby: () => {
        const modal = document.getElementById('room-modal');
        if (modal) modal.style.display = 'flex';
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
        const modal = document.getElementById('room-modal');
        if (modal) modal.style.display = 'none';
    }
};
