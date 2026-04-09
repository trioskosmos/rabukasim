import { State } from '../state.js';
import { getAppBaseUrl } from '../constants.js';
import { TextEnricher } from './TextEnricher.js';

let sourceLoadPromise = null;
let sourceData = null;
let cardNoIndex = new Map();
let cardIdIndex = new Map();

const FLOW_OPS = new Set(['RETURN', 'JUMP', 'JUMP_IF_FALSE', 'META_RULE', 'NOP']);

const TRIGGER_LABELS = {
    NONE: 'Passive',
    CONSTANT: 'Constant',
    ACTIVATED: 'Activated',
    ON_PLAY: 'On Play',
    ON_LIVE_START: 'On Live Start',
    ON_LIVE_SUCCESS: 'On Live Success',
    ON_LEAVES: 'On Leaves',
    ON_MOVE_TO_DISCARD: 'On Move To Discard',
    ON_MEMBER_TAP: 'On Member Tap',
    ON_POSITION_CHANGE: 'On Position Change',
    ON_REVEAL: 'On Reveal',
    ON_ABILITY_RESOLVE: 'On Ability Resolve'
};

const CATEGORY_LABELS = {
    choice: 'Choice',
    cost: 'Cost',
    check: 'Check',
    action: 'Action',
    flow: 'Flow',
    meta: 'Meta'
};

const escapeHtml = (text) => String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');

const formatInlineValue = (value) => {
    if (value === null || value === undefined || value === '') return '';
    if (typeof value === 'object') {
        try {
            return JSON.stringify(value);
        } catch (err) {
            return '[object]';
        }
    }
    return String(value);
};

const describeZone = (zone) => {
    if (!zone) return '';
    return String(zone)
        .replace(/_/g, ' ')
        .toLowerCase()
        .replace(/\b([a-z])/g, (m) => m.toUpperCase());
};

const describeSlot = (slot = {}) => {
    const parts = [];
    if (slot.source_zone) parts.push(`from ${describeZone(slot.source_zone)}`);
    if (slot.target_slot) parts.push(`to ${describeZone(slot.target_slot)}`);
    if (slot.source_slot) parts.push(`source ${describeZone(slot.source_slot)}`);
    if (slot.target_zone) parts.push(`target ${describeZone(slot.target_zone)}`);
    return parts.join(' ');
};

const describeParams = (frame) => {
    const parts = [];
    const params = frame.params || {};
    const interesting = ['MIN', 'MAX', 'COUNT', 'card_type', 'group_id', 'unit_id', 'special_id', 'raw_cond', 'per_card', 'divisor', 'value'];

    for (const key of interesting) {
        if (params[key] !== undefined && params[key] !== null && params[key] !== '') {
            parts.push(`${key}=${params[key]}`);
        }
    }

    if (frame.value !== undefined && frame.value !== null && frame.value !== '') {
        parts.push(`value=${formatInlineValue(frame.value)}`);
    }

    if (frame.attr && typeof frame.attr === 'object') {
        const flags = [];
        const semanticKeys = ['group_id', 'unit_id', 'card_type', 'zone_mask', 'special_id', 'value_threshold', 'comparison', 'unique_names', 'is_le', 'is_cost_type'];
        for (const key of semanticKeys) {
            if (frame.attr[key] !== undefined && frame.attr[key] !== null && frame.attr[key] !== '') {
                parts.push(`${key}=${formatInlineValue(frame.attr[key])}`);
            }
        }
        if (frame.attr.is_optional) flags.push('optional');
        if (frame.attr.is_center) flags.push('center');
        if (frame.attr.is_self) flags.push('self');
        if (flags.length > 0) parts.push(flags.join(', '));
    }

    return parts.join(', ');
};

