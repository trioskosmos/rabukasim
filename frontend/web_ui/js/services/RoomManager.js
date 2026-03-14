import { State } from '../state.js';
import { log } from '../logger.js';
import { ModalManager } from '../utils/ModalManager.js';
import { DOMUtils } from '../utils/DOMUtils.js';
import { DOM_IDS } from '../constants_dom.js';

export const RoomManager = {
    // Session Management
    saveSession: (room, sessionData) => {
        if (!room) return;
        const key = `lovelive_session_${room}`;
        localStorage.setItem(key, JSON.stringify(sessionData));
        State.sessionToken = sessionData.token;
        if (sessionData.playerId !== undefined) State.perspectivePlayer = sessionData.playerId;
    },

    loadSession: (room) => {
        if (!room) return null;
        const key = `lovelive_session_${room}`;
        const saved = localStorage.getItem(key);
        if (saved) {
            try {
                const data = JSON.parse(saved);
                State.sessionToken = data.token;
                if (data.playerId !== undefined) State.perspectivePlayer = data.playerId;
                return data;
            } catch (e) {
                console.error("Failed to load session", e);
            }
        }
        return null;
    },

    // Room Management
    createRoom: async (mode = 'pve', networkFacade) => {
        try {
            State.resetForNewGame();

            const res = await fetch('api/rooms/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: mode })
            });
            const data = await res.json();
            if (data.success) {
                State.roomCode = data.room_id;
                State.offlineMode = false;
                if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
                localStorage.setItem('lovelive_room_code', State.roomCode);

                State.sessionToken = null;
                localStorage.removeItem(`lovelive_session_${State.roomCode}`);

                ModalManager.hide(DOM_IDS.MODAL_ROOM);
                log(`Created Room: ${State.roomCode} (${mode})`);

                if (networkFacade?.fetchState) await networkFacade.fetchState();
                if (networkFacade?.triggerRoomUpdate) networkFacade.triggerRoomUpdate();

                if (mode === 'pvp' && networkFacade?.fetchState) {
                    setTimeout(() => networkFacade.fetchState(), 1000);
                }
            } else {
                alert('Failed to create room: ' + data.error);
            }
        } catch (e) {
            console.error(e);
            alert('Network error creating room');
        }
    },

    joinRoom: async (code = null, networkFacade) => {
        if (!code) {
            const input = DOMUtils.getElement(DOM_IDS.ROOM_CODE_INPUT);
            if (input) code = input.value.toUpperCase();
        }
        if (!code || code.length !== 4) {
            alert('Please enter a 4-letter room code.');
            return;
        }
        
        State.resetForNewGame();
        State.roomCode = code;
        State.offlineMode = false;
        if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
        localStorage.setItem('lovelive_room_code', State.roomCode);

        RoomManager.loadSession(code);

        try {
            const res = await fetch('api/rooms/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_id: code })
            });
            const data = await res.json();
            if (data.success) {
                State.cardSet = data.card_set || 'compiled';
                RoomManager.saveSession(code, { token: data.session, playerId: data.player_idx });
            }
        } catch (e) {
            console.error("Join API error", e);
        }

        ModalManager.hide(DOM_IDS.MODAL_ROOM);
        log(`Joining Room: ${State.roomCode}...`);

        if (networkFacade?.triggerRoomUpdate) networkFacade.triggerRoomUpdate();
        if (networkFacade?.fetchState) await networkFacade.fetchState();
    },

    leaveRoom: async (networkFacade) => {
        try {
            await fetch('api/rooms/leave', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Session-Token': State.sessionToken || ''
                }
            });
        } catch (e) {
            console.warn('Failed to notify server of leaving room:', e);
        }

        State.resetForNewGame();
        State.roomCode = null;
        State.sessionToken = null;
        if (typeof networkFacade?.updateStateData === 'function') {
             networkFacade.updateStateData(null);
        } else {
             // Fallback if facade not passed
             import('../state.js').then(m => m.updateStateData(null));
        }
        
        localStorage.removeItem('lovelive_room_code');
        ModalManager.show(DOM_IDS.MODAL_ROOM);
        ModalManager.hide('performance-modal');
        ModalManager.hide(DOM_IDS.MODAL_SETUP);
        history.pushState({}, document.title, window.location.pathname);
        if (networkFacade?.triggerRoomUpdate) networkFacade.triggerRoomUpdate();
    },

    fetchPublicRooms: async () => {
        const list = DOMUtils.getElement(DOM_IDS.PUBLIC_ROOMS_LIST);
        if (!list) return;

        DOMUtils.setHTML(DOM_IDS.PUBLIC_ROOMS_LIST, '<div style="color:#666;text-align:center;padding-top:20px;">Loading...</div>');

        try {
            const res = await fetch('api/rooms/list');
            const data = await res.json();

            if (!data.rooms || data.rooms.length === 0) {
                DOMUtils.setHTML(DOM_IDS.PUBLIC_ROOMS_LIST, '<div style="color:#666;text-align:center;padding-top:20px;">No active public rooms.</div>');
                return;
            }

            DOMUtils.clear(DOM_IDS.PUBLIC_ROOMS_LIST);
            data.rooms.forEach(r => {
                const div = document.createElement('div');
                div.className = 'public-room-item';
                div.style.padding = '5px';
                div.style.borderBottom = '1px solid #444';
                div.style.cursor = 'pointer';
                div.style.display = 'flex';
                div.style.justifyContent = 'space-between';
                div.innerHTML = `
                    <span>Room <b>${r.id}</b> (${r.mode})</span>
                    <span style="color:#aaa; font-size:0.8rem;">${r.players_count}/2</span>
                `;
                div.onclick = () => {
                    const input = DOMUtils.getElement(DOM_IDS.ROOM_CODE_INPUT);
                    if (input) input.value = r.id;
                    // Note: joinRoom needs the network facade, so we'll let the UI call the facade version
                    if (window.Network && window.Network.joinRoom) {
                        window.Network.joinRoom(r.id);
                    }
                };
                list.appendChild(div);
            });
        } catch (e) {
            DOMUtils.setHTML(DOM_IDS.PUBLIC_ROOMS_LIST, '<div style="color:#e74c3c;text-align:center;padding-top:20px;">Failed to load rooms.</div>');
        }
    }
};
