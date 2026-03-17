import { State } from './state.js';
import { Network } from './network.js';
import { DragDrop } from './ui_drag_drop.js';
import { Modals } from './ui_modals.js';
import { Rendering } from './ui_rendering.js';
import { Replay } from './replay_system.js';
import { toggleSidebar, switchBoard } from './layout.js';
import { loadTranslations } from './i18n/index.js';
import { DOMUtils } from './utils/DOMUtils.js';
import { ModalManager } from './utils/ModalManager.js';
import { DebugModal } from './modals/DebugModal.js';
import { LogViewerModal } from './modals/LogViewerModal.js';
import { DOM_IDS, COLORS, DISPLAY_VALUES } from './constants_dom.js';

const POLL_DELAYS = {
    idle: 1000,
    liveWatch: 500,
    thinking: 250,
    error: 2000,
    healthCheck: 10000,
};

let initialized = false;
let pollingTimeout = null;
let healthCheckInterval = null;
let heartbeat = 0;

const debugElements = {
    sync: null,
    room: null,
    session: null,
    view: null,
    poll: null,
    delay: null,
};

function initializeDebugElementCache() {
    if (debugElements.sync) {
        return;
    }

    debugElements.sync = DOMUtils.getElement(DOM_IDS.DEBUG_SYNC);
    debugElements.room = DOMUtils.getElement(DOM_IDS.DEBUG_ROOM);
    debugElements.session = DOMUtils.getElement(DOM_IDS.DEBUG_SESSION);
    debugElements.view = DOMUtils.getElement(DOM_IDS.DEBUG_VIEW);
    debugElements.poll = DOMUtils.getElement(DOM_IDS.DEBUG_POLL);
    debugElements.delay = DOMUtils.getElement(DOM_IDS.DEBUG_DELAY);
}

function getPollingMode() {
    if (State.offlineMode) {
        return 'OFFLINE';
    }
    if (State.replayMode) {
        return 'REPLAY';
    }
    return 'LIVE';
}

function getNextPollDelay() {
    if (State.replayMode || State.offlineMode || !State.roomCode) {
        return POLL_DELAYS.idle;
    }
    if (State.data?.is_ai_thinking) {
        return POLL_DELAYS.thinking;
    }
    if (State.isLiveWatchOn) {
        return POLL_DELAYS.liveWatch;
    }
    return POLL_DELAYS.idle;
}

function updateDebugOverlay() {
    initializeDebugElementCache();

    const isSynced = window.StateMaster === State;
    DOMUtils.updateText({
        [DOM_IDS.DEBUG_SYNC]: isSynced ? 'OK' : 'MISMATCH',
        [DOM_IDS.DEBUG_ROOM]: String(State.roomCode || 'NULL'),
        [DOM_IDS.DEBUG_SESSION]: State.sessionToken ? 'VALID' : 'MISSING',
        [DOM_IDS.DEBUG_VIEW]: `P${State.perspectivePlayer + 1}`,
        [DOM_IDS.DEBUG_POLL]: heartbeat,
        [DOM_IDS.DEBUG_DELAY]: getPollingMode(),
    });

    if (debugElements.sync) {
        debugElements.sync.style.color = isSynced ? '#00ff00' : COLORS.ACCENT_RED;
    }

    if (debugElements.delay) {
        debugElements.delay.style.color = (State.offlineMode || State.replayMode)
            ? COLORS.ACCENT_GOLD
            : '#00ff00';
    }
}

function schedulePoll(delay) {
    if (pollingTimeout) {
        clearTimeout(pollingTimeout);
    }
    pollingTimeout = window.setTimeout(AppController.pollOnce, delay);
}

function syncRoomDisplay() {
    DOMUtils.setText(DOM_IDS.ROOM_CODE_HEADER, State.roomCode || '---');
    DOMUtils.setVisible(DOM_IDS.ROOM_DISPLAY, Boolean(State.roomCode), DISPLAY_VALUES.FLEX);
}

function getPerspectivePlayerForOwner(owner) {
    return owner === 'opponent'
        ? 1 - State.perspectivePlayer
        : State.perspectivePlayer;
}

function clickTarget(targetId) {
    if (!targetId) {
        return;
    }

    document.getElementById(targetId)?.click();
}

