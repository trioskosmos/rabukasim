use crate::core::enums::*;
use crate::core::generated_constants::{ACTION_BASE_RPS, ACTION_BASE_RPS_P2};
use crate::core::logic::constants::STAGE_SLOT_COUNT;
use crate::core::logic::{
    ability_patterns::{
        encode_optional_mode_mask, is_optional_live_start_discard_count_ability,
        optional_mode_effect, pending_live_ability, pending_member_ability,
        pending_optional_mode_mask, pending_targeted_live_heart_bonus,
    },
    action_factory::DecodedAction,
    interpreter::costs,
    AbilityContext, ActionFactory, CardDatabase, GameState, PendingInteraction, Phase,
};
// use crate::core::hearts::*;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;
use smallvec::SmallVec;

pub trait TurnController {
    fn handle_rps(&mut self, action: i32) -> Result<(), String>;
    fn handle_turn_choice(&mut self, action: i32) -> Result<(), String>;
}

pub trait MulliganController {
    fn handle_mulligan(&mut self, action: i32) -> Result<(), String>;
    fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>);
}

pub trait MainPhaseController {
    fn handle_main(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    fn handle_liveset(&mut self, action: i32) -> Result<(), String>;
    fn handle_liveresult(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    fn end_main_phase(&mut self, db: &CardDatabase);
}

pub trait ResponseController {
    fn handle_response(&mut self, db: &CardDatabase, action: i32) -> Result<(), String>;
    fn play_member_with_choice(
        &mut self,
        db: &CardDatabase,
        hand_idx: usize,
        slot_idx: usize,
        secondary_slot_idx: i16,
        choice_idx: i32,
        start_ab_idx: usize,
    ) -> Result<(), String>;
    fn activate_ability(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
    ) -> Result<(), String>;
    fn activate_ability_with_choice(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
        choice_idx: i32,
        target_slot: i32,
    ) -> Result<(), String>;
}

pub trait TurnPhaseController {
    fn do_active_phase(&mut self, db: &CardDatabase);
    fn do_energy_phase(&mut self);
    fn do_draw_phase(&mut self, db: &CardDatabase);
}

impl TurnController for GameState {
    fn handle_rps(&mut self, action: i32) -> Result<(), String> {
        let (p_idx, choice) = if action >= ACTION_BASE_RPS_P2 {
            (1, action - ACTION_BASE_RPS_P2)
        } else if action >= ACTION_BASE_RPS {
            (0, action - ACTION_BASE_RPS)
        } else {
            return Ok(());
        };

        if choice < 0 || choice > 2 {
            return Err("Invalid RPS choice".to_string());
        }

        if self.rps_choices[p_idx] != -1 {
            if self.rps_choices[p_idx] == choice as i8 {
                return Ok(()); // Idempotent
            }
            return Err(format!(
                "Player {} already chose a different move ({})",
                p_idx, self.rps_choices[p_idx]
            ));
        }

        if !self.ui.silent {
            self.log(format!(
                "Rule 6.2.1.3 (7.1.1): Player {} chose RPS move {}.",
                p_idx, choice
            ));
        }

        self.rps_choices[p_idx] = choice as i8;

        if self.rps_choices[0] != -1 && self.rps_choices[1] == -1 {
            self.current_player = 1;
        } else if self.rps_choices[1] != -1 && self.rps_choices[0] == -1 {
            self.current_player = 0;
        }

        if self.rps_choices[0] != -1 && self.rps_choices[1] != -1 {
            let p0 = self.rps_choices[0];
            let p1 = self.rps_choices[1];
            if !self.ui.silent {
                self.log(format!("[[rps_result:p0={}:p1={}]]", p0, p1));
            }

            if p0 == p1 {
                self.rps_draw_count = self.rps_draw_count.saturating_add(1);
                let draw_count = self.rps_draw_count;

                if !self.ui.silent {
                    self.log(format!("[[rps_draw:count={}]]", draw_count));
                }

                if draw_count >= 5 {
                    if !self.ui.silent {
                        self.log(
                            "Maximum RPS draws reached. P0 wins by default to progress."
                                .to_string(),
                        );
                    }
                    self.current_player = 0;
                    self.first_player = 0;
                    self.phase = Phase::Setup;
                    self.rps_draw_count = 0;
                } else {
                    self.rps_choices = [-1, -1];
                    self.current_player = 0;
                }
            } else {
                self.rps_draw_count = 0;
                let p0_wins = (p0 == 0 && p1 == 2) || (p0 == 1 && p1 == 0) || (p0 == 2 && p1 == 1);
                let winner = if p0_wins { 0 } else { 1 };
                if !self.ui.silent {
                    self.log(format!("[[rps_winner_chooses:winner={}]]", winner));
                }
                self.current_player = winner as u8;
                self.phase = Phase::TurnChoice;
                if !self.ui.silent {
                    self.log(
                        "Rule 7.1.1: Winner of RPS chooses to go first or second.".to_string(),
                    );
                }
            }
        }
        Ok(())
    }

    fn handle_turn_choice(&mut self, action: i32) -> Result<(), String> {
        if action == Self::ACTION_TURN_CHOICE_FIRST {
            let winner = self.current_player;
            self.first_player = winner;
            if !self.ui.silent {
                self.log(format!(
                    "Rule 6.2.1.3 (7.1.1): Player {} (winner) chose to go first!",
                    winner
                ));
            }
            self.phase = Phase::MulliganP1;
            self.current_player = winner;
        } else if action == Self::ACTION_TURN_CHOICE_SECOND {
            let winner = self.current_player;
            self.first_player = 1 - winner;
            if !self.ui.silent {
                self.log(format!(
                    "Rule 6.2.1.3 (7.1.1): Player {} (winner) chose to go second!",
                    winner
                ));
            }
            self.phase = Phase::MulliganP1;
            self.current_player = 1 - winner;
            if !self.ui.silent {
                self.log("Rule 7.1.2: Order of players decided.".to_string());
            }
        }
        Ok(())
    }
}

impl MulliganController for GameState {
    fn handle_mulligan(&mut self, action: i32) -> Result<(), String> {
        let p_idx = self.current_player as usize;
        if self.debug.debug_mode {
            println!(
                "[DEBUG] handle_mulligan: current_player={}, phase={:?}",
                p_idx, self.phase
            );
        }
        if action == 0 {
            let selection = self.core.players[p_idx].mulligan_selection;
            let discard_indices = self.core.players[p_idx]
                .hand
                .iter()
                .enumerate()
                .filter_map(|(idx, _)| ((selection >> idx) & 1 == 1).then_some(idx))
                .collect();
            self.execute_mulligan(p_idx, discard_indices);
        } else if action >= ACTION_BASE_MULLIGAN && action <= ACTION_BASE_MULLIGAN + 59 {
            let card_idx = (action - ACTION_BASE_MULLIGAN) as usize;
            if card_idx < self.core.players[p_idx].hand.len() {
                self.core.players[p_idx].mulligan_selection ^= 1u64 << card_idx;
            }
        }
        Ok(())
    }

    fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>) {
        if self.debug.debug_mode {
            println!(
                "[DEBUG] execute_mulligan: player={}, discard_indices={:?}, current_phase={:?}",
                player_idx, discard_indices, self.phase
            );
        }
        let mut count = 0;
        let mut discards = Vec::new();
        let mut new_hand = SmallVec::new();
        let discard_set: std::collections::HashSet<usize> = discard_indices.into_iter().collect();
        for (i, &cid) in self.core.players[player_idx].hand.iter().enumerate() {
            if discard_set.contains(&i) {
                discards.push(cid);
                count += 1;
            } else {
                new_hand.push(cid);
            }
        }

        if !self.ui.silent {
            self.log(format!(
                "Rule 6.2.1.6 (1.3.2): Player {} finished mulligan ({} cards moved to bottom of Main Deck).",
                player_idx, count
            ));
        }
        self.core.players[player_idx].hand = new_hand;
        let t = self.turn as i32;
        for _ in 0..count {
            if self.core.players[player_idx].deck.is_empty() {
                self.resolve_deck_refresh(player_idx);
            }
            if let Some(card_id) = self.core.players[player_idx].pop_deck_card() {
                self.core.players[player_idx].draw_hand_card(card_id, t);
            }
        }
        self.core.players[player_idx].deck.extend(discards);
        let mut rng = Pcg64::from_os_rng();
        self.core.players[player_idx].deck.shuffle(&mut rng);
        self.core.players[player_idx].mulligan_selection = 0;
        self.resolve_deck_refresh(player_idx);
        let prev_phase = self.phase;
        if self.phase == Phase::MulliganP1 {
            self.current_player = 1 - self.first_player;
            self.phase = Phase::MulliganP2;
        } else if self.phase == Phase::MulliganP2 {
            self.current_player = self.first_player;
            self.phase = Phase::Active;
            if !self.ui.silent {
                self.log("Rule 7.1: Preparation finished. Starting first turn.".to_string());
            }
        }
        if self.debug.debug_mode {
            println!(
                "[DEBUG] execute_mulligan: transition {:?} -> {:?}",
                prev_phase, self.phase
            );
        }
    }
}

impl MainPhaseController for GameState {
    fn handle_main(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        let decoded = ActionFactory::parse_action(action);

        if db.is_vanilla {
            match decoded {
                DecodedAction::ActivateMember { .. }
                | DecodedAction::ActivateFromDiscard { .. }
                | DecodedAction::ActivateFromHand { .. }
                | DecodedAction::PlayMember {
                    choice_idx: Some(_),
                    ..
                } => {
                    return Err("Abilities are disabled in vanilla mode".to_string());
                }
                _ => {}
            }
        }

        match decoded {
            DecodedAction::Pass => {
                self.end_main_phase(db);
            }
            DecodedAction::PlayMember {
                hand_idx,
                slot_idx,
                other_slot,
                choice_idx,
            } => {
                if hand_idx < self.core.players[self.current_player as usize].hand.len() {
                    let other = other_slot.map(|s| s as i16).unwrap_or(-1);
                    let choice = choice_idx.unwrap_or(-1);
                    self.play_member_with_choice(db, hand_idx, slot_idx, other, choice, 0)?;
                }
            }
            DecodedAction::ActivateMember {
                slot_idx,
                ab_idx,
                choice_idx,
            } => {
                let choice = choice_idx.unwrap_or(-1);
                self.activate_ability_with_choice(db, slot_idx, ab_idx, choice, 0)?;
            }
            DecodedAction::ActivateFromDiscard {
                discard_idx,
                ab_idx,
            } => {
                if discard_idx
                    < self.core.players[self.current_player as usize]
                        .discard
                        .len()
                {
                    self.activate_ability_with_choice(db, 100 + discard_idx, ab_idx, -1, -1)?;
                }
            }
            DecodedAction::ActivateFromHand { hand_idx, ab_idx } => {
                if hand_idx < self.core.players[self.current_player as usize].hand.len() {
                    self.activate_ability_with_choice(db, 200 + hand_idx, ab_idx, -1, -1)?;
                }
            }
            _ => {}
        }
        Ok(())
    }

