/**
 * Frontend API Integration Mock Test
 * Simulates a headless browser environment to verify that JS modules handle API responses correctly.
 */
const fs = require('fs');
const path = require('path');

console.log("--- Frontend API Integration Test (Headless) ---");

// 1. Mock the DOM Environment
global.window = {
    location: { pathname: '/index.html' },
    onload: null
};
global.document = {
    getElementById: (id) => ({
        style: {},
        appendChild: () => { },
        querySelector: () => ({ appendChild: () => { } }),
        dataset: {},
        innerHTML: '',
        value: ''
    }),
    querySelectorAll: () => [],
    body: {
        addEventListener: () => { },
        classList: { add: () => { }, remove: () => { } }
    },
    createElement: () => ({
        style: {},
        appendChild: () => { },
        classList: { add: () => { }, remove: () => { } },
        getBoundingClientRect: () => ({ top: 0, right: 0 }),
        addEventListener: () => { }
    })
};
global.localStorage = {
    getItem: () => null,
    setItem: () => { },
    removeItem: () => { }
};
global.sessionStorage = {
    getItem: () => null,
    setItem: () => { },
    removeItem: () => { }
};
global.navigator = { language: 'en' };
global.history = { pushState: () => { } };
global.alert = (msg) => console.log("[MOCK ALERT]", msg);
global.confirm = () => true;

// 2. Mock Fetch API
let mockFetchResponse = { success: true, decks: [{ id: 'test_deck', name: 'Test', card_count: 30 }] };

global.fetch = async (url, options) => {
    console.log(`[MOCK FETCH] ${url}`);
    return {
        ok: true,
        status: 200,
        json: async () => mockFetchResponse,
        text: async () => JSON.stringify(mockFetchResponse)
    };
};

// 3. Load Modules (using CJS require simulation or dynamic import if node permits)
// Since the files use ESM 'import', we either need --experimental-modules or a simple regex hack for this specific test
function loadModule(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    // Strip imports/exports for simple execution in Node
    content = content.replace(/import\s+.*?;/g, '');
    content = content.replace(/export\s+const\s+(\w+)\s*=/g, 'global.$1 =');
    content = content.replace(/export\s+function\s+(\w+)/g, 'global.$1 = function');

    // Evaluate in global context
    try {
        eval(content);
        console.log(`[LOADED] ${path.basename(filePath)}`);
    } catch (e) {
        console.error(`[ERROR] Failed to load ${path.basename(filePath)}:`, e.message);
        process.exit(1);
    }
}

const JS_DIR = path.resolve(__dirname, '../frontend/web_ui/js');
loadModule(path.join(JS_DIR, 'state.js'));
loadModule(path.join(JS_DIR, 'network.js'));
loadModule(path.join(JS_DIR, 'ui_modals.js'));

// 4. Run Test Flow
async function runTest() {
    console.log("\nStarting Test Scenario: Game Setup Flow");

    try {
        // Step A: Fetch Decks
        console.log("1. Simulating Modals.fetchAndPopulateDecks()");
        await global.Modals.fetchAndPopulateDecks();

        if (global.Modals.deckPresets && global.Modals.deckPresets.length > 0) {
            console.log("[PASS] deckPresets populated correctly.");
        } else {
            throw new Error("deckPresets is empty or undefined after fetch.");
        }

        // Step B: Open Setup Modal
        console.log("2. Simulating Modals.openSetupModal('pve')");
        global.Modals.openSetupModal('pve');
        console.log("[PASS] openSetupModal executed without crash.");

        // Step C: Submit Setup
        console.log("3. Simulating Modals.submitGameSetup()");
        // Mocking getDeckConfig to return a valid preset config
        global.Modals.getDeckConfig = (pid) => ({ type: 'preset', id: 'test_deck', preset: global.Modals.deckPresets[0] });

        await global.Modals.submitGameSetup();
        console.log("[PASS] submitGameSetup executed without crash.");

        console.log("\n--- [ALL TESTS PASSED] ---");
        process.exit(0);

    } catch (e) {
        console.error("\n--- [TEST FAILED] ---");
        console.error(e.stack);
        process.exit(1);
    }
}

runTest();
