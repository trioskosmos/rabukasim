import { ICON_DATA_URIs } from './assets_registry.js';
import { State } from './state.js';
import { Phase, fixImg } from './constants.js';
import * as i18n from './i18n/index.js';
import { Network } from './network.js';
import { Tooltips } from './ui_tooltips.js';
import { Rendering } from './ui_rendering.js';
import { DragDrop } from './ui_drag_drop.js';
import { Modals } from './ui_modals.js';
import { Replay } from './replay_system.js';
import { toggleSidebar, switchBoard } from './layout.js';
import { loadTranslations } from './i18n/index.js';
import { DOMUtils } from './utils/DOMUtils.js';
import { ModalManager } from './utils/ModalManager.js';
import { DOM_IDS, COLORS } from './constants_dom.js';

// Global UI object for layout/switching
window.UI = {
    toggleSidebar,
    switchBoard,
    showPerformanceForTurn: Modals.showPerformanceForTurn,
    showLastPerformance: Modals.showLastPerformance,
    closePerformanceModal: Modals.closePerformanceModal,
    showDiscardModal: Rendering.showDiscardModal,
    showZoneViewer: Rendering.showZoneViewer,
    showPerfTab: Rendering.showPerfTab
};

// Network Aliases (for legacy compatibility if needed)
const fetchState = Network.fetchState;

// Polling Logic
let pollingTimeout = null;

// Cache debug elements for performance
const debugElements = {
    sync: null,
    room: null,
    session: null,
    view: null,
    poll: null,
    delay: null
};

function initializeDebugElementCache() {
    debugElements.sync = DOMUtils.getElement(DOM_IDS.DEBUG_SYNC);
    debugElements.room = DOMUtils.getElement(DOM_IDS.DEBUG_ROOM);
    debugElements.session = DOMUtils.getElement(DOM_IDS.DEBUG_SESSION);
    debugElements.view = DOMUtils.getElement(DOM_IDS.DEBUG_VIEW);
    debugElements.poll = DOMUtils.getElement(DOM_IDS.DEBUG_POLL);
    debugElements.delay = DOMUtils.getElement(DOM_IDS.DEBUG_DELAY);
}

function updatePolling() {
    if (pollingTimeout) clearTimeout(pollingTimeout);
    if (!debugElements.sync) initializeDebugElementCache();

    let heartbeat = 0;
    const poll = async () => {
        try {
            heartbeat++;

            // Batch debug info updates
            const isSynced = (window.StateMaster === State);
            const debugUpdates = {
                [DOM_IDS.DEBUG_SYNC]: isSynced ? 'OK' : 'MISMATCH',
                [DOM_IDS.DEBUG_ROOM]: String(State.roomCode) || 'NULL',
                [DOM_IDS.DEBUG_SESSION]: State.sessionToken ? 'VALID' : 'MISSING',
                [DOM_IDS.DEBUG_VIEW]: `P${State.perspectivePlayer + 1}`,
                [DOM_IDS.DEBUG_POLL]: heartbeat,
                [DOM_IDS.DEBUG_DELAY]: State.offlineMode ? 'OFFLINE' : (State.replayMode ? 'REPLAY' : 'LIVE')
            };
            DOMUtils.updateText(debugUpdates);

            // Update sync color
            if (debugElements.sync) {
                debugElements.sync.style.color = isSynced ? '#00ff00' : '#ff0000';
            }

            // Update delay color
            if (debugElements.delay) {
                debugElements.delay.style.color = (State.offlineMode || State.replayMode) ? COLORS.ACCENT_GOLD : '#00ff00';
            }

            // Verbose logging for Phase 6
            console.log(`[Poll#${heartbeat}] room="${State.roomCode}" | offline=${State.offlineMode} | replay=${State.replayMode} | sync=${window.StateMaster === State}`);

            if (State.replayMode || State.offlineMode || !State.roomCode) {
                // Not in a game, keep checking slowly
                pollingTimeout = setTimeout(poll, 1000);
                return;
            }

            const isThinking = State.data && State.data.is_ai_thinking;
            // 250ms if thinking/live, 500ms if just live, 1000ms fallback
            let delay = 1000;
            if (isThinking) delay = 250;
            else if (State.isLiveWatchOn) delay = 500;

            await fetchState();
            pollingTimeout = setTimeout(poll, delay);
        } catch (e) {
            console.error("[Polling] Critical Error in Loop:", e);
            // Always reschedule even on error to prevent loop death
            pollingTimeout = setTimeout(poll, 2000);
        }
    };

    poll();
}

// --- Error Handling ---
window.onerror = function (msg, url, line, col, error) {
    console.error("[CRITICAL] Global Error Caught:", msg, "at", url, ":", line);
    const logEl = document.getElementById('rule-log');
    if (logEl) {
        const div = document.createElement('div');
        div.className = 'log-item error';
        div.innerHTML = `<span style="color:#ff5555;font-weight:bold;">[ERROR]</span> UI Crash: ${msg}`;
        logEl.prepend(div);
    }
    return false;
};

