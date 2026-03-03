use crate::core::enums::*;
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::{AbilityContext, ActionReceiver, CardDatabase, GameState};

pub struct MainPhaseGenerator;

impl ActionGenerator for MainPhaseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let player = &state.core.players[p_idx];
        receiver.add_action(0);

        // Optimization 3: Loop Hoisting
        let available_energy = (0..player.energy_zone.len())
            .filter(|&i| !player.is_energy_tapped(i))
            .count() as i32;

        // Pre-calculate stage slot costs, data, and restrictions (CRITICAL OPTIMIZATION)
        let mut slot_costs = [0; 3];
        let mut stage_data = [None; 3];
        let mut slot_prevents_baton_touch = [false; 3];
        for s in 0..3 {
            if player.stage[s] >= 0 {
                if let Some(prev) = db.get_member(player.stage[s]) {
                    slot_costs[s] = prev.cost as i32;
                    stage_data[s] = Some(prev);
                    slot_prevents_baton_touch[s] =
                        GameState::has_restriction(state, p_idx, s, O_PREVENT_BATON_TOUCH, db);
                }
            }
        }

        // 1. Play Member from Hand
        for (hand_idx, &cid) in player.hand.iter().enumerate() {
            let i = hand_idx as i32;
            if i >= 60 {
                break;
            } // Safety cap

            if let Some(card) = db.get_member(cid) {
                let base_cost = (card.cost as i32 - player.cost_reduction as i32).max(0);

                for slot_idx in 0..3 {
                    if player.is_moved(slot_idx) {
                        continue;
                    }

                    // Check play restriction
                    if (player.prevent_play_to_slot_mask & (1 << slot_idx)) != 0 {
                        continue;
                    }

                    let mut cost = base_cost;
                    if player.stage[slot_idx] >= 0 {
                        cost = (cost - slot_costs[slot_idx]).max(0);
                        // Check global baton touch prevention
                        if player.prevent_baton_touch > 0 {
                            continue;
                        }
                        // Check card-specific restriction (cached)
                        if slot_prevents_baton_touch[slot_idx] {
                            continue;
                        }
                    }

                    if cost <= available_energy {
                        // Check for OnPlay choices (Limit to first 10 cards to stay within Action ID space)
                        let mut has_choice_on_play = false;
                        if hand_idx < 10 {
                            for ab in &card.abilities {
                                if ab.trigger == TriggerType::OnPlay {
                                    // OPTIMIZATION: Use pre-computed flags
                                    let has_select_mode = (ab.choice_flags & CHOICE_FLAG_MODE) != 0;
                                    let has_color_select =
                                        (ab.choice_flags & CHOICE_FLAG_COLOR) != 0;

                                    if has_color_select {
                                        has_choice_on_play = true;
                                        for c in 0..6 {
                                            let choice_aid =
                                                crate::core::logic::ACTION_BASE_HAND_CHOICE
                                                    + (i * 100)
                                                    + (slot_idx as i32 * 10)
                                                    + (c as i32);
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
                    let multi_limit = crate::core::logic::rules::has_multi_baton(card);
                    if multi_limit >= 2 && hand_idx < 10 && player.stage[slot_idx] >= 0 {
                        // Check baton touch prevention for this primary slot
                        if player.prevent_baton_touch > 0 {
                            continue;
                        }
                        if slot_prevents_baton_touch[slot_idx] {
                            continue;
                        }

                        for other_slot in 0..3 {
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

                            let combined_cost =
                                (base_cost - slot_costs[slot_idx] - slot_costs[other_slot]).max(0);
                            if combined_cost <= available_energy {
                                let is_next = other_slot == (slot_idx + 1) % 3;
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

        // 2. Activate Stage Ability
        if player.prevent_activate == 0 {
            for slot_idx in 0..3 {
                let cid = player.stage[slot_idx];
                if cid >= 0 {
                    if let Some(card) = stage_data[slot_idx] {
                        // USE CACHED STAGE DATA
                        for (ab_idx, ab) in card.abilities.iter().enumerate() {
                            if ab.trigger == TriggerType::Activated {
                                let ctx = AbilityContext {
                                    player_id: state.current_player,
                                    area_idx: slot_idx as i16,
                                    source_card_id: cid,
                                    ..Default::default()
                                };

                                let cond_ok = ab
                                    .conditions
                                    .iter()
                                    .all(|c| state.check_condition(db, p_idx, c, &ctx, 0));
                                let cost_ok = ab
                                    .costs
                                    .iter()
                                    .all(|c| state.check_cost(db, p_idx, c, &ctx));

                                if cond_ok
                                    && cost_ok
                                    && state.check_once_per_turn(p_idx, 0, cid as u32, ab_idx)
                                {
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

        // 3. Activate Hand Ability
        if player.prevent_activate == 0 {
            for (hand_idx, &cid) in player.hand.iter().enumerate() {
                let i = hand_idx as i32;
                if i >= 60 {
                    break;
                }

                if let Some(card) = db.get_member(cid) {
                    for (ab_idx, ab) in card.abilities.iter().enumerate() {
                        if ab.trigger == TriggerType::Activated {
                            let ctx = AbilityContext {
                                player_id: state.current_player,
                                area_idx: 6, // Hand
                                source_card_id: cid,
                                ..Default::default()
                            };
                            let cond_ok = ab
                                .conditions
                                .iter()
                                .all(|c| state.check_condition(db, p_idx, c, &ctx, 0));
                            let cost_ok = ab
                                .costs
                                .iter()
                                .all(|c| state.check_cost(db, p_idx, c, &ctx));
                            if cond_ok
                                && cost_ok
                                && state.check_once_per_turn(p_idx, 1, cid as u32, ab_idx)
                            {
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
}
