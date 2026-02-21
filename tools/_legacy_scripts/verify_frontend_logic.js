/**
 * Frontend Logic Verification Script (Headless)
 * Verifies that the modular JS files export the expected functions and variables.
 */
const fs = require('fs');
const path = require('path');

const JS_DIR = path.resolve(__dirname, '../frontend/web_ui/js');

const filesToVerify = [
    {
        name: 'ui_modals.js',
        expectedExports: ['Modals'],
        expectedInObject: { 'Modals': ['openSetupModal', 'onDeckSelectChange', 'submitGameSetup'] }
    },
    {
        name: 'ui_rendering.js',
        expectedExports: ['Rendering'],
        expectedInObject: { 'Rendering': ['render', 'renderActiveAbilities'] }
    },
    {
        name: 'ui_tooltips.js',
        expectedExports: ['Tooltips'],
        expectedInObject: { 'Tooltips': ['enrichAbilityText', 'getEffectiveAbilityText'] }
    },
    {
        name: 'network.js',
        expectedExports: ['Network'],
        expectedInObject: { 'Network': ['fetchState', 'sendAction'] }
    },
    {
        name: 'state.js',
        expectedExports: ['State', 'updateStateData']
    }
];

console.log("--- Frontend Logic Verification (Robust) ---");

let totalIssues = 0;

filesToVerify.forEach(file => {
    const filePath = path.join(JS_DIR, file.name);
    if (!fs.existsSync(filePath)) {
        console.error(`[FAIL] File missing: ${file.name}`);
        totalIssues++;
        return;
    }

    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n').filter(l => !l.trim().startsWith('//') && !l.trim().startsWith('*')); // Basic comment filtering
    const cleanContent = lines.join('\n');

    // Check for exports
    file.expectedExports.forEach(exp => {
        const regex = new RegExp(`export\\s+(const|let|var|function)\\s+${exp}`);
        if (!regex.test(cleanContent)) {
            console.error(`[FAIL] ${file.name}: Missing export '${exp}'`);
            totalIssues++;
        }
    });

    // Check for specific functions inside objects
    if (file.expectedInObject) {
        for (const [obj, fns] of Object.entries(file.expectedInObject)) {
            fns.forEach(fn => {
                // Look for fn: or fn( or fn = 
                const regex = new RegExp(`${fn}\\s*[:(=]`);
                if (!regex.test(cleanContent)) {
                    console.error(`[FAIL] ${file.name}: Missing function '${fn}' in ${obj}`);
                    totalIssues++;
                }
            });
        }
    }
});

// Verify main.js global mapping
const mainPath = path.join(JS_DIR, 'main.js');
if (fs.existsSync(mainPath)) {
    const mainContent = fs.readFileSync(mainPath, 'utf8');
    const mainLines = mainContent.split('\n').filter(l => !l.trim().startsWith('//'));
    const cleanMain = mainLines.join('\n');

    const requiredGlobals = [
        /window\.openGameSetup\s*=\s*(Modals\.)?openSetupModal/,
        /window\.render\s*=\s*(Rendering\.)?render/,
        /window\.fetchState\s*=\s*(Network\.)?fetchState/
    ];

    requiredGlobals.forEach(regex => {
        if (!regex.test(cleanMain)) {
            console.error(`[FAIL] main.js: Missing global mapping for ${regex}`);
            totalIssues++;
        }
    });

    // Check for residual calls that should be gone
    // We want to make sure it's NOT there and NOT commented out in a way that looks active
    if (/^\s*Tooltips\.init\(\)/m.test(cleanMain)) {
        console.error(`[FAIL] main.js: Still contains active Tooltips.init() call`);
        totalIssues++;
    }
}

if (totalIssues === 0) {
    console.log("[SUCCESS] Frontend module structure verified!");
    process.exit(0);
} else {
    console.error(`[FAILURE] ${totalIssues} structural issues found.`);
    process.exit(1);
}