    fn handle_liveset(&mut self, action: i32) -> Result<(), String> {
        let p_idx = self.current_player as usize;
        if action == 0 {
            let draws = self.live_set_pending_draws[p_idx];
            if draws > 0 {
                if !self.ui.silent {
                    self.log(format!(
                        "Rule 8.2.2: Live Set End: Player {} draws {} cards.",
                        p_idx, draws
                    ));
                }
                self.draw_cards(p_idx, draws as u32);
                self.live_set_pending_draws[p_idx] = 0;
            }

            if self.current_player == self.first_player {
                self.current_player = 1 - self.first_player;
                if !self.ui.silent {
                    self.log(
                        "Rule 8.2.4: Player 1 (Second Player) now sets live cards.".to_string(),
                    );
                }
            } else {
                self.phase = Phase::PerformanceP1;
                self.current_player = self.first_player;
                if !self.ui.silent {
                    self.log(
                        "Rule 8.2.5: Live Card Set Phase ended. Moving to Performance Phase."
                            .to_string(),
                    );
                }
            }
        } else if action >= ACTION_BASE_LIVESET && action < ACTION_BASE_LIVESET + 100 {
            let hand_idx = (action - ACTION_BASE_LIVESET) as usize;
            if hand_idx < self.core.players[p_idx].hand.len() {
                let cid = self.core.players[p_idx].hand[hand_idx];
                self.core.players[p_idx].remove_hand_card(hand_idx);
                for i in 0..3 {
                    if self.core.players[p_idx].live_zone[i] == -1 {
                        self.core.players[p_idx].live_zone[i] = cid;
                        self.core.players[p_idx].set_revealed(i, false);
                        self.live_set_pending_draws[p_idx] += 1;
                        if !self.ui.silent {
                            self.log(format!(
                                "Rule 8.2.2: Player {} sets live card. Draw pending (+1).",
                                p_idx
                            ));
                        }
                        break;
                    }
                }
            }
        }
        Ok(())
    }

    fn handle_liveresult(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        if action == 0 {
            self.do_live_result(db);
        } else if action >= 600 && action <= 602 {
            let p_idx = self.current_player as usize;
            let slot_idx = (action - 600) as usize;
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            if cid >= 0 {
                let is_prevented = if let Some(card) = db.get_live(cid) {
                    card.abilities.iter().any(|a| {
                        a.effects
                            .iter()
                            .any(|e| e.effect_type == EffectType::PreventSetToSuccessPile)
                    })
                } else {
                    false
                };

                self.core.players[p_idx].live_zone[slot_idx] = -1;

                if is_prevented || self.core.players[p_idx].success_lives.len() >= 3 {
                    if !self.ui.silent {
                        let reason = if is_prevented {
                            "prevented by effect"
                        } else {
                            "already at 3-card limit"
                        };
                        self.log(format!(
                            "Player {} SELECTED Success Live {}. Moving to discard: Card ID {}",
                            p_idx, reason, cid
                        ));
                    }
                    self.core.players[p_idx].push_discard_card(cid);
                } else {
                    self.core.players[p_idx].success_lives.push(cid);
                    self.obtained_success_live[p_idx] = true;
                    if !self.ui.silent {
                        self.log(format!(
                            "Player {} SELECTED Success Live: Card ID {}",
                            p_idx, cid
                        ));
                    }
                }

                self.check_win_condition();
                if self.phase == Phase::Terminal {
                    return Ok(());
                }

                // Continue do_live_result to check for more winners or finalize
                self.do_live_result(db);
            }
        }
        Ok(())
    }

