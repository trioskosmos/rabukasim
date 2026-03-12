import { State } from '../state.js';
import { Network } from '../network.js';
import {
    ChoiceTypes,
    ConditionTypes,
    CostTypes,
    ExtraConstants,
    Opcodes,
    Phases,
    TargetType,
    TriggerType,
} from '../generated_constants.js';

const buildReverseLookup = (source) => Object.fromEntries(
    Object.entries(source)
        .filter(([key, value]) => typeof value === 'number' && !/^[-]?\d+$/.test(key))
        .map(([key, value]) => [value, key])
);

const TRIGGER_NAMES = buildReverseLookup(TriggerType);
const CONDITION_NAMES = buildReverseLookup(ConditionTypes);
const EFFECT_NAMES = buildReverseLookup(Opcodes);
const COST_NAMES = buildReverseLookup(CostTypes);
const CHOICE_NAMES = buildReverseLookup(ChoiceTypes);
const TARGET_NAMES = buildReverseLookup(TargetType);
const PHASE_NAMES = buildReverseLookup(Phases);

const pickBits = (names) => names
    .filter((name) => Number.isSafeInteger(ExtraConstants[name]))
    .map((name) => ({ name, value: ExtraConstants[name] }));

const ABILITY_FLAG_BITS = pickBits([
    'FLAG_DRAW',
    'FLAG_SEARCH',
    'FLAG_RECOVER',
    'FLAG_BUFF',
    'FLAG_CHARGE',
    'FLAG_TEMPO',
    'FLAG_REDUCE',
    'FLAG_BOOST',
    'FLAG_TRANSFORM',
    'FLAG_WIN_COND',
    'FLAG_MOVE',
    'FLAG_TAP',
]);

const COST_FLAG_BITS = pickBits(['COST_FLAG_DISCARD', 'COST_FLAG_TAP']);
const CHOICE_FLAG_BITS = pickBits(['CHOICE_FLAG_LOOK', 'CHOICE_FLAG_DISCARD', 'CHOICE_FLAG_MODE', 'CHOICE_FLAG_COLOR', 'CHOICE_FLAG_ORDER']);
const SYNERGY_FLAG_BITS = pickBits(['SYN_FLAG_GROUP', 'SYN_FLAG_COLOR', 'SYN_FLAG_BATON', 'SYN_FLAG_CENTER', 'SYN_FLAG_LIFE_LEAD']);
const FILTER_FLAG_BITS = pickBits([
    'FILTER_TYPE_MEMBER',
    'FILTER_TYPE_LIVE',
    'FILTER_GROUP_ENABLE',
    'FILTER_TAPPED',
    'FILTER_HAS_BLADE_HEART',
    'FILTER_NOT_HAS_BLADE_HEART',
    'FILTER_UNIQUE_NAMES',
    'FILTER_UNIT_ENABLE',
    'FILTER_COST_ENABLE',
    'FILTER_COST_LE',
    'FILTER_BLADE_FILTER_FLAG',
    'FILTER_ANY_STAGE',
    'FILTER_OPPONENT',
    'FILTER_REVEALED_CONTEXT',
    'FILTER_TOTAL_COST',
    'FILTER_COST_TYPE_FLAG',
    'FILTER_IS_OPTIONAL',
]);

const cloneDeep = (value) => JSON.parse(JSON.stringify(value));

const escapeHtml = (value) => String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const summarizeObject = (value) => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'string') return value;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    return JSON.stringify(value);
};

const formatPacked = (value) => {
    if (value === undefined || value === null) return '0';
    if (typeof value !== 'number' || !Number.isFinite(value)) return summarizeObject(value);
    return `0x${value.toString(16)}`;
};

const decodeBitmask = (value, bits) => {
    if (!Number.isSafeInteger(value) || value <= 0) return [];
    return bits
        .filter((bit) => bit.value !== 0 && (value & bit.value) === bit.value)
        .map((bit) => bit.name);
};

const renderChips = (items, accent = '#7dd3fc') => {
    if (!items || items.length === 0) {
        return '<span style="opacity:0.45; font-size:10px;">none</span>';
    }

    return items.map((item) => `
        <span style="display:inline-flex; align-items:center; padding:2px 7px; border-radius:999px; border:1px solid ${accent}; color:${accent}; background:rgba(0,0,0,0.22); font-size:10px; line-height:1.2;">${escapeHtml(item)}</span>
    `).join('');
};

const zoneDefinitions = (player) => [
    { key: 'stage', label: 'Stage', cards: player?.stage || [] },
    { key: 'live', label: 'Live', cards: player?.live_zone || [] },
    { key: 'hand', label: 'Hand', cards: player?.hand || [] },
    { key: 'success', label: 'Success', cards: player?.success_lives || player?.success_zone || player?.success_pile || [] },
    { key: 'energy', label: 'Energy', cards: player?.energy || [] },
    { key: 'discard', label: 'Discard', cards: player?.discard || [] },
    { key: 'looked', label: 'Looked', cards: player?.looked_cards || [] },
];

const extractScalarEntries = (value) => Object.entries(value || {})
    .filter(([, item]) => item === null || ['string', 'number', 'boolean'].includes(typeof item));

const describeNumber = (key, value, itemType) => {
    if (key === 'trigger') return `${TRIGGER_NAMES[value] || value} (${value})`;
    if (key === 'condition_type') return `${CONDITION_NAMES[value] || value} (${value})`;
    if (key === 'effect_type') return `${EFFECT_NAMES[value] || value} (${value})`;
    if (key === 'cost_type') return `${COST_NAMES[value] || value} (${value})`;
    if (key === 'choice_type' || key === 'choice') return `${CHOICE_NAMES[value] || value} (${value})`;
    if (key === 'target') return `${TARGET_NAMES[value] || value} (${value})`;
    if (key === 'phase') return `${PHASE_NAMES[value] || value} (${value})`;
    if (key.includes('flags') || key.includes('filter') || key === 'attr') {
        const bits = key.startsWith('choice')
            ? CHOICE_FLAG_BITS
            : (itemType === 'cost' && key.includes('flag'))
                ? COST_FLAG_BITS
                : FILTER_FLAG_BITS;
        const decoded = decodeBitmask(value, bits);
        return decoded.length > 0 ? `${value} [${decoded.join(', ')}]` : String(value);
    }
    return String(value);
};

const renderScalarCell = (label, value) => `
    <div style="padding:7px 8px; border-radius:6px; background:rgba(255,255,255,0.04); font-size:10px; line-height:1.35; min-width:0;">
        <div style="opacity:0.6; text-transform:uppercase; letter-spacing:0.04em;">${escapeHtml(label)}</div>
        <div style="font-family:'Cascadia Code', monospace; word-break:break-word;">${escapeHtml(value)}</div>
    </div>
`;

