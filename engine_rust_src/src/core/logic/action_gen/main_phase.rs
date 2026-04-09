use crate::core::enums::*;
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::constants::{DECK_TOP_LOOK_WINDOW, FILTER_COLOR_SHIFT_R5};
use crate::core::logic::interpreter::costs::check_frame_cost;
use crate::core::logic::{AbilityContext, ActionReceiver, CardDatabase, GameState};
use crate::core::types::{MAX_HAND_SIZE, STAGE_SLOT_COUNT};
use std::time::Instant;

pub struct MainPhaseGenerator;

fn legal_profile_enabled() -> bool {
    std::env::var("BENCH_PROFILE_LEGAL_ACTIONS")
        .ok()
        .map(|value| {
            let value = value.trim();
            !matches!(value, "0" | "false" | "FALSE" | "off" | "OFF")
        })
        .unwrap_or(false)
}

fn legal_profile_threshold_us() -> u64 {
    std::env::var("BENCH_PROFILE_STEP_THRESHOLD_US")
        .ok()
        .and_then(|value| value.parse().ok())
        .unwrap_or(2000)
}

fn ability_requires_deck_top_window(ab: &crate::core::logic::Ability) -> bool {
    ab.runtime_has_deck_top_window()
}

fn ability_needs_condition_check(ab: &crate::core::logic::Ability) -> bool {
    ab.runtime_has_activation_conditions()
}

fn ability_is_trivially_activatable(ab: &crate::core::logic::Ability) -> bool {
    ab.per_turn_limit() == 0
        && ab.costs.is_empty()
        && !ability_needs_condition_check(ab)
        && !ab.runtime_has_frame_cost_checks()
        && !ab.runtime_has_look_choose_checks()
        && !ability_requires_deck_top_window(ab)
}

fn projected_aura_mask(slot_idx: i16, secondary_slot_idx: i16) -> usize {
    let mut mask = 0u8;

    for candidate_slot in [slot_idx, secondary_slot_idx] {
        if candidate_slot >= 0 && candidate_slot < STAGE_SLOT_COUNT as i16 {
            mask |= 1u8 << (candidate_slot as u32);
        }
    }

    mask as usize
}

fn projected_aura_for_slots<'a>(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    slot_idx: i16,
    secondary_slot_idx: i16,
    cache: &'a mut [Option<crate::core::logic::rules::BoardAura>; 8],
) -> &'a crate::core::logic::rules::BoardAura {
    let cache_idx = projected_aura_mask(slot_idx, secondary_slot_idx);
    cache[cache_idx].get_or_insert_with(|| {
        crate::core::logic::rules::calculate_projected_board_aura(
            state,
            p_idx,
            db,
            slot_idx,
            secondary_slot_idx,
        )
    })
}

fn finalize_hand_play_cost(db: &CardDatabase, raw_cost: i32) -> i32 {
    if db.is_truly_vanilla() {
        raw_cost.max(0)
    } else {
        raw_cost
    }
}

fn stage_card_may_prevent_baton_touch(card: &crate::core::logic::card_db::MemberCard) -> bool {
    let opcode_bit = 1u128 << (O_PREVENT_BATON_TOUCH as u32 % 128);
    (card.ability_opcodes_mask & opcode_bit) != 0
}

fn ability_costs_payable(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    ctx: &AbilityContext,
    ab: &crate::core::logic::Ability,
) -> bool {
    if !ab.costs.iter().all(|c| state.check_cost(db, p_idx, c, ctx)) {
        return false;
    }

    let frames = ab.resolved_frames();

    if ab.runtime_has_frame_cost_checks() {
        for frame in frames.iter() {
            let frame_data = frame.components();
            let implicit_deck_cost = matches!(
                frame_data.opcode,
                O_MOVE_MEMBER | O_MOVE_TO_DISCARD | O_MOVE_TO_DECK
            ) && matches!(
                frame_data.slot.source_zone,
                Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
            );
            if frame.is_cost() || implicit_deck_cost {
                if !check_frame_cost(state, db, p_idx, frame, ctx) {
                    return false;
                }
            }
        }
    }

    if ab.runtime_has_look_choose_checks() {
        for frame in frames.iter() {
            if frame.opcode() == crate::core::generated_constants::O_LOOK_AND_CHOOSE {
                let is_cost = frame.is_cost();
                if is_cost {
                    continue;
                }

                let choose_count: i32 = frame.look_choose().choose_count as i32;
                let required = choose_count.max(1) as usize;
                let slot = frame.dslot();
                let available = match slot.source_zone {
                    Zone::Hand => state.players[p_idx].hand.len(),
                    Zone::Discard => state.players[p_idx].discard.len(),
                    Zone::Stage => {
                        state.players[p_idx].stage.iter().filter(|&&cid| cid >= 0).count()
                    }
                    Zone::LiveSet | Zone::SuccessPile => state.players[p_idx].success_lives.len(),
                    Zone::Yell => state.players[p_idx].yell_cards.len(),
                    Zone::Energy => state.players[p_idx].energy_zone.len(),
                    Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
                        state.players[p_idx].deck.len() + state.players[p_idx].discard.len()
                    }
                };

                if available < required {
                    return false;
                }
            }
        }
    }

    if ability_requires_deck_top_window(ab)
        && state.players[p_idx].deck.len() < DECK_TOP_LOOK_WINDOW
    {
        return false;
    }

    true
}