    fn end_main_phase(&mut self, db: &CardDatabase) {
        if !self.ui.silent {
            self.log(format!(
                "Rule 7.5.3, Rule 7.8, Rule 7.8.1: Player {} ends Main Phase.",
                self.current_player
            ));
        }
        
        // Fast path: skip TurnEnd trigger if no cards on board (nothing to trigger)
        let p_idx = self.current_player as usize;
        let has_cards = self.core.players[p_idx].stage.iter().any(|&c| c >= 0)
            || self.core.players[p_idx].live_zone.iter().any(|&c| c >= 0);
        
        if has_cards || !db.is_vanilla {
            self.trigger_event(
                db,
                TriggerType::TurnEnd,
                self.current_player as usize,
                -1,
                -1,
                0,
                -1,
            );
        }

        if self.current_player == self.first_player {
            self.current_player = 1 - self.first_player;
            self.phase = Phase::Active;
            if !self.ui.silent {
                self.log_rule(
                    "Rule 7.4",
                    &format!("Entering Active Phase for Player {}.", self.current_player),
                );
            }
        } else {
            self.phase = Phase::LiveSet;
            self.current_player = self.first_player;
            if !self.ui.silent {
                self.log_rule("Rule 7.6, Rule 8.2", &format!("Entering Live Set Phase."));
            }
        }
    }
}
impl ResponseController for GameState {
    fn handle_response(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        let decoded_action = ActionFactory::parse_action(action);
        let response_origin = crate::core::logic::interpreter::suspension::capture_response_origin(self);
        
        // ANTI-SOFTLOCK: Detect Response phase loops and break them
        if self.phase == Phase::Response && matches!(decoded_action, DecodedAction::Pass) {
            // Use a simple field in debug state to track consecutive PASS actions
            let pass_count = self.debug.response_pass_count;
            self.debug.response_pass_count = pass_count + 1;
            
            // If we've seen too many PASS actions in a row, force cleanup
            if pass_count > 10 {
                if !self.ui.silent {
                    println!("[ANTI_SOFTLOCK] Detected Response phase loop after {} PASS actions - forcing cleanup", pass_count + 1);
                }
                
                // Clear the entire interaction stack
                self.interaction_stack.clear();
                self.ui.current_execution_id = None;
                self.debug.response_pass_count = 0;
                
                // Restore response state to get out of Response phase
                crate::core::logic::interpreter::restore_response_state(
                    self,
                    response_origin.0,
                    response_origin.1,
                );
                self.process_rule_checks(db);
                return Ok(());
            }
        } else {
            // Reset counter when not a PASS action
            self.debug.response_pass_count = 0;
        }
        
        if let Some(pi) = self.interaction_stack.last().cloned() {
            let is_optional_prompt = matches!(
                pi.choice_type,
                ChoiceType::Optional | ChoiceType::SelectHandDiscard | ChoiceType::SelectDiscardPlay
            );
            let is_optional_skip = is_optional_prompt
                && if (pi.filter_attr & crate::core::logic::constants::FILTER_IS_OPTIONAL) != 0 {
                match decoded_action {
                    DecodedAction::Pass => true,
                    DecodedAction::SelectChoice { choice_idx } => {
                        // Only treat choice_idx == 1 as CHOICE_NO for actual Optional prompts
                        // For other types like SelectDiscardPlay, choice_idx is a valid selection
                        choice_idx == crate::core::logic::constants::CHOICE_NO as i32
                            && pi.choice_type == ChoiceType::Optional
                    }
                    _ => false,
                }
            } else {
                matches!(decoded_action, DecodedAction::Pass)
            };
            if is_optional_skip {
                let current_execution_id = self.ui.current_execution_id;
                println!(
                    "[OPT_SKIP_DBG] before finish card={} choice_type={:?} exec={:?} stack={}",
                    pi.card_id,
                    pi.choice_type,
                    current_execution_id,
                    self.interaction_stack.len()
                );
                crate::core::logic::interpreter::suspension::finish_pending_interaction(self);
                if let Some(exec_id) = current_execution_id {
                    while self
                        .interaction_stack
                        .last()
                        .map(|interaction| interaction.execution_id == exec_id)
                        .unwrap_or(false)
                    {
                        self.interaction_stack.pop();
                    }
                }
                println!(
                    "[OPT_SKIP_DBG] after pop stack={} phase={:?}",
                    self.interaction_stack.len(),
                    self.phase
                );
                self.process_rule_checks(db);
                if self.interaction_stack.is_empty() {
                    crate::core::logic::interpreter::restore_response_state(
                        self,
                        response_origin.0,
                        response_origin.1,
                    );
                }
                return Ok(());
            }
        }
        if let Some(pi) = self.interaction_stack.last().cloned() {
            let choice_idx = match decoded_action {
                DecodedAction::Pass => 99,
                DecodedAction::SelectMode { mode_idx } => mode_idx,
                DecodedAction::PlayMember { hand_idx, .. } => hand_idx as i32,
                DecodedAction::SelectChoice { choice_idx } => choice_idx,
                DecodedAction::SelectColor { color_idx } => color_idx,
                DecodedAction::SelectEnergy { energy_idx } => energy_idx as i32,
                DecodedAction::SelectStageSlot { slot_idx } => slot_idx as i32,
                _ => -1,
            };

            if let Some(mask) = pending_optional_mode_mask(db, &pi) {
                if matches!(decoded_action, DecodedAction::SelectMode { .. }) {
                    let ability = pending_live_ability(db, &pi).ok_or("Ability not found")?;
                    let (selected_frame, remaining_mask) =
                        optional_mode_effect(ability, mask, choice_idx)
                            .ok_or("Invalid optional mode selection".to_string())?;

                    self.interaction_stack.pop();

                    let p_idx = pi.ctx.player_id as usize;
                    if selected_frame.opcode() == O_ENERGY_CHARGE {
                        if let Some(cid) = self.players[p_idx].energy_deck.pop() {
                            let is_wait = selected_frame
                                .components()
                                .params
                                .and_then(|params| params.get("wait"))
                                .and_then(|value| value.as_bool())
                                .unwrap_or(false);
                            self.players[p_idx].push_energy_card(cid, is_wait);
                        }
                    } else if selected_frame.opcode() == O_RECOVER_MEMBER {
                        if let Some(recover_pos) =
                            self.players[p_idx].discard.iter().position(|&cid| {
                                db.get_member(cid).is_some()
                                    && self.card_matches_filter_with_ctx(
                                        db,
                                        cid,
                                        selected_frame.attr(),
                                        &pi.ctx,
                                    )
                            })
                        {
                            if let Some(cid) = self.players[p_idx].remove_discard_card(recover_pos)
                            {
                                self.players[p_idx].gain_hand_card(cid);
                            }
                        }
                    }

                    if remaining_mask > 0 {
                        let mut next_ctx = pi.ctx.clone();
                        if !next_ctx.selected_cards.contains(&choice_idx) {
                            next_ctx.selected_cards.push(choice_idx);
                        }
                        next_ctx.choice_index = -1;
                        next_ctx.v_accumulated = encode_optional_mode_mask(remaining_mask);
                        let choice_text =
                            crate::core::logic::interpreter::get_choice_text(db, &next_ctx);
                        crate::core::logic::interpreter::suspend_interaction(
                            self,
                            db,
                            &next_ctx,
                            0,
                            O_SELECT_MODE,
                            0,
                            ChoiceType::SelectMode,
                            &choice_text,
                            0,
                            remaining_mask.count_ones() as i16,
                            Vec::new(),
                            Vec::new(),
                        );
                        return Ok(());
                    }

                    crate::core::logic::interpreter::restore_response_state(
                        self,
                        response_origin.0,
                        response_origin.1,
                    );
                    self.check_win_condition();
                    return Ok(());
                }
            }

            if let Some((_filter_attr, heart_color_idx)) =
                pending_targeted_live_heart_bonus(db, &pi)
            {
                if let DecodedAction::SelectStageSlot { slot_idx } = decoded_action {
                    let p_idx = pi.ctx.player_id as usize;
                    if (slot_idx as usize) < STAGE_SLOT_COUNT {
                        self.players[p_idx].heart_buffs[slot_idx as usize]
                            .add_to_color(heart_color_idx as usize, 1);
                    }
                    self.interaction_stack.pop();

                    let current_execution_id = self.ui.current_execution_id.unwrap_or(0);
                    let was_cancelled = current_execution_id > 0
                        && self
                            .ui
                            .cancelled_execution_ids
                            .remove(&current_execution_id);
                    if !was_cancelled {
                        let res_trigger = match pi.ctx.trigger_type {
                            crate::core::enums::TriggerType::OnLiveStart => {
                                Some(crate::core::enums::TriggerType::OnAbilityResolve)
                            }
                            crate::core::enums::TriggerType::OnLiveSuccess => {
                                Some(crate::core::enums::TriggerType::OnAbilitySuccess)
                            }
                            _ => None,
                        };

                        if let Some(t) = res_trigger {
                            let mut res_ctx = pi.ctx.clone();
                            res_ctx.target_card_id = pi.ctx.source_card_id;
                            self.trigger_abilities_from(db, t, &res_ctx, 0);
                        }
                    }

                    crate::core::logic::interpreter::restore_response_state(
                        self,
                        response_origin.0,
                        response_origin.1,
                    );
                    self.check_win_condition();
                    return Ok(());
                }
            }

            if is_optional_live_start_discard_decline(db, &pi.ctx, choice_idx) {
                if let Some(execution_id) = self.ui.current_execution_id {
                    self.ui.cancelled_execution_ids.insert(execution_id);
                }
            }
        }

        if self.interaction_stack.is_empty() {
            crate::core::logic::interpreter::restore_response_state(
                self,
                response_origin.0,
                response_origin.1,
            );
            self.check_win_condition();
            return Ok(());
        }

        let (execution_id, ctx_res) = {
            let pi = if let Some(p) = self.interaction_stack.last() {
                p
            } else {
                return Ok(());
            };
            (pi.execution_id, pi.ctx.clone())
        };

        let choice_idx = match decoded_action {
            DecodedAction::Pass => 99,
            DecodedAction::SelectMode { mode_idx }
            | DecodedAction::SelectChoice { choice_idx: mode_idx }
            | DecodedAction::SelectColor { color_idx: mode_idx } => mode_idx,
            DecodedAction::PlayMember { hand_idx, .. }
            | DecodedAction::SelectEnergy { energy_idx: hand_idx }
            | DecodedAction::SelectStageSlot { slot_idx: hand_idx } => hand_idx as i32,
            _ => -1,
        };

        self.ui.current_execution_id = if execution_id > 0 {
            Some(execution_id)
        } else {
            None
        };

        let pending_choice_type = self
            .interaction_stack
            .last()
            .map(|pi| pi.choice_type)
            .unwrap_or(ChoiceType::None);

        let slot_idx = ctx_res.area_idx as usize;
        let ab_idx_call = if ctx_res.ability_index < 0 {
            0
        } else {
            ctx_res.ability_index as usize
        };
        let target_slot = ctx_res.target_slot as i32;

        if self.debug.debug_mode {
            println!(
                "[DEBUG_RESPONSE_DISPATCH] decoded={:?} pending={:?} choice_idx={} target_slot={} slot_idx={} ab_idx={} hand_idx={} target_card_id={}",
                decoded_action,
                pending_choice_type,
                choice_idx,
                target_slot,
                slot_idx,
                ab_idx_call,
                self.interaction_stack
                    .last()
                    .map(|pi| pi.ctx.selected_hand_idx)
                    .unwrap_or(-1),
                self.interaction_stack
                    .last()
                    .map(|pi| pi.ctx.target_card_id)
                    .unwrap_or(-1)
            );
        }

        let target_slot = match pending_choice_type {
            ChoiceType::SelectStage
            | ChoiceType::SelectStageEmpty
            | ChoiceType::SelectStageEmptyBaton => choice_idx,
            ChoiceType::SelectMember => -1,
            _ => target_slot,
        };

        self.activate_ability_with_choice(db, slot_idx, ab_idx_call, choice_idx, target_slot)?;

        if !self.interaction_stack.is_empty() {
            return Ok(());
        }

        if matches!(
            pending_choice_type,
            ChoiceType::SelectStage | ChoiceType::SelectMember
        ) && ctx_res.source_card_id >= 0
        {
            crate::core::logic::interpreter::restore_response_state(
                self,
                response_origin.0,
                response_origin.1,
            );
            self.process_rule_checks(db);
            self.check_win_condition();
            return Ok(());
        }

        self.clear_execution_id();
        crate::core::logic::interpreter::restore_response_state(
            self,
            response_origin.0,
            response_origin.1,
        );
        self.check_win_condition(); // Check if ability caused a win
        Ok(())
    }