const categorizeFrame = (op) => {
    if (!op) return 'meta';
    if (FLOW_OPS.has(op)) return op === 'META_RULE' ? 'meta' : 'flow';
    if (op.startsWith('SELECT_') || op.startsWith('LOOK_') || op === 'ORDER_DECK' || op === 'REVEAL_CARDS' || op === 'REVEAL_UNTIL') return 'choice';
    if (op.startsWith('COUNT_') || op === 'HAS_' || op === 'TYPE_CHECK' || op === 'AREA_CHECK' || op === 'SCORE_COMPARE' || op === 'SCORE_TOTAL_CHECK' || op === 'HEART_LEAD' || op === 'NOT_HAS_EXCESS_HEART' || op === 'TARGET_MEMBER_HAS_NO_HEARTS') return 'check';
    if (op.startsWith('PAY_') || op.startsWith('MOVE_') || op.startsWith('RECOVER_') || op.startsWith('PLAY_') || op.startsWith('ADD_') || op.startsWith('BOOST_') || op.startsWith('SET_') || op.startsWith('ACTIVATE_') || op.startsWith('ENERGY_') || op.startsWith('TRANSFORM_') || op === 'SWAP_AREA' || op === 'GRANT_ABILITY' || op === 'PREVENT_BATON_TOUCH' || op === 'PREVENT_PLAY_TO_SLOT' || op === 'PREVENT_SET_TO_SUCCESS_PILE') return 'action';
    return 'action';
};

