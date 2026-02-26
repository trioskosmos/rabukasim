export const LobbyModal = {
    openLobby: () => {
        const modal = document.getElementById('room-modal');
        if (modal) modal.style.display = 'flex';
        if (window.fetchPublicRooms) window.fetchPublicRooms();
    },

    closeLobby: () => {
        const modal = document.getElementById('room-modal');
        if (modal) modal.style.display = 'none';
    }
};