    fn play_member_with_choice(
        &mut self,
        db: &CardDatabase,
        hand_idx: usize,
        slot_idx: usize,
        secondary_slot_idx: i16,
        choice_idx: i32,
        start_ab_idx: usize,
    ) -> Result<(), String> {
        let p_idx = self.current_player as usize;
        if self.phase == Phase::Response {
            return self.resume_play_member(db, choice_idx, start_ab_idx);
        }
        if hand_idx >= self.core.players[p_idx].hand.len() {
            return Err("Invalid hand index".to_string());
        }
        if slot_idx >= 3 {
            return Err("Invalid slot index".to_string());
        }

        let card_id = self.core.players[p_idx].hand[hand_idx];
        let card = db.get_member(card_id).ok_or("Card not found")?;
        self.check_play_legality(db, p_idx, card_id, slot_idx, secondary_slot_idx)?;

        let mut cost =
            self.get_member_cost(p_idx, card_id, slot_idx as i16, secondary_slot_idx, db, 0);
        cost = cost.max(0);
        let untap_energy_indices =
            self.core.players[p_idx].get_untapped_energy_indices(cost as usize);

        if !self.debug.debug_ignore_conditions {
            if untap_energy_indices.len() < cost as usize {
                if self.debug.debug_mode {
                    println!(
                        "[DEBUG] play_member_with_choice: FAILED! cost={}, available={}",
                        cost,
                        untap_energy_indices.len()
                    );
                }
                return Err("Not enough energy".to_string());
            }
            if !self.ui.silent {
                if cost > 0 {
                    self.log(format!(
                        "Rule 9.6.2.3: Tapping {} energy for play cost (Rule 9.4).",
                        cost
                    ));
                } else {
                    self.log("Rule 9.6.2.3: No energy tapped (cost <= 0).".to_string());
                }
            }
            for i in untap_energy_indices {
                self.core.players[p_idx].set_energy_tapped(i, true);
            }
        }

        // Unified logging: records to both turn_history and rule_log
        self.log_event(
            "PLAY",
            &format!(
                "Player {} plays {} to Slot {}",
                p_idx,
                card.name,
                slot_idx + 1
            ),
            card_id,
            -1,
            p_idx as u8,
            Some("Rule 9.6.2.1, Rule 9.6.2.4.1 (Placement)"),
            true,
        );
        if !self.ui.silent {
            if secondary_slot_idx >= 0 {
                self.log(format!("Rule 9.6.2.3.2, Rule 9.6.2.3.2.1: Player {} performs [バトンタッチ] (Baton Touch) at Slot {} with Slot {}. (Q194, Q199 verified)", p_idx, slot_idx + 1, secondary_slot_idx + 1));
            } else {
                self.log(format!(
                    "Rule 9.6.2.4.1: Player {} plays card ID {} to Slot {}.",
                    p_idx,
                    card_id,
                    slot_idx + 1
                ));
            }
            self.log(format!(
                "Rule 3.2.1, 3.2.2, 3.2.3, 3.2.4, 3.2.5 (2.2.1, 2.3.1, 2.4.1, 2.5.1, 2.6.1, 2.7.1): Played member attributes: Cost={}, Blades={}, Hearts={:?}.",
                card.cost, card.blades, card.hearts
            ));
        }

        self.execute_play_member_state(
            db,
            p_idx,
            hand_idx,
            card_id,
            slot_idx,
            secondary_slot_idx,
            start_ab_idx,
            choice_idx,
        );
        Ok(())
    }

