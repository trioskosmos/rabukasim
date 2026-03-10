use super::constants::*;
use crate::core::enums::*;
use crate::core::logic::filter::map_filter_string_to_attr;
use crate::core::logic::{AbilityContext, CardDatabase, Cost, GameState, TriggerType};

pub fn pay_costs_transactional(
    state: &mut GameState,
    db: &CardDatabase,
    costs: &[Cost],
    ctx: &AbilityContext,
) -> bool {
    let p_idx = ctx.player_id as usize;

    // 1. Pre-check all costs
    for cost in costs {
        if cost.is_optional {
            continue;
        } // Skip optional costs in the transactional shell
        if !check_cost(state, db, p_idx, cost, ctx) {
            return false;
        }
    }

    // 2. Pay all costs
    // Note: Since we pre-checked, these should succeed.
    // If a cost has side effects that invalidate subsequent costs,
    // we might need a more complex rollback mechanism.
    for cost in costs {
        if cost.is_optional {
            continue;
        } // Skip optional costs in the transactional shell
        if !pay_cost(state, db, p_idx, cost, ctx) {
            // This shouldn't happen if check_cost is accurate
            return false;
        }
    }

    true
}

pub fn check_cost(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    cost: &Cost,
    ctx: &AbilityContext,
) -> bool {
    let player = &state.players[p_idx];
    let val = cost.value as usize;
    let mut attr: u64 = 0;
    if let Some(params) = cost.params.as_object() {
        let get_param = |key: &str| -> Option<&serde_json::Value> {
            params.get(key).or_else(|| params.get(&key.to_uppercase()))
        };
        if let Some(filter_str) = get_param("filter").and_then(|v| v.as_str()) {
            attr = map_filter_string_to_attr(filter_str);
        }
    }
    let result = match cost.cost_type {
        AbilityCostType::None => true,
        AbilityCostType::Energy => {
            let available =
                (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32;
            available >= cost.value
        }
        AbilityCostType::TapSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                !player.is_tapped(ctx.area_idx as usize)
            } else {
                false
            }
        }
        AbilityCostType::TapMember => {
            if val == 0 {
                // FALLBACK: TapMember(0) refers to self (Wait self)
                if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    player.stage[ctx.area_idx as usize] >= 0
                        && !player.is_tapped(ctx.area_idx as usize)
                } else {
                    false
                }
            } else {
                let untapped_count = (0..3)
                    .filter(|&i| player.stage[i] >= 0 && !player.is_tapped(i))
                    .count();
                untapped_count >= val
            }
        }
        AbilityCostType::TapEnergy => {
            let untap_count =
                player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones();
            untap_count as usize >= val
        }
        AbilityCostType::DiscardHand => {
            if (attr & FILTER_TYPE_MASK) != 0 {
                player
                    .hand
                    .iter()
                    .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr))
                    .count()
                    >= val
            } else {
                player.hand.len() >= val
            }
        }
        AbilityCostType::SacrificeSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                player.stage[ctx.area_idx as usize] >= 0
            } else {
                false
            }
        }
        AbilityCostType::RevealHand => {
            if (attr & FILTER_TYPE_MASK) != 0 {
                player
                    .hand
                    .iter()
                    .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr))
                    .count()
                    >= val
            } else {
                player.hand.len() >= val
            }
        }
        AbilityCostType::SacrificeUnder => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                player.stage_energy[ctx.area_idx as usize].len() >= val
            } else {
                false
            }
        }
        AbilityCostType::DiscardEnergy => player.energy_zone.len() >= val,
        AbilityCostType::ReturnMemberToDeck => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                player.stage[ctx.area_idx as usize] >= 0
            } else {
                false
            }
        }
        AbilityCostType::ReturnDiscardToDeck => player.discard.len() >= val,
        AbilityCostType::ReturnHand => {
            if (attr & FILTER_TYPE_MASK) != 0 {
                player
                    .stage
                    .iter()
                    .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr))
                    .count()
                    >= val
            } else {
                player.stage.iter().filter(|&&id| id >= 0).count() >= val
            }
        }
        AbilityCostType::DiscardMember => {
            if (attr & FILTER_TYPE_MASK) != 0 {
                player
                    .stage
                    .iter()
                    .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr))
                    .count()
                    >= val
            } else {
                player.stage.iter().filter(|&&id| id >= 0).count() >= val
            }
        }
        AbilityCostType::DiscardSuccessLive => {
            if (attr & FILTER_TYPE_MASK) != 0 {
                player
                    .success_lives
                    .iter()
                    .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, attr))
                    .count()
                    >= val
            } else {
                player.success_lives.len() >= val
            }
        }
        AbilityCostType::DiscardTopDeck => player.deck.len() >= val,
        _ => true,
    };

    if !result && state.debug.debug_ignore_conditions {
        if let Some(ref log) = state.debug.bypassed_conditions {
            if let Ok(mut bypassed) = log.0.lock() {
                bypassed.push(format!(
                    "BYPASS Cost: Type {:?}, Value {}",
                    cost.cost_type, cost.value
                ));
            }
        }
        return true;
    }
    result
}