// --- Global Initialization ---
export async function initialize() {
    console.log("[Init] Starting Rabukasim UI Initialization...");


    try {
        // 0. Load translations
        console.log("[Init] Loading translations...");
        await loadTranslations(State.currentLang);

        // 0.5 Start Adaptive Polling (PROMOTED to first step)
        console.log("[Init] Starting polling (immediate)...");
        updatePolling();

        // 1. Listen for State Changes
        console.log("[Init] Wiring listeners...");
        State.on('room-change', () => {
            DOMUtils.setText(DOM_IDS.ROOM_CODE_HEADER, State.roomCode || '---');
            const roomDisplay = DOMUtils.getElement(DOM_IDS.ROOM_DISPLAY);
            if (roomDisplay) roomDisplay.style.display = State.roomCode ? 'flex' : 'none';
        });

        // Legacy alias for ui_modals.js
        window.onRoomUpdate = () => Network.triggerRoomUpdate();

        Network.setRenderCallback(() => {}); // No-op, handled by events now
        Replay.setRenderCallback(() => {});

        Network.setOpenDeckModalCallback((pid) => {
            try {
                // Only show the deck modal to the player who needs a deck
                if (pid === undefined || pid === null) {
                    Modals.openDeckModal();
                    return;
                }
                if (State.perspectivePlayer === undefined || State.perspectivePlayer === null) {
                    // If we don't yet know our perspective, avoid forcing the modal open for others.
                    console.log('[Init] Deck modal requested but perspective unknown; skipping.');
                    return;
                }
                if (pid === State.perspectivePlayer) {
                    Modals.openDeckModal();
                } else {
                    console.log(`[Init] Deck modal requested for P${pid + 1}, not current perspective P${State.perspectivePlayer + 1}; ignoring.`);
                }
            } catch (e) {
                console.error('Error handling openDeckModal callback', e);
            }
        });
        Modals.updateLanguage();

        // 2. Initial State Check (Important for re-joining)
        console.log("[Init] Checking system status...");
        await Network.checkSystemStatus();

        console.log("[Init] Fetching initial state...");
        await Network.fetchState();

        // 3. Initialize Drag & Drop
        console.log("[Init] Wiring drag & drop...");
        DragDrop.init();

        // Start Periodic Health Check
        setInterval(() => Network.checkSystemStatus(), 10000);

        // 6. Apply Saved Zoom
        const savedScale = localStorage.getItem('lovelive_board_scale');
        if (savedScale) {
            Modals.updateBoardScale(savedScale);
        }

        // 7. Initial render
        console.log("[Init] Final rendering...");
        window.render();

        // 8. Event Delegation for UI Actions
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('[data-action]');
            if (!btn) return;

            const action = btn.getAttribute('data-action');
            const id = btn.getAttribute('data-id');
            const value = btn.getAttribute('data-value');

            console.log(`[EventDelegation] Action: ${action}, ID: ${id}, Value: ${value}`);

            if (action === 'send-action' && id) window.sendAction(id);
            else if (action === 'set-perspective' && id) window.setPerspective(id);
            else if (action === 'toggle-sidebar') window.UI.toggleSidebar();
            else if (action === 'close-modal') {
                const modal = btn.closest('.modal') || btn.closest('.modal-overlay');
                if (modal) modal.style.display = 'none';
            }
        });

        // Show Lobby if not in a room and not in offline mode
        if (!State.roomCode && !State.offlineMode && !State.replayMode) {
            console.log("[Init] No room detected, showing lobby.");
            ModalManager.show(DOM_IDS.MODAL_ROOM);
        }
    } catch (e) {
        console.error("[Init] Initialization Failed:", e);
        ModalManager.show(DOM_IDS.MODAL_ROOM);
    }

    console.log("[Init] Done.");
}

// Start Initialization
initialize();

// --- Re-attach Globals (For legacy onclick handlers in index.html) ---
window.App = {
    render: Rendering.render,
    fetchState: Network.fetchState,
    refreshTurnPlanner: () => Network.fetchPlannerData(),
    scoreTurnPlanner: () => Network.fetchPlannerData({ score: true }),
    forceReset: () => {
        console.log("[Lobby] Force Reset triggered. Clearing all data...");
        localStorage.removeItem('lovelive_room_code');
        localStorage.removeItem('lovelive_sessions');
        localStorage.removeItem('lovelive_board_scale');
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('lovelive_')) {
                localStorage.removeItem(key);
                i--;
            }
        }
        window.location.reload();
    }
};