const actionHandlers = {
    'toggle-sidebar': () => toggleSidebar(),
    'save-state': () => Modals.saveState(),
    'load-state': () => Modals.loadState(),
    rewind: () => Modals.rewind(),
    redo: () => Modals.redo(),
    'open-debug-modal': () => Modals.openDebugModal(),
    'open-report-modal': () => Modals.openReportModal(),
    'open-settings-modal': () => Modals.openSettingsModal(),
    'close-settings-modal': () => Modals.closeSettingsModal(),
    'leave-room': () => Network.leaveRoom(),
    'click-target': ({ targetId }) => clickTarget(targetId),
    'open-paste-replay-modal': () => Replay.openPasteReplayModal(),
    'close-paste-replay-modal': () => Replay.closePasteReplayModal(),
    'submit-paste-replay': () => Replay.submitPasteReplay(),
    'load-replay': () => Replay.loadReplay(),
    'replay-prev-turn': () => Replay.replayPrevTurn(),
    'replay-prev-phase': () => Replay.replayPrevPhase(),
    'replay-prev': () => Replay.replayPrev(),
    'toggle-play': () => Replay.togglePlay(),
    'replay-next': () => Replay.replayNext(),
    'replay-next-phase': () => Replay.replayNextPhase(),
    'replay-next-turn': () => Replay.replayNextTurn(),
    'switch-board': ({ value }) => switchBoard(value),
    'show-zone-viewer': ({ owner }) => Rendering.showZoneViewer(getPerspectivePlayerForOwner(owner)),
    'show-discard': ({ owner }) => Rendering.showDiscardModal(getPerspectivePlayerForOwner(owner)),
    'show-last-performance': () => Modals.showLastPerformance(),
    'close-performance-modal': () => Modals.closePerformanceModal(),
    'show-performance-tab': ({ value }) => Rendering.showPerfTab(value),
    'close-selection-modal': () => ModalManager.hide(DOM_IDS.SELECTION_MODAL),
    'close-report-modal': () => Modals.closeReportModal(),
    'download-report': () => Modals.downloadReport(),
    'submit-report': () => Modals.submitReport(),
    'open-help-modal': () => Modals.openHelpModal(),
    'close-help-modal': () => Modals.closeHelpModal(),
    'fetch-state': () => Network.fetchState(),
    'reset-game': () => Network.resetGame(),
    navigate: ({ href }) => {
        if (href) {
            window.location.href = href;
        }
    },
    'open-deck-modal': () => Modals.openDeckModal(),
    'close-deck-modal': () => Modals.closeDeckModal(),
    'submit-deck': () => Modals.submitDeck(),
    'load-test-deck': () => Modals.loadTestDeck(),
    'load-random-deck': () => Modals.loadRandomDeck(),
    'toggle-hotseat': () => window.Actions.toggleHotseat(),
    'toggle-perspective': () => window.Actions.togglePerspective(),
    'toggle-live-watch': () => window.Actions.toggleLiveWatch(),
    'toggle-friendly-abilities': () => Modals.toggleFriendlyAbilities(),
    'toggle-lang': () => Modals.toggleLang(),
    'toggle-replay-mode': () => Replay.toggleReplayMode(),
    'toggle-debug-mode': () => Modals.toggleDebugMode(),
    'close-setup-modal': () => Modals.closeSetupModal(),
    'submit-game-setup': () => Modals.submitGameSetup(),
    'open-setup-modal': ({ value }) => Modals.openSetupModal(value),
    'join-room': () => {
        const roomCode = document.getElementById('room-code-input')?.value || '';
        Network.joinRoom(roomCode);
    },
    'start-offline': () => Network.startOffline(),
    'force-reset': () => window.App.forceReset(),
    'set-perspective': ({ value }) => window.Actions.setPerspective(value),
    'close-log-viewer': () => LogViewerModal.close(),
    'open-log-viewer': ({ value, event }) => {
        event.stopPropagation();
        LogViewerModal.open(value);
    },
    'debug-rewind': () => DebugModal.rewind(),
    'debug-redo': () => DebugModal.redo(),
    'debug-render-all': () => DebugModal.renderAll(),
    'close-debug-modal': () => DebugModal.closeDebugModal(),
    'debug-switch-tab': ({ value }) => DebugModal.switchTab(value),
    'debug-copy-state-string': () => DebugModal.copyStateString(),
    'debug-load-state-string': () => DebugModal.loadStateString(),
    'debug-trigger-file-load': () => DebugModal.triggerFileLoad(),
    'debug-render-minimal-json': () => DebugModal.renderMinimalJSON(),
    'debug-render-checkpoint-json': () => DebugModal.renderCheckpointJSON(),
    'debug-render-rich-json': () => DebugModal.renderRichJSON(),
    'debug-copy-json-state': () => DebugModal.copyJsonState(),
    'debug-load-json-file': () => DebugModal.loadJsonFile(),
    'debug-apply-json-state': () => DebugModal.applyJsonState(),
    'debug-export-game': () => DebugModal.exportGameWithHistory(),
    'debug-import-game': () => DebugModal.importGameWithHistory(),
    'show-performance-turn': ({ value }) => Modals.showPerformanceForTurn(Number(value)),
    'close-discard-modal': () => ModalManager.hide(DOM_IDS.MODAL_DISCARD),
    'reload-page': () => window.location.reload(),
};