impl ActionGenerator for MainPhaseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let _condition_cache_scope = crate::core::logic::interpreter::conditions::ConditionEvalCacheScope::activate();
        let _filter_cache_scope = crate::core::logic::game_rules_ext::FilterMatchCacheScope::activate();
        let profile_enabled = legal_profile_enabled();
        let profile_start = if profile_enabled {
            Some(Instant::now())
        } else {
            None
        };
        let player = &state.players[p_idx];
        let abilities_enabled = !db.is_vanilla;
        receiver.add_action(0);

        // Optimization 3: Bitmask-based Energy counting
        let available_energy =
            player.energy_zone.len() as i32 - player.tapped_energy_count() as i32;
        let prevent_activate = player.prevent_activate();
        let prevent_play_to_slot_mask = player.prevent_play_to_slot_mask();
        let prevent_baton_touch = player.prevent_baton_touch();
        let board_has_dynamic_cost_modifiers = !player.board_aura.cost_modifiers.is_empty();
        let board_has_slot_cost_modifiers = player.board_aura.slot_cost_modifiers != [0; STAGE_SLOT_COUNT];
        let t_granted_cost_scan = profile_enabled.then(Instant::now);
        let hand_has_granted_cost_modifiers: [bool; MAX_HAND_SIZE] = if player.granted_abilities.is_empty() {
            [false; MAX_HAND_SIZE]
        } else {
            let mut granted_costs = [false; MAX_HAND_SIZE];
            for (hand_idx, &cid) in player.hand.iter().enumerate().take(MAX_HAND_SIZE) {
                granted_costs[hand_idx] = player
                    .granted_abilities
                    .iter()
                    .any(|(target_cid, _, _)| *target_cid == cid);
            }
            granted_costs
        };
        let granted_cost_modifier_us = t_granted_cost_scan
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        // Pre-calculate stage slot costs, data, and restrictions (CRITICAL OPTIMIZATION)
        let mut stage_data = [None; STAGE_SLOT_COUNT];
        let mut slot_prevents_baton_touch = [false; STAGE_SLOT_COUNT];
        let mut has_empty_slots = [false; STAGE_SLOT_COUNT];
        let mut single_slot_cost_deltas = [0i32; STAGE_SLOT_COUNT];
        let mut single_slot_requires_full_cost = [false; STAGE_SLOT_COUNT];
        let mut multi_slot_cost_deltas = [[0i32; STAGE_SLOT_COUNT]; STAGE_SLOT_COUNT];
        let mut multi_slot_requires_full_cost = [[true; STAGE_SLOT_COUNT]; STAGE_SLOT_COUNT];
        let t_slot_projection = profile_enabled.then(Instant::now);
        let mut projected_aura_cache: [Option<crate::core::logic::rules::BoardAura>; 8] =
            std::array::from_fn(|_| None);

        let can_skip_projected_aura = prevent_baton_touch == 0
            && !board_has_dynamic_cost_modifiers
            && !board_has_slot_cost_modifiers
            && player.granted_abilities.is_empty();

        for s in 0..STAGE_SLOT_COUNT {
            if player.stage[s] >= 0 {
                if let Some(prev) = db.get_member(player.stage[s]) {
                    stage_data[s] = Some(prev);
                    let use_simple_replacement_cost = can_skip_projected_aura
                        && !stage_card_may_prevent_baton_touch(prev);

                    if use_simple_replacement_cost {
                        slot_prevents_baton_touch[s] = false;
                        single_slot_cost_deltas[s] = -(prev.cost as i32);
                        single_slot_requires_full_cost[s] = false;
                    } else {
                        slot_prevents_baton_touch[s] =
                            GameState::has_restriction(state, p_idx, s, O_PREVENT_BATON_TOUCH, db);

                        let projected_aura = projected_aura_for_slots(
                            state,
                            db,
                            p_idx,
                            s as i16,
                            -1,
                            &mut projected_aura_cache,
                        );
                        single_slot_cost_deltas[s] =
                            projected_aura.slot_cost_modifiers[s] as i32 - prev.cost as i32;
                        single_slot_requires_full_cost[s] = !projected_aura.cost_modifiers.is_empty();
                    }

                    for other_slot in 0..STAGE_SLOT_COUNT {
                        if other_slot == s || player.stage[other_slot] < 0 {
                            continue;
                        }
                        let Some(other_prev) = stage_data[other_slot].or_else(|| db.get_member(player.stage[other_slot])) else {
                            continue;
                        };
                        if use_simple_replacement_cost
                            && !stage_card_may_prevent_baton_touch(other_prev)
                        {
                            multi_slot_cost_deltas[s][other_slot] =
                                -(prev.cost as i32) - other_prev.cost as i32;
                            multi_slot_requires_full_cost[s][other_slot] = false;
                        } else {
                            let projected_aura = projected_aura_for_slots(
                                state,
                                db,
                                p_idx,
                                s as i16,
                                other_slot as i16,
                                &mut projected_aura_cache,
                            );
                            multi_slot_cost_deltas[s][other_slot] = projected_aura.slot_cost_modifiers[s]
                                as i32
                                - prev.cost as i32
                                - other_prev.cost as i32;
                            multi_slot_requires_full_cost[s][other_slot] =
                                !projected_aura.cost_modifiers.is_empty();
                        }
                    }
                }
            } else {
                has_empty_slots[s] = true;
                single_slot_cost_deltas[s] = player.board_aura.slot_cost_modifiers[s] as i32;
                single_slot_requires_full_cost[s] = board_has_dynamic_cost_modifiers;
            }
        }
        let slot_projection_us = t_slot_projection
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);
        let precompute_us = granted_cost_modifier_us + slot_projection_us;

        let t_play_hand = profile_enabled.then(Instant::now);
        // 1. Play Member from Hand
        for (hand_idx, &cid) in player.hand.iter().enumerate() {
            let i = hand_idx as i32;
            if i >= MAX_HAND_SIZE as i32 {
                break;
            } // Safety cap

            if let Some(card) = db.get_member(cid) {
                let hand_base_cost = crate::core::logic::rules::get_member_hand_base_cost(
                    state,
                    p_idx,
                    cid,
                    db,
                    0,
                    hand_idx,
                );
                for slot_idx in 0..STAGE_SLOT_COUNT {
                    if player.is_moved(slot_idx) {
                        continue;
                    }

                    // Check play restriction
                    if (prevent_play_to_slot_mask & (1 << slot_idx)) != 0 {
                        continue;
                    }

                    if player.stage[slot_idx] >= 0 {
                        // Check global baton touch prevention
                        if prevent_baton_touch > 0 {
                            continue;
                        }
                        // Check card-specific restriction (cached)
                        if slot_prevents_baton_touch[slot_idx] {
                            continue;
                        }
                    }

                    let cost = if !single_slot_requires_full_cost[slot_idx]
                        && !hand_has_granted_cost_modifiers
                            .get(hand_idx)
                            .copied()
                            .unwrap_or(false)
                    {
                        finalize_hand_play_cost(
                            db,
                            hand_base_cost + single_slot_cost_deltas[slot_idx],
                        )
                    } else {
                        let projected_aura = if player.stage[slot_idx] >= 0 {
                            Some(projected_aura_for_slots(
                                state,
                                db,
                                p_idx,
                                slot_idx as i16,
                                -1,
                                &mut projected_aura_cache,
                            ))
                        } else {
                            None
                        };
                        crate::core::logic::rules::get_member_cost_from_hand_base_and_aura(
                            state,
                            p_idx,
                            cid,
                            slot_idx as i16,
                            -1,
                            db,
                            0,
                            hand_base_cost,
                            projected_aura,
                        )
                    };

                    if cost <= available_energy {
                        // Check for OnPlay choices (Limit to first 10 cards to stay within Action ID space)
                        let mut has_choice_on_play = false;
                        if abilities_enabled && hand_idx < 10 && card.has_on_play_choice {
                            for ab in &card.abilities {
                                if ab.trigger == TriggerType::OnPlay && ab.choice_flags != 0 {
                                    // OPTIMIZATION: Use pre-computed flags
                                    let has_select_mode = (ab.choice_flags & CHOICE_FLAG_MODE) != 0;
                                    let has_color_select =
                                        (ab.choice_flags & CHOICE_FLAG_COLOR) != 0;

                                    if has_color_select {
                                        has_choice_on_play = true;
                                        // Extract color_mask from ability effects to filter choices
                                        let mut allowed_colors: Vec<i32> = (0..6).collect();
                                        for effect in &ab.effects {
                                            if effect.runtime_opcode == crate::core::generated_constants::O_COLOR_SELECT {
                                                let color_mask = ((effect.runtime_attr >> FILTER_COLOR_SHIFT_R5) & 0x7F) as u8;
                                                if color_mask != 0 {
                                                    allowed_colors = (0..6)
                                                        .filter(|&c| (color_mask & (1 << c)) != 0)
                                                        .map(|c| c as i32)
                                                        .collect();
                                                }
                                                break;
                                            }
                                        }
                                        for &c in &allowed_colors {
                                            let choice_aid =
                                                crate::core::logic::ACTION_BASE_HAND_CHOICE
                                                    + (i * 100)
                                                    + (slot_idx as i32 * 10)
                                                    + c;
                                            receiver.add_action(choice_aid as usize);
                                        }
                                    } else if has_select_mode {
                                        has_choice_on_play = true;
                                        let count = ab.choice_count as i32;
                                        for c in 0..count {
                                            let choice_aid =
                                                crate::core::logic::ACTION_BASE_HAND_CHOICE
                                                    + (i * 100)
                                                    + (slot_idx as i32 * 10)
                                                    + (c as i32);
                                            receiver.add_action(choice_aid as usize);
                                        }
                                    }
                                }
                            }
                        }

                        if !has_choice_on_play {
                            let aid =
                                crate::core::logic::ACTION_BASE_HAND + (i * 10) + slot_idx as i32;
                            receiver.add_action(aid as usize);
                        }
                    }

                    // Double Baton Touch (Card 560 etc.)
                    // Move OUTSIDE single-slot affordability check
                    // Note: multi-baton abilities won't exist in vanilla mode cards (empty abilities list)
                    if card.has_multi_baton && hand_idx < 10 && player.stage[slot_idx] >= 0 {
                        // Check baton touch prevention for this primary slot
                        if prevent_baton_touch > 0 {
                            continue;
                        }
                        if slot_prevents_baton_touch[slot_idx] {
                            continue;
                        }

                        for other_slot in 0..STAGE_SLOT_COUNT {
                            if other_slot == slot_idx {
                                continue;
                            }
                            if player.stage[other_slot] < 0 {
                                continue;
                            }
                            if player.is_moved(other_slot) {
                                continue;
                            }
                            // Also check baton touch prevention for second slot
                            if slot_prevents_baton_touch[other_slot] {
                                continue;
                            }

                            let combined_cost = if !multi_slot_requires_full_cost[slot_idx][other_slot]
                                && !hand_has_granted_cost_modifiers
                                    .get(hand_idx)
                                    .copied()
                                    .unwrap_or(false)
                            {
                                finalize_hand_play_cost(
                                    db,
                                    hand_base_cost + multi_slot_cost_deltas[slot_idx][other_slot],
                                )
                            } else {
                                let projected_aura = Some(projected_aura_for_slots(
                                    state,
                                    db,
                                    p_idx,
                                    slot_idx as i16,
                                    other_slot as i16,
                                    &mut projected_aura_cache,
                                ));
                                crate::core::logic::rules::get_member_cost_from_hand_base_and_aura(
                                    state,
                                    p_idx,
                                    cid,
                                    slot_idx as i16,
                                    other_slot as i16,
                                    db,
                                    0,
                                    hand_base_cost,
                                    projected_aura,
                                )
                            };
                            if combined_cost <= available_energy {
                                let is_next = other_slot == (slot_idx + 1) % STAGE_SLOT_COUNT;
                                let combo_idx = slot_idx * 2 + (if is_next { 1 } else { 0 });
                                let aid = crate::core::logic::ACTION_BASE_HAND
                                    + (i * 10)
                                    + 3
                                    + combo_idx as i32;
                                receiver.add_action(aid as usize);
                            }
                        }
                    }
                }
            }
        }
        let play_hand_us = t_play_hand
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        let t_stage_abilities = profile_enabled.then(Instant::now);
        // 2. Activate Stage Ability
        if abilities_enabled && prevent_activate == 0 {
            for slot_idx in 0..STAGE_SLOT_COUNT {
                let cid = player.stage[slot_idx];
                if cid >= 0 {
                    if let Some(card) = stage_data[slot_idx] {
                        if card.has_activated_stage {
                            for (ab_idx, ab) in card.abilities.iter().enumerate() {
                                if ab.trigger == TriggerType::Activated {
                                    if ability_is_trivially_activatable(ab) {
                                        let ab_aid = crate::core::logic::ACTION_BASE_STAGE
                                            + (slot_idx as i32 * 100)
                                            + (ab_idx as i32 * 10);
                                        receiver.add_action(ab_aid as usize);
                                        continue;
                                    }

                                    let ctx = AbilityContext {
                                        player_id: state.current_player,
                                        activator_id: state.current_player,
                                        area_idx: slot_idx as i16,
                                        source_card_id: cid,
                                        choice_index: -1,
                                        ..Default::default()
                                    };
                                    let mut ctx = ctx;
                                    ctx.capture_state_raw(state.phase, state.current_player);

                                    let cond_ok = !ability_needs_condition_check(ab)
                                        || ab.conditions
                                            .iter()
                                            .filter(|condition| {
                                                !matches!(
                                                    condition.condition_type,
                                                    ConditionType::SumValue | ConditionType::DiscardedCards
                                                )
                                            })
                                            .all(|c| state.check_condition(db, p_idx, c, &ctx, 0));
                                    let cost_ok = ability_costs_payable(state, db, p_idx, &ctx, ab);

                                    let once_per_turn_ok = ab.per_turn_limit() == 0
                                        || state.check_once_per_turn(
                                            p_idx,
                                            0,
                                            state.get_once_per_turn_instance_key(
                                                p_idx,
                                                0,
                                                slot_idx as i16,
                                                cid,
                                            ),
                                            cid as u32,
                                            ab_idx,
                                            ab.per_turn_limit(),
                                        );

                                    if cond_ok && cost_ok && once_per_turn_ok {
                                        let ab_aid = crate::core::logic::ACTION_BASE_STAGE
                                            + (slot_idx as i32 * 100)
                                            + (ab_idx as i32 * 10);
                                        receiver.add_action(ab_aid as usize);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        let stage_ability_us = t_stage_abilities
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        let t_hand_abilities = profile_enabled.then(Instant::now);
        // 3. Activate Hand Ability
        if abilities_enabled && prevent_activate == 0 {
            for (hand_idx, &cid) in player.hand.iter().enumerate() {
                let i = hand_idx as i32;
                if i >= MAX_HAND_SIZE as i32 {
                    break;
                }

                if let Some(card) = db.get_member(cid) {
                    if card.has_activated_hand {
                        for (ab_idx, ab) in card.abilities.iter().enumerate() {
                            if ab.trigger == TriggerType::Activated {
                                if ability_is_trivially_activatable(ab) {
                                    let ab_aid = crate::core::logic::ACTION_BASE_HAND_ACTIVATE
                                        + (i * 10)
                                        + (ab_idx as i32);
                                    receiver.add_action(ab_aid as usize);
                                    continue;
                                }

                                let ctx = AbilityContext {
                                    player_id: state.current_player,
                                    activator_id: state.current_player,
                                    area_idx: 6, // Hand
                                    source_card_id: cid,
                                    choice_index: -1,
                                    ..Default::default()
                                };
                                let mut ctx = ctx;
                                ctx.capture_state_raw(state.phase, state.current_player);
                                let cond_ok = !ability_needs_condition_check(ab)
                                    || ab
                                        .conditions
                                        .iter()
                                        .filter(|condition| {
                                            !matches!(
                                                condition.condition_type,
                                                ConditionType::SumValue | ConditionType::DiscardedCards
                                            )
                                        })
                                        .all(|c| state.check_condition(db, p_idx, c, &ctx, 0));
                                let cost_ok = ability_costs_payable(state, db, p_idx, &ctx, ab);
                                let once_per_turn_ok = ab.per_turn_limit() == 0
                                    || state.check_once_per_turn(
                                        p_idx,
                                        1,
                                        hand_idx as u8,
                                        cid as u32,
                                        ab_idx,
                                        ab.per_turn_limit(),
                                    );

                                if cond_ok && cost_ok && once_per_turn_ok {
                                    let ab_aid = crate::core::logic::ACTION_BASE_HAND_ACTIVATE
                                        + (i * 10)
                                        + (ab_idx as i32);
                                    receiver.add_action(ab_aid as usize);
                                }
                            }
                        }
                    }
                }
            }
        }
        let hand_ability_us = t_hand_abilities
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        if let Some(profile_start) = profile_start {
            let total_us = profile_start.elapsed().as_nanos() as u64 / 1000;
            if total_us >= legal_profile_threshold_us() {
                println!(
                    "[PROFILE] LegalActionsMain total_us={} precompute_us={} granted_cost_mod_us={} slot_projection_us={} play_hand_us={} stage_abilities_us={} hand_abilities_us={} p={} hand={} stage0={} stage1={}",
                    total_us,
                    precompute_us,
                    granted_cost_modifier_us,
                    slot_projection_us,
                    play_hand_us,
                    stage_ability_us,
                    hand_ability_us,
                    p_idx,
                    player.hand.len(),
                    player.stage.iter().filter(|&&cid| cid >= 0).count(),
                    player.live_zone.iter().filter(|&&cid| cid >= 0).count(),
                );
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::generated_constants::{
        ACTION_BASE_HAND_ACTIVATE, ACTION_BASE_HAND_CHOICE, ACTION_BASE_STAGE,
        ACTION_BASE_STAGE_CHOICE,
    };
    use crate::core::logic::card_db::LOGIC_ID_MASK;
    use crate::core::models::FrameProgram;
    use crate::test_helpers::{create_test_state, TestActionReceiver};

    fn insert_member(db: &mut CardDatabase, cid: i32, card: crate::core::logic::MemberCard) {
        db.members.insert(cid, card.clone());
        let logic_id = (cid & LOGIC_ID_MASK) as usize;
        if logic_id >= db.members_vec.len() {
            db.members_vec.resize(logic_id + 1, None);
        }
        db.members_vec[logic_id] = Some(card);
    }

    #[test]
    fn vanilla_mode_does_not_generate_ability_actions() {
        let mut db = CardDatabase::default();
        db.is_vanilla = true;

        let activated_card = crate::core::logic::MemberCard {
            card_id: 100,
            abilities: vec![crate::core::logic::Ability {
                trigger: TriggerType::Activated,
                frame_program: Some(FrameProgram::from_instruction_words(&[
                    O_DRAW, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0,
                ])),
                ..Default::default()
            }],
            ..Default::default()
        };
        insert_member(&mut db, 100, activated_card);

        let on_play_choice_card = crate::core::logic::MemberCard {
            card_id: 101,
            cost: 1,
            abilities: vec![crate::core::logic::Ability {
                trigger: TriggerType::OnPlay,
                choice_flags: CHOICE_FLAG_MODE,
                choice_count: 2,
                ..Default::default()
            }],
            ..Default::default()
        };
        insert_member(&mut db, 101, on_play_choice_card);

        let mut state = create_test_state();
        state.players[0].stage[0] = 100;
        state.players[0].hand = vec![101, 100].into();

        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);

        assert!(
            receiver
                .actions
                .iter()
                .all(|action| *action < ACTION_BASE_HAND_CHOICE
                    || *action >= ACTION_BASE_STAGE_CHOICE),
            "vanilla mode should not expose main-phase choice-based ability actions: {:?}",
            receiver.actions
        );
        assert!(
            receiver
                .actions
                .iter()
                .all(|action| *action < ACTION_BASE_HAND_ACTIVATE
                    || *action >= ACTION_BASE_HAND_CHOICE),
            "vanilla mode should not expose hand ability activations: {:?}",
            receiver.actions
        );
        assert!(
            receiver
                .actions
                .iter()
                .all(|action| *action < ACTION_BASE_STAGE || *action >= ACTION_BASE_STAGE_CHOICE),
            "vanilla mode should not expose stage ability activations: {:?}",
            receiver.actions
        );
        assert!(
            receiver.actions.iter().any(|action| {
                *action >= crate::core::logic::ACTION_BASE_HAND
                    && *action < ACTION_BASE_HAND_ACTIVATE
            }),
            "normal non-ability play actions should still exist in vanilla mode"
        );
    }
}
