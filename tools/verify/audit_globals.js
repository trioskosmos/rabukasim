
const fs = require('fs');
const path = require('path');

const htmlPath = 'c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/frontend/web_ui/index.html';
const mainJsPath = 'c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/frontend/web_ui/js/main.js';
const uiModalsJsPath = 'c:/Users/trios/.gemini/antigravity/vscode/loveca-copy/frontend/web_ui/js/ui_modals.js';

function extractHtmlCalls(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const regex = /onclick="([^"(]+)\(/g;
    const calls = new Set();
    let match;
    while ((match = regex.exec(content)) !== null) {
        calls.add(match[1]);
    }
    return calls;
}

function extractExports(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');

    // Check for 'window.funcName =' assignments
    const assignments = [];
    const windowRegex = /window\.(\w+)\s*=/g;
    let match;
    while ((match = windowRegex.exec(content)) !== null) {
        assignments.push(match[1]);
    }
    return new Set(assignments);
}

// Manual Check for re-exports in main.js
const htmlCalls = extractHtmlCalls(htmlPath);
const mainExports = extractExports(mainJsPath);

console.log("HTML requires:", Array.from(htmlCalls));
console.log("Main.js exports:", Array.from(mainExports));

console.log("\n--- Mismatches ---");
const missing = [];
for (const call of htmlCalls) {
    if (!mainExports.has(call)) {
        missing.push(call);
        console.log(`MISSING: ${call}`);
    }
}

if (missing.length === 0) {
    console.log("All HTML calls are satisfied!");
}

