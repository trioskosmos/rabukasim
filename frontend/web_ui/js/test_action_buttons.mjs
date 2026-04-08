globalThis.localStorage = globalThis.localStorage || {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
    clear: () => {},
};
globalThis.window = globalThis.window || globalThis;
globalThis.window.addEventListener = globalThis.window.addEventListener || (() => {});
globalThis.window.removeEventListener = globalThis.window.removeEventListener || (() => {});
globalThis.window.location = globalThis.window.location || {
    hostname: 'localhost',
    protocol: 'http:',
    pathname: '/',
    port: '',
};
globalThis.document = globalThis.document || {
    getElementById: () => null,
    querySelectorAll: () => [],
    addEventListener: () => {},
    body: {
        addEventListener: () => {},
    },
};

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(`${message}\nExpected: ${expected}\nActual:   ${actual}`);
    }
}

const { ActionButtons } = await import('./components/ActionButtons.js');
const { Phase } = await import('./constants.js');
const { State } = await import('./state.js');

State.currentLang = 'en';

function run() {
    const state = {
        pending_choice: { choice_type: 1 },
        phase: Phase.RESPONSE,
    };

    const label = ActionButtons.getActionLabel(
        {
            id: 0,
            name: 'No / Skip',
            metadata: { name: 'No / Skip' },
        },
        false,
        state,
    );

    assertEqual(label, 'No / Skip', 'pending-choice action 0 should preserve the backend skip label');
    console.log('ActionButtons skip-label regression passed');
}

run();
