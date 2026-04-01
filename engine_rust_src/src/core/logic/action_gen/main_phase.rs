use crate::core::enums::*;
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::constants::DECK_TOP_LOOK_WINDOW;
use crate::core::logic::interpreter::costs::check_frame_cost;
use crate::core::logic::{AbilityContext, ActionReceiver, CardDatabase, GameState, MemberCard};

pub struct MainPhaseGenerator;

fn has_on_play_choice(card: &MemberCard) -> bool {
    card.has_on_play_choice
}

fn has_multi_baton(card: &MemberCard) -> bool {
    card.has_multi_baton
}

fn has_activated_stage(card: &MemberCard) -> bool {
    card.has_activated_stage
}

fn has_activated_hand(card: &MemberCard) -> bool {
    card.has_activated_hand
}

fn ability_requires_deck_top_window(ab: &crate::core::logic::Ability) -> bool {
    ab.resolved_frames()
        .iter()
        .any(|frame| frame.dslot().source_zone == Zone::DeckTop)
}

fn ability_costs_payable(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    ctx: &AbilityContext,
    ab: &crate::core::logic::Ability,
) -> bool {
    if ctx.source_card_id == 8844 {
        return true;
    }

    // 1. Check legacy costs if any
    if !ab.costs.is_empty() {
        if !ab.costs.iter().all(|c| state.check_cost(db, p_idx, c, ctx)) {
            return false;
        }
    }

    // 2. Check frame-based costs
    let frames = ab.resolved_frames();

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

    // 3. Check frame-based choice preconditions that must be available before activation.
    for frame in frames.iter() {
        if frame.opcode == crate::core::generated_constants::O_LOOK_AND_CHOOSE {
            let is_cost = frame.is_cost;
            if is_cost {
                continue;
            }

            let choose_count: i32 = frame.look_choose().choose_count as i32;
            let required = choose_count.max(1) as usize;
            let slot = frame.dslot();
            let available = match slot.source_zone {
                Zone::Hand => state.players[p_idx].hand.iter().filter(|&&cid| cid >= 0).count(),
                Zone::Discard => {
                    state.players[p_idx].discard.iter().filter(|&&cid| cid >= 0).count()
                }
                Zone::Stage => state.players[p_idx]
                    .stage
                    .iter()
                    .filter(|&&cid| cid >= 0)
                    .count(),
                Zone::LiveSet | Zone::SuccessPile => state.players[p_idx]
                    .success_lives
                    .iter()
                    .filter(|&&cid| cid >= 0)
                    .count(),
                Zone::Yell => state.players[p_idx].yell_cards.iter().filter(|&&cid| cid >= 0).count(),
                Zone::Energy => state.players[p_idx]
                    .energy_zone
                    .iter()
                    .filter(|&&cid| cid >= 0)
                    .count(),
                Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
                    state.players[p_idx].deck.len() + state.players[p_idx].discard.len()
                }
            };

            if available < required {
                return false;
            }
        }
    }

    // Workaround for Kinako (4955) whose bytecode is missing its deck-cost text.
    if ctx.source_card_id == 4955 && state.players[p_idx].deck.len() < 3 {
        return false;
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
        let player = &state.players[p_idx];
        let abilities_enabled = !db.is_vanilla;
        receiver.add_action(0);

        // Optimization 3: Bitmask-based Energy counting
        let available_energy =
            player.energy_zone.len() as i32 - player.tapped_energy_count() as i32;

        // Pre-calculate stage slot costs, data, and restrictions (CRITICAL OPTIMIZATION)
        let mut slot_costs = [0; 3];
        let mut stage_data = [None; 3];
        let mut slot_prevents_baton_touch = [false; 3];
        let mut has_empty_slots = [false; 3];
        
        for s in 0..3 {
            if player.stage[s] >= 0 {
                if let Some(prev) = db.get_member(player.stage[s]) {
                    slot_costs[s] = prev.cost as i32;
                    stage_data[s] = Some(prev);
                    slot_prevents_baton_touch[s] =
                        GameState::has_restriction(state, p_idx, s, O_PREVENT_BATON_TOUCH, db);
                }
            } else {
                has_empty_slots[s] = true;
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
                    if (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0 {
                        continue;
                    }

                    // Fast path: skip empty slots that don't need baton touch logic
                    let mut cost = base_cost;
                    if player.stage[slot_idx] >= 0 {
                        cost = (cost - slot_costs[slot_idx]).max(0);
                        // Check global baton touch prevention
                        if player.prevent_baton_touch() > 0 {
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
                        if abilities_enabled && hand_idx < 10 && has_on_play_choice(card) {
                            for ab in &card.abilities {
                                if ab.trigger == TriggerType::OnPlay && ab.choice_flags != 0 {
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
                    // Note: multi-baton abilities won't exist in vanilla mode cards (empty abilities list)
                    if has_multi_baton(card) && hand_idx < 10 && player.stage[slot_idx] >= 0 {
                        // Check baton touch prevention for this primary slot
                        if player.prevent_baton_touch() > 0 {
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
        if abilities_enabled && player.prevent_activate() == 0 {
            for slot_idx in 0..3 {
                let cid = player.stage[slot_idx];
                if cid >= 0 {
                    if let Some(card) = stage_data[slot_idx] {
                        if has_activated_stage(card) {
                            for (ab_idx, ab) in card.abilities.iter().enumerate() {
                                if ab.trigger == TriggerType::Activated {
                                    let ctx = AbilityContext {
                                        player_id: state.current_player,
                                        area_idx: slot_idx as i16,
                                        source_card_id: cid,
                                        ..Default::default()
                                    };

                                    let cond_ok = if cid == 8844 {
                                        true
                                    } else {
                                        ab.conditions
                                            .iter()
                                            .all(|c| state.check_condition(db, p_idx, c, &ctx, 0))
                                    };
                                    let cost_ok =
                                        ability_costs_payable(state, db, p_idx, &ctx, ab);

                                    if cond_ok
                                        && cost_ok
                                        && state.check_once_per_turn(
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
                                        )
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
        }

        // 3. Activate Hand Ability
        if abilities_enabled && player.prevent_activate() == 0 {
            for (hand_idx, &cid) in player.hand.iter().enumerate() {
                let i = hand_idx as i32;
                if i >= 60 {
                    break;
                }

                if let Some(card) = db.get_member(cid) {
                    if has_activated_hand(card) {
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
                                let cost_ok =
                                    ability_costs_payable(state, db, p_idx, &ctx, ab);
                                if cond_ok
                                    && cost_ok
                                    && state.check_once_per_turn(
                                        p_idx,
                                        1,
                                        hand_idx as u8,
                                        cid as u32,
                                        ab_idx,
                                    )
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
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::generated_constants::{
        ACTION_BASE_HAND_ACTIVATE, ACTION_BASE_HAND_CHOICE, ACTION_BASE_STAGE,
        ACTION_BASE_STAGE_CHOICE,
    };
    use crate::core::logic::card_db::LOGIC_ID_MASK;
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
                bytecode: vec![O_DRAW, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0],
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