// Actions (Buttons)
window.Actions = {
    sendAction: (actionId, target = null) => Network.sendAction(actionId, target),
    doAction: (actionId, target = null) => Network.sendAction(actionId, target),
    toggleHotseat: () => { State.hotseatMode = !State.hotseatMode; window.render(); },
    toggleLiveWatch: () => { State.isLiveWatchOn = !State.isLiveWatchOn; updatePolling(); window.render(); },
    togglePerspective: () => { State.perspectivePlayer = 1 - State.perspectivePlayer; window.render(); },
    setPerspective: (id) => {
        State.perspectivePlayer = parseInt(id);
        ModalManager.hide(DOM_IDS.MODAL_PERSPECTIVE);
        DOMUtils.setText(DOM_IDS.SWITCH_BTN, `View: P${State.perspectivePlayer + 1}`);
        Network.fetchState();
    },
    leaveRoom: () => Network.leaveRoom(),
    joinRoom: (code) => Network.joinRoom(code),
    resetGame: () => Network.resetGame(),
    forceAdvance: () => Network.forceAction(-1),
    changeAI: (m) => Network.changeAI(m),
    forceAction: (id) => Network.forceAction(id),
    execCode: (c) => Network.execCode(c),
    startOffline: (u) => Network.startOffline(u)
};

// Modals
window.Modals = Modals;

// Attach top-level aliases for index.html compatibility
window.render = window.App.render;
window.fetchState = window.App.fetchState;
window.refreshTurnPlanner = window.App.refreshTurnPlanner;
window.scoreTurnPlanner = window.App.scoreTurnPlanner;
window.forceReset = window.App.forceReset;

window.sendAction = window.Actions.sendAction;
window.doAction = window.Actions.doAction;
window.toggleHotseat = window.Actions.toggleHotseat;
window.toggleLiveWatch = window.Actions.toggleLiveWatch;
window.togglePerspective = window.Actions.togglePerspective;
window.setPerspective = window.Actions.setPerspective;
window.leaveRoom = window.Actions.leaveRoom;
window.joinRoom = window.Actions.joinRoom;
window.resetGame = window.Actions.resetGame;
window.forceAdvance = window.Actions.forceAdvance;
window.changeAI = window.Actions.changeAI;
window.forceAction = window.Actions.forceAction;
window.execCode = window.Actions.execCode;
window.startOffline = window.Actions.startOffline;

window.openDeckModal = Modals.openDeckModal;
window.closeDeckModal = Modals.closeDeckModal;
window.submitDeck = Modals.submitDeck;
window.loadTestDeck = Modals.loadTestDeck;
window.loadRandomDeck = Modals.loadRandomDeck;
window.openSetupModal = Modals.openSetupModal;
window.closeSetupModal = Modals.closeSetupModal;
window.submitGameSetup = Modals.submitGameSetup;
window.onDeckSelectChange = Modals.onDeckSelectChange;
window.openSettingsModal = Modals.openSettingsModal;
window.closeSettingsModal = Modals.closeSettingsModal;
window.toggleLang = Modals.toggleLang;
window.toggleFriendlyAbilities = Modals.toggleFriendlyAbilities;
window.updateBoardScale = Modals.updateBoardScale;
window.openHelpModal = Modals.openHelpModal;
window.closeHelpModal = Modals.closeHelpModal;
window.openLobby = Modals.openLobby;
window.closeLobby = Modals.closeLobby;
window.openReportModal = Modals.openReportModal;
window.closeReportModal = Modals.closeReportModal;
window.submitReport = Modals.submitReport;
window.downloadReport = Modals.downloadReport;
window.showLastPerformance = Modals.showLastPerformance;
window.showPerformanceForTurn = Modals.showPerformanceForTurn;
window.closePerformanceModal = Modals.closePerformanceModal;
window.dismissPerformanceModal = Modals.closePerformanceModal;

// Replay System Actions
window.Replay = { ...Replay, loadReplay: Replay.loadReplay, toggleReplayMode: Replay.toggleReplayMode };
window.toggleReplayMode = Replay.toggleReplayMode;
window.loadReplay = Replay.loadReplay;
window.loadReplayFromFile = Replay.loadReplayFromFile;
window.openPasteReplayModal = Replay.openPasteReplayModal;
window.closePasteReplayModal = Replay.closePasteReplayModal;
window.submitPasteReplay = Replay.submitPasteReplay;
window.jumpToFrame = Replay.jumpToFrame;
window.replayPrev = Replay.replayPrev;
window.replayNext = Replay.replayNext;
window.replayPrevTurn = Replay.replayPrevTurn;
window.replayNextTurn = Replay.replayNextTurn;
window.replayPrevPhase = Replay.replayPrevPhase;
window.replayNextPhase = Replay.replayNextPhase;
window.togglePlay = Replay.togglePlay;
window.startReplay = Replay.loadReplay;
window.stopReplay = Replay.toggleReplayMode;

// Utility exports
window.State = State;
window.Network = Network;
window.Rendering = Rendering;
window.Tooltips = Tooltips;

console.log("Rabukasim modular main.js loaded and globals wired.");
