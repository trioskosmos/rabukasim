export function getActionMeta(action) {
    return action?.metadata || action || {};
}

export function getActionValue(action, ...keys) {
    const meta = getActionMeta(action);
    for (const key of keys) {
        if (action && action[key] !== undefined) {
            return action[key];
        }
        if (meta && meta[key] !== undefined) {
            return meta[key];
        }
    }
    return undefined;
}

export function getDisplayCardId(action) {
    return getActionValue(action, 'card_id', 'source_card_id');
}

export function getActionName(action) {
    return getActionValue(action, 'display_name', 'name') || '';
}

export function getActionCategory(action) {
    return getActionValue(action, 'category', 'type') || '';
}

export function isSystemAction(action) {
    const name = getActionName(action);
    return action?.id === 0
        || getActionCategory(action) === 'SYSTEM'
        || action?.type === 'SYSTEM'
        || Boolean(name && (name.includes('End') || name.includes('終了')));
}

export function isMulliganAction(action) {
    return getActionCategory(action) === 'MULLIGAN' || action?.type === 'MULLIGAN';
}

export function ensureSourceCardId(action, state, perspectivePlayer) {
    if (!action) {
        return action;
    }

    if (action.source_card_id === undefined && action.card_id !== undefined) {
        action.source_card_id = action.card_id;
    }
    if (action.source_card_id !== undefined) {
        return action;
    }

    const sourceZone = getActionValue(action, 'source_zone');
    const sourceIndex = getActionValue(action, 'source_index', 'hand_idx', 'slot_idx', 'area_idx', 'discard_idx');
    const sourcePlayer = getActionValue(action, 'source_player');
    const playerIdx = sourcePlayer ?? perspectivePlayer;
    const player = state?.players?.[playerIdx];
    if (!player) {
        return action;
    }

    if (sourceZone === 'hand' && player.hand?.[sourceIndex]) {
        action.source_card_id = player.hand[sourceIndex].id;
    } else if (sourceZone === 'stage' && player.stage?.[sourceIndex]) {
        action.source_card_id = player.stage[sourceIndex].id;
    } else if (sourceZone === 'discard' && player.discard?.[sourceIndex]) {
        action.source_card_id = player.discard[sourceIndex].id ?? player.discard[sourceIndex];
    }
    return action;
}

export function findMatchingAction(actions, predicate) {
    return Array.isArray(actions) ? actions.find(predicate) || null : null;
}

export function getActionTargetElementIds(action, source, index) {
    const targetIds = new Set();
    const sourceZone = getActionValue(action, 'source_zone');
    const sourceIndex = getActionValue(action, 'source_index', 'hand_idx', 'slot_idx', 'area_idx', 'discard_idx');
    const targetZone = getActionValue(action, 'target_zone');
    const targetIndex = getActionValue(action, 'target_index', 'selection_index', 'hand_idx', 'slot_idx', 'area_idx', 'energy_idx');

    if (source !== sourceZone || index !== sourceIndex) {
        return targetIds;
    }

    if (targetZone === 'stage' && targetIndex !== undefined) {
        targetIds.add(`my-stage-slot-${targetIndex}`);
    } else if (targetZone === 'live') {
        if (targetIndex !== undefined) {
            targetIds.add(`my-live-slot-${targetIndex}`);
        } else {
            for (let liveIdx = 0; liveIdx < 3; liveIdx++) {
                targetIds.add(`my-live-slot-${liveIdx}`);
            }
        }
    } else if (targetZone === 'discard') {
        targetIds.add('my-discard-visual');
    } else if (targetZone === 'hand') {
        targetIds.add('my-hand');
    }

    return targetIds;
}

export function getPlayerPrefix(playerId, perspectivePlayer, fallbackPrefix = 'my') {
    if (playerId === undefined || playerId === null || playerId < 0) {
        return fallbackPrefix;
    }
    return playerId === perspectivePlayer ? 'my' : 'opp';
}

export function zoneElementId(prefix, zone, index) {
    if (!zone) {
        return null;
    }

    if (zone === 'hand' && index !== undefined) {
        return `${prefix}-hand-card-${index}`;
    }
    if (zone === 'stage' && index !== undefined) {
        return `${prefix}-stage-slot-${index}`;
    }
    if (zone === 'live') {
        return index !== undefined ? `${prefix}-live-slot-${index}` : `${prefix}-live`;
    }
    if (zone === 'energy' && index !== undefined) {
        return `${prefix}-energy-slot-${index}`;
    }
    if (zone === 'discard') {
        return `${prefix}-discard-visual`;
    }
    if (zone === 'selection' && index !== undefined) {
        return `select-list-item-${index}`;
    }
    return null;
}