    fn activate_ability(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
    ) -> Result<(), String> {
        self.activate_ability_with_choice(db, slot_idx, ab_idx, -1, -1)
    }

    fn activate_ability_with_choice(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
        choice_idx: i32,
        target_slot: i32,
    ) -> Result<(), String> {
        if db.is_vanilla {
            return Err("Abilities are disabled in vanilla mode".to_string());
        }
        if !self.ui.silent && self.interaction_stack.is_empty() {
            self.log("Rule 9.1.1.1 (11.5.1): Activating [起動] (Activated) ability.".to_string());
        }

        let p_idx = self.current_player as usize;
        if self.phase == Phase::Response || !self.interaction_stack.is_empty() {
            let response_origin = pending_response_origin(self);
            let pending = if let Some(pi) = self.interaction_stack.last().cloned() {
                pi
            } else {
                return Err("No pending interaction".to_string());
            };
            let (cid, mut ctx) = {
                let restored_phase = pending.ctx.original_phase.unwrap_or_else(|| {
                    if pending.original_phase == Phase::Setup {
                        self.phase
                    } else {
                        pending.original_phase
                    }
                });
                let mut c = pending.ctx.clone();
                c.choice_index = choice_idx as i16;
                c.original_phase = Some(restored_phase);
                if pending.choice_type == ChoiceType::SelectMember {
                    let selected_card_id = self.core.players[p_idx]
                        .looked_cards
                        .get(choice_idx.max(0) as usize)
                        .copied()
                        .or_else(|| {
                            self.core.players[p_idx]
                                .hand
                                .get(choice_idx.max(0) as usize)
                                .copied()
                        })
                        .unwrap_or(-1);
                    c.selected_hand_idx = choice_idx as i16;
                    c.target_card_id = selected_card_id;
                    if c.target_card_id >= 0 && !c.selected_cards.contains(&c.target_card_id) {
                        c.selected_cards.push(c.target_card_id);
                    }
                }
                if target_slot >= 0 {
                    c.target_slot = target_slot as i16;
                }
                (pending.card_id, c)
            };

            if pending.choice_type == ChoiceType::SelectStage {
                match pending.effect_opcode {
                    O_PLAY_MEMBER_FROM_HAND => {
                        let stage_slot =
                            self.resolve_pending_stage_slot(&pending, choice_idx, p_idx);
                        let mut play_ctx = pending.ctx.clone();
                        play_ctx.choice_index = stage_slot as i16;
                        play_ctx.target_slot = stage_slot as i16;
                        let p_idx = play_ctx.player_id as usize;
                        let hand_idx = if play_ctx.target_card_id >= 0 {
                            let card_id = play_ctx.target_card_id;
                            self.core.players[p_idx]
                                .hand
                                .iter()
                                .position(|&cid| cid == card_id)
                        } else {
                            None
                        };

                        let Some(hand_idx) = hand_idx else {
                            return Err("No selected hand card".to_string());
                        };

                        if play_ctx.selected_hand_idx < 0 {
                            play_ctx.selected_hand_idx = hand_idx as i16;
                        }

                        let result = crate::core::logic::interpreter::handlers::state::finalize_play_member_from_hand(
                            self,
                            db,
                            &mut play_ctx,
                            p_idx,
                            hand_idx,
                            stage_slot,
                        );

                        if let Some(pos) = self.interaction_stack.iter().rposition(|pi| {
                            pi.choice_type == pending.choice_type
                                && pi.effect_opcode == O_PLAY_MEMBER_FROM_HAND
                                && pi.card_id == pending.card_id
                        }) {
                            self.interaction_stack.remove(pos);
                        }

                        if !self.interaction_stack.is_empty() {
                            return Ok(());
                        }

                        if matches!(result, crate::core::logic::interpreter::HandlerResult::Suspend) {
                            return Ok(());
                        }

                        if !self.trigger_queue.is_empty() {
                            self.process_trigger_queue(db);
                        }
                        self.process_rule_checks(db);
                        crate::core::logic::interpreter::restore_response_state(
                            self,
                            response_origin.0,
                            response_origin.1,
                        );
                        self.check_win_condition();
                        return Ok(());
                    }
                    O_PLAY_MEMBER_FROM_DISCARD => {
                        let stage_slot =
                            self.resolve_pending_stage_slot(&pending, choice_idx, p_idx);
                        let mut play_ctx = pending.ctx.clone();
                        play_ctx.choice_index = stage_slot as i16;
                        let p_idx = play_ctx.player_id as usize;
                        if play_ctx.target_card_id < 0 {
                            return Err("No pending discard-play card".to_string());
                        }

                        if let Some(pos) = self.interaction_stack.iter().rposition(|pi| {
                            pi.choice_type == pending.choice_type
                                && pi.effect_opcode == O_PLAY_MEMBER_FROM_DISCARD
                                && pi.card_id == pending.card_id
                        }) {
                            self.interaction_stack.remove(pos);
                        }

                        let is_total_cost = (pending.filter_attr & (1u64 << 60)) != 0
                            || (pending.filter_attr & (1u64 << 50)) != 0;
                        let frame_idx = play_ctx.program_counter as usize;
                        let remaining = play_ctx.v_remaining;

                        let result = crate::core::logic::interpreter::handlers::state::handle_discard_placement(
                            self,
                            db,
                            &mut play_ctx,
                            p_idx,
                            pending.filter_attr,
                            false,
                            false,
                            is_total_cost,
                            frame_idx,
                            remaining,
                            stage_slot as i32,
                        );

                        if !self.interaction_stack.is_empty() {
                            return Ok(());
                        }

                        if matches!(result, crate::core::logic::interpreter::HandlerResult::Suspend) {
                            return Ok(());
                        }

                        if !self.trigger_queue.is_empty() {
                            self.process_trigger_queue(db);
                        }
                        self.process_rule_checks(db);
                        crate::core::logic::interpreter::restore_response_state(
                            self,
                            response_origin.0,
                            response_origin.1,
                        );
                        self.check_win_condition();
                        return Ok(());
                    }
                    _ => {}
                }
            }

            if pending.choice_type == ChoiceType::SelectDiscardPlay
                && pending.effect_opcode == O_PLAY_MEMBER_FROM_DISCARD
            {
                // Handle CHOICE_DONE (99) - user wants to skip selecting more cards
                if choice_idx == crate::core::logic::constants::CHOICE_DONE as i32 {
                    crate::core::logic::interpreter::suspension::finish_pending_interaction(self);
                    return Ok(());
                }

                let pick_idx = choice_idx.max(0) as usize;
                let selected_card_id = self
                    .core
                    .players
                    .get(p_idx)
                    .and_then(|player| player.looked_cards.get(pick_idx).copied())
                    .unwrap_or(-1);
                if selected_card_id < 0 {
                    return Err("No selected discard card".to_string());
                }

                let mut play_ctx = pending.ctx.clone();
                play_ctx.choice_index = -1;
                play_ctx.target_card_id = selected_card_id;
                play_ctx.v_remaining = pending.v_remaining;
                if !play_ctx.selected_cards.contains(&selected_card_id) {
                    play_ctx.selected_cards.push(selected_card_id);
                }

                crate::core::logic::interpreter::suspension::finish_pending_interaction(self);
                crate::core::logic::interpreter::suspension::suspend_interaction(
                    self,
                    db,
                    &play_ctx,
                    play_ctx.program_counter as usize,
                    O_PLAY_MEMBER_FROM_DISCARD,
                    -1,
                    ChoiceType::SelectStage,
                    &crate::core::models::interpreter::get_choice_text(db, &play_ctx),
                    pending.filter_attr,
                    pending.v_remaining,
                    Vec::new(),
                    Vec::new(),
                );
                return Ok(());
            }

            // Consume the answered prompt using the shared stack/phase helper.
            crate::core::logic::interpreter::suspension::finish_pending_interaction(self);

            let semantic_frames = if cid == -1 {
                Some(vec![
                    crate::core::logic::models::AbilityFrame::Semantic {
                        opcode: pending.effect_opcode,
                        value: pending.ctx.v_remaining as i32,
                        filter: crate::core::logic::filter::CardFilter::from_attr(
                            pending.filter_attr as i64,
                        ),
                        slot: crate::core::logic::interpreter::instruction::DecodedSlot::default(),
                        is_negated: false,
                        is_cost: false,
                        params: serde_json::Value::Null,
                    },
                    crate::core::logic::models::AbilityFrame::Return,
                ])
            } else {
                None
            };

            if let Some(frames) = semantic_frames {
                let _ = crate::core::logic::interpreter::resolve_semantic_frames(
                    self, db, &frames, &ctx,
                );
            } else {
                if let Some(member) = db.get_member(cid) {
                    if let Some(ab) = member.abilities.get(ab_idx) {
                        if ab.costs.iter().any(|cost| cost.is_optional)
                            && !crate::core::logic::interpreter::costs::pay_costs_transactional_including_optional(
                                self,
                                db,
                                &ab.costs,
                                &mut ctx,
                            )
                        {
                            return Err("Cannot afford costs".to_string());
                        }
                        self.resolve_ability(db, ab, &ctx);
                    } else {
                        return Err(format!(
                            "Ability index {} not found on card {}",
                            ab_idx, cid
                        ));
                    }
                } else if let Some(live) = db.get_live(cid) {
                    if let Some(ab) = live.abilities.get(ab_idx) {
                        if ab.costs.iter().any(|cost| cost.is_optional)
                            && !crate::core::logic::interpreter::costs::pay_costs_transactional_including_optional(
                                self,
                                db,
                                &ab.costs,
                                &mut ctx,
                            )
                        {
                            return Err("Cannot afford costs".to_string());
                        }
                        self.resolve_ability(db, ab, &ctx);
                    } else {
                        return Err(format!(
                            "Ability index {} not found on card {}",
                            ab_idx, cid
                        ));
                    }
                } else {
                    return Err(format!(
                        "Ability index {} not found on card {}",
                        ab_idx, cid
                    ));
                }
            }

            if is_optional_live_start_discard_decline(db, &ctx, choice_idx) {
                let p_idx = ctx.player_id as usize;
                let slot_idx = ctx.area_idx as usize;
                if slot_idx < STAGE_SLOT_COUNT {
                    self.players[p_idx].heart_buffs[slot_idx].add_to_color(6, -1);
                }
            }

            // Restore phase only if no new suspension occurred
            let current_execution_id = self.ui.current_execution_id.unwrap_or(0);
            let was_cancelled = current_execution_id > 0
                && self
                    .ui
                    .cancelled_execution_ids
                    .remove(&current_execution_id);
            let suppress_resolve_trigger =
                is_optional_live_start_discard_decline(db, &ctx, choice_idx);
            if !was_cancelled {
                let res_trigger = match ctx.trigger_type {
                    crate::core::enums::TriggerType::OnLiveStart => {
                        Some(crate::core::enums::TriggerType::OnAbilityResolve)
                    }
                    crate::core::enums::TriggerType::OnLiveSuccess => {
                        Some(crate::core::enums::TriggerType::OnAbilitySuccess)
                    }
                    _ => None,
                };

                if let Some(t) = res_trigger {
                    if !suppress_resolve_trigger {
                        let mut res_ctx = ctx.clone();
                        res_ctx.target_card_id = cid;
                        self.trigger_abilities_from(db, t, &res_ctx, 0);
                    }
                }
            }

            if !self.interaction_stack.is_empty() {
                return Ok(());
            }

            self.process_rule_checks(db);

            crate::core::logic::interpreter::restore_response_state(
                self,
                response_origin.0,
                response_origin.1,
            );
            return Ok(());
        }

        let cid = if slot_idx < STAGE_SLOT_COUNT as usize {
            let scid = self.core.players[p_idx].stage[slot_idx];
            if scid >= 0 {
                scid
            } else {
                self.core.players[p_idx].live_zone[slot_idx]
            }
        } else if slot_idx >= 100 && slot_idx < 200 {
            let d_idx = slot_idx - 100;
            self.core.players[p_idx]
                .discard
                .get(d_idx)
                .cloned()
                .unwrap_or(-1)
        } else if slot_idx >= 200 && slot_idx < 300 {
            let h_idx = slot_idx - 200;
            self.core.players[p_idx]
                .hand
                .get(h_idx)
                .cloned()
                .unwrap_or(-1)
        } else {
            -1
        };

        let card = db
            .get_member(cid)
            .ok_or_else(|| format!("Card not found: {}", cid))?;
        let ab = card
            .abilities
            .get(ab_idx)
            .ok_or_else(|| format!("Ability index {} not found on {}", ab_idx, card.name))?;

        if !self.debug.debug_ignore_conditions
            && ab.trigger != TriggerType::Activated
            && self.phase != Phase::Response
        {
            return Err("Not an activated ability".to_string());
        }

        // Unified logging: records to both turn_history and rule_log
        let p_code = if ab.pseudocode.is_empty() {
            ""
        } else {
            &format!(": {}", ab.pseudocode)
        };
        self.log_event(
            "ACTIVATE",
            &format!(
                "Player {} activates ability of {}{}",
                p_idx, card.name, p_code
            ),
            cid,
            ab_idx as i16,
            p_idx as u8,
            Some("Rule 7.7.2.1"),
            true,
        );

        let mut ctx = AbilityContext {
            source_card_id: cid,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: slot_idx as i16,
            ability_index: ab_idx as i16,
            choice_index: choice_idx as i16,
            ..Default::default()
        };
        ctx.capture_state_raw(self.phase, self.current_player);
        if target_slot >= 0 {
            ctx.target_slot = target_slot as i16;
        }
        let source_type = if slot_idx < STAGE_SLOT_COUNT as usize {
            0
        } else {
            1
        }; // 0=Stage, 1=Other
        let instance_key =
            self.get_once_per_turn_instance_key(p_idx, source_type, slot_idx as i16, cid);

        // ENFORCEMENT PHASE: Check conditions and costs
        if !self.debug.debug_ignore_conditions {
            if self.core.players[p_idx].prevent_activate() > 0 {
                return Err("Cannot activate abilities due to restriction".to_string());
            }

            if ab.is_once_per_turn {
                if !self.check_once_per_turn(p_idx, source_type, instance_key, cid as u32, ab_idx) {
                    return Err("Ability already used this turn".to_string());
                }
            }

            for cond in &ab.conditions {
                if !self.check_condition_opcode(
                    db,
                    cond.condition_type as i32,
                    cond.value,
                    cond.attr,
                    cond.target_slot as i32,
                    &ctx,
                    1,
                ) {
                    if !self.ui.silent {
                        let cond_desc = super::interpreter::logging::describe_condition(
                            cond.condition_type as i32,
                            cond.value,
                            cond.attr,
                        );
                        self.log(format!("Ability activation failed: {}.", cond_desc));
                    }
                    return Err("Conditions not met".to_string());
                }
            }
            if !costs::pay_costs_transactional(self, db, &ab.costs, &mut ctx) {
                return Err("Cannot afford costs".to_string());
            }

            if ab.is_once_per_turn {
                self.consume_once_per_turn(p_idx, source_type, instance_key, cid as u32, ab_idx);
            }
        }

        self.resolve_ability(db, ab, &ctx);
        self.process_rule_checks(db);
        Ok(())
    }
}

fn is_optional_live_start_discard_decline(
    db: &CardDatabase,
    ctx: &AbilityContext,
    choice_idx: i32,
) -> bool {
    choice_idx == 1
        && ctx.trigger_type == crate::core::enums::TriggerType::OnLiveStart
        && pending_member_ability(db, ctx.source_card_id, ctx.ability_index)
            .map(is_optional_live_start_discard_count_ability)
            .unwrap_or(false)
}

fn pending_response_origin(state: &GameState) -> (Phase, u8) {
    state
        .interaction_stack
        .last()
        .map(|pi| (pi.original_phase, pi.original_current_player))
        .unwrap_or((state.phase, state.current_player))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::generated_constants::ACTION_BASE_STAGE;
    use crate::core::logic::card_db::LOGIC_ID_MASK;
    use crate::core::models::{Ability, MemberCard};
    use crate::test_helpers::create_test_state;

    #[test]
    fn vanilla_mode_rejects_manual_activated_ability_actions() {
        let mut db = CardDatabase::default();
        db.is_vanilla = true;

        let member = MemberCard {
            card_id: 700,
            abilities: vec![Ability {
                trigger: TriggerType::Activated,
                bytecode: vec![O_DRAW, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0],
                ..Default::default()
            }],
            ..Default::default()
        };

        db.members.insert(700, member.clone());
        let logic_id = (700 & LOGIC_ID_MASK) as usize;
        if logic_id >= db.members_vec.len() {
            db.members_vec.resize(logic_id + 1, None);
        }
        db.members_vec[logic_id] = Some(member);

        let mut state = create_test_state();
        state.players[0].stage[0] = 700;

        let err = state.step(&db, ACTION_BASE_STAGE).unwrap_err();
        assert!(
            err.contains("Abilities are disabled in vanilla mode"),
            "unexpected error: {err}"
        );
    }
}

impl TurnPhaseController for GameState {
    fn do_active_phase(&mut self, db: &CardDatabase) {
        if self.phase != Phase::Active {
            return;
        }
        let p_idx = self.current_player as usize;
        self.setup_turn_log();

        let skip = self.core.players[p_idx].skip_next_activate();
        if skip {
            if !self.ui.silent {
                self.log(format!("Rule 7.2, Rule 7.2.1, Rule 7.2.1.1, Rule 7.2.1.2: [Active Phase] SKIPPED (untapping skipped) for Player {}.", p_idx));
            }
            self.core.players[p_idx].set_skip_next_activate(false);
        } else {
            if !self.ui.silent {
                self.log(format!("Rule 7.2, Rule 7.2.1, Rule 7.2.1.1, Rule 7.2.1.2: [Active Phase] Untapping all cards for Player {}.", p_idx));
            }
        }

        self.core.players[p_idx].untap_all(skip);
        
        // Fast path: skip TurnStart trigger if no cards (nothing to trigger)
        let has_cards = self.core.players[p_idx].stage.iter().any(|&c| c >= 0)
            || self.core.players[p_idx].live_zone.iter().any(|&c| c >= 0);
        if has_cards || !db.is_vanilla {
            let ctx = AbilityContext {
                source_card_id: -1,
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: -1,
                ..Default::default()
            };
            self.trigger_abilities(db, TriggerType::TurnStart, &ctx);
        }
        
        if self.phase == Phase::Active {
            self.phase = Phase::Energy;
            if !self.ui.silent {
                self.log("Rule 7, Rule 7.3, Rule 7.3.1, Rule 7.3.2, Rule 7.3.2.1, Rule 7.3.3: --- ENERGY PHASE ---".to_string());
                self.log(format!(
                    "Rule 7.3.1: Entering Energy Phase for Player {}.",
                    p_idx
                ));
            }
        }
    }