const describeFrame = (frame) => {
    const op = frame.op || 'UNKNOWN';
    const slotText = describeSlot(frame.slot);
    const paramsText = describeParams(frame);
    const value = frame.value !== undefined && frame.value !== null ? frame.value : null;
    const valueText = formatInlineValue(value);
    let summary = op;

    switch (op) {
        case 'MOVE_TO_DISCARD':
            summary = `Discard ${value ?? 1} card(s)${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'MOVE_TO_DECK':
            summary = `Move ${value ?? 1} card(s) to deck${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'DRAW':
            summary = `Draw ${value ?? 1} card(s)`;
            break;
        case 'DRAW_UNTIL':
            summary = `Draw until ${paramsText || value || 'condition met'}`;
            break;
        case 'LOOK_AND_CHOOSE':
            summary = `Look and choose ${value ?? 1} card(s)`;
            break;
        case 'LOOK_DECK':
            summary = `Look at the top ${value ?? 1} card(s) of the deck`;
            break;
        case 'SELECT_CARDS':
            summary = `Select ${value ?? 1} card(s)${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'SELECT_MEMBER':
            summary = `Select a member${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'SELECT_LIVE':
            summary = `Select a live card${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'SELECT_MODE':
            summary = `Choose between modes${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'MOVE_MEMBER':
            summary = `Move a member${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'SWAP_AREA':
            summary = `Swap two stage areas`;
            break;
        case 'RECOVER_LIVE':
            summary = `Recover a live card${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'RECOVER_MEMBER':
            summary = `Recover a member${slotText ? ` ${slotText}` : ''}`;
            break;
        case 'BOOST_SCORE':
            summary = `Score +${value ?? 1}`;
            break;
        case 'ADD_HEARTS':
            summary = `Gain ${value ?? 1} heart(s)`;
            break;
        case 'ADD_BLADES':
            summary = `Gain ${value ?? 1} blade(s)`;
            break;
        case 'ACTIVATE_ENERGY':
            summary = `Activate ${value ?? 1} energy`;
            break;
        case 'PAY_ENERGY':
        case 'PAY_ENERGY_DYNAMIC':
            summary = `Pay energy${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'COUNT_STAGE':
            summary = `Count stage${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'COUNT_DISCARD':
            summary = `Count discard${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'COUNT_HAND':
            summary = `Count hand${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'COUNT_LIVE_ZONE':
            summary = `Count live zone${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'COUNT_GROUP':
            summary = `Count cards with a group match${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'HEART_LEAD':
            summary = `Check heart lead${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'AREA_CHECK':
            summary = `Check area state${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'HAS_LIVE_CARD':
            summary = `Check for a live card`;
            break;
        case 'HAS_MEMBER':
            summary = `Check for a member`;
            break;
        case 'JUMP_IF_FALSE':
            summary = `If the previous check fails, jump`;
            break;
        case 'JUMP':
            summary = `Jump`;
            break;
        case 'RETURN':
            summary = `Return`;
            break;
        case 'META_RULE':
            summary = `Meta rule${paramsText ? ` (${paramsText})` : ''}`;
            break;
        case 'NOP':
            summary = `Placeholder / no-op`;
            break;
        default:
            if (paramsText) summary = `${op} (${paramsText})`;
            break;
    }

    if (op === 'SET_HEART_COST' && typeof value === 'object') {
        summary = `Set heart cost (${valueText})`;
    }

    return {
        category: categorizeFrame(op),
        op,
        summary,
        paramsText,
        raw: frame
    };
};

const summarizeEntry = (entry) => {
    const steps = (entry.frames || [])
        .map(describeFrame)
        .filter(step => step.category !== 'flow' && step.op !== 'META_RULE' && step.op !== 'NOP' && step.op !== 'RETURN');
    if (steps.length === 0) return 'No executable steps detected.';
    return steps.map(step => step.summary).join(' → ');
};

const renderFrameList = (entry) => {
    const frames = Array.isArray(entry.frames) ? entry.frames : [];
    if (frames.length === 0) {
        return '<div class="ability-inspector-empty">No frame steps recorded.</div>';
    }
    const items = frames.map((frame, idx) => {
        const desc = describeFrame(frame);
        const params = desc.paramsText ? `<div class="ability-frame-meta">${escapeHtml(desc.paramsText)}</div>` : '';
        return `<li class="ability-frame-step ability-frame-${escapeHtml(desc.category)}">
            <div class="ability-frame-head">
                <span class="ability-frame-idx">${idx + 1}</span>
                <span class="ability-frame-op">${escapeHtml(desc.op)}</span>
            </div>
            <div class="ability-frame-summary">${escapeHtml(desc.summary)}</div>
            ${params}
        </li>`;
    }).join('');
    return `<ol class="ability-frame-list">${items}</ol>`;
};

const renderSourceTextBlock = (label, text) => {
    if (!text) return '';
    return `
        <div class="ability-inspector-block">
            <div class="ability-inspector-label">${escapeHtml(label)}</div>
            <div class="ability-inspector-text">${TextEnricher.enrichAbilityText(text)}</div>
        </div>`;
};

const renderCardExamples = (examples = []) => {
    if (!examples || examples.length === 0) return '';
    const pills = examples.map(example => `<span class="ability-ref-pill">${escapeHtml(example)}</span>`).join('');
    return `
        <div class="ability-inspector-block">
            <div class="ability-inspector-label">Card Examples</div>
            <div class="ability-ref-list">${pills}</div>
        </div>`;
};

const renderPillList = (items = [], emptyLabel = 'none') => {
    if (!items || items.length === 0) {
        return `<span class="ability-inspector-empty-inline">${escapeHtml(emptyLabel)}</span>`;
    }
    return items.map((item) => `<span class="ability-ref-pill">${escapeHtml(item)}</span>`).join('');
};

const renderFlagGroup = (label, items = []) => {
    if (!items || items.length === 0) return '';
    return `
        <div class="ability-inspector-block">
            <div class="ability-inspector-label">${escapeHtml(label)}</div>
            <div class="ability-ref-list">${renderPillList(items)}</div>
        </div>
    `;
};

const renderPlayerStatusFlags = (player, playerLabel) => {
    if (!player) return '';

    const flags = [];
    if (player.prevent_activate > 0) flags.push('Cannot Activate');
    if (player.prevent_baton_touch > 0) flags.push('Cannot Baton Touch');
    if (player.cost_reduction && player.cost_reduction !== 0) flags.push(`Cost ${player.cost_reduction > 0 ? '-' : '+'}${Math.abs(player.cost_reduction)}`);

    const activeBladeBuffs = Array.isArray(player.blade_buffs)
        ? player.blade_buffs
            .map((val, idx) => (Number.isFinite(val) && val !== 0 ? `Blade ${idx + 1} ${val > 0 ? '+' : ''}${val}` : null))
            .filter(Boolean)
        : [];

    const activeHeartBuffs = Array.isArray(player.heart_buffs)
        ? player.heart_buffs.flatMap((row, rowIdx) => Array.isArray(row)
            ? row.map((count, idx) => count > 0 ? `Heart ${rowIdx + 1}.${idx + 1} +${count}` : null).filter(Boolean)
            : [])
        : [];

    const extras = [];
    if (activeBladeBuffs.length > 0) extras.push(renderFlagGroup('Blade Buffs', activeBladeBuffs));
    if (activeHeartBuffs.length > 0) extras.push(renderFlagGroup('Heart Buffs', activeHeartBuffs));

    return `
        <div class="ability-inspector-block">
            <div class="ability-inspector-label">${escapeHtml(playerLabel)} Status Flags</div>
            <div class="ability-ref-list">${renderPillList(flags, 'No active restrictions')}</div>
        </div>
        ${extras.join('')}
    `;
};

const renderStateSnapshot = (state) => {
    if (!state) return '';

    const players = Array.isArray(state.players) ? state.players : [];
    const perspectiveIdx = State.perspectivePlayer || 0;
    const currentPlayer = players[perspectiveIdx] || null;
    const opponentPlayer = players[1 - perspectiveIdx] || null;
    const pending = state.pending_choice || null;

    const scalarBits = [
        `Turn ${state.turn ?? '?'}`,
        `Phase ${state.phase ?? '?'}`,
        `Perspective P${perspectiveIdx + 1}`,
        `Legal actions ${Array.isArray(state.legal_actions) ? state.legal_actions.length : 0}`,
    ];

    if (State.hoveredCardId !== null && State.hoveredCardId !== undefined) {
        scalarBits.push(`Hovered Card ${State.hoveredCardId}`);
    }

    if (State.hoveredActionId !== null && State.hoveredActionId !== undefined) {
        scalarBits.push(`Hovered Action ${State.hoveredActionId}`);
    }

    if (pending) {
        const pendingBits = [];
        if (pending.choice_type !== undefined) pendingBits.push(`choice_type=${pending.choice_type}`);
        if (pending.choose_count !== undefined) pendingBits.push(`choose_count=${pending.choose_count}`);
        if (pending.v_remaining !== undefined) pendingBits.push(`v_remaining=${pending.v_remaining}`);
        if (pending.source_card_id !== undefined) pendingBits.push(`source_card_id=${pending.source_card_id}`);
        if (pending.text) pendingBits.push(String(pending.text));
        scalarBits.push(`Pending ${pendingBits.join(', ')}`);
    }

    return `
        <div class="ability-inspector-block">
            <div class="ability-inspector-label">Current State</div>
            <div class="ability-ref-list">${renderPillList(scalarBits)}</div>
        </div>
        ${renderPlayerStatusFlags(currentPlayer, 'You')}
        ${renderPlayerStatusFlags(opponentPlayer, 'Opponent')}
    `;
};

const resolveFocusCard = (card = null) => {
    if (card) return card;
    if (State.hoveredCardId !== null && State.hoveredCardId !== undefined) {
        const hovered = State.resolveCardData(State.hoveredCardId);
        if (hovered) return hovered;
    }

    const pending = State.data?.pending_choice || null;
    const fallbackId = pending?.source_card_id ?? pending?.card_id ?? pending?.params?.source_card_id ?? null;
    if (fallbackId !== null && fallbackId !== undefined) {
        const pendingCard = State.resolveCardData(fallbackId);
        if (pendingCard) return pendingCard;
    }

    return null;
};

const renderEntry = (entry, index) => {
    const refs = Array.isArray(entry.card_refs) ? entry.card_refs : [];
    const refText = refs.map(ref => `${ref.card_no}${ref.ability_index !== undefined ? `#${ref.ability_index}` : ''}`).join(', ');
    const trigger = TRIGGER_LABELS[entry.trigger] || entry.trigger || 'Unknown';
    const summary = summarizeEntry(entry);
    const sourceTexts = Array.isArray(entry.source_ability_texts) ? entry.source_ability_texts : [];
    const sourceBlocks = sourceTexts.map(block => {
        const jp = block.jp ? renderSourceTextBlock('Source JP', block.jp) : '';
        const en = block.en ? renderSourceTextBlock('Source EN', block.en) : '';
        const examples = renderCardExamples(block.card_examples || []);
        return `<div class="ability-source-block">${jp}${en}${examples}</div>`;
    }).join('');

    return `
        <details class="ability-inspector-entry" ${index === 0 ? 'open' : ''}>
            <summary class="ability-inspector-summary-line">
                <span class="ability-inspector-trigger">${escapeHtml(trigger)}</span>
                <span class="ability-inspector-flow">${escapeHtml(summary)}</span>
                <span class="ability-inspector-refcount">${refs.length} ref(s)</span>
            </summary>
            <div class="ability-inspector-body">
                ${renderSourceTextBlock('Primary JP', entry.primary_text_jp)}
                ${renderSourceTextBlock('Primary EN', entry.primary_text_en)}
                <div class="ability-inspector-block">
                    <div class="ability-inspector-label">Card Refs</div>
                    <div class="ability-ref-list">${escapeHtml(refText || 'None')}</div>
                </div>
                <div class="ability-inspector-block">
                    <div class="ability-inspector-label">Frame Flow</div>
                    <div class="ability-inspector-overview">${escapeHtml(summary)}</div>
                </div>
                <div class="ability-inspector-block">
                    <div class="ability-inspector-label">Frame Steps</div>
                    ${renderFrameList(entry)}
                </div>
                ${sourceBlocks}
            </div>
        </details>`;
};

const buildIndexes = (abilities) => {
    cardNoIndex = new Map();
    cardIdIndex = new Map();

    abilities.forEach((entry, entryIndex) => {
        for (const ref of (entry.card_refs || [])) {
            if (ref.card_no) {
                const key = String(ref.card_no).toUpperCase();
                if (!cardNoIndex.has(key)) cardNoIndex.set(key, []);
                cardNoIndex.get(key).push(entryIndex);
            }
            if (ref.card_id !== undefined && ref.card_id !== null) {
                const key = Number(ref.card_id);
                if (!cardIdIndex.has(key)) cardIdIndex.set(key, []);
                cardIdIndex.get(key).push(entryIndex);
            }
        }
    });
};

export const AbilityInspector = {
    ensureLoaded: async () => {
        if (sourceData) return sourceData;
        if (!sourceLoadPromise) {
            sourceLoadPromise = (async () => {
                const base = getAppBaseUrl();
                const res = await fetch(`${base}data/ability_frame_source.json`);
                if (!res.ok) {
                    throw new Error(`Failed to load ability frame source: ${res.status}`);
                }
                const json = await res.json();
                sourceData = json;
                buildIndexes(json.abilities || []);
                return sourceData;
            })();
        }
        return sourceLoadPromise;
    },

    getEntriesForCard: (card) => {
        if (!card || !sourceData) return [];
        const results = new Set();
        const cardNo = card.card_no ? String(card.card_no).toUpperCase() : null;
        const cardId = card.card_id !== undefined ? Number(card.card_id) : (card.id !== undefined ? Number(card.id) : null);

        if (cardNo && cardNoIndex.has(cardNo)) {
            for (const idx of cardNoIndex.get(cardNo)) results.add(idx);
        }
        if (cardId !== null && cardIdIndex.has(cardId)) {
            for (const idx of cardIdIndex.get(cardId)) results.add(idx);
        }

        return [...results].sort((a, b) => a - b).map(idx => sourceData.abilities[idx]);
    },

    renderCardInspector: (card) => {
        if (!sourceData) {
            return `<div class="ability-inspector-loading">Loading frame source…</div>`;
        }
        const entries = AbilityInspector.getEntriesForCard(card);
        if (!entries.length) {
            return `<div class="ability-inspector-empty">No authored frame source found for this card.</div>`;
        }
        return `<div class="ability-inspector">${entries.map((entry, idx) => renderEntry(entry, idx)).join('')}</div>`;
    },

    renderCardInspectorAsync: async (card) => {
        await AbilityInspector.ensureLoaded();
        return AbilityInspector.renderCardInspector(card);
    },

    renderSidebarExamView: (card = null, state = State.data) => {
        const panel = document.getElementById('ability-exam-panel');
        if (!panel) return '';

        const focusCard = resolveFocusCard(card);
        const focusCardId = focusCard && (focusCard.id !== undefined ? focusCard.id : focusCard.card_id);
        const focusTitle = focusCard?.name || focusCard?.card_name || 'Ability Examination';
        const focusCardLine = focusCardId !== undefined && focusCardId !== null
            ? `${focusTitle} (ID: ${focusCardId})`
            : focusTitle;

        const body = `
            <div class="ability-exam-shell">
                <div class="ability-inspector-block">
                    <div class="ability-inspector-label">Focused Ability</div>
                    <div class="ability-inspector-overview">${escapeHtml(focusCardLine)}</div>
                </div>
                ${renderStateSnapshot(state)}
                ${focusCard ? AbilityInspector.renderCardInspector(focusCard) : '<div class="ability-inspector-empty">Hover a card or action to inspect its authored frames.</div>'}
            </div>
        `;

        panel.innerHTML = body;
        return body;
    },

    renderSidebarExamViewAsync: async (card = null, state = State.data) => {
        await AbilityInspector.ensureLoaded().catch(() => null);
        return AbilityInspector.renderSidebarExamView(card, state);
    },

    describeFrame,
    summarizeEntry
};
