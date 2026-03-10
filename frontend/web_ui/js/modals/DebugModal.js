import { State } from '../state.js';
import { fixImg } from '../constants.js';
import { Network } from '../network.js';

// Metadata Constants for Debug Display (mirrors data/metadata.json)
const DEBUG_CONSTANTS = {
    // Ability Effect Flags
    FLAG_DRAW: 1,
    FLAG_SEARCH: 2,
    FLAG_RECOVER: 4,
    FLAG_BUFF: 8,
    FLAG_CHARGE: 16,
    FLAG_TEMPO: 32,
    FLAG_REDUCE: 64,
    FLAG_BOOST: 128,
    FLAG_TRANSFORM: 256,
    FLAG_WIN_COND: 512,
    FLAG_MOVE: 1024,
    FLAG_TAP: 2048,
    // Cost Flags
    COST_FLAG_DISCARD: 1,
    COST_FLAG_TAP: 2,
    // Choice Flags
    CHOICE_FLAG_LOOK: 1,
    CHOICE_FLAG_DISCARD: 2,
    CHOICE_FLAG_MODE: 4,
    CHOICE_FLAG_COLOR: 8,
    CHOICE_FLAG_ORDER: 16,
    // Synergy Flags
    SYN_FLAG_GROUP: 1,
    SYN_FLAG_COLOR: 2,
    SYN_FLAG_BATON: 4,
    SYN_FLAG_CENTER: 8,
    SYN_FLAG_LIFE_LEAD: 16,
    // Filter Flags (partial)
    FILTER_TYPE_MEMBER: 4,
    FILTER_TYPE_LIVE: 8,
    FILTER_GROUP_ENABLE: 16,
    FILTER_TAPPED: 4096,
    FILTER_HAS_BLADE_HEART: 8192,
    FILTER_NOT_HAS_BLADE_HEART: 16384,
    FILTER_UNIQUE_NAMES: 32768,
    FILTER_UNIT_ENABLE: 65536,
    // Area Constants
    AREA_LEFT: 1,
    AREA_CENTER: 2,
    AREA_RIGHT: 3,
    // Zones
    ZONE_MASK_STAGE: 4,
    ZONE_MASK_HAND: 6,
    ZONE_MASK_DISCARD: 7,
};

