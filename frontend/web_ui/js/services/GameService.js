import { State, updateStateData } from '../state.js';
import { log } from '../logger.js';
import { Phase, getAppBaseUrl } from '../constants.js';
import { DOMUtils } from '../utils/DOMUtils.js';
import { ModalManager } from '../utils/ModalManager.js';
import { DOM_IDS, COLORS } from '../constants_dom.js';

export const GameService = {
    checkSystemStatus: async () => {
        const badge = DOMUtils.getElement(DOM_IDS.SYSTEM_STATUS_BADGE);
        if (!badge) return;
        try {
            const res = await fetch('api/status');
            const data = await res.json();
            if (data.status === 'rust_server') {
                const cardCount = (data.members || 0) + (data.lives || 0);
                DOMUtils.setText(DOM_IDS.SYSTEM_STATUS_BADGE, cardCount > 0 ? `ONLINE: ${cardCount} Cards` : "ONLINE: 0 Cards (ERROR)");
                DOMUtils.setBackground(DOM_IDS.SYSTEM_STATUS_BADGE, cardCount > 100 ? COLORS.ONLINE : COLORS.WARNING);
                badge.title = `Members: ${data.members}, Lives: ${data.lives} | ID: ${data.instance_id}`;

                if (data.instance_id) {
                    const lastId = localStorage.getItem('lovelive_server_instance_id');
                    if (lastId && lastId !== String(data.instance_id)) {
                        console.warn("[Network] Server instance ID changed! Forcing local reset...");
                        localStorage.setItem('lovelive_server_instance_id', data.instance_id);
                        if (typeof window.forceReset === 'function') {
                            window.forceReset();
                        }
                    } else {
                        localStorage.setItem('lovelive_server_instance_id', data.instance_id);
                    }
                }
                return data;
            } else {
                DOMUtils.setText(DOM_IDS.SYSTEM_STATUS_BADGE, "UNKNOWN");
                DOMUtils.setBackground(DOM_IDS.SYSTEM_STATUS_BADGE, COLORS.UNKNOWN);
            }
        } catch (e) {
            DOMUtils.setText(DOM_IDS.SYSTEM_STATUS_BADGE, "OFFLINE");
            DOMUtils.setBackground(DOM_IDS.SYSTEM_STATUS_BADGE, COLORS.OFFLINE);
        }
        return null;
    },

    fetchState: async (networkFacade) => {
        let receivedResponse = false;
        try {
            if (State.replayMode) return;

            if (State.offlineMode) {
                if (!State.wasmAdapter) return;
                const res = await State.wasmAdapter.fetchState();
                if (res.success) {
                    State.lastStateJson = JSON.stringify(res.state);
                    updateStateData(res.state);
                    if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
                }
                return;
            }

            if (!State.roomCode) return;

            const perfModal = document.getElementById('performance-modal');
            if (perfModal && (perfModal.style.display === 'flex' || perfModal.style.display === 'block')) {
                return;
            }

            if (!State.sessionToken && State.roomCode && networkFacade?.loadSession) {
                networkFacade.loadSession(State.roomCode);
            }

            const headers = networkFacade?.getHeaders ? networkFacade.getHeaders() : {};
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            const viewer = State.perspectivePlayer;
            const timestamp = Date.now();
            const url = `api/state?viewer=${viewer}&_t=${timestamp}`;

            const res = await fetch(url, {
                headers,
                signal: controller.signal
            });
            receivedResponse = true;
            clearTimeout(timeoutId);

            if (res.status === 404) {
                if (State.roomCode) {
                    console.warn(`[Network] Room ${State.roomCode} not found (404). Resetting local state.`);
                    const codeToClear = State.roomCode;
                    localStorage.removeItem('lovelive_room_code');
                    localStorage.removeItem(`lovelive_session_${codeToClear}`);

                    State.resetForNewGame();
                    if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
                    updateStateData(null);

                    if (networkFacade?.triggerRoomUpdate) networkFacade.triggerRoomUpdate();
                    ModalManager.show(DOM_IDS.MODAL_ROOM);
                    log(`Room ${codeToClear} expired or not found.`, 'error');
                }
                return;
            }

            const raw = await res.text();
            if (raw === State.lastStateJson) return;

            State.lastStateJson = raw;
            const data = JSON.parse(raw);

            if (data.success) {
                updateStateData(data.state);

                if (State.data.my_player_id !== undefined && State.data.my_player_id !== -1 && !State.hotseatMode) {
                    State.perspectivePlayer = State.data.my_player_id;
                }

                const currentState = State.data;
                const hasGameStarted = !!(currentState && currentState.legal_actions && currentState.legal_actions.length > 0);
                if (hasGameStarted && currentState.phase !== Phase.SETUP) {
                    State.gameHasStarted = true;
                }
                
                if (State.data.needs_deck && State.data.phase === Phase.SETUP && !State.gameHasStarted && !hasGameStarted && !State.hotseatMode && !State.offlineMode) {
                    if (!ModalManager.isVisible(DOM_IDS.MODAL_SETUP)) {
                        if (networkFacade?.onOpenDeckModal) {
                            networkFacade.onOpenDeckModal(State.perspectivePlayer);
                        }
                    }
                }
            } else {
                console.error("State fetch unsuccessful:", data.error);
                return;
            }

            const turnNum = State.data.turn_number || State.data.turn || 0;
            const perfRes = State.data.performance_results || State.data.last_performance_results;

            if (perfRes && Object.keys(perfRes).length > 0) {
                State.lastPerformanceData = perfRes;
            }

            if (perfRes && Object.keys(perfRes).length > 0 && (!State.data.performance_history || State.data.performance_history.length === 0)) {
                if (!State.performanceHistory[turnNum]) {
                    State.performanceHistory[turnNum] = perfRes;
                    if (!State.performanceHistoryTurns.includes(turnNum)) {
                        State.performanceHistoryTurns.push(turnNum);
                        State.performanceHistoryTurns.sort((a, b) => b - a);
                    }
                }
            }

            if (networkFacade?.getPlannerFetchKey && networkFacade?.shouldAutoFetchPlanner && networkFacade?.fetchPlannerData) {
                const plannerKey = networkFacade.getPlannerFetchKey();
                if (networkFacade.shouldAutoFetchPlanner() && plannerKey !== State.lastPlannerFetchKey) {
                    networkFacade.fetchPlannerData({ silent: true });
                }
            }
        } catch (e) {
            console.error("Fetch Error:", e);
            if (e.name === 'AbortError') {
                console.warn("[Network] Fetch state timed out.");
            } else if (State.roomCode && !receivedResponse) {
                console.error("[Network] Critical connection failure. Returning to lobby.");
                const codeToClear = State.roomCode;
                State.resetForNewGame();
                if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
                localStorage.removeItem('lovelive_room_code');
                localStorage.removeItem(`lovelive_session_${codeToClear}`);
                updateStateData(null);
                if (networkFacade?.triggerRoomUpdate) networkFacade.triggerRoomUpdate();

                ModalManager.show(DOM_IDS.MODAL_ROOM);
                log("Connection lost or server unreachable.", 'error');
            }
        }
    },

    sendAction: async (id, networkFacade) => {
        const state = State.data;
        if (!state) return;

        const isRpsPhase = state.phase === Phase.RPS;
        if (!isRpsPhase && state.active_player !== State.perspectivePlayer && !State.hotseatMode) {
            console.warn("[Network] Action blocked: Not your turn.");
            return;
        }

        if (window.pendingAction) return;
        window.pendingAction = true;
        document.body.classList.add('action-pending');
        log(`Action: ${id}`, 'action');

        try {
            if (State.offlineMode) {
                const res = await State.wasmAdapter.doAction(id);
                if (res.success) {
                    updateStateData(res.state);
                    if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
                    State.lastStateJson = JSON.stringify(res.state);
                    log('Action completed');
                } else {
                    alert(res.error);
                }
                return;
            }

            const res = await fetch('api/action', {
                method: 'POST',
                headers: networkFacade?.getHeaders ? networkFacade.getHeaders() : {},
                body: JSON.stringify({ action_id: id })
            });
            const text = await res.text();
            State.lastStateJson = text;
            const data = JSON.parse(text);

            if (data.success) {
                updateStateData(data.state);
                if (State.data.my_player_id !== undefined && State.data.my_player_id !== -1 && !State.hotseatMode) {
                    State.perspectivePlayer = State.data.my_player_id;
                }
                if (networkFacade?.fetchPlannerData) await networkFacade.fetchPlannerData({ silent: true });
                log('Action completed');
            } else {
                alert(data.error || 'Unknown error');
            }
        } finally {
            window.pendingAction = false;
            document.body.classList.remove('action-pending');
        }
    },

    resetGame: async (networkFacade) => {
        log('Resetting game...');
        State.resetForNewGame();
        if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();

        if (State.offlineMode) {
            const res = await State.wasmAdapter.resetGame();
            if (res.success) {
                updateStateData(res.state);
                window.lastShownPerformanceHash = "";
                log('New game started');
            }
            return;
        }

        const state = State.data;
        const modeToUse = (state && state.mode) ? state.mode : (State.hotseatMode ? "pvp" : "pve");

        try {
            const res = await fetch('api/reset', {
                method: 'POST',
                headers: networkFacade?.getHeaders ? networkFacade.getHeaders() : {},
                body: JSON.stringify({ mode: modeToUse })
            });

            if (!res.ok) {
                log(`Reset failed: ${res.status}`);
                return;
            }

            const text = await res.text();
            State.lastStateJson = text;
            const data = JSON.parse(text);

            if (data.success) {
                updateStateData(data.state);
                window.lastShownPerformanceHash = "";
                log('New game started');
                if (networkFacade?.fetchState) await networkFacade.fetchState();
            } else {
                log(`Reset failed: ${data.error}`);
            }
        } catch (e) {
            log(`Reset error: ${e.message}`);
        }
    },

    startOffline: async (userInitiated = true, networkFacade) => {
        if (userInitiated) {
            const confirmMsg = "Offline mode runs entirely in your browser using WebAssembly.\n\n" +
                "It may take a moment to load the engine.";
            if (!confirm(confirmMsg)) return;
        }

        try {
            if (!State.wasmAdapter) {
                try {
                    const base = getAppBaseUrl();
                    const mod = await import(`${base}js/wasm_adapter.js`);
                    State.wasmAdapter = mod.wasmAdapter;
                    await State.wasmAdapter.init();
                } catch (e) {
                    console.error("Failed to load WASM:", e);
                    alert("Failed to load Offline Engine: " + e.message);
                    return;
                }
            }

            State.offlineMode = true;
            State.roomCode = null;
            State.sessionToken = null;
            if (networkFacade?.clearPlannerData) networkFacade.clearPlannerData();
            updateStateData(null);

            ModalManager.hide(DOM_IDS.MODAL_ROOM);
            DOMUtils.setText(DOM_IDS.HEADER_DEBUG_INFO, "Offline (WASM)");

            if (networkFacade?.triggerRoomUpdate) networkFacade.triggerRoomUpdate();

            const res = await State.wasmAdapter.resetGame();
            if (res.success) {
                updateStateData(res.state);
                log("Offline Game Started!");
            } else {
                alert("Failed to start offline game: " + res.error);
            }
        } catch (e) {
            console.error(e);
            alert("Offline mode error: " + e.message);
        }
    },

    changeAI: async (aiMode, networkFacade) => {
        try {
            const res = await fetch('api/set_ai', {
                method: 'POST',
                headers: networkFacade?.getHeaders ? networkFacade.getHeaders() : {},
                body: JSON.stringify({ ai_mode: aiMode })
            });
            const data = await res.json();
            if (!data.success) alert('Failed: ' + data.error);
        } catch (e) { console.error(e); }
    }
};