const renderStatusBanner = (status) => {
    if (!status?.message) return '';
    const colors = status.kind === 'error'
        ? { border: '#ef4444', background: 'rgba(239,68,68,0.12)', text: '#fecaca' }
        : { border: '#22c55e', background: 'rgba(34,197,94,0.12)', text: '#bbf7d0' };

    return `
        <div style="padding:9px 12px; border-radius:6px; border-left:3px solid ${colors.border}; background:${colors.background}; color:${colors.text}; font-size:11px; line-height:1.45;">
            ${escapeHtml(status.message)}
        </div>
    `;
};

const renderLogLines = (lines, emptyMessage) => {
    if (!lines || lines.length === 0) {
        return `<div style="padding:20px; opacity:0.55; font-size:11px; text-align:center;">${emptyMessage}</div>`;
    }

    return lines.map((line) => {
        let color = '#94a3b8';
        let background = 'transparent';
        if (line.includes('ERR')) {
            color = '#f87171';
            background = 'rgba(248,113,113,0.08)';
        } else if (line.includes('BC_COND') || line.includes('COND')) {
            color = '#38bdf8';
            background = 'rgba(56,189,248,0.08)';
        } else if (line.includes('TRIGGER')) {
            color = '#4ade80';
            background = 'rgba(74,222,128,0.08)';
        } else if (line.includes('EXECUTE') || line.includes('BC_STEP')) {
            color = '#fbbf24';
            background = 'rgba(251,191,36,0.08)';
        }

        return `<div style="padding:4px 8px; color:${color}; background:${background}; font-size:10px; border-bottom:1px solid #16202f; white-space:pre-wrap; word-break:break-word; line-height:1.35;">${escapeHtml(line)}</div>`;
    }).join('');
};