    fn do_energy_phase(&mut self) {
        if self.phase != Phase::Energy {
            return;
        }
        let p_idx = self.current_player as usize;
        if let Some(card_id) = self.core.players[p_idx].energy_deck.pop() {
            if !self.ui.silent {
                self.log(format!(
                    "Rule 7.3.2, Rule 7.3.2.1: Player {} placed Energy from Energy Deck",
                    p_idx
                ));
            }
            self.core.players[p_idx].push_energy_card(card_id, false);
        }
        self.phase = Phase::Draw;
        if !self.ui.silent {
            self.log(
                "Rule 7.4, Rule 7.4.1, Rule 7.4.2, Rule 7.4.3: --- DRAW PHASE ---".to_string(),
            );
            self.log(format!(
                "Rule 7.4.1: Entering Draw Phase for Player {}.",
                p_idx
            ));
        }
    }

    fn do_draw_phase(&mut self, db: &CardDatabase) {
        let p_idx = self.current_player as usize;
        
        // Fast path: skip TurnStart trigger if no cards (nothing to trigger)
        let has_cards = self.core.players[p_idx].stage.iter().any(|&c| c >= 0)
            || self.core.players[p_idx].live_zone.iter().any(|&c| c >= 0);
        if has_cards || !db.is_vanilla {
            let ctx = AbilityContext {
                source_card_id: -1,
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: -1,
                ..Default::default()
            };
            self.trigger_abilities(db, TriggerType::TurnStart, &ctx);
        }

        if self.phase != Phase::Draw {
            return;
        }
        if !self.ui.silent {
            self.log(format!("Rule 7.6.2: Player {} draws a card.", p_idx));
            self.log_event(
                "DRAW",
                "Player draws 1 card",
                -1,
                -1,
                p_idx as u8,
                Some("Rule 7.4.2"),
                true,
            );
        }
        self.draw_cards(p_idx, 1);
        self.phase = Phase::Main;
        if !self.ui.silent {
            self.log(
                "Rule 7.5, Rule 7.5.1, Rule 7.5.2, Rule 7.5.3: --- MAIN PHASE ---".to_string(),
            );
            self.log(format!(
                "Rule 7.5.1: Entering Main Phase for Player {}.",
                p_idx
            ));
        }
    }
}

// Extracted helpers that remain in GameState impl but in this file
impl GameState {
    fn resolve_pending_stage_slot(
        &self,
        pending: &PendingInteraction,
        choice_idx: i32,
        p_idx: usize,
    ) -> usize {
        let stage_slot = pending
            .actions
            .get(choice_idx.max(0) as usize)
            .copied()
            .and_then(|action| match ActionFactory::parse_action(action) {
                DecodedAction::SelectStageSlot { slot_idx } => Some(slot_idx),
                DecodedAction::SelectChoice { choice_idx } => Some(choice_idx.max(0) as usize),
                _ => None,
            })
            .unwrap_or_else(|| choice_idx.max(0) as usize);

        if stage_slot >= 3 {
            return stage_slot;
        }

        let player = &self.core.players[p_idx];
        let is_open = |slot_idx: usize| {
            let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
            !prevented && !player.is_moved(slot_idx)
        };

        if is_open(stage_slot) {
            stage_slot
        } else {
            (0..3).find(|&slot_idx| is_open(slot_idx)).unwrap_or(stage_slot)
        }
    }