function handleDelegatedClick(event) {
    const button = event.target.closest('[data-action]');
    if (!button) {
        return;
    }

    const action = button.getAttribute('data-action');
    const id = button.getAttribute('data-id');
    const value = button.getAttribute('data-value');
    const owner = button.getAttribute('data-owner');
    const targetId = button.getAttribute('data-target-id');
    const href = button.getAttribute('data-href');

    if (action === 'send-action' && id) {
        window.sendAction(id);
        return;
    }

    if (action === 'close-modal') {
        const modal = button.closest('.modal') || button.closest('.modal-overlay');
        if (modal) {
            ModalManager.hideElement(modal);
        }
        return;
    }

    const handler = actionHandlers[action];
    if (handler) {
        handler({ button, event, id, value, owner, targetId, href });
    }
}

function installGlobalErrorHandler() {
    window.onerror = function (msg, url, line) {
        console.error('[CRITICAL] Global Error Caught:', msg, 'at', url, ':', line);
        const logEl = document.getElementById(DOM_IDS.CONTAINER_RULE_LOG);
        if (logEl) {
            const div = document.createElement('div');
            div.className = 'log-item error';
            div.innerHTML = `<span style="color:#ff5555;font-weight:bold;">[ERROR]</span> UI Crash: ${msg}`;
            logEl.prepend(div);
        }
        return false;
    };
}

function wireStateListeners() {
    const syncRoomState = () => syncRoomDisplay();
    State.on('roomUpdate', syncRoomState);
    State.on('room-change', syncRoomState);
}

function openDeckModalForPlayer(playerIdx) {
    try {
        if (playerIdx === undefined || playerIdx === null) {
            Modals.openDeckModal();
            return;
        }

        if (State.perspectivePlayer === undefined || State.perspectivePlayer === null) {
            console.log('[Init] Deck modal requested but perspective unknown; skipping.');
            return;
        }

        if (playerIdx === State.perspectivePlayer) {
            Modals.openDeckModal();
            return;
        }

        console.log(`[Init] Deck modal requested for P${playerIdx + 1}, not current perspective P${State.perspectivePlayer + 1}; ignoring.`);
    } catch (error) {
        console.error('Error handling openDeckModal callback', error);
    }
}

export const AppController = {
    async initialize() {
        if (initialized) {
            return;
        }

        initialized = true;
        installGlobalErrorHandler();

        await loadTranslations(State.currentLang);

        AppController.restartPolling();
        wireStateListeners();
        document.addEventListener('click', handleDelegatedClick);

        window.onRoomUpdate = () => {
            syncRoomDisplay();
            Network.triggerRoomUpdate();
        };
        Network.onOpenDeckModal = openDeckModalForPlayer;

        Modals.updateLanguage();
        syncRoomDisplay();

        await Network.checkSystemStatus();
        await Network.fetchState();

        DragDrop.init();

        if (!healthCheckInterval) {
            healthCheckInterval = window.setInterval(() => Network.checkSystemStatus(), POLL_DELAYS.healthCheck);
        }

        const savedScale = localStorage.getItem('lovelive_board_scale');
        if (savedScale) {
            Modals.updateBoardScale(savedScale);
        }

        if (!State.roomCode && !State.offlineMode && !State.replayMode) {
            ModalManager.show(DOM_IDS.MODAL_ROOM);
        }
    },

    restartPolling() {
        heartbeat = 0;
        schedulePoll(0);
    },

    async pollOnce() {
        heartbeat += 1;

        try {
            updateDebugOverlay();
            console.log(`[Poll#${heartbeat}] room="${State.roomCode}" | offline=${State.offlineMode} | replay=${State.replayMode} | sync=${window.StateMaster === State}`);

            if (!State.replayMode && !State.offlineMode && State.roomCode) {
                await Network.fetchState();
            }

            schedulePoll(getNextPollDelay());
        } catch (error) {
            console.error('[Polling] Critical Error in Loop:', error);
            schedulePoll(POLL_DELAYS.error);
        }
    },
};