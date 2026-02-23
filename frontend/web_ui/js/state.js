/**
 * Central State Management
 * Holds the current game state, configuration, and connectivity flags.
 */

// We use a mutable object to share state across modules
const stateInternal = {
    // Core Game Data (from backend)
    data: null, // The "state" object from JSON

    // Identity & Session
    roomCode: localStorage.getItem('lovelive_room_code'),
    sessionToken: null,
    perspectivePlayer: 0, // 0 or 1 (Who are we viewing?)

    // Connectivity & Mode
    offlineMode: false,
    wasmAdapter: null,
    hotseatMode: false,
    replayMode: false,
    isLiveWatchOn: false,


    // Replay Data
    replayData: null,
    currentFrame: 0,
    playInterval: null,

    // UI Cache & Optimization
    lastStateJson: null,
    lastPerformanceData: null,
    lastAssetsHash: null,

    // Card ID Index for O(1) lookups (performance optimization)
    cardIndex: null,
    lastIndexedStateId: null,

    // Config
    currentLang: 'jp',
    showFriendlyAbilities: localStorage.getItem('lovelive_friendly_abilities') !== 'false',

    // UI State & Cache
    selectedTurn: -1, // Log selection (-1 means all)
    selectedHandIdx: -1,
    selectedPerfTurn: -1, // Performance result selection (-1 means latest)
    showingFullLog: false,
    lastPerformanceTurn: -1,
    fullLogData: null,
    lastActionsHash: null,
    lastShownPerformanceHash: null,
    performanceHistory: {}, // Stores results by turn number
    performanceHistoryTurns: [], // Sorted list of turns with performance results

    // Error Tracking
    capturedErrors: [],

    // State management helpers
    update: (newData) => {
        if (!newData) {
            State.data = null;
            State.cardIndex = null;
            return;
        }
        State.data = { ...State.data, ...newData };
        // Rebuild card index when state updates
        State.rebuildCardIndex();
    },

    /**
     * Rebuilds the card ID index for O(1) lookups.
     * Called automatically on state update.
     */
    rebuildCardIndex: () => {
        const state = State.data;
        if (!state || !state.players) {
            State.cardIndex = null;
            return;
        }

        const index = {};

        state.players.forEach((p, playerIdx) => {
            if (!p) return;

            // Helper to add cards to index
            const addCard = (card, zone) => {
                if (card && card.id !== undefined && card.id >= 0) {
                    // Store first occurrence (or update with more complete data)
                    if (!index[card.id] || (card.name && !index[card.id].name)) {
                        index[card.id] = card;
                    }
                }
            };

            // Index all zones
            if (p.hand) p.hand.forEach(c => addCard(c, 'hand'));
            if (p.stage) p.stage.forEach(c => addCard(c, 'stage'));
            if (p.live_zone) p.live_zone.forEach(c => addCard(c, 'live_zone'));
            if (p.energy) p.energy.forEach(e => { if (e && e.card) addCard(e.card, 'energy'); });
            if (p.discard) p.discard.forEach(c => addCard(c, 'discard'));
            if (p.waiting_room) p.waiting_room.forEach(c => addCard(c, 'waiting_room'));
            if (p.success_lives) p.success_lives.forEach(c => addCard(c, 'success_lives'));
            if (p.success_pile) p.success_pile.forEach(c => addCard(c, 'success_pile'));
        });

        // Also index looked_cards
        if (state.looked_cards) {
            state.looked_cards.forEach(c => {
                if (c && c.id !== undefined && c.id >= 0) {
                    index[c.id] = c;
                }
            });
        }

        State.cardIndex = index;
    },

    resolveCardData: (cid) => {
        if (cid === null || cid === undefined || cid < 0) return null;

        // O(1) lookup using card index
        if (State.cardIndex && State.cardIndex[cid]) {
            return State.cardIndex[cid];
        }

        // Fallback: return placeholder
        return { id: cid, name: `Card ${cid}`, img: 'icon_blade.png', text: "", original_text: "" };
    },

    resolveCardDataByName: (name) => {
        const state = State.data;
        if (!state) return null;

        // Use card index if available
        if (State.cardIndex) {
            for (const card of Object.values(State.cardIndex)) {
                if (card && card.name === name) return card;
            }
        }

        // Fallback to linear search
        for (const p of state.players) {
            if (!p) continue;
            const allZones = [(p.hand || []), (p.stage || []), (p.live_zone || []), (p.energy || []), (p.discard || []), (p.success_lives || p.success_zone || [])];
            for (const zone of allZones) {
                for (const c of zone) {
                    const card = (typeof c === 'object' && c !== null) ? (c.card || c) : null;
                    if (card && card.name === name) return card;
                }
            }
        }
        if (state.looked_cards) {
            const found = state.looked_cards.find(c => c.name === name);
            if (found) return found;
        }
        return null;
    }
};

// Singleton Logic: Ensure all modules share the EXACT same object instance
if (typeof window !== 'undefined') {
    if (!window.StateMaster) {
        window.StateMaster = stateInternal;
    } else {
        // console.warn("[State] Module mismatch potential avoided. Using global StateMaster.");
    }
}

export const State = typeof window !== 'undefined' ? window.StateMaster : stateInternal;

export function updateStateData(newData) {
    State.update(newData);
}
// Global error handler setup (moved here or kept in main, but state tracks errors)
if (typeof window !== 'undefined') {
    window.capturedErrors = State.capturedErrors;
}