    fn resume_play_member(
        &mut self,
        db: &CardDatabase,
        choice_idx: i32,
        start_ab_idx: usize,
    ) -> Result<(), String> {
        let stack_len_before = self.interaction_stack.len();
        let (card_id, ctx) = if let Some(pi) = self.interaction_stack.last() {
            let mut c = pi.ctx.clone();
            c.choice_index = choice_idx as i16;
            (pi.card_id, c)
        } else {
            return Err("No pending interaction found in Response phase".to_string());
        };

        let card = db.get_member(card_id as i32).ok_or("Card not found")?;
        if !self.ui.silent {
            self.log_rule(
                "Rule 11.3",
                &format!(
                    "Resuming [登場] (On Play) abilities for {} from idx {}.",
                    card.name, start_ab_idx
                ),
            );
        }

        self.trigger_event(
            db,
            TriggerType::OnPlay,
            ctx.player_id as usize,
            card_id as i32,
            ctx.area_idx,
            start_ab_idx,
            ctx.choice_index,
        );
        if self.interaction_stack.len() >= stack_len_before && stack_len_before > 0 {
            let remove_idx = stack_len_before - 1;
            if remove_idx < self.interaction_stack.len() {
                self.interaction_stack.remove(remove_idx);
            }
        }
        self.process_rule_checks(db);
        Ok(())
    }

