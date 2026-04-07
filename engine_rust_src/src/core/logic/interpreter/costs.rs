use super::constants::*;
use crate::core::enums::*;
use crate::core::logic::filter::map_filter_string_to_attr;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, Cost, GameState, TriggerType};

fn resolve_energy_cost(state: &GameState, db: &CardDatabase, p_idx: usize, cost: &Cost) -> i32 {
    let mut resolved_cost = cost.value;
    if let Some(params) = cost.params.as_object() {
        let reduction = params
            .get("REDUCTION")
            .or_else(|| params.get("reduction"))
            .and_then(|value| value.as_str())
            .unwrap_or("");
        if reduction.eq_ignore_ascii_case("COUNT_GROUPS") {
            let mut group_mask: u32 = 0;
            for &cid in &state.players[p_idx].stage {
                if cid < 0 {
                    continue;
                }
                if let Some(member) = db.get_member(cid) {
                    for &group_id in &member.groups {
                        if group_id < 32 {
                            group_mask |= 1u32 << group_id;
                        }
                    }
                }
            }
            resolved_cost = (resolved_cost - group_mask.count_ones() as i32).max(0);
        }
    }
    resolved_cost
}

fn untapped_energy_count(state: &GameState, p_idx: usize) -> usize {
    state.players[p_idx].energy_zone.len() - state.players[p_idx].tapped_energy_count() as usize
}

fn matches_filter_attr(state: &GameState, db: &CardDatabase, cid: i32, attr: u64) -> bool {
    attr & FILTER_TYPE_MASK == 0 || state.card_matches_filter(db, cid, attr)
}

fn dynamic_energy_cost_from_frame(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    frame: &AbilityFrame,
    ctx: &AbilityContext,
) -> Option<i32> {
    let comp = frame.components();
    if comp.opcode != O_PAY_ENERGY_DYNAMIC {
        return None;
    }

    let params = comp.params?;
    let source = params
        .get("source")
        .and_then(|value| value.as_str())
        .unwrap_or("");

    if source.eq_ignore_ascii_case("selected_live_score") {
        let selected_live_score = ctx
            .selected_cards
            .iter()
            .rev()
            .find_map(|&cid| db.get_live(cid).map(|live| live.score as i32))
            .unwrap_or(0);
        return Some(selected_live_score + comp.value);
    }

    Some(state.players[p_idx].score as i32 + comp.value)
}

fn prepend_single_card_to_deck(deck: &mut smallvec::SmallVec<[i32; 60]>, card_id: i32) {
    let mut new_deck = smallvec::SmallVec::<[i32; 60]>::new();
    new_deck.push(card_id);
    new_deck.extend(deck.drain(..));
    *deck = new_deck;
}

fn count_matching_cards<I>(state: &GameState, db: &CardDatabase, cards: I, attr: u64) -> usize
where
    I: IntoIterator<Item = i32>,
{
    cards
        .into_iter()
        .filter(|&cid| cid >= 0 && matches_filter_attr(state, db, cid, attr))
        .count()
}

fn source_stage_slot(ctx: &AbilityContext) -> Option<usize> {
    (ctx.area_idx >= 0 && ctx.area_idx < 3).then_some(ctx.area_idx as usize)
}

fn tap_member_cost_slots(
    state: &GameState,
    p_idx: usize,
    ctx: &AbilityContext,
    required: usize,
) -> Option<smallvec::SmallVec<[usize; 3]>> {
    let preferred_slot = source_stage_slot(ctx);
    let player = &state.players[p_idx];

    if required == 0 {
        let slot = preferred_slot?;
        if player.stage[slot] >= 0 && !player.is_tapped(slot) {
            let mut slots = smallvec::SmallVec::<[usize; 3]>::new();
            slots.push(slot);
            return Some(slots);
        }
        return None;
    }

    let mut slots = smallvec::SmallVec::<[usize; 3]>::new();
    if let Some(slot) = preferred_slot {
        if player.stage[slot] >= 0 && !player.is_tapped(slot) {
            slots.push(slot);
        }
    }

    for slot in 0..3 {
        if slots.len() >= required {
            break;
        }
        if Some(slot) == preferred_slot {
            continue;
        }
        if player.stage[slot] >= 0 && !player.is_tapped(slot) {
            slots.push(slot);
        }
    }

    (slots.len() >= required).then_some(slots)
}

fn can_pay_tap_member_cost(
    state: &GameState,
    p_idx: usize,
    ctx: &AbilityContext,
    required: usize,
) -> bool {
    tap_member_cost_slots(state, p_idx, ctx, required).is_some()
}

fn pay_tap_member_cost(
    state: &mut GameState,
    p_idx: usize,
    ctx: &AbilityContext,
    required: usize,
) -> bool {
    let Some(slots) = tap_member_cost_slots(state, p_idx, ctx, required) else {
        return false;
    };

    for slot in slots {
        state.players[p_idx].set_tapped(slot, true);
    }

    true
}

pub(crate) fn tap_first_untapped_energy(
    state: &GameState,
    p_idx: usize,
    count: usize,
) -> smallvec::SmallVec<[usize; 8]> {
    let tapped_indices = state.players[p_idx].get_untapped_energy_indices(count);
    tapped_indices
}