export const DebugModal = {
    init: () => { },

    openDebugModal: () => {
        const modal = document.getElementById('debug-modal');
        if (modal) {
            modal.style.display = 'flex';
            if (!State.data) {
                const containers = ['debug-flags-content', 'debug-bytecode-content', 'debug-json-content'];
                containers.forEach(id => {
                    const el = document.getElementById(id);
                    if (el) {
                        if (el.tagName === 'TEXTAREA') el.value = 'Loading state...';
                        else el.innerHTML = '<div class="debug-loading">Waiting for game state...</div>';
                    }
                });
                return;
            }
            DebugModal.renderAll();
        }
    },

    closeDebugModal: () => {
        const modal = document.getElementById('debug-modal');
        if (modal) modal.style.display = 'none';
    },

    switchTab: (tabId) => {
        const contents = document.querySelectorAll('.debug-tab-content');
        contents.forEach(c => { c.style.display = 'none'; });

        const selected = document.getElementById(`debug-${tabId}-tab`);
        if (selected) {
            selected.style.display = tabId === 'json' ? 'flex' : 'block';
        }

        const buttons = document.querySelectorAll('.debug-tab-btn');
        buttons.forEach(b => {
            if (b.getAttribute('onclick')?.includes(`'${tabId}'`)) {
                b.classList.add('active');
                b.style.borderBottom = '2px solid var(--accent-blue)';
                b.style.color = '#fff';
            } else {
                b.classList.remove('active');
                b.style.borderBottom = '2px solid transparent';
                b.style.color = 'var(--text-dim)';
            }
        });

        if (tabId === 'json') DebugModal.renderJson();
        if (tabId === 'string') DebugModal.renderStringTab();
        if (tabId === 'bytecode') DebugModal.renderBytecode();
    },

    renderAll: async () => {
        if (State.roomCode) { await Network.fetchState(); }
        if (!State.data) return;
        try { DebugModal.renderFlags(); } catch (e) { console.error("Debug Flags Render Fail:", e); }
        try { DebugModal.renderBytecode(); } catch (e) { console.error("Debug Bytecode Error:", e); }
        try { DebugModal.renderJson(); } catch (e) { console.error("Debug JSON Error:", e); }
        try { DebugModal.renderStringTab(); } catch (e) { console.error("Debug String Error:", e); }
    },

    renderStringTab: () => {
        const container = document.getElementById('debug-string-content');
        if (!container || !State.data) return;

        // Generate current state string
        let blob = "";
        try {
            // Strip rich objects away before serializing
            const source = State.stripRichData(State.data);
            blob = btoa(unescape(encodeURIComponent(JSON.stringify(source))));
        } catch (e) {
            blob = "Error generating blob: " + e.message;
        }

        container.innerHTML = `
            <div style="display: flex; flex-direction: column; height: 100%; padding: 10px; gap: 10px;">
                <p style="margin: 0; opacity: 0.8; font-size: 12px; line-height: 1.4;">
                    Game State Sequence (Base64). Paste a sequence here and click <b>Load</b> to warp the board.
                </p>
                <textarea id="debug-string-textarea"
                    style="flex: 1; background: #1a1a1a; color: #00ff00; border: 1px solid #333; border-radius: 4px; padding: 10px; font-family: monospace; font-size: 11px; resize: none; min-height: 200px;"
                    spellcheck="false">${blob}</textarea>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-primary" style="flex: 1; min-width: 150px;" onclick="DebugModal.copyStateString()">Copy to Clipboard (Base64)</button>
                    <button class="btn btn-secondary" style="flex: 1; min-width: 150px;" onclick="DebugModal.loadStateString()">Load from Textarea</button>
                    <button class="btn btn-accent" style="flex: 1; min-width: 150px; background: var(--accent-gold); color: #000;" onclick="DebugModal.triggerFileLoad()">Load JSON File</button>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                    <button class="btn" style="flex: 1; background: #9b59b6; color: #fff; border: none;" onclick="DebugModal.copyStandardizedJson()">Copy Standardized JSON (Master)</button>
                    <button class="btn" style="flex: 1; background: #2c3e50; color: #fff; border: none;" onclick="DebugModal.saveStandardizedJson()">Save Standardized JSON (Master)</button>
                    <input type="file" id="debug-state-file-input" style="display: none;" accept=".json" onchange="DebugModal.loadStateFile(this)">
                </div>
            </div>
        `;
    },

    triggerFileLoad: () => {
        const input = document.getElementById('debug-state-file-input');
        if (input) input.click();
    },

    loadStateFile: (input) => {
        if (!input.files || !input.files[0]) return;
        const file = input.files[0];
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const json = JSON.parse(e.target.result);
                // Strip if it's rich data
                const source = State.stripRichData(json);
                const ok = await Network.applyState(JSON.stringify(source));
                if (ok) {
                    alert("State Loaded from File and Applied.");
                    DebugModal.renderAll();
                } else {
                    alert("Apply failed — check server console.");
                }
            } catch (err) {
                alert("File Read/Parse Error: " + err.message);
            }
            // Reset input so the same file can be picked again
            input.value = "";
        };
        reader.readAsText(file);
    },

    _flag: (label, val, color = '#ccc') => {
        if (val === undefined || val === null) return '';
        const display = typeof val === 'boolean' ? (val ? 'YES' : 'NO') : val;
        const c = (typeof val === 'boolean' && val) ? '#e74c3c' : (typeof val === 'boolean' ? '#2ecc71' : color);
        return `<div style="font-size:11px;"><span style="opacity:0.5;">${label}:</span> <span style="color:${c}">${display}</span></div>`;
    },

    _renderLogicList: (title, items, color) => {
        if (!items || items.length === 0) return '';
        return `
            <div style="margin-top:5px; border-left: 2px solid ${color}; padding-left: 8px;">
                <div style="font-size: 9px; opacity: 0.5; text-transform: uppercase;">${title}</div>
                ${items.map(item => {
            const typeName = item.condition_type || item.effect_type || item.cost_type || item.type || 'Unknown';
            return `
                    <div style="font-size: 10px; margin-bottom: 2px;">
                        <span style="color:${color}">${typeName}:</span>
                        ${item.value !== undefined ? `v=${item.value}` : ''}
                        ${item.attr !== undefined ? `a=0x${Number(item.attr).toString(16)}` : ''}
                        ${item.target !== undefined ? `t=${item.target}` : ''}
                        ${item.is_negated ? '<span style="color:#e74c3c">[NEG]</span>' : ''}
                        ${item.is_optional ? '<span style="color:#3498db">[OPT]</span>' : ''}
                    </div>`;
        }).join('')}
            </div>
        `;
    },

    _renderCardDiag: (c, slotLabel) => {
        if (!c || c === -1 || c.id === -1 || c.id === -2) {
            return `<div style="font-size:11px; opacity:0.3; padding:8px; border:1px dashed #444; border-radius:4px; text-align:center;">EMPTY (${slotLabel})</div>`;
        }
        const flags = [];
        if (c.tapped) flags.push('<span style="color:#e74c3c">TAPPED</span>');
        if (c.moved) flags.push('<span style="color:#3498db">MOVED</span>');
        if (c.revealed) flags.push('<span style="color:#2ecc71">REVEALED</span>');

        const type = c.type || (c.score !== undefined ? 'live' : 'member');
        const isLive = type === 'live';

        return `
            <div style="font-size:11px; background: rgba(255,255,255,0.03); padding: 10px; border: 1px solid #444; border-radius: 4px; display:flex; flex-direction:column; gap:6px;">
                <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:4px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <strong style="color:${isLive ? '#e74c3c' : 'var(--accent-blue)'}; font-size:12px;">${c.name}</strong>
                        <span style="opacity:0.5; font-size:10px;">[${slotLabel}]</span>
                        <span style="opacity:0.4; font-size:9px; background:rgba(255,255,255,0.1); padding:0 4px; border-radius:3px;">${type.toUpperCase()}</span>
                    </div>
                    <span style="opacity:0.5; font-family:monospace; font-size:10px;">ID ${c.id}</span>
                </div>

                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap:6px; background: rgba(0,0,0,0.2); padding:4px 6px; border-radius:4px; font-size:10px;">
                    ${isLive ? `<span><strong>Score:</strong> ${c.score ?? 0}</span>` : `<span><strong>Cost:</strong> ${c.cost ?? 0}</span>`}
                    ${isLive ? `<span><strong>Req:</strong> ${JSON.stringify(c.required_hearts || [])}</span>` : `<span><strong>Hearts:</strong> ${JSON.stringify(c.hearts || [])}</span>`}
                    ${!isLive ? `<span><strong>Blades:</strong> ${c.blades ?? 0}</span>` : ''}
                    <span><strong>Vol:</strong> ${c.note_icons ?? 0}</span>
                </div>

                <div style="display:flex; flex-wrap:wrap; gap:8px; font-size:9px;">
                    <div title="Semantic Flags">Sem: <span style="color:#3498db">0x${(c.semantic_flags || 0).toString(16)}</span></div>
                    ${!isLive ? `<div title="Ability Flags">Ab: <span style="color:#2ecc71">0x${(c.ability_flags || 0).toString(16)}</span></div>` : ''}
                    <div title="Synergy Flags">Syn: <span style="color:#f1c40f">0x${(c.synergy_flags || 0).toString(16)}</span></div>
                    ${!isLive ? `<div title="Cost Flags">CostF: <span style="color:#9b59b6">0x${(c.cost_flags || 0).toString(16)}</span></div>` : ''}
                </div>

                ${flags.length ? `<div style="display:flex; flex-wrap:wrap; gap:4px; font-size:9px; font-weight:bold;">${flags.join(' ')}</div>` : ''}

                <div class="debug-abilities" style="margin-top:4px; border-top:1px solid rgba(255,255,255,0.05); padding-top:6px; display:flex; flex-direction:column; gap:10px;">
                    ${(c.abilities || []).map((ab, ai) => `
                        <div style="background: rgba(255,255,255,0.02); padding:6px; border-radius:4px; border: 1px solid rgba(255,255,255,0.05);">
                            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                                <div style="color:#f1c40f; font-size:10px; font-weight:bold;">Ab#${ai + 1} [${ab.trigger}]</div>
                                <div style="display:flex; gap:4px;">
                                    ${ab.is_once_per_turn ? '<span style="font-size:8px; color:#e67e22; border:1px solid #e67e22; padding:0 3px; border-radius:3px;">1/TURN</span>' : ''}
                                    ${ab.requires_selection ? '<span style="font-size:8px; color:#9b59b6; border:1px solid #9b59b6; padding:0 3px; border-radius:3px;">CHOICE</span>' : ''}
                                    ${ab.choice_count > 0 ? `<span style="font-size:8px; color:#3498db; border:1px solid #3498db; padding:0 3px; border-radius:3px;">x${ab.choice_count}</span>` : ''}
                                </div>
                            </div>
                            <div style="opacity:0.8; font-style:italic; margin-bottom:6px; font-size:10px; border-bottom: 1px dashed rgba(255,255,255,0.1); padding-bottom:4px;">"${ab.pseudocode || 'No pseudocode'}"</div>

                            ${DebugModal._renderLogicList('Conditions', ab.conditions, '#3498db')}
                            ${DebugModal._renderLogicList('Costs', ab.costs, '#e67e22')}
                            ${DebugModal._renderLogicList('Effects', ab.effects, '#2ecc71')}

                            ${(ab.decoded_bytecode && ab.decoded_bytecode.length > 0) ? `
                            <details style="margin-top:4px;">
                                <summary style="cursor:pointer; opacity:0.5; font-size:9px; padding:2px; background:rgba(255,255,255,0.05); border-radius:3px;">Decoded Bytecode (${ab.decoded_bytecode.length})</summary>
                                <pre style="font-size:9px; background:#000; padding:6px; border-radius:4px; margin:4px 0; max-height:150px; overflow-y:auto; color:#0f0; font-family: 'Cascadia Code', monospace; line-height:1.2;">${ab.decoded_bytecode.join('\n')}</pre>
                            </details>` : ''}

                            ${(ab.bytecode && ab.bytecode.length > 0) ? `
                            <details style="margin-top:2px;">
                                <summary style="cursor:pointer; opacity:0.4; font-size:8px; padding:1px 2px; background:rgba(255,255,255,0.03); border-radius:3px;">Raw Bytecode (${ab.bytecode.length} words)</summary>
                                <pre style="font-size:8px; background:#000; padding:4px; border-radius:4px; margin:2px 0; max-height:80px; overflow-y:auto; color:#888; font-family:monospace;">${ab.bytecode.join(', ')}</pre>
                            </details>` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    },

    // Render constants reference section
    _renderConstantsRef: () => {
        const C = DEBUG_CONSTANTS;
        return `
            <details style="margin-top:8px;">
                <summary style="cursor:pointer; font-size:10px; font-weight:bold; text-transform:uppercase; opacity:0.6; letter-spacing:1px;">Constants Reference</summary>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-top:4px; font-size:9px;">
                    <div style="grid-column: span 4; font-weight:bold; color:#f1c40f; border-bottom:1px solid #444; margin-bottom:4px;">Ability Flags</div>
                    ${Object.entries({ FLAG_DRAW: 1, FLAG_SEARCH: 2, FLAG_RECOVER: 4, FLAG_BUFF: 8, FLAG_CHARGE: 16, FLAG_TEMPO: 32, FLAG_REDUCE: 64, FLAG_BOOST: 128, FLAG_TRANSFORM: 256, FLAG_WIN_COND: 512, FLAG_MOVE: 1024, FLAG_TAP: 2048 }).map(([k, v]) => `<span>${k}:${v}</span>`).join('')}
                    <div style="grid-column: span 4; font-weight:bold; color:#e67e22; border-bottom:1px solid #444; margin-bottom:4px; margin-top:4px;">Cost Flags</div>
                    ${Object.entries({ COST_FLAG_DISCARD: 1, COST_FLAG_TAP: 2 }).map(([k, v]) => `<span>${k}:${v}</span>`).join('')}
                    <div style="grid-column: span 4; font-weight:bold; color:#3498db; border-bottom:1px solid #444; margin-bottom:4px; margin-top:4px;">Choice Flags</div>
                    ${Object.entries({ CHOICE_FLAG_LOOK: 1, CHOICE_FLAG_DISCARD: 2, CHOICE_FLAG_MODE: 4, CHOICE_FLAG_COLOR: 8, CHOICE_FLAG_ORDER: 16 }).map(([k, v]) => `<span>${k}:${v}</span>`).join('')}
                    <div style="grid-column: span 4; font-weight:bold; color:#9b59b6; border-bottom:1px solid #444; margin-bottom:4px; margin-top:4px;">Synergy Flags</div>
                    ${Object.entries({ SYN_FLAG_GROUP: 1, SYN_FLAG_COLOR: 2, SYN_FLAG_BATON: 4, SYN_FLAG_CENTER: 8, SYN_FLAG_LIFE_LEAD: 16 }).map(([k, v]) => `<span>${k}:${v}</span>`).join('')}
                    <div style="grid-column: span 4; font-weight:bold; color:#2ecc71; border-bottom:1px solid #444; margin-bottom:4px; margin-top:4px;">Filter Flags</div>
                    ${Object.entries({ FILTER_TYPE_MEMBER: 4, FILTER_TYPE_LIVE: 8, FILTER_GROUP_ENABLE: 16, FILTER_TAPPED: 4096, FILTER_HAS_BLADE_HEART: 8192, FILTER_NOT_HAS_BLADE_HEART: 16384, FILTER_UNIQUE_NAMES: 32768, FILTER_UNIT_ENABLE: 65536 }).map(([k, v]) => `<span>${k}:${v}</span>`).join('')}
                    <div style="grid-column: span 4; font-weight:bold; color:#e74c3c; border-bottom:1px solid #444; margin-bottom:4px; margin-top:4px;">Area/Zones</div>
                    ${Object.entries({ AREA_LEFT: 1, AREA_CENTER: 2, AREA_RIGHT: 3, ZONE_MASK_STAGE: 4, ZONE_MASK_HAND: 6, ZONE_MASK_DISCARD: 7 }).map(([k, v]) => `<span>${k}:${v}</span>`).join('')}
                </div>
            </details>
        `;
    },

    // Render conditions reference
    _renderConditionsRef: () => {
        const conditions = [
            { n: 'TURN_1', v: 200 }, { n: 'HAS_MEMBER', v: 201 }, { n: 'HAS_COLOR', v: 202 }, { n: 'COUNT_STAGE', v: 203 }, { n: 'COUNT_HAND', v: 204 }, { n: 'COUNT_DISCARD', v: 205 }, { n: 'IS_CENTER', v: 206 }, { n: 'LIFE_LEAD', v: 207 }, { n: 'COUNT_GROUP', v: 208 }, { n: 'GROUP_FILTER', v: 209 }, { n: 'OPPONENT_HAS', v: 210 }, { n: 'SELF_IS_GROUP', v: 211 }, { n: 'MODAL_ANSWER', v: 212 }, { n: 'COUNT_ENERGY', v: 213 }, { n: 'HAS_LIVE_CARD', v: 214 }, { n: 'COST_CHECK', v: 215 }, { n: 'RARITY_CHECK', v: 216 }, { n: 'HAND_HAS_NO_LIVE', v: 217 }, { n: 'COUNT_SUCCESS_LIVE', v: 218 }, { n: 'OPPONENT_HAND_DIFF', v: 219 }, { n: 'SCORE_COMPARE', v: 220 }, { n: 'HAS_CHOICE', v: 221 }, { n: 'OPPONENT_CHOICE', v: 222 }, { n: 'COUNT_HEARTS', v: 223 }, { n: 'COUNT_BLADES', v: 224 }, { n: 'OPPONENT_ENERGY_DIFF', v: 225 }, { n: 'HAS_KEYWORD', v: 226 }, { n: 'DECK_REFRESHED', v: 227 }, { n: 'HAS_MOVED', v: 228 }, { n: 'HAND_INCREASED', v: 229 }, { n: 'COUNT_LIVE_ZONE', v: 230 }, { n: 'BATON', v: 231 }, { n: 'TYPE_CHECK', v: 232 }, { n: 'IS_IN_DISCARD', v: 233 }, { n: 'AREA_CHECK', v: 234 }, { n: 'COST_LEAD', v: 235 }, { n: 'SCORE_LEAD', v: 236 }, { n: 'HEART_LEAD', v: 237 }, { n: 'HAS_EXCESS_HEART', v: 238 }, { n: 'NOT_HAS_EXCESS_HEART', v: 239 }, { n: 'TOTAL_BLADES', v: 240 }, { n: 'COST_COMPARE', v: 241 }, { n: 'BLADE_COMPARE', v: 242 }, { n: 'HEART_COMPARE', v: 243 }, { n: 'OPPONENT_HAS_WAIT', v: 244 }, { n: 'IS_TAPPED', v: 245 }, { n: 'IS_ACTIVE', v: 246 }, { n: 'LIVE_PERFORMED', v: 247 }, { n: 'IS_PLAYER', v: 248 }, { n: 'IS_OPPONENT', v: 249 }, { n: 'COUNT_UNIQUE_COLORS', v: 250 }, { n: 'COUNT_ENERGY_EXACT', v: 301 }, { n: 'COUNT_BLADE_HEART_TYPES', v: 302 }, { n: 'OPPONENT_HAS_EXCESS_HEART', v: 303 }, { n: 'SCORE_TOTAL_CHECK', v: 304 }, { n: 'MAIN_PHASE', v: 305 }, { n: 'SELECT_MEMBER', v: 306 }, { n: 'SUCCESS_PILE_COUNT', v: 307 }, { n: 'IS_SELF_MOVE', v: 308 }, { n: 'DISCARDED_CARDS', v: 309 }, { n: 'YELL_REVEALED_UNIQUE_COLORS', v: 310 }, { n: 'SYNC_COST', v: 311 }, { n: 'SUM_VALUE', v: 312 }, { n: 'IS_WAIT', v: 313 }
        ];
        return `
            <details style="margin-top:8px;">
                <summary style="cursor:pointer; font-size:10px; font-weight:bold; text-transform:uppercase; opacity:0.6; letter-spacing:1px;">Conditions Reference (${conditions.length})</summary>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 2px; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-top:4px; font-size:8px; max-height:200px; overflow-y:auto;">
                    ${conditions.map(c => `<span style="color:#3498db;">${c.n}:${c.v}</span>`).join('')}
                </div>
            </details>
        `;
    },

    // Render phases reference
    _renderPhasesRef: () => {
        const phases = [
            { n: 'SETUP', v: -4 }, { n: 'RPS', v: -3 }, { n: 'TURN_CHOICE', v: -2 }, { n: 'MULLIGAN_P1', v: -1 }, { n: 'MULLIGAN_P2', v: 0 }, { n: 'ACTIVE', v: 1 }, { n: 'ENERGY', v: 2 }, { n: 'DRAW', v: 3 }, { n: 'MAIN', v: 4 }, { n: 'LIVE_SET', v: 5 }, { n: 'PERFORMANCE_P1', v: 6 }, { n: 'PERFORMANCE_P2', v: 7 }, { n: 'LIVE_RESULT', v: 8 }, { n: 'TERMINAL', v: 9 }, { n: 'RESPONSE', v: 10 }
        ];
        return `
            <details style="margin-top:8px;">
                <summary style="cursor:pointer; font-size:10px; font-weight:bold; text-transform:uppercase; opacity:0.6; letter-spacing:1px;">Phases Reference</summary>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 2px; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-top:4px; font-size:9px;">
                    ${phases.map(p => `<span style="color:#f1c40f;">${p.n}:${p.v}</span>`).join('')}
                </div>
            </details>
        `;
    },

    // Render triggers reference
    _renderTriggersRef: () => {
        const triggers = [
            { n: 'NONE', v: 0 }, { n: 'ON_PLAY', v: 1 }, { n: 'ON_LIVE_START', v: 2 }, { n: 'ON_LIVE_SUCCESS', v: 3 }, { n: 'TURN_START', v: 4 }, { n: 'TURN_END', v: 5 }, { n: 'CONSTANT', v: 6 }, { n: 'ACTIVATED', v: 7 }, { n: 'ON_LEAVES', v: 8 }, { n: 'ON_REVEAL', v: 9 }, { n: 'ON_POSITION_CHANGE', v: 10 }
        ];
        return `
            <details style="margin-top:8px;">
                <summary style="cursor:pointer; font-size:10px; font-weight:bold; text-transform:uppercase; opacity:0.6; letter-spacing:1px;">Triggers Reference</summary>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 2px; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-top:4px; font-size:9px;">
                    ${triggers.map(t => `<span style="color:#2ecc71;">${t.n}:${t.v}</span>`).join('')}
                </div>
            </details>
        `;
    },

    renderFlags: () => {
        const container = document.getElementById('debug-flags-content');
        if (!container || !State.data) return;

        const d = State.data;
        const F = DebugModal._flag;

        let html = `
            <div class="debug-grid" style="display: flex; flex-direction: column; gap: 16px; padding-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; border: 1px solid var(--border);">
                    <h3 style="margin-top:0; color: var(--accent-blue); display:flex; justify-content:space-between;">
                        <span>System Engine Tracer</span>
                        <span style="font-size: 11px; opacity: 0.5;">v2.0-deep-diag</span>
                    </h3>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 12px;">
                        ${F('Phase', `${d.phase}`, '#f1c40f')}
                        ${F('Turn', d.turn)}
                        ${F('Active', `P${(d.active_player ?? 0) + 1}`, '#3498db')}
                        ${F('Queue', d.queue_depth || 0)}
                        ${F('RPS', JSON.stringify(d.rps_choices || []))}
                        ${F('Winner', d.winner !== undefined && d.winner !== -1 ? 'P' + (d.winner + 1) : 'NONE')}
                        ${F('FirstPl', `P${(d.first_player ?? 0) + 1}`)}
                        ${F('TrigDepth', d.trigger_depth || 0)}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 11px; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                        ${F('InteractDepth', d.pending_choice ? 1 : 0)}
                        ${F('LiveResPend', d.live_result_selection_pending ? 'YES' : 'NO')}
                        ${F('NeedsDeck', d.needs_deck ? 'YES' : 'NO')}
                        ${F('Spectators', d.spectators || 0)}
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; font-size: 11px; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                        ${F('PrevPhase', d.prev_phase ?? '-')}
                        ${F('PrevCard', d.prev_card_id ?? -1)}
                        ${F('LiveSetDraws', JSON.stringify(d.live_set_pending_draws || [0, 0]))}
                        ${F('LiveResTrigDone', d.live_result_triggers_done ? 'YES' : 'NO')}
                        ${F('LiveStartTrigDone', d.live_start_triggers_done ? 'YES' : 'NO')}
                        ${F('ScoreReqPlayer', d.score_req_player ?? -1)}
                        ${F('ScoreReqList', JSON.stringify(d.score_req_list || []))}
                    </div>
                </div>
        `;

        d.players.forEach((p, i) => {
            const isViewer = (i === State.perspectivePlayer);
            const hearts = p.total_hearts || [0, 0, 0, 0, 0, 0, 0];

            html += `
                <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; border: 1px solid var(--border);">
                    <h4 style="margin-top:0; border-bottom: 1px solid var(--border); padding-bottom: 5px; display:flex; justify-content:space-between;">
                        <span>Player ${i + 1} ${isViewer ? '<span style="font-size:10px; opacity:0.6;">(VIEWER)</span>' : ''}</span>
                        <span style="font-size:12px; color:var(--accent-blue);">Score: ${p.score}</span>
                    </h4>

                    <!-- RESOURCES -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 10px;">
                        ${F('Energy', `${p.energy_untapped ?? 0}/${p.energy_count ?? 0}`)}
                        ${F('Hand', p.hand?.length || 0)}
                        ${F('Deck', p.deck_count ?? 0)}
                        ${F('Discard', p.discard_count ?? 0)}
                        ${F('EnergyDeck', p.energy_deck_count ?? 0)}
                        ${F('SuccessLives', p.success_lives?.length || 0)}
                        ${F('LiveZone', (p.live_zone || []).filter(c => c && c.id !== -1).length)}
                        ${F('YellCards', p.yell_cards?.length || 0)}
                        ${F('Exile', p.exile_count || 0)}
                        ${F('LiveDeck', p.live_deck_count || 0)}
                    </div>

                    <!-- HEARTS BAR -->
                    <div style="display: flex; gap: 2px; margin-bottom: 10px;">
                        ${hearts.map((h, hi) => `<div style="flex:1; height:20px; background:var(--color-${hi}); color:#000; font-size:10px; font-weight:bold; display:flex; align-items:center; justify-content:center; border-radius:2px;" title="Color ${hi}">${h}</div>`).join('')}
                    </div>

                    <!-- ALL FLAGS -->
                    <details open>
                        <summary style="cursor:pointer; font-size:11px; font-weight:bold; text-transform:uppercase; opacity:0.7; letter-spacing:1px; margin-bottom:6px;">Engine Flags & Conditions</summary>
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-bottom:10px;">
                            ${F('CostReduction', p.cost_reduction ?? 0)}
                            ${F('BatonCount', `${p.baton_touch_count ?? 0}/${p.baton_touch_limit ?? 3}`)}
                            ${F('PrevActivate', p.prevent_activate, p.prevent_activate ? '#e74c3c' : '#2ecc71')}
                            ${F('PrevBaton', p.prevent_baton_touch, p.prevent_baton_touch ? '#e74c3c' : '#2ecc71')}
                            ${F('PrevSuccess', p.prevent_success_pile_set, p.prevent_success_pile_set ? '#e74c3c' : '#2ecc71')}
                            ${F('PrevPlaySlotMask', `0x${(p.prevent_play_to_slot_mask || 0).toString(16)}`)}
                            ${F('SkipNextAct', p.skip_next_activate)}
                            ${F('LiveScoreBonus', p.live_score_bonus ?? 0)}
                            ${F('YellReduction', p.yell_count_reduction ?? 0)}
                            ${F('CheerMod', p.cheer_mod_count ?? 0)}
                            ${F('PlayCount', p.play_count_this_turn ?? 0)}
                            ${F('HandIncrTurn', p.hand_increased_this_turn ?? 0)}
                            ${F('DiscardedTurn', p.discarded_this_turn ?? 0)}
                            ${F('TurnVolume', p.current_turn_notes ?? 0)}
                            ${F('ExcessHearts', p.excess_hearts ?? 0)}
                            ${F('FlagsBits', `0x${(p.flags || 0).toString(16).toUpperCase()}`)}
                            ${F('PlayedGrpMask', `0x${(p.played_group_mask || 0).toString(16).toUpperCase()}`)}
                            ${F('ActEnergyGrp', `0x${(p.activated_energy_group_mask || 0).toString(16).toUpperCase()}`)}
                            ${F('ActMemberGrp', `0x${(p.activated_member_group_mask || 0).toString(16).toUpperCase()}`)}
                            ${F('ColorXforms', p.color_transforms_count ?? 0)}
                            ${F('NegatedTrigs', p.negated_triggers_count ?? 0)}
                            ${F('GrantedAbs', p.granted_abilities_count ?? 0)}
                            ${F('UsedAbs', p.used_abilities_count ?? 0)}
                            ${F('Restrictions', JSON.stringify(p.restrictions || []))}
                            ${F('MullSelection', `0x${(p.mulligan_selection || 0).toString(16).toUpperCase()}`)}
                            ${F('ObtSuccess', p.obtained_success_live ? 'YES' : 'NO')}
                            ${F('LvRevealed', JSON.stringify(p.live_zone_revealed || [false, false, false]))}
                            <!-- NEW: Additional Missing Fields -->
                            ${F('TappedEnergyMask', `0x${(p.tapped_energy_mask || 0).toString(16).toUpperCase()}`)}
                            ${F('CostMods', JSON.stringify(p.cost_modifiers || []))}
                            ${F('BladeBuffLogs', JSON.stringify(p.blade_buff_logs || []))}
                            ${F('HeartBuffLogs', JSON.stringify(p.heart_buff_logs || []))}
                            ${F('HandAddedTurn', JSON.stringify(p.hand_added_turn || []))}
                            ${F('PerfTrigAbs', JSON.stringify(p.perf_triggered_abilities || []))}
                            <!-- NEW: Flags Bit Breakdown -->
                            <div style="grid-column: span 4; display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px; padding: 4px; background: rgba(0,0,0,0.3); border-radius: 4px;">
                                <span style="font-size:9px; color: ${(p.flags || 0) & 1 ? '#e74c3c' : '#2ecc71'}">CANNOT_LIVE:${(p.flags || 0) & 1 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 2 ? '#e74c3c' : '#2ecc71'}">DECK_REFRESHED:${(p.flags || 0) & 2 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 4 ? '#e74c3c' : '#2ecc71'}">IMMUNITY:${(p.flags || 0) & 4 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 8 ? '#e74c3c' : '#2ecc71'}">TAPPED_M0:${(p.flags || 0) & 8 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 16 ? '#e74c3c' : '#2ecc71'}">TAPPED_M1:${(p.flags || 0) & 16 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 32 ? '#e74c3c' : '#2ecc71'}">TAPPED_M2:${(p.flags || 0) & 32 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 64 ? '#e74c3c' : '#2ecc71'}">MOVED_M0:${(p.flags || 0) & 64 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 128 ? '#e74c3c' : '#2ecc71'}">MOVED_M1:${(p.flags || 0) & 128 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 256 ? '#e74c3c' : '#2ecc71'}">MOVED_M2:${(p.flags || 0) & 256 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 512 ? '#e74c3c' : '#2ecc71'}">LIVE_REV0:${(p.flags || 0) & 512 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 1024 ? '#e74c3c' : '#2ecc71'}">LIVE_REV1:${(p.flags || 0) & 1024 ? 'Y' : 'N'}</span>
                                <span style="font-size:9px; color: ${(p.flags || 0) & 2048 ? '#e74c3c' : '#2ecc71'}">LIVE_REV2:${(p.flags || 0) & 2048 ? 'Y' : 'N'}</span>
                            </div>
                        </div>
                    </details>

                    <!-- PER-SLOT DATA -->
                    <details open>
                        <summary style="cursor:pointer; font-size:11px; font-weight:bold; text-transform:uppercase; opacity:0.7; letter-spacing:1px; margin-bottom:6px;">Per-Slot Buffs & Energy</summary>
                        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-bottom:10px;">
                            ${[0, 1, 2].map(s => `
                                <div style="padding:4px; border:1px solid #333; border-radius:4px; font-size:10px;">
                                    <div style="font-weight:bold; margin-bottom:3px;">Slot ${s + 1}</div>
                                    ${F('BladeBuffs', (p.blade_buffs || [])[s] ?? 0)}
                                    ${F('HeartBuffs', JSON.stringify((p.heart_buffs || [])[s] || []))}
                                    ${F('CostMod', (p.slot_cost_modifiers || [])[s] ?? 0)}
                                    ${F('StgEnergy', (p.stage_energy_count || [])[s] ?? 0)}
                                    ${F('StgEnergyCards', JSON.stringify((p.stage_energy || [])[s] || []))}
                                </div>
                            `).join('')}
                        </div>
                    </details>

                    ${(p.heart_req_reductions && p.heart_req_reductions.some(v => v > 0)) || (p.heart_req_additions && p.heart_req_additions.some(v => v > 0)) ? `
                    <details>
                        <summary style="cursor:pointer; font-size:11px; font-weight:bold; text-transform:uppercase; opacity:0.7; letter-spacing:1px; margin-bottom:6px;">Heart Requirement Mods</summary>
                        <div style="background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-bottom:10px; font-size:10px;">
                            ${F('Reductions', JSON.stringify(p.heart_req_reductions || []))}
                            ${F('Additions', JSON.stringify(p.heart_req_additions || []))}
                        </div>
                    </details>` : ''}

                    ${(p.live_score_bonus_logs && p.live_score_bonus_logs.length > 0) ? `
                    <details>
                        <summary style="cursor:pointer; font-size:11px; font-weight:bold; text-transform:uppercase; opacity:0.7; letter-spacing:1px; margin-bottom:6px;">Score Bonus Logs (${p.live_score_bonus_logs.length})</summary>
                        <div style="background:rgba(0,0,0,0.2); padding:8px; border-radius:4px; margin-bottom:10px; font-size:10px;">
                            ${p.live_score_bonus_logs.map(l => `<div>Source: ${l.source}, Amount: +${l.amount}</div>`).join('')}
                        </div>
                    </details>` : ''}

                    <!-- STAGE DIAGNOSTICS -->
                    <h5 style="margin: 8px 0 6px 0; font-size: 11px; text-transform: uppercase; opacity: 0.7; letter-spacing: 1px;">Stage Cards</h5>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${(p.stage || []).map((c, si) => DebugModal._renderCardDiag(c, `Stage ${si + 1}`)).join('')}
                    </div>

                    <!-- LIVE ZONE DIAGNOSTICS -->
                    <h5 style="margin: 12px 0 6px 0; font-size: 11px; text-transform: uppercase; opacity: 0.7; letter-spacing: 1px;">Live Set Slots</h5>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                        ${(p.live_zone || []).map((c, li) => DebugModal._renderCardDiag(c, `Live ${li + 1}`)).join('')}
                    </div>
                </div>
            `;
        });

        html += '</div>';

        // Add Constants Reference Section at the end
        html += `
            <div style="background: rgba(0,0,0,0.2); padding: 12px; border-radius: 8px; border: 1px solid var(--border);">
                <h4 style="margin-top:0; color: var(--accent-gold);">Metadata Constants Reference</h4>
                ${DebugModal._renderConstantsRef()}
                ${DebugModal._renderConditionsRef()}
                ${DebugModal._renderPhasesRef()}
                ${DebugModal._renderTriggersRef()}
            </div>
        `;

        container.innerHTML = html;
    },

    renderBytecode: () => {
        const container = document.getElementById('debug-bytecode-content');
        if (!container || !State.data) return;
        const logs = State.data.bytecode_log || [];
        if (logs.length === 0) {
            container.innerHTML = '<div style="padding:40px; text-align:center; opacity:0.5;">No execution traces. Enable Debug Mode (<code>Network.toggleDebugMode()</code>) to capture bytecode execution logs.</div>';
            return;
        }
        container.innerHTML = logs.map(l => {
            let color = '#ccc';
            let bg = 'transparent';
            if (l.includes('ERR')) color = '#ff5555';
            if (l.includes('TRIGGER')) { color = '#fff'; bg = 'rgba(52, 152, 219, 0.2)'; }
            if (l.includes('EXECUTE')) { color = '#fff'; bg = 'rgba(46, 204, 113, 0.1)'; }
            return `<div style="padding: 2px 5px; border-bottom: 1px solid #222; color:${color}; background:${bg}; white-space: pre-wrap; word-break: break-all;">${l}</div>`;
        }).join('');
        container.scrollTop = container.scrollHeight;
    },

    renderJson: () => {
        const tx = document.getElementById('debug-json-textarea');
        if (!tx || !State.data) return;
        // Default to minimal board view (card IDs by zone only)
        DebugModal.renderMinimalJSON();
    },

    renderMinimalJSON: () => {
        if (!State.data) return;
        const getId = c => {
            if (!c) return -1;
            if (typeof c === 'object') return c.id ?? -1;
            return c;
        };
        const minimal = {
            phase: State.data.phase,
            turn: State.data.turn,
            players: State.data.players.map((p, pi) => ({
                _label: `Player ${pi + 1}`,
                stage: (p.stage || []).map(getId),
                live_zone: (p.live_zone || []).map(getId),
                hand: (p.hand || []).map(getId),
                success_lives: (p.success_lives || []).map(getId),
                energy: (p.energy || []).map(getId),
                discard: (p.discard || []).map(getId),
            }))
        };
        const tx = document.getElementById('debug-json-textarea');
        if (tx) tx.value = JSON.stringify(minimal, null, 2);
    },

    renderFullJSON: () => {
        const tx = document.getElementById('debug-json-textarea');
        if (tx && State.data) {
            tx.value = JSON.stringify(State.data, null, 2);
        }
    },

    applyCustomState: async () => {
        const tx = document.getElementById('debug-json-textarea');
        if (!tx) return;
        try {
            let newState = JSON.parse(tx.value);
            // Ensure any objects in the JSON are converted back to IDs
            newState = State.stripRichData(newState);
            const ok = await Network.applyState(JSON.stringify(newState));
            if (ok) {
                alert("Game Engine Overridden Successfully.");
                DebugModal.renderAll();
            } else {
                alert("Apply failed. Check server console for errors.");
            }
        } catch (e) {
            alert("Parse Error: " + e.message);
        }
    },

    applyBoardOnly: async () => {
        const tx = document.getElementById('debug-json-textarea');
        if (!tx || !State.data) return;
        try {
            let editState = JSON.parse(tx.value);
            // Ensure ID format for board override too
            editState = State.stripRichData(editState);
            const ok = await Network.boardOverride(JSON.stringify(editState));
            if (ok) {
                alert("Board Override Success.");
                DebugModal.renderAll();
            } else {
                alert("Override failed. Check server console.");
            }
        } catch (e) {
            alert("JSON Error: " + e.message);
        }
    },

    toggleEngineDebug: async () => {
        const ok = await Network.toggleDebugMode();
        if (ok) {
            alert("Engine Debug Mode Toggled.");
            DebugModal.renderAll();
        } else {
            alert("Toggle failed.");
        }
    },

    rewind: async () => {
        const ok = await Network.rewind();
        if (ok) {
            await DebugModal.renderAll();
            if (window.Rendering) Rendering.render();
        } else { alert("Undo failed (History empty?)"); }
    },

    redo: async () => {
        const ok = await Network.redo();
        if (ok) {
            await DebugModal.renderAll();
            if (window.Rendering) Rendering.render();
        } else { alert("Redo failed (Redo history empty?)"); }
    },

    copyStateString: () => {
        const textarea = document.getElementById('debug-string-textarea');
        if (textarea) {
            textarea.select();
            textarea.setSelectionRange(0, 99999); // For mobile devices
            try {
                document.execCommand('copy');
                alert('State string copied to clipboard!');
            } catch (err) {
                // Fallback for some browsers
                navigator.clipboard.writeText(textarea.value).then(() => {
                    alert('State string copied to clipboard!');
                });
            }
        } else if (State.data) {
            // Strip before copying from memory
            const source = State.stripRichData(State.data);
            const blob = btoa(unescape(encodeURIComponent(JSON.stringify(source))));
            navigator.clipboard.writeText(blob).then(() => alert("State Sequence Copied."));
        }
    },

    loadStateString: async () => {
        const textarea = document.getElementById('debug-string-textarea');
        const blob = textarea ? textarea.value : prompt("Input State Sequence:");
        if (!blob) return;
        try {
            const json = JSON.parse(decodeURIComponent(escape(atob(blob))));
            const ok = await Network.applyState(JSON.stringify(json));
            if (ok) {
                alert("State Decoded and Applied.");
                DebugModal.renderAll();
            } else { alert("Apply failed — check server console."); }
        } catch (e) { alert("Decode Error: " + e.message); }
    },

    saveState: () => {
        if (!State.data) return;
        // Strip rich data before saving to file
        const source = State.stripRichData(State.data);
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(source, null, 2));
        const a = document.createElement('a');
        a.setAttribute("href", dataStr);
        a.setAttribute("download", `lovelivesim_state_${Date.now()}.json`);
        document.body.appendChild(a);
        a.click();
        a.remove();
    },

    copyStandardizedJson: async () => {
        const data = await Network.fetchStandardizedState();
        if (data) {
            navigator.clipboard.writeText(JSON.stringify(data, null, 2))
                .then(() => alert("Standardized JSON copied to clipboard!"))
                .catch(err => alert("Failed to copy: " + err));
        } else {
            alert("Failed to fetch standardized state from server.");
        }
    },

    saveStandardizedJson: async () => {
        const data = await Network.fetchStandardizedState();
        if (data) {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `lovecasim_master_${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            alert("Failed to fetch standardized state from server.");
        }
    },

    async runModelAnalysis() {
        const tx = document.getElementById('debug-json-textarea');
        const resultsDiv = document.getElementById('debug-analysis-results');
        if (!tx || !resultsDiv) return;

        try {
            const state = JSON.parse(tx.value);
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = '<div style="color: #aaa;">Analyzing with Neural Network...</div>';

            const res = await fetch('/api/v1/analyze_model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(state)
            });
            const data = await res.json();

            if (data.success) {
                let html = `
                    <div style="display: flex; gap: 10px; margin-bottom: 8px; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 4px;">
                        <span style="color: #2ecc71;">Win: ${(data.value.win_prob * 100).toFixed(1)}%</span>
                        <span style="color: #4a9eff;">Mom: ${data.value.momentum.toFixed(2)}</span>
                        <span style="color: #f1c40f;">Eff: ${(data.value.efficiency * 100).toFixed(1)}%</span>
                    </div>
                    <div style="font-family: monospace; display: flex; flex-direction: column; gap: 4px;">`;

                data.actions.forEach(a => {
                    const probColor = a.logit > 0 ? '#2ecc71' : (a.logit > -2 ? '#f1c40f' : '#aaa');
                    html += `
                        <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 3px;">
                            <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 10px;">${a.desc}</span>
                            <span style="color: ${probColor}; font-weight: bold; min-width: 45px; text-align: right;">${a.logit.toFixed(2)}</span>
                        </div>`;
                });
                html += '</div>';
                resultsDiv.innerHTML = html;
            } else {
                resultsDiv.innerHTML = `<div style="color: #e74c3c;">Error: ${data.error || 'Unknown error'}</div>`;
            }
        } catch (e) {
            resultsDiv.innerHTML = `<div style="color: #e74c3c;">Failed to analyze: ${e.message}</div>`;
        }
    }
};

// Wired to Globals
window.openDebugModal = DebugModal.openDebugModal;
window.closeDebugModal = DebugModal.closeDebugModal;
window.switchDebugTab = DebugModal.switchTab;
window.applyDebugState = DebugModal.applyCustomState;
window.copyDebugState = DebugModal.copyStateString;
window.loadDebugState = DebugModal.loadStateString;
window.renderFullJSON = DebugModal.renderFullJSON;
window.renderMinimalJSON = DebugModal.renderMinimalJSON;
window.DebugModal = DebugModal;