export const DebugModal = {
    _filters: {
        selectedPlayer: 0,
        selectedZone: 'all',
        abilitySearch: '',
    },

    _activeTab: 'inspector',
    _snapshot: null,
    _status: null,

    init: () => {},

    openDebugModal: async () => {
        const modal = document.getElementById('debug-modal');
        if (!modal) return;

        modal.style.display = 'flex';
        await DebugModal.renderAll();
        DebugModal.switchTab(DebugModal._activeTab);
    },

    closeDebugModal: () => {
        const modal = document.getElementById('debug-modal');
        if (modal) modal.style.display = 'none';
    },

    _setStatus: (kind, message) => {
        DebugModal._status = message ? { kind, message } : null;
    },

    _clearStatus: () => {
        DebugModal._status = null;
    },

    switchTab: (tabId) => {
        DebugModal._activeTab = tabId;

        document.querySelectorAll('[data-tab-pane]').forEach((el) => {
            el.style.display = 'none';
        });

        const pane = document.querySelector(`[data-tab-pane="${tabId}"]`);
        if (pane) pane.style.display = 'block';

        document.querySelectorAll('[data-tab-btn]').forEach((btn) => {
            const active = btn.getAttribute('data-tab-btn') === tabId;
            btn.style.borderBottom = active ? '2px solid var(--accent-blue)' : '2px solid transparent';
            btn.style.color = active ? '#fff' : 'var(--text-dim)';
        });

        if (tabId === 'inspector') DebugModal.renderInspectorTab();
        if (tabId === 'trace') DebugModal.renderTraceTab();
        if (tabId === 'string') DebugModal.renderStringTab();
        if (tabId === 'json') DebugModal.renderJsonTab();
    },

    renderAll: async () => {
        if (State.roomCode) await Network.fetchState();
        await DebugModal._refreshSnapshot();

        if (!State.data) {
            const emptyMarkup = '<div style="padding:24px; opacity:0.6; text-align:center; font-size:12px;">Waiting for game state...</div>';
            document.querySelectorAll('[data-tab-pane]').forEach((pane) => {
                pane.innerHTML = emptyMarkup;
            });
            return;
        }

        DebugModal.renderInspectorTab();
        DebugModal.renderTraceTab();
        DebugModal.renderStringTab();
        DebugModal.renderJsonTab();
        DebugModal.switchTab(DebugModal._activeTab);
    },

    _refreshSnapshot: async () => {
        const snapshot = await Network.fetchDebugSnapshot();
        DebugModal._snapshot = snapshot && snapshot.success ? snapshot : null;
    },

    _getCheckpointPayload: (source = null) => {
        if (!source && DebugModal._snapshot?.raw_state) {
            return cloneDeep(DebugModal._snapshot.raw_state);
        }
        if (typeof State.createCheckpointData === 'function') {
            return State.createCheckpointData(source);
        }
        return State.stripRichData(source ?? State.data);
    },

    _decodeStateInput: (rawInput) => {
        const content = String(rawInput || '').trim();
        if (!content) throw new Error('No state payload provided');

        if (/^[\[{]/.test(content)) {
            return JSON.parse(content);
        }

        if (/^[A-Za-z0-9+/=\s_-]+$/.test(content)) {
            const normalized = content.replace(/-/g, '+').replace(/_/g, '/').replace(/\s+/g, '');
            return JSON.parse(decodeURIComponent(escape(atob(normalized))));
        }

        throw new Error('Unrecognized state payload format');
    },

    _extractApplyMessage: (result) => {
        if (!result) return 'Apply failed with no response.';
        if (result.ok) {
            return result.data?.message || result.data?.status || 'Checkpoint applied successfully.';
        }

        if (typeof result.error === 'string') return result.error;
        if (result.error?.error) return result.error.error;
        if (result.error?.message) return result.error.message;
        if (result.data?.error) return result.data.error;
        return 'Apply failed.';
    },

    _applyCheckpointPayload: async (payload) => {
        const cleanState = DebugModal._getCheckpointPayload(payload);
        return Network.applyState(JSON.stringify(cleanState));
    },

    _normalizeCard: (rawEntry) => {
        if (rawEntry === null || rawEntry === undefined) return null;
        if (typeof rawEntry === 'number') return State.resolveCardData(rawEntry);

        if (typeof rawEntry === 'object' && rawEntry.card) {
            const { card, ...rest } = rawEntry;
            const resolvedCard = DebugModal._normalizeCard(card);
            if (!resolvedCard) return null;
            return { ...resolvedCard, ...rest };
        }

        if (typeof rawEntry === 'object') {
            if (rawEntry.id === undefined && rawEntry.card_id !== undefined) {
                return { ...rawEntry, id: rawEntry.card_id };
            }
            return rawEntry;
        }

        return null;
    },

    _collectVisibleCards: (player, zoneKey) => {
        const defs = zoneDefinitions(player);
        const selectedDefs = zoneKey === 'all' ? defs : defs.filter((zone) => zone.key === zoneKey);
        return selectedDefs.flatMap((zone) => zone.cards.map((rawEntry, index) => ({
            zoneKey: zone.key,
            zoneLabel: zone.label,
            slotLabel: `${zone.label} ${index + 1}`,
            slotIndex: index,
            card: DebugModal._normalizeCard(rawEntry),
        })));
    },

    _matchesSearch: (entry, search) => {
        if (!search) return true;
        const card = entry.card;
        if (!card) return false;

        const needle = search.toLowerCase();
        if ((card.name || '').toLowerCase().includes(needle)) return true;
        if (String(card.id || '').includes(needle)) return true;
        if ((entry.zoneLabel || '').toLowerCase().includes(needle)) return true;

        return (card.abilities || []).some((ability) => {
            if ((ability.pseudocode || '').toLowerCase().includes(needle)) return true;
            const triggerName = TRIGGER_NAMES[ability.trigger] || '';
            if (triggerName.toLowerCase().includes(needle)) return true;
            return (ability.conditions || []).some((condition) => {
                const conditionName = CONDITION_NAMES[condition.condition_type] || '';
                return conditionName.toLowerCase().includes(needle);
            });
        });
    },

    _renderSummaryCards: (players, visibleCards) => {
        const phaseName = PHASE_NAMES[State.data.phase] || String(State.data.phase ?? '?');
        const traceCount = DebugModal._snapshot?.trace_log?.length || 0;
        const bytecodeCount = DebugModal._snapshot?.bytecode_log?.length || State.data.bytecode_log?.length || 0;

        return `
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px;">
                <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:6px;">
                    <div style="font-size:10px; letter-spacing:0.08em; text-transform:uppercase; opacity:0.6;">State</div>
                    <div style="display:grid; grid-template-columns:repeat(2, minmax(60px, 1fr)); gap:8px; font-size:11px;">
                        ${renderScalarCell('turn', summarizeObject(State.data.turn ?? '?'))}
                        ${renderScalarCell('phase', phaseName)}
                        ${renderScalarCell('active', `P${(State.data.active_player ?? 0) + 1}`)}
                        ${renderScalarCell('visible cards', String(visibleCards.length))}
                    </div>
                </div>
                <div style="background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:6px;">
                    <div style="font-size:10px; letter-spacing:0.08em; text-transform:uppercase; opacity:0.6;">Debug Snapshot</div>
                    <div style="display:grid; grid-template-columns:repeat(2, minmax(60px, 1fr)); gap:8px; font-size:11px;">
                        ${renderScalarCell('snapshot', DebugModal._snapshot ? 'available' : 'fallback')}
                        ${renderScalarCell('debug_mode', DebugModal._snapshot?.debug_mode ? 'enabled' : 'disabled')}
                        ${renderScalarCell('trace lines', String(traceCount))}
                        ${renderScalarCell('bytecode lines', String(bytecodeCount))}
                    </div>
                </div>
                ${players.map((player, index) => `
                    <div style="background:${index === DebugModal._filters.selectedPlayer ? 'rgba(56,189,248,0.12)' : 'rgba(255,255,255,0.04)'}; border:1px solid ${index === DebugModal._filters.selectedPlayer ? 'rgba(56,189,248,0.4)' : 'rgba(255,255,255,0.08)'}; border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:6px;">
                        <div style="display:flex; justify-content:space-between; gap:8px; align-items:center;">
                            <strong style="font-size:11px; color:${index === DebugModal._filters.selectedPlayer ? '#7dd3fc' : '#fff'};">Player ${index + 1}${State.data.active_player === index ? ' [active]' : ''}</strong>
                            <span style="font-size:10px; opacity:0.72;">Score ${escapeHtml(player?.score ?? 0)}</span>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(2, minmax(70px, 1fr)); gap:6px;">
                            ${zoneDefinitions(player).map((zone) => renderScalarCell(zone.label, String(zone.cards.length))).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    },

    _renderPendingChoice: () => {
        if (!State.data?.pending_choice) return '';

        const pending = State.data.pending_choice;
        const choiceType = CHOICE_NAMES[pending.choice_type] || CHOICE_NAMES[pending.type] || 'PENDING_CHOICE';

        return `
            <div style="background:rgba(251,191,36,0.08); border-left:3px solid #fbbf24; padding:10px 12px; border-radius:6px; display:flex; flex-direction:column; gap:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <strong style="font-size:11px; color:#fbbf24; letter-spacing:0.06em; text-transform:uppercase;">Pending Choice</strong>
                    <span style="font-size:10px; opacity:0.85;">${escapeHtml(choiceType)}</span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(120px, 1fr)); gap:6px;">
                    ${extractScalarEntries(pending).map(([key, value]) => renderScalarCell(key, summarizeObject(value))).join('')}
                </div>
            </div>
        `;
    },

    _buildZoneDiagnostic: (player, zone) => {
        const entries = zone.cards.map((entry, index) => ({
            index,
            card: DebugModal._normalizeCard(entry),
        })).filter((entry) => entry.card && entry.card.id !== -1 && entry.card.id !== -2);

        const triggers = new Set();
        const conditions = new Set();
        const effects = new Set();
        const costs = new Set();
        const abilityFlags = new Set();
        const synergyFlags = new Set();
        const semanticFlags = new Set();

        let tapped = 0;
        let moved = 0;
        let revealed = 0;
        let totalAbilities = 0;
        let totalNotes = 0;

        entries.forEach(({ card }) => {
            if (card.tapped) tapped += 1;
            if (card.moved) moved += 1;
            if (card.revealed) revealed += 1;
            totalNotes += Number(card.note_icons || 0);
            decodeBitmask(card.ability_flags || 0, ABILITY_FLAG_BITS).forEach((item) => abilityFlags.add(item));
            decodeBitmask(card.synergy_flags || 0, SYNERGY_FLAG_BITS).forEach((item) => synergyFlags.add(item));
            if (Number.isFinite(card.semantic_flags)) semanticFlags.add(formatPacked(card.semantic_flags));

            (card.abilities || []).forEach((ability) => {
                totalAbilities += 1;
                triggers.add(TRIGGER_NAMES[ability.trigger] || `TRIGGER_${ability.trigger ?? '?'}`);
                (ability.conditions || []).forEach((condition) => {
                    conditions.add(CONDITION_NAMES[condition.condition_type] || `COND_${condition.condition_type ?? '?'}`);
                });
                (ability.effects || []).forEach((effect) => {
                    effects.add(EFFECT_NAMES[effect.effect_type] || `EFFECT_${effect.effect_type ?? '?'}`);
                });
                (ability.costs || []).forEach((cost) => {
                    costs.add(COST_NAMES[cost.cost_type] || `COST_${cost.cost_type ?? '?'}`);
                });
            });
        });

        return {
            cards: entries.length,
            tapped,
            moved,
            revealed,
            totalAbilities,
            totalNotes,
            triggers: Array.from(triggers).sort(),
            conditions: Array.from(conditions).sort(),
            effects: Array.from(effects).sort(),
            costs: Array.from(costs).sort(),
            abilityFlags: Array.from(abilityFlags).sort(),
            synergyFlags: Array.from(synergyFlags).sort(),
            semanticFlags: Array.from(semanticFlags).sort(),
        };
    },

    _renderZoneDiagnostics: (player) => {
        const zones = zoneDefinitions(player);
        return `
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:10px; overflow:hidden;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <strong style="font-size:12px;">Zone Diagnostics</strong>
                    <span style="font-size:10px; opacity:0.7;">All visible trigger, condition, cost, effect, and flag surfaces per zone</span>
                </div>
                <div style="overflow:auto; border:1px solid rgba(255,255,255,0.06); border-radius:6px;">
                    <table style="width:100%; border-collapse:collapse; min-width:1180px; font-size:10px;">
                        <thead>
                            <tr style="background:rgba(15,23,42,0.95); text-transform:uppercase; letter-spacing:0.04em;">
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Zone</th>
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Counts</th>
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Triggers</th>
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Conditions</th>
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Costs</th>
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Effects</th>
                                <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Flags</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${zones.map((zone) => {
                                const diag = DebugModal._buildZoneDiagnostic(player, zone);
                                return `
                                    <tr style="vertical-align:top; background:${DebugModal._filters.selectedZone === zone.key ? 'rgba(56,189,248,0.06)' : 'transparent'};">
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); font-weight:700;">${escapeHtml(zone.label)}</td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:180px;">
                                            <div style="display:grid; grid-template-columns:repeat(2, minmax(80px, 1fr)); gap:6px;">
                                                ${renderScalarCell('cards', String(diag.cards))}
                                                ${renderScalarCell('abilities', String(diag.totalAbilities))}
                                                ${renderScalarCell('tapped', String(diag.tapped))}
                                                ${renderScalarCell('revealed', String(diag.revealed))}
                                                ${renderScalarCell('moved', String(diag.moved))}
                                                ${renderScalarCell('notes', String(diag.totalNotes))}
                                            </div>
                                        </td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:180px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(diag.triggers, '#4ade80')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:240px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(diag.conditions, '#38bdf8')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:180px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(diag.costs, '#fb923c')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:220px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(diag.effects, '#facc15')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:260px;">
                                            <div style="display:flex; flex-direction:column; gap:6px;">
                                                <div><span style="opacity:0.65;">ability</span><div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">${renderChips(diag.abilityFlags, '#22c55e')}</div></div>
                                                <div><span style="opacity:0.65;">synergy</span><div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">${renderChips(diag.synergyFlags, '#eab308')}</div></div>
                                                <div><span style="opacity:0.65;">semantic</span><div style="display:flex; flex-wrap:wrap; gap:4px; margin-top:4px;">${renderChips(diag.semanticFlags, '#c084fc')}</div></div>
                                            </div>
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    },

    _collectAbilityRows: (visibleCards) => visibleCards.flatMap((entry) => {
        const card = entry.card;
        return (card.abilities || []).map((ability, abilityIndex) => ({
            cardName: card.name || `Card ${card.id}`,
            cardId: card.id ?? card.card_id ?? '?',
            slotLabel: entry.slotLabel,
            abilityIndex,
            trigger: TRIGGER_NAMES[ability.trigger] || `TRIGGER_${ability.trigger ?? '?'}`,
            conditions: (ability.conditions || []).map((condition) => CONDITION_NAMES[condition.condition_type] || `COND_${condition.condition_type ?? '?'}`),
            costs: (ability.costs || []).map((cost) => COST_NAMES[cost.cost_type] || `COST_${cost.cost_type ?? '?'}`),
            effects: (ability.effects || []).map((effect) => EFFECT_NAMES[effect.effect_type] || `EFFECT_${effect.effect_type ?? '?'}`),
            flags: [
                ...(ability.choice_flags !== undefined ? decodeBitmask(ability.choice_flags, CHOICE_FLAG_BITS) : []),
                ...(ability.filter_flags !== undefined ? decodeBitmask(ability.filter_flags, FILTER_FLAG_BITS) : []),
                ...(ability.cost_flags !== undefined ? decodeBitmask(ability.cost_flags, COST_FLAG_BITS) : []),
            ],
            pseudocode: ability.pseudocode || '',
        }));
    }),

    _renderAbilityMatrix: (visibleCards) => {
        const rows = DebugModal._collectAbilityRows(visibleCards);
        return `
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:10px; overflow:hidden;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <strong style="font-size:12px;">Ability Matrix</strong>
                    <span style="font-size:10px; opacity:0.7;">Every visible ability in the current filter window</span>
                </div>
                ${rows.length === 0 ? '<div style="opacity:0.55; text-align:center; padding:20px; font-size:11px;">No abilities match the current zone/search filter.</div>' : `
                    <div style="overflow:auto; border:1px solid rgba(255,255,255,0.06); border-radius:6px;">
                        <table style="width:100%; border-collapse:collapse; min-width:1350px; font-size:10px;">
                            <thead>
                                <tr style="background:rgba(15,23,42,0.95); text-transform:uppercase; letter-spacing:0.04em;">
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Card</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Zone</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Trigger</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Conditions</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Costs</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Effects</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Flags</th>
                                    <th style="padding:8px; text-align:left; border-bottom:1px solid rgba(255,255,255,0.08);">Pseudocode</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rows.map((row) => `
                                    <tr style="vertical-align:top;">
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:180px;">
                                            <strong>${escapeHtml(row.cardName)}</strong><br/>
                                            <span style="opacity:0.6; font-family:'Cascadia Code', monospace;">id=${escapeHtml(row.cardId)} a${row.abilityIndex + 1}</span>
                                        </td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:120px;">${escapeHtml(row.slotLabel)}</td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:140px;">${escapeHtml(row.trigger)}</td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:220px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(row.conditions, '#38bdf8')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:180px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(row.costs, '#fb923c')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:220px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(row.effects, '#facc15')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:190px;"><div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(row.flags, '#22c55e')}</div></td>
                                        <td style="padding:8px; border-bottom:1px solid rgba(255,255,255,0.06); min-width:280px; line-height:1.4;">${escapeHtml(row.pseudocode || '-')}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `}
            </div>
        `;
    },

    _renderFlagRow: (label, value, bits, accent) => {
        if (value === undefined || value === null) return '';
        const decoded = bits.length > 0 ? decodeBitmask(value, bits) : [];

        return `
            <div style="border:1px solid rgba(255,255,255,0.08); border-radius:6px; padding:8px; background:rgba(255,255,255,0.025); display:flex; flex-direction:column; gap:6px;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:10px;">
                    <strong style="color:${accent};">${escapeHtml(label)}</strong>
                    <span style="font-family:'Cascadia Code', monospace; opacity:0.7;">${escapeHtml(formatPacked(value))}</span>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:4px;">${renderChips(decoded.length > 0 ? decoded : [formatPacked(value)], accent)}</div>
            </div>
        `;
    },

    _renderLogicItem: (item, itemType, accent) => {
        const typeField = itemType === 'condition' ? 'condition_type' : itemType === 'effect' ? 'effect_type' : 'cost_type';
        const labelMap = itemType === 'condition' ? CONDITION_NAMES : itemType === 'effect' ? EFFECT_NAMES : COST_NAMES;
        const typeValue = item[typeField];
        const itemLabel = labelMap[typeValue] || `${itemType.toUpperCase()}_${typeValue ?? '?'}`;
        const scalarEntries = extractScalarEntries(item);

        return `
            <div style="border:1px solid rgba(255,255,255,0.08); border-left:3px solid ${accent}; border-radius:6px; padding:8px; background:rgba(255,255,255,0.025); display:flex; flex-direction:column; gap:8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
                    <strong style="font-size:10px; color:${accent};">${escapeHtml(itemLabel)}</strong>
                    <span style="font-size:9px; opacity:0.65; font-family:'Cascadia Code', monospace;">${escapeHtml(typeField)}=${escapeHtml(typeValue ?? '?')}</span>
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(110px, 1fr)); gap:6px;">
                    ${scalarEntries.map(([key, value]) => renderScalarCell(key, typeof value === 'number' ? describeNumber(key, value, itemType) : summarizeObject(value))).join('')}
                </div>
                <details>
                    <summary style="cursor:pointer; opacity:0.65; font-size:9px;">Raw JSON</summary>
                    <pre style="margin:6px 0 0 0; padding:8px; background:#05070d; border-radius:4px; font-size:9px; line-height:1.35; color:#dbeafe; white-space:pre-wrap; word-break:break-word;">${escapeHtml(JSON.stringify(item, null, 2))}</pre>
                </details>
            </div>
        `;
    },

    _renderLogicGroup: (title, items, itemType, accent) => {
        if (!items || items.length === 0) return '';
        return `
            <div style="display:flex; flex-direction:column; gap:6px;">
                <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.06em; color:${accent};">${title} (${items.length})</div>
                ${items.map((item) => DebugModal._renderLogicItem(item, itemType, accent)).join('')}
            </div>
        `;
    },

    _renderAbilityBlock: (ability, abilityIndex) => {
        const triggerLabel = TRIGGER_NAMES[ability.trigger] || `TRIGGER_${ability.trigger ?? '?'}`;
        const abilityTags = [
            ability.is_once_per_turn ? 'ONCE_PER_TURN' : null,
            ability.requires_selection ? 'REQUIRES_SELECTION' : null,
            ability.choice_count ? `CHOICE_COUNT=${ability.choice_count}` : null,
        ].filter(Boolean);

        return `
            <div style="display:flex; flex-direction:column; gap:8px; padding:10px; border-radius:8px; background:rgba(0,0,0,0.18); border:1px solid rgba(255,255,255,0.08);">
                <div style="display:flex; justify-content:space-between; gap:8px; align-items:flex-start;">
                    <div style="display:flex; flex-direction:column; gap:4px; min-width:0;">
                        <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                            <strong style="font-size:11px; color:#fbbf24;">Ability ${abilityIndex + 1}</strong>
                            <span style="font-size:9px; padding:2px 6px; border-radius:999px; background:rgba(251,191,36,0.12); border:1px solid rgba(251,191,36,0.35); color:#fbbf24;">${escapeHtml(triggerLabel)}</span>
                            ${abilityTags.map((tag) => `<span style="font-size:9px; padding:2px 6px; border-radius:999px; background:rgba(255,255,255,0.08);">${escapeHtml(tag)}</span>`).join('')}
                        </div>
                        <div style="font-size:10px; line-height:1.45; opacity:0.88;">${escapeHtml(ability.pseudocode || 'No pseudocode')}</div>
                    </div>
                    <div style="font-size:9px; opacity:0.65; font-family:'Cascadia Code', monospace;">trigger=${escapeHtml(ability.trigger ?? '?')}</div>
                </div>

                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(110px, 1fr)); gap:6px;">
                    ${ability.choice_type !== undefined ? renderScalarCell('choice_type', describeNumber('choice_type', ability.choice_type)) : ''}
                    ${ability.choice_flags !== undefined ? renderScalarCell('choice_flags', describeNumber('choice_flags', ability.choice_flags)) : ''}
                    ${ability.filter_flags !== undefined ? renderScalarCell('filter_flags', describeNumber('filter_flags', ability.filter_flags)) : ''}
                </div>

                ${DebugModal._renderLogicGroup('Conditions', ability.conditions, 'condition', '#38bdf8')}
                ${DebugModal._renderLogicGroup('Costs', ability.costs, 'cost', '#fb923c')}
                ${DebugModal._renderLogicGroup('Effects', ability.effects, 'effect', '#22c55e')}

                ${(ability.decoded_bytecode && ability.decoded_bytecode.length > 0) ? `
                    <details>
                        <summary style="cursor:pointer; opacity:0.65; font-size:9px;">Decoded Bytecode (${ability.decoded_bytecode.length})</summary>
                        <pre style="margin:6px 0 0 0; padding:8px; background:#05070d; border-radius:4px; font-size:9px; line-height:1.3; color:#8df58d; white-space:pre-wrap; word-break:break-word;">${escapeHtml(ability.decoded_bytecode.join('\n'))}</pre>
                    </details>
                ` : ''}
            </div>
        `;
    },

    _renderCardInspector: (entry, index) => {
        const card = entry.card;
        if (!card) return '';

        const abilities = card.abilities || [];
        const cardType = card.type || (card.score !== undefined ? 'live' : 'member');
        const statusBits = [
            card.tapped ? 'TAPPED' : null,
            card.moved ? 'MOVED' : null,
            card.revealed ? 'REVEALED' : null,
            card.is_active ? 'ACTIVE' : null,
            card.waiting ? 'WAIT' : null,
        ].filter(Boolean);

        return `
            <div style="background:rgba(255,255,255,0.045); border:1px solid #334155; border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:10px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.08);">
                    <div style="display:flex; flex-direction:column; gap:4px; min-width:0;">
                        <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                            <strong style="font-size:13px; color:${cardType === 'live' ? '#f87171' : '#7dd3fc'};">${escapeHtml(card.name || `Card ${card.id}`)}</strong>
                            <span style="font-size:9px; padding:2px 6px; border-radius:999px; background:rgba(255,255,255,0.08); opacity:0.75;">${escapeHtml(entry.zoneLabel)}</span>
                            <span style="font-size:9px; padding:2px 6px; border-radius:999px; background:rgba(255,255,255,0.08); opacity:0.75;">${escapeHtml(cardType.toUpperCase())}</span>
                            <span style="font-size:9px; opacity:0.55;">#${index + 1}</span>
                        </div>
                        <div style="font-size:10px; opacity:0.72;">${escapeHtml(entry.slotLabel)}</div>
                    </div>
                    <div style="font-size:10px; opacity:0.72; font-family:'Cascadia Code', monospace; text-align:right;">ID ${escapeHtml(card.id ?? card.card_id ?? '?')}</div>
                </div>

                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(115px, 1fr)); gap:6px;">
                    ${renderScalarCell('type', cardType)}
                    ${renderScalarCell(cardType === 'live' ? 'score' : 'cost', String(cardType === 'live' ? (card.score ?? 0) : (card.cost ?? 0)))}
                    ${renderScalarCell('blades', String(card.blades ?? 0))}
                    ${renderScalarCell('hearts', summarizeObject(card.hearts ?? card.required_hearts ?? []))}
                    ${renderScalarCell('notes', String(card.note_icons ?? 0))}
                    ${renderScalarCell('status', statusBits.join(', ') || 'none')}
                </div>

                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:8px;">
                    ${DebugModal._renderFlagRow('Semantic Flags', card.semantic_flags ?? 0, [], '#c084fc')}
                    ${DebugModal._renderFlagRow('Ability Flags', card.ability_flags ?? 0, ABILITY_FLAG_BITS, '#22c55e')}
                    ${DebugModal._renderFlagRow('Synergy Flags', card.synergy_flags ?? 0, SYNERGY_FLAG_BITS, '#eab308')}
                    ${DebugModal._renderFlagRow('Cost Flags', card.cost_flags ?? 0, COST_FLAG_BITS, '#f97316')}
                </div>

                ${abilities.length === 0 ? '<div style="opacity:0.5; font-size:10px;">No abilities on this card.</div>' : `
                    <div style="display:flex; flex-direction:column; gap:10px;">
                        ${abilities.map((ability, abilityIndex) => DebugModal._renderAbilityBlock(ability, abilityIndex)).join('')}
                    </div>
                `}
            </div>
        `;
    },

    renderInspectorTab: () => {
        const container = document.querySelector('[data-tab-pane="inspector"]');
        if (!container || !State.data) return;

        const players = State.data.players || [];
        const playerIdx = DebugModal._filters.selectedPlayer;
        const currentPlayer = players[playerIdx] || players[0] || null;
        const zone = DebugModal._filters.selectedZone;
        const search = DebugModal._filters.abilitySearch.trim();
        const visibleCards = DebugModal._collectVisibleCards(currentPlayer, zone)
            .filter((entry) => entry.card && entry.card.id !== -1 && entry.card.id !== -2)
            .filter((entry) => DebugModal._matchesSearch(entry, search));

        container.innerHTML = `
            <div style="display:flex; flex-direction:column; height:100%; padding:14px; gap:12px; overflow:auto;">
                ${renderStatusBanner(DebugModal._status)}
                <div style="display:grid; grid-template-columns:minmax(140px, 0.9fr) minmax(140px, 0.9fr) minmax(220px, 1.4fr); gap:8px;">
                    <div>
                        <label style="font-size:10px; opacity:0.7; display:block; margin-bottom:4px;">Player</label>
                        <select onchange="DebugModal.onPlayerChange(this.value)" style="width:100%; padding:6px; background:rgba(0,0,0,0.3); border:1px solid #475569; color:#fff; border-radius:6px; font-size:11px;">
                            ${players.map((player, index) => `<option value="${index}" ${index === playerIdx ? 'selected' : ''}>Player ${index + 1}${State.data.active_player === index ? ' [active]' : ''}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label style="font-size:10px; opacity:0.7; display:block; margin-bottom:4px;">Zone</label>
                        <select onchange="DebugModal.onZoneChange(this.value)" style="width:100%; padding:6px; background:rgba(0,0,0,0.3); border:1px solid #475569; color:#fff; border-radius:6px; font-size:11px;">
                            <option value="all" ${zone === 'all' ? 'selected' : ''}>All Zones</option>
                            <option value="stage" ${zone === 'stage' ? 'selected' : ''}>Stage</option>
                            <option value="live" ${zone === 'live' ? 'selected' : ''}>Live</option>
                            <option value="hand" ${zone === 'hand' ? 'selected' : ''}>Hand</option>
                            <option value="success" ${zone === 'success' ? 'selected' : ''}>Success</option>
                            <option value="energy" ${zone === 'energy' ? 'selected' : ''}>Energy</option>
                            <option value="discard" ${zone === 'discard' ? 'selected' : ''}>Discard</option>
                            <option value="looked" ${zone === 'looked' ? 'selected' : ''}>Looked</option>
                        </select>
                    </div>
                    <div>
                        <label style="font-size:10px; opacity:0.7; display:block; margin-bottom:4px;">Search</label>
                        <input type="text" placeholder="card, trigger, condition, pseudocode" value="${escapeHtml(DebugModal._filters.abilitySearch)}" oninput="DebugModal.onSearchChange(this.value)" style="width:100%; padding:8px; background:rgba(0,0,0,0.3); border:1px solid #475569; color:#fff; border-radius:6px; font-size:11px; box-sizing:border-box;">
                    </div>
                </div>

                ${DebugModal._renderSummaryCards(players, visibleCards)}
                ${DebugModal._renderPendingChoice()}
                ${currentPlayer ? DebugModal._renderZoneDiagnostics(currentPlayer) : ''}
                ${DebugModal._renderAbilityMatrix(visibleCards)}

                <div style="display:flex; flex-direction:column; gap:10px;">
                    <strong style="font-size:12px;">Card Detail</strong>
                    ${visibleCards.length === 0
                        ? '<div style="opacity:0.55; text-align:center; padding:24px; font-size:11px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:8px;">No cards match the current zone/search filters.</div>'
                        : visibleCards.map((entry, index) => DebugModal._renderCardInspector(entry, index)).join('')}
                </div>
            </div>
        `;
    },

    renderTraceTab: () => {
        const container = document.querySelector('[data-tab-pane="trace"]');
        if (!container || !State.data) return;

        const traceLines = DebugModal._snapshot?.trace_log || [];
        const bytecodeLines = DebugModal._snapshot?.bytecode_log || State.data.bytecode_log || [];

        container.innerHTML = `
            <div style="display:flex; flex-direction:column; height:100%; padding:14px; gap:12px; overflow:hidden;">
                ${renderStatusBanner(DebugModal._status)}
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:10px;">
                    ${renderScalarCell('debug_mode', DebugModal._snapshot?.debug_mode ? 'enabled' : 'disabled')}
                    ${renderScalarCell('trace lines', String(traceLines.length))}
                    ${renderScalarCell('bytecode lines', String(bytecodeLines.length))}
                    ${renderScalarCell('snapshot', DebugModal._snapshot ? 'backend /api/debug/snapshot' : 'viewer fallback')}
                </div>
                <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:12px; flex:1; min-height:0;">
                    <div style="display:flex; flex-direction:column; min-height:0; background:#020617; border:1px solid #1e293b; border-radius:8px; overflow:hidden;">
                        <div style="padding:8px 10px; border-bottom:1px solid #1e293b; font-size:11px; text-transform:uppercase; letter-spacing:0.06em; color:#7dd3fc;">Engine Trace</div>
                        <div id="debug-trace-log" style="flex:1; overflow:auto; font-family:'Cascadia Code', monospace;">${renderLogLines(traceLines, 'No engine trace has been captured. Enable Debug Mode, then execute game actions.')}</div>
                    </div>
                    <div style="display:flex; flex-direction:column; min-height:0; background:#020617; border:1px solid #1e293b; border-radius:8px; overflow:hidden;">
                        <div style="padding:8px 10px; border-bottom:1px solid #1e293b; font-size:11px; text-transform:uppercase; letter-spacing:0.06em; color:#86efac;">UI Bytecode Log</div>
                        <div id="debug-bytecode-log" style="flex:1; overflow:auto; font-family:'Cascadia Code', monospace;">${renderLogLines(bytecodeLines, 'No bytecode log has been captured for the current state.')}</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderStringTab: () => {
        const container = document.querySelector('[data-tab-pane="string"]');
        if (!container || !State.data) return;

        let serialized = '';
        try {
            serialized = JSON.stringify(DebugModal._getCheckpointPayload());
        } catch (error) {
            serialized = `Error: ${error.message}`;
        }

        container.innerHTML = `
            <div style="display:flex; flex-direction:column; height:100%; padding:14px; gap:10px; overflow:hidden;">
                ${renderStatusBanner(DebugModal._status)}
                <div style="font-size:11px; opacity:0.88; background:rgba(56,189,248,0.1); padding:10px 12px; border-radius:6px; border-left:3px solid #38bdf8; line-height:1.45;">
                    <strong>Raw GameState snapshot</strong><br/>
                    <span style="font-size:10px;">This payload comes from the backend snapshot route when available, so apply uses the same raw shape the Rust endpoint expects.</span><br/>
                    <span style="font-size:9px; font-family:'Cascadia Code', monospace; opacity:0.72;">${(serialized.length / 1024).toFixed(2)} KB</span>
                </div>
                <textarea id="debug-string-textarea" spellcheck="false" style="flex:1; width:100%; background:#020617; color:#dbeafe; border:1px solid #334155; border-radius:6px; padding:10px; font-family:'Cascadia Code', monospace; font-size:11px; resize:none; word-break:break-all; box-sizing:border-box;">${escapeHtml(serialized)}</textarea>
                <div style="display:flex; gap:8px; flex-wrap:wrap; font-size:11px;">
                    <button class="btn btn-primary" style="flex:1; min-width:110px;" onclick="DebugModal.copyStateString()">Copy</button>
                    <button class="btn btn-secondary" style="flex:1; min-width:110px;" onclick="DebugModal.loadStateString()">Apply</button>
                    <button class="btn btn-accent" style="flex:1; min-width:110px; background:var(--accent-gold); color:#000;" onclick="DebugModal.triggerFileLoad()">Load File</button>
                    <input type="file" id="debug-state-file" style="display:none;" accept=".json,.txt,.b64" onchange="DebugModal.loadStateFile(this)">
                </div>
            </div>
        `;
    },

    renderJsonTab: () => {
        const container = document.querySelector('[data-tab-pane="json"]');
        if (!container || !State.data) return;

        container.innerHTML = `
            <div style="display:flex; flex-direction:column; height:100%; padding:14px; gap:10px; overflow:hidden;">
                ${renderStatusBanner(DebugModal._status)}
                <div style="display:flex; gap:8px; flex-wrap:wrap;">
                    <button class="btn btn-secondary btn-xs" onclick="DebugModal.renderMinimalJSON()">Minimal</button>
                    <button class="btn btn-secondary btn-xs" onclick="DebugModal.renderCheckpointJSON()">Raw Snapshot</button>
                    <button class="btn btn-secondary btn-xs" onclick="DebugModal.renderRichJSON()">Viewer State</button>
                    <button class="btn btn-secondary btn-xs" onclick="DebugModal.copyJsonState()">Copy</button>
                    <button class="btn btn-secondary btn-xs" onclick="DebugModal.loadJsonFile()">Load File</button>
                    <button class="btn btn-primary btn-xs" onclick="DebugModal.applyJsonState()">Apply</button>
                    <input type="file" id="debug-json-file" style="display:none;" accept=".json,.txt,.b64" onchange="DebugModal.onJsonFileSelected(this)">
                    <span style="flex-grow:1;"></span>
                    <button class="btn btn-success btn-xs" onclick="DebugModal.exportGameWithHistory()">Export Game</button>
                    <button class="btn btn-accent btn-xs" style="background:#059669; color:#fff;" onclick="DebugModal.importGameWithHistory()">Import Game</button>
                </div>
                <textarea id="debug-json-textarea" spellcheck="false" style="flex:1; width:100%; background:#020617; color:#e2e8f0; border:1px solid #334155; border-radius:6px; padding:10px; font-family:'Cascadia Code', monospace; font-size:12px; resize:none; box-sizing:border-box;"></textarea>
                <div id="debug-json-result" style="font-size:10px; opacity:0.84; background:rgba(255,255,255,0.05); padding:8px; border-radius:6px; border-left:2px solid #666; display:none;"></div>
            </div>
        `;

        DebugModal.renderCheckpointJSON();
    },

    renderMinimalJSON: () => {
        if (!State.data) return;

        const getId = (entry) => {
            const card = DebugModal._normalizeCard(entry);
            return card?.id ?? card?.card_id ?? -1;
        };

        const minimal = {
            phase: State.data.phase,
            turn: State.data.turn,
            active_player: State.data.active_player,
            pending_choice: State.data.pending_choice || null,
            players: (State.data.players || []).map((player, index) => ({
                _label: `Player ${index + 1}`,
                score: player.score,
                stage: (player.stage || []).map(getId),
                live_zone: (player.live_zone || []).map(getId),
                hand: (player.hand || []).map(getId),
                energy: (player.energy || []).map(getId),
                discard: (player.discard || []).map(getId),
                success_lives: (player.success_lives || player.success_zone || player.success_pile || []).map(getId),
            })),
        };

        const textarea = document.getElementById('debug-json-textarea');
        if (textarea) textarea.value = JSON.stringify(minimal, null, 2);
    },

    renderCheckpointJSON: () => {
        const textarea = document.getElementById('debug-json-textarea');
        if (textarea) textarea.value = JSON.stringify(DebugModal._getCheckpointPayload(), null, 2);
    },

    renderFullJSON: () => {
        DebugModal.renderCheckpointJSON();
    },

    renderRichJSON: () => {
        const textarea = document.getElementById('debug-json-textarea');
        if (textarea) textarea.value = JSON.stringify(State.data, null, 2);
    },

    applyJsonState: async () => {
        const textarea = document.getElementById('debug-json-textarea');
        const result = document.getElementById('debug-json-result');
        if (!textarea || !result) return;

        try {
            const payload = DebugModal._decodeStateInput(textarea.value);
            const response = await DebugModal._applyCheckpointPayload(payload);
            const ok = Boolean(response?.ok);
            const message = DebugModal._extractApplyMessage(response);

            result.style.display = 'block';
            result.style.borderLeftColor = ok ? '#22c55e' : '#ef4444';
            result.textContent = message;
            DebugModal._setStatus(ok ? 'success' : 'error', message);

            if (ok) {
                await DebugModal.renderAll();
                if (window.Rendering) window.Rendering.render();
            }
        } catch (error) {
            const message = `Parse error: ${error.message}`;
            result.style.display = 'block';
            result.style.borderLeftColor = '#ef4444';
            result.textContent = message;
            DebugModal._setStatus('error', message);
        }
    },

    copyJsonState: () => {
        const textarea = document.getElementById('debug-json-textarea');
        if (!textarea) return;
        textarea.select();
        document.execCommand('copy');
        DebugModal._setStatus('success', 'JSON copied to clipboard.');
        DebugModal.renderJsonTab();
    },

    loadJsonFile: () => {
        const input = document.getElementById('debug-json-file');
        if (input) input.click();
    },

    onJsonFileSelected: (input) => {
        if (!input.files || !input.files[0]) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            const textarea = document.getElementById('debug-json-textarea');
            if (textarea) textarea.value = event.target.result;
            input.value = '';
        };
        reader.readAsText(input.files[0]);
    },

    triggerFileLoad: () => {
        const input = document.getElementById('debug-state-file');
        if (input) input.click();
    },

    loadStateFile: (input) => {
        if (!input.files || !input.files[0]) return;
        const reader = new FileReader();
        reader.onload = async (event) => {
            try {
                const payload = DebugModal._decodeStateInput(event.target.result);
                const response = await DebugModal._applyCheckpointPayload(payload);
                const ok = Boolean(response?.ok);
                const message = DebugModal._extractApplyMessage(response);
                DebugModal._setStatus(ok ? 'success' : 'error', message);
                if (ok) {
                    await DebugModal.renderAll();
                    if (window.Rendering) window.Rendering.render();
                } else {
                    DebugModal.renderStringTab();
                }
            } catch (error) {
                DebugModal._setStatus('error', `File error: ${error.message}`);
                DebugModal.renderStringTab();
            }
            input.value = '';
        };
        reader.readAsText(input.files[0]);
    },

    copyStateString: () => {
        const textarea = document.getElementById('debug-string-textarea');
        if (!textarea) return;
        textarea.select();
        document.execCommand('copy');
        DebugModal._setStatus('success', 'State snapshot copied to clipboard.');
        DebugModal.renderStringTab();
    },

    loadStateString: async () => {
        const textarea = document.getElementById('debug-string-textarea');
        const rawValue = textarea ? textarea.value : '';
        if (!rawValue) return;

        try {
            const payload = DebugModal._decodeStateInput(rawValue);
            const response = await DebugModal._applyCheckpointPayload(payload);
            const ok = Boolean(response?.ok);
            const message = DebugModal._extractApplyMessage(response);
            DebugModal._setStatus(ok ? 'success' : 'error', message);

            if (ok) {
                await DebugModal.renderAll();
                if (window.Rendering) window.Rendering.render();
            } else {
                DebugModal.renderStringTab();
            }
        } catch (error) {
            DebugModal._setStatus('error', `Decode error: ${error.message}`);
            DebugModal.renderStringTab();
        }
    },

    onPlayerChange: (value) => {
        DebugModal._filters.selectedPlayer = parseInt(value, 10);
        DebugModal.renderInspectorTab();
    },

    onZoneChange: (value) => {
        DebugModal._filters.selectedZone = value;
        DebugModal.renderInspectorTab();
    },

    onSearchChange: (value) => {
        DebugModal._filters.abilitySearch = value;
        DebugModal.renderInspectorTab();
    },

    rewind: async () => {
        const ok = await Network.rewind();
        if (!ok) {
            DebugModal._setStatus('error', 'Undo failed.');
            await DebugModal.renderAll();
            return;
        }
        DebugModal._clearStatus();
        await DebugModal.renderAll();
        if (window.Rendering) window.Rendering.render();
    },

    redo: async () => {
        const ok = await Network.redo();
        if (!ok) {
            DebugModal._setStatus('error', 'Redo failed.');
            await DebugModal.renderAll();
            return;
        }
        DebugModal._clearStatus();
        await DebugModal.renderAll();
        if (window.Rendering) window.Rendering.render();
    },

    toggleDebugMode: async () => {
        const ok = await Network.toggleDebugMode();
        DebugModal._setStatus(ok ? 'success' : 'error', ok ? 'Debug mode toggled.' : 'Toggle debug mode failed.');
        await DebugModal.renderAll();
    },

    exportGameWithHistory: async () => {
        try {
            const { GameExport } = await import('../replay_system.js');
            await GameExport.downloadGameAsJSON();
            DebugModal._setStatus('success', 'Game exported to file');
        } catch (e) {
            console.error('Export error:', e);
            DebugModal._setStatus('error', `Export failed: ${e.message}`);
        }
    },

    importGameWithHistory: async () => {
        try {
            const text = prompt('Paste exported game JSON:', '');
            if (!text || !text.trim()) return;
            const { GameExport } = await import('../replay_system.js');
            const success = await GameExport.importGameFromPaste(text);
            if (success) {
                DebugModal._clearStatus();
                await DebugModal.renderAll();
                if (window.Rendering) window.Rendering.render();
            } else {
                DebugModal._setStatus('error', 'Failed to import game');
            }
        } catch (e) {
            console.error('Import error:', e);
            DebugModal._setStatus('error', `Import failed: ${e.message}`);
        }
    },
};

window.DebugModal = DebugModal;
window.openDebugModal = () => DebugModal.openDebugModal();
window.closeDebugModal = () => DebugModal.closeDebugModal();
window.switchDebugTab = (tab) => DebugModal.switchTab(tab);

window.Modals = window.Modals || {};
window.Modals.openDebugModal = () => DebugModal.openDebugModal();
window.Modals.closeDebugModal = () => DebugModal.closeDebugModal();
window.Modals.toggleDebugMode = () => DebugModal.toggleDebugMode();
window.Modals.rewind = () => DebugModal.rewind();
window.Modals.redo = () => DebugModal.redo();