pub fn pay_costs_transactional(
    state: &mut GameState,
    db: &CardDatabase,
    costs: &[Cost],
    ctx: &mut AbilityContext,
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

pub fn pay_costs_transactional_including_optional(
    state: &mut GameState,
    db: &CardDatabase,
    costs: &[Cost],
    ctx: &mut AbilityContext,
) -> bool {
    let p_idx = ctx.player_id as usize;

    for cost in costs {
        if !check_cost(state, db, p_idx, cost, ctx) {
            return false;
        }
    }

    for cost in costs {
        if !pay_cost(state, db, p_idx, cost, ctx) {
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
    let has_filter = (attr & FILTER_TYPE_MASK) != 0;
    let result = match cost.cost_type {
        AbilityCostType::None => true,
        AbilityCostType::Energy => {
            untapped_energy_count(state, p_idx) as i32
                >= resolve_energy_cost(state, db, p_idx, cost)
        }
        AbilityCostType::TapSelf => {
            if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                !player.is_tapped(ctx.area_idx as usize)
            } else {
                false
            }
        }
        AbilityCostType::TapMember => can_pay_tap_member_cost(state, p_idx, ctx, val),
        AbilityCostType::TapEnergy => untapped_energy_count(state, p_idx) >= val,
        AbilityCostType::DiscardHand => {
            if has_filter {
                count_matching_cards(state, db, player.hand.iter().copied(), attr) >= val
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
            if has_filter {
                count_matching_cards(state, db, player.hand.iter().copied(), attr) >= val
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
            if has_filter {
                count_matching_cards(state, db, player.stage.iter().copied(), attr) >= val
            } else {
                player.stage.iter().filter(|&&id| id >= 0).count() >= val
            }
        }
        AbilityCostType::DiscardMember => {
            if has_filter {
                count_matching_cards(state, db, player.stage.iter().copied(), attr) >= val
            } else {
                player.stage.iter().filter(|&&id| id >= 0).count() >= val
            }
        }
        AbilityCostType::DiscardSuccessLive => {
            if has_filter {
                count_matching_cards(state, db, player.success_lives.iter().copied(), attr) >= val
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

pub fn check_frame_cost(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    frame: &AbilityFrame,
    ctx: &AbilityContext,
) -> bool {
    let comp = frame.components();
    if !comp.is_cost {
        return true;
    }

    match comp.opcode {
        O_PAY_ENERGY | O_ACTIVATE_ENERGY => {
            untapped_energy_count(state, p_idx) as i32 >= comp.value
        }
        O_PAY_ENERGY_DYNAMIC => {
            if comp.filter.is_optional {
                true
            } else {
                dynamic_energy_cost_from_frame(state, db, p_idx, frame, ctx)
                    .map(|resolved| untapped_energy_count(state, p_idx) as i32 >= resolved.max(0))
                    .unwrap_or(true)
            }
        }
        O_MOVE_TO_DISCARD | O_MOVE_TO_DECK | O_MOVE_MEMBER => {
            let source_zone = comp.slot.source_zone;
            let available = match source_zone {
                Zone::Hand => count_matching_cards(
                    state,
                    db,
                    state.players[p_idx].hand.iter().copied(),
                    comp.filter.to_attr(),
                ) as i32,
                Zone::Stage => count_matching_cards(
                    state,
                    db,
                    state.players[p_idx].stage.iter().copied(),
                    comp.filter.to_attr(),
                ) as i32,
                Zone::LiveSet | Zone::SuccessPile => count_matching_cards(
                    state,
                    db,
                    state.players[p_idx].success_lives.iter().copied(),
                    comp.filter.to_attr(),
                ) as i32,
                Zone::Energy => state.players[p_idx].energy_zone.len() as i32,
                Zone::Discard => state.players[p_idx].discard.len() as i32,
                Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
                    state.players[p_idx].deck.len() as i32
                }
                _ => 0,
            };
            available >= comp.value
        }
        O_SET_TAPPED | O_TAP_MEMBER => {
            let required = comp.value.max(0) as usize;
            can_pay_tap_member_cost(state, p_idx, ctx, required)
        }
        _ => true,
    }
}

pub fn pay_cost(
    state: &mut GameState,
    db: &CardDatabase,
    p_idx: usize,
    cost: &Cost,
    ctx: &mut AbilityContext,
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
            let resolved_cost = resolve_energy_cost(state, db, p_idx, cost);
            let untap_indices = tap_first_untapped_energy(state, p_idx, resolved_cost as usize);
            if untap_indices.len() < resolved_cost as usize {
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
        AbilityCostType::TapMember => pay_tap_member_cost(state, p_idx, ctx, cost.value.max(0) as usize),
        AbilityCostType::TapEnergy => {
            let untap_indices = tap_first_untapped_energy(state, p_idx, cost.value as usize);
            if untap_indices.len() < cost.value as usize {
                return false;
            }
            for idx in untap_indices {
                state.players[p_idx].set_energy_tapped(idx, true);
            }
            true
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
                    if let Some(pos) = state.players[p_idx].hand.iter().position(|&x| x == cid) {
                        state.players[p_idx].remove_hand_card(pos);
                        state.players[p_idx].push_discard_card(cid);
                        ctx.selected_cards.push(cid);
                    }
                }
                true
            } else {
                let player = &mut state.players[p_idx];
                if player.hand.len() < count {
                    return false;
                }
                for _ in 0..count {
                    if let Some(cid) = player.pop_hand_card() {
                        player.push_discard_card(cid);
                        ctx.selected_cards.push(cid);
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
                    player.push_discard_card(cid as i32);
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
                        player.push_discard_card(cid);
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
                if let Some(cid) = player.pop_energy_card() {
                    player.push_discard_card(cid);
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
                    prepend_single_card_to_deck(&mut player.deck, cid as i32);
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
                if let Some(cid) = player.pop_discard_card() {
                    player.push_deck_card(cid);
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
                        state.players[p_idx].push_discard_card(old);
                    } else {
                        state.players[p_idx].push_hand_card(old);
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
                state.players[p_idx].push_discard_card(cid);
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
                    let cid = player.remove_deck_card(0).unwrap();
                    player.push_discard_card(cid);
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