pub fn pay_cost(
    state: &mut GameState,
    db: &CardDatabase,
    p_idx: usize,
    cost: &Cost,
    ctx: &AbilityContext,
) -> bool {
    let mut attr = 0;
    if let Some(params) = cost.params.as_object() {
        let get_param = |key: &str| -> Option<&serde_json::Value> {
            params.get(key).or_else(|| params.get(&key.to_uppercase()))
        };
        if let Some(filter_str) = get_param("filter").and_then(|v| v.as_str()) {
            attr = map_filter_string_to_attr(filter_str);
        }
    }

    if state.debug.debug_mode {
        // if state.debug.debug_mode {
        //     println!("[DEBUG] Paying Cost: {:?}, Value: {}, Card: {}", cost.cost_type, cost.value, ctx.source_card_id);
        // }
    }
    let result = match cost.cost_type {
        AbilityCostType::None => true,
        AbilityCostType::Energy => {
            let untap_indices: Vec<usize> = (0..state.players[p_idx].energy_zone.len())
                .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
                .take(cost.value as usize)
                .collect();
            if untap_indices.len() < cost.value as usize {
                return false;
            }
            for idx in untap_indices {
                state.players[p_idx].set_energy_tapped(idx, true);
            }
            true
        }
        AbilityCostType::TapSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                state.players[p_idx].set_tapped(ctx.area_idx as usize, true);
                true
            } else {
                false
            }
        }
        AbilityCostType::TapMember => {
            let player = &mut state.players[p_idx];
            let mut needed = cost.value as usize;
            if needed == 0 {
                // FALLBACK: Value 0 means "Tap Self"
                if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    player.set_tapped(ctx.area_idx as usize, true);
                    return true;
                }
                return false;
            }

            // Prioritize source slot if it's untapped (Wait Self behavior)
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let slot = ctx.area_idx as usize;
                if !player.is_tapped(slot) && player.stage[slot] >= 0 {
                    player.set_tapped(slot, true);
                    needed -= 1;
                }
            }

            if needed > 0 {
                for i in 0..3 {
                    if !player.is_tapped(i) && player.stage[i] >= 0 {
                        player.set_tapped(i, true);
                        needed -= 1;
                        if needed == 0 {
                            break;
                        }
                    }
                }
            }
            needed == 0
        }
        AbilityCostType::TapEnergy => {
            let player = &mut state.players[p_idx];
            let mut needed = cost.value as usize;
            if needed == 0 {
                return true;
            }
            for i in 0..player.energy_zone.len() {
                if !player.is_energy_tapped(i) {
                    player.set_energy_tapped(i, true);
                    needed -= 1;
                    if needed == 0 {
                        break;
                    }
                }
            }
            needed == 0
        }
        AbilityCostType::DiscardHand => {
            let count = cost.value as usize;
            let filter_attr = attr;

            if (filter_attr & FILTER_TYPE_MASK) != 0 {
                let mut to_discard = Vec::new();
                for &cid in &state.players[p_idx].hand {
                    if state.card_matches_filter(db, cid, filter_attr) {
                        to_discard.push(cid);
                        if to_discard.len() >= count {
                            break;
                        }
                    }
                }

                if to_discard.len() < count {
                    return false;
                }

                for cid in to_discard {
                    if let Some(pos) = state.players[p_idx]
                        .hand
                        .iter()
                        .position(|&x| x == cid)
                    {
                        state.players[p_idx].hand.remove(pos);
                        state.players[p_idx].discard.push(cid);
                    }
                }
                true
            } else {
                let player = &mut state.players[p_idx];
                if player.hand.len() < count {
                    return false;
                }
                for _ in 0..count {
                    if let Some(cid) = player.hand.pop() {
                        player.discard.push(cid);
                    }
                }
                true
            }
        }
        AbilityCostType::SacrificeSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let slot = ctx.area_idx as usize;
                let cid = state.players[p_idx].stage[slot];
                if cid >= 0 {
                    let mut leave_ctx = ctx.clone();
                    leave_ctx.source_card_id = cid;
                    leave_ctx.area_idx = ctx.area_idx;
                    state.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);

                    let player = &mut state.players[p_idx];
                    player.stage[slot] = -1;
                    player.discard.push(cid as i32);
                    let under_cards = std::mem::take(&mut player.stage_energy[slot]);
                    player.discard.extend(under_cards);
                    player.stage_energy_count[slot] = 0;
                    true
                } else {
                    false
                }
            } else {
                false
            }
        }
        AbilityCostType::RevealHand => {
            let val = cost.value as usize;
            let mut revealed = 0;
            // Clear previous looked_cards and revealed_cards
            state.players[p_idx].looked_cards.clear();
            state.players[p_idx].revealed_cards.clear();

            // Collect the first N cards that match the filter for auto-reveal
            let hand = state.players[p_idx].hand.to_vec();
            for cid in hand {
                if cid >= 0 && (attr == 0 || state.card_matches_filter(db, cid, attr)) {
                    state.players[p_idx].looked_cards.push(cid);
                    state.players[p_idx].revealed_cards.push(cid);
                    revealed += 1;
                    if revealed >= val {
                        break;
                    }
                }
            }
            revealed >= val
        }
        AbilityCostType::SacrificeUnder => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let player = &mut state.players[p_idx];
                let count = cost.value as usize;
                let slot = ctx.area_idx as usize;
                if player.stage_energy[slot].len() < count {
                    return false;
                }
                for _ in 0..count {
                    if let Some(cid) = player.stage_energy[slot].pop() {
                        player.discard.push(cid);
                    }
                }
                player.stage_energy_count[slot] = player.stage_energy[slot].len() as u8;
                true
            } else {
                false
            }
        }
        AbilityCostType::DiscardEnergy => {
            let player = &mut state.players[p_idx];
            let count = cost.value as usize;
            if player.energy_zone.len() < count {
                return false;
            }
            for _ in 0..count {
                if let Some(cid) = player.energy_zone.pop() {
                    player.discard.push(cid);
                }
            }
            true
        }
        AbilityCostType::ReturnMemberToDeck => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let slot = ctx.area_idx as usize;
                let cid = state.players[p_idx].stage[slot];
                if cid >= 0 {
                    let mut leave_ctx = ctx.clone();
                    leave_ctx.source_card_id = cid;
                    leave_ctx.area_idx = slot as i16;
                    state.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);

                    let player = &mut state.players[p_idx];
                    player.stage[slot] = -1;
                    player.deck.insert(0, cid as i32);
                    true
                } else {
                    false
                }
            } else {
                false
            }
        }
        AbilityCostType::ReturnDiscardToDeck => {
            let player = &mut state.players[p_idx];
            let count = cost.value as usize;
            if player.discard.len() < count {
                return false;
            }
            for _ in 0..count {
                if let Some(cid) = player.discard.pop() {
                    player.deck.push(cid);
                }
            }
            true
        }
        AbilityCostType::ReturnHand
        | AbilityCostType::DiscardMember
        | AbilityCostType::ReturnMemberToHand
        | AbilityCostType::ReturnMemberToDiscard => {
            let count = cost.value as usize;
            let filter_attr = attr;
            let is_discard = cost.cost_type == AbilityCostType::DiscardMember;
            let mut slots_to_move = Vec::new();
            for i in 0..3 {
                let cid = state.players[p_idx].stage[i];
                if cid >= 0
                    && ((filter_attr & FILTER_TYPE_MASK) == 0
                        || state.card_matches_filter(db, cid, filter_attr))
                {
                    slots_to_move.push(i);
                    if slots_to_move.len() >= count {
                        break;
                    }
                }
            }
            if slots_to_move.len() < count {
                return false;
            }
            for slot in slots_to_move {
                if let Some(old) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                    if is_discard {
                        state.players[p_idx].discard.push(old);
                    } else {
                        state.players[p_idx].hand.push(old);
                    }
                }
            }
            true
        }
        AbilityCostType::DiscardSuccessLive => {
            let count = cost.value as usize;
            let filter_attr = attr;
            let mut indices = Vec::new();
            for (idx, &cid) in state.players[p_idx].success_lives.iter().enumerate() {
                if (filter_attr & FILTER_TYPE_MASK) == 0
                    || state.card_matches_filter(db, cid, filter_attr)
                {
                    indices.push(idx);
                    if indices.len() >= count {
                        break;
                    }
                }
            }
            if indices.len() < count {
                return false;
            }
            for &idx in indices.iter().rev() {
                let cid = state.players[p_idx].success_lives.remove(idx);
                state.players[p_idx].discard.push(cid);
            }
            true
        }
        AbilityCostType::DiscardTopDeck => {
            let player = &mut state.players[p_idx];
            let count = cost.value as usize;
            if player.deck.len() < count {
                return false;
            }
            for _ in 0..count {
                if !player.deck.is_empty() {
                    let cid = player.deck.remove(0);
                    player.discard.push(cid);
                }
            }
            true
        }
        _ => false,
    };
    if !result && state.debug.debug_ignore_conditions {
        return true;
    }
    if state.debug.debug_mode && !result {
        println!("[DEBUG] Cost Payment FAILED");
    }
    result
}
