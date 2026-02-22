use crate::core::logic::{ActionReceiver, CardDatabase, GameState, AbilityContext};
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::enums::*;

pub struct MainPhaseGenerator;

impl ActionGenerator for MainPhaseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R) {
        let player = &state.core.players[p_idx];
        receiver.add_action(0);

        // Optimization 3: Loop Hoisting
        let available_energy = (0..player.energy_zone.len()).filter(|&i| !player.is_energy_tapped(i)).count() as i32;

        // Pre-calculate stage slot costs
        let mut slot_costs = [0; 3];
        for s in 0..3 {
            if player.stage[s] >= 0 {
                 if let Some(prev) = db.get_member(player.stage[s]) {
                     slot_costs[s] = prev.cost as i32;
                 }
            }
        }

        // 1. Play Member from Hand
        for (hand_idx, &cid) in player.hand.iter().enumerate().take(60) {
            if let Some(card) = db.get_member(cid) {
                let base_cost = (card.cost as i32 - player.cost_reduction as i32).max(0);

                for slot_idx in 0..3 {
                    if player.is_moved(slot_idx) { continue; }

                    // Check play restriction
                    if (player.prevent_play_to_slot_mask & (1 << slot_idx)) != 0 { continue; }

                    let mut cost = base_cost;
                    if player.stage[slot_idx] >= 0 {
                        cost = (cost - slot_costs[slot_idx]).max(0);
                        // Check global baton touch prevention
                        if player.prevent_baton_touch > 0 { continue; }
                        // Check card-specific restriction (if implemented via O_META)
                        if GameState::has_restriction(state, p_idx, slot_idx, O_PREVENT_BATON_TOUCH, db) { continue; }
                    }

                    if cost <= available_energy {
                        // Check for OnPlay choices (Limit to first 10 cards to stay within Action ID space)
                        let mut has_choice_on_play = false;
                        if hand_idx < 10 {
                            for ab in &card.abilities {
                                if ab.trigger == TriggerType::OnPlay {
                                    // OPTIMIZATION: Use pre-computed flags
                                    let _has_look_choose = (ab.choice_flags & CHOICE_FLAG_LOOK) != 0;
                                    let has_select_mode = (ab.choice_flags & CHOICE_FLAG_MODE) != 0;
                                    let has_color_select = (ab.choice_flags & CHOICE_FLAG_COLOR) != 0;
                                    let _has_order_deck = (ab.choice_flags & CHOICE_FLAG_ORDER) != 0;

                                    if has_color_select {
                                        has_choice_on_play = true;
                                        for c in 0..6 {
                                            let choice_aid = crate::core::logic::ACTION_BASE_HAND_CHOICE + (hand_idx as i32 * 100) + (slot_idx as i32 * 10) + (c as i32);
                                            receiver.add_action(choice_aid as usize);
                                        }
                                    } else if has_select_mode {
                                        has_choice_on_play = true;
                                        let count = ab.choice_count as i32;
                                        for c in 0..count {
                                            let choice_aid = crate::core::logic::ACTION_BASE_HAND_CHOICE + (hand_idx as i32 * 100) + (slot_idx as i32 * 10) + (c as i32);
                                            receiver.add_action(choice_aid as usize);
                                        }
                                    }
                                }
                            }
                        }

                        if !has_choice_on_play {
                             let aid = crate::core::logic::ACTION_BASE_HAND + (hand_idx as i32 * 10) + slot_idx as i32;
                            receiver.add_action(aid as usize);
                        }

                        // Double Baton Touch (Card 560 etc.)
                        let multi_limit = crate::core::logic::rules::has_multi_baton(card);
                        if multi_limit >= 2 && hand_idx < 10 {
                            for other_slot in 0..3 {
                                if other_slot == slot_idx { continue; }
                                if player.stage[other_slot] < 0 { continue; }
                                if player.is_moved(other_slot) { continue; }

                                let combined_cost = (base_cost - slot_costs[slot_idx] - slot_costs[other_slot]).max(0);
                                if combined_cost <= available_energy {
                                    let is_next = other_slot == (slot_idx + 1) % 3;
                                    let combo_idx = slot_idx * 2 + (if is_next { 1 } else { 0 });
                                    let aid = crate::core::logic::ACTION_BASE_HAND + (hand_idx as i32 * 10) + 3 + combo_idx as i32;
                                    receiver.add_action(aid as usize);
                                }
                            }
                        }
                    }
                }
            }
        }

        // 2. Activate Stage Ability
        if player.prevent_activate == 0 {
            for slot_idx in 0..3 {
                if let Some(cid_val) = player.stage.get(slot_idx) {
                    let cid = *cid_val;
                    if cid >= 0 {
                        if let Some(card) = db.get_member(cid) {
                            for (ab_idx, ab) in card.abilities.iter().enumerate() {
                                if ab.trigger == TriggerType::Activated {
                                    let ctx = AbilityContext {
                                        player_id: state.current_player,
                                        area_idx: slot_idx as i16,
                                        source_card_id: cid,
                                        ..Default::default()
                                    };

                                    let cond_ok = ab.conditions.iter().all(|c| state.check_condition(db, p_idx, c, &ctx, 0));
                                    let cost_ok = ab.costs.iter().all(|c| state.check_cost(db, p_idx, c, &ctx));

                                    if cond_ok && cost_ok && state.check_once_per_turn(p_idx, 1, slot_idx as u32, ab_idx) {
                                        let ab_aid = crate::core::logic::ACTION_BASE_STAGE + (slot_idx as i32 * 100) + (ab_idx as i32 * 10);
                                        receiver.add_action(ab_aid as usize);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