    fn check_play_legality(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        _card_id: i32,
        slot_idx: usize,
        secondary_slot_idx: i16,
    ) -> Result<(), String> {
        if self.debug.debug_ignore_conditions {
            return Ok(());
        }
        let player = &self.core.players[p_idx];
        if (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0
            && player.stage[slot_idx] >= 0
        {
            return Err("Cannot play to this slot due to restriction".to_string());
        }
        if player.is_moved(slot_idx) {
            if !self.ui.silent {
                self.log("Compliance Check: Rule 9.6.2.1.2.1 (Q194, Q199) - Cannot play to a slot where a member already moved/placed this turn.".to_string());
            }
            return Err("Already played/moved to this slot this turn".to_string());
        }

        let old_card_id = player.stage[slot_idx];
        if old_card_id >= 0 {
            if player.baton_touch_count() >= player.baton_touch_limit() {
                return Err("Baton touch limit reached".to_string());
            }
            if player.prevent_baton_touch() > 0 {
                return Err("Baton Touch is restricted".to_string());
            }
            if GameState::has_restriction(self, p_idx, slot_idx, O_PREVENT_BATON_TOUCH, db) {
                return Err("Baton Touch is not allowed for this member".to_string());
            }
        }

        if secondary_slot_idx >= 0 {
            let s_idx = secondary_slot_idx as usize;
            if s_idx >= 3 || player.stage[s_idx] < 0 || player.is_moved(s_idx) {
                if !self.ui.silent && player.is_moved(s_idx) {
                    self.log("Compliance Check: Rule 9.6.2.1.2.1 (Q194, Q199) - Cannot [バトンタッチ] (Baton Touch) a member that joined the stage this turn.".to_string());
                }
                return Err("Invalid secondary baton touch target".to_string());
            }
        }
        Ok(())
    }

    fn execute_play_member_state(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        hand_idx: usize,
        card_id: i32,
        slot_idx: usize,
        secondary_slot_idx: i16,
        start_ab_idx: usize,
        choice: i32,
    ) {
        let old_card_id = self.core.players[p_idx].stage[slot_idx];
        if old_card_id >= 0 {
            if !self.ui.silent {
                self.log("Rule 11.6, Rule 11.6.4 (Q24, Q27): Performing [バトンタッチ] (Baton Touch) replacing 1 member.".to_string());
            }
            self.core.players[p_idx]
                .set_baton_touch_count(self.core.players[p_idx].baton_touch_count() + 1);
            self.core.players[p_idx].baton_source_ids.push(old_card_id);
            self.core.players[p_idx].baton_source_slots.push(slot_idx);
        }
        if secondary_slot_idx >= 0 {
            let s_idx = secondary_slot_idx as usize;
            self.core.players[p_idx]
                .set_baton_touch_count(self.core.players[p_idx].baton_touch_count() + 1);
            let secondary_old_id = self.core.players[p_idx].stage[s_idx];
            if secondary_old_id >= 0 {
                self.core.players[p_idx]
                    .baton_source_ids
                    .push(secondary_old_id);
                self.core.players[p_idx].baton_source_slots.push(s_idx);
            }
            let leave_ctx = AbilityContext {
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: s_idx as i16,
                target_card_id: card_id,
                ..Default::default()
            };
            if let Some(old) = self.handle_member_leaves_stage(p_idx, s_idx, db, &leave_ctx) {
                self.core.players[p_idx].push_discard_card(old);
            }
            if !self.ui.silent {
                self.log("Rule 11.6, Rule 11.6.4 (Q24): Performing secondary [バトンタッチ] (Baton Touch).".to_string());
            }
            self.core.players[p_idx].set_moved(s_idx, true);
        }

        self.core.players[p_idx].remove_hand_card(hand_idx);

        if old_card_id >= 0 {
            let leave_ctx = AbilityContext {
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: slot_idx as i16,
                target_card_id: card_id,
                ..Default::default()
            };
            if let Some(old) = self.handle_member_leaves_stage(p_idx, slot_idx, db, &leave_ctx) {
                if !self.ui.silent {
                    self.log(format!(
                        "Rule 11.6.3 (4.11.2): Moving old member {} to Discard.",
                        old
                    ));
                }
                self.core.players[p_idx].push_discard_card(old);
            }
        }

        self.prev_card_id = old_card_id;
        self.core.players[p_idx].stage[slot_idx] = card_id;
        self.core.players[p_idx].set_tapped(slot_idx, false);
        self.core.players[p_idx].set_moved(slot_idx, true);

        self.register_played_member(p_idx, card_id, db);

        self.trigger_event(
            db,
            TriggerType::OnPlay,
            p_idx,
            card_id,
            slot_idx as i16,
            start_ab_idx,
            choice as i16,
        );
        self.process_rule_checks(db);
    }
}
