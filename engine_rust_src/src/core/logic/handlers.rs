use crate::core::enums::*;
use crate::core::generated_constants::{ACTION_BASE_RPS, ACTION_BASE_RPS_P2};
use crate::core::logic::{
    action_factory::DecodedAction, interpreter::costs, AbilityContext, ActionFactory, CardDatabase,
    GameState, Phase,
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
                self.log(format!("Rule 11.1.1: RPS Result: P0={}, P1={}", p0, p1));
            }

            if p0 == p1 {
                // Track draw count in turn - using turn field as a temporary overflow for RPS draws
                // if turn is 0 (RPS phase).
                let draw_count = (self.turn & 0x7) + 1;
                self.turn = (self.turn & !0x7) | (draw_count & 0x7);

                if !self.ui.silent {
                    self.log(format!("Rule 11.1.1: Draw #{}! Restarting RPS.", draw_count));
                }

                if draw_count >= 5 {
                    if !self.ui.silent {
                        self.log("Maximum RPS draws reached. P0 wins by default to progress.".to_string());
                    }
                    self.current_player = 0;
                    self.first_player = 0;
                    self.phase = Phase::Setup;
                    self.turn = 0; // Reset turn for game start
                } else {
                    self.rps_choices = [-1, -1];
                    self.current_player = 0;
                }
            } else {
                let p0_wins = (p0 == 0 && p1 == 2) || (p0 == 1 && p1 == 0) || (p0 == 2 && p1 == 1);
                let winner = if p0_wins { 0 } else { 1 };
                if !self.ui.silent {
                    self.log(format!(
                        "Rule 11.1.1: Player {} wins the RPS and chooses turn order.",
                        winner
                    ));
                }
                self.current_player = winner as u8;
                self.phase = Phase::TurnChoice;
            }
        }
        Ok(())
    }

    fn handle_turn_choice(&mut self, action: i32) -> Result<(), String> {
        if action == Self::ACTION_TURN_CHOICE_FIRST {
            let winner = self.current_player;
            self.first_player = winner;
            self.log(format!("Player {} chose to go first!", winner));
            self.phase = Phase::MulliganP1;
            self.current_player = winner;
        } else if action == Self::ACTION_TURN_CHOICE_SECOND {
            let winner = self.current_player;
            self.first_player = 1 - winner;
            self.log(format!("Player {} chose to go second!", winner));
            self.phase = Phase::MulliganP1;
            self.current_player = 1 - winner;
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
            let mut discards = Vec::new();
            for i in 0..60 {
                if (self.core.players[p_idx].mulligan_selection >> i) & 1 == 1 {
                    discards.push(i as usize);
                }
            }
            self.execute_mulligan(p_idx, discards);
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
                "[DEBUG] execute_mulligan: player={}, discards_len={}, current_phase={:?}",
                player_idx,
                discard_indices.len(),
                self.phase
            );
        }
        self.log(format!(
            "Rule 6.2.1.6: Player {} finished mulligan ({} cards)",
            player_idx,
            discard_indices.len()
        ));
        let mut count = 0;
        let mut discards = Vec::new();
        let mut new_hand = SmallVec::new();
        for (i, &cid) in self.core.players[player_idx].hand.iter().enumerate() {
            if discard_indices.contains(&i) {
                discards.push(cid);
                count += 1;
            } else {
                new_hand.push(cid);
            }
        }
        self.core.players[player_idx].hand = new_hand;
        let t = self.turn as i32;
        for _ in 0..count {
            if self.core.players[player_idx].deck.is_empty() {
                self.resolve_deck_refresh(player_idx);
            }
            if let Some(card_id) = self.core.players[player_idx].deck.pop() {
                self.core.players[player_idx].hand.push(card_id);
                self.core.players[player_idx].hand_added_turn.push(t);
            }
        }
        self.core.players[player_idx].deck.extend(discards);
        let mut rng = Pcg64::from_os_rng();
        self.core.players[player_idx].deck.shuffle(&mut rng);
        self.resolve_deck_refresh(player_idx);
        let prev_phase = self.phase;
        if self.phase == Phase::MulliganP1 {
            self.current_player = 1 - self.first_player;
            self.phase = Phase::MulliganP2;
        } else if self.phase == Phase::MulliganP2 {
            self.current_player = self.first_player;
            self.phase = Phase::Active;
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
        match ActionFactory::parse_action(action) {
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
            } else {
                self.phase = Phase::PerformanceP1;
                self.current_player = self.first_player;
            }
        } else if action >= ACTION_BASE_LIVESET && action < ACTION_BASE_LIVESET + 100 {
            let hand_idx = (action - ACTION_BASE_LIVESET) as usize;
            if hand_idx < self.core.players[p_idx].hand.len() {
                let cid = self.core.players[p_idx].hand[hand_idx];
                self.core.players[p_idx].hand.remove(hand_idx);
                if hand_idx < self.core.players[p_idx].hand_added_turn.len() {
                    self.core.players[p_idx].hand_added_turn.remove(hand_idx);
                }
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
                    self.core.players[p_idx].discard.push(cid);
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
                "Rule 7.7.3: Player {} ends Main Phase.",
                self.current_player
            ));
        }
        self.trigger_event(
            db,
            TriggerType::TurnEnd,
            self.current_player as usize,
            -1,
            -1,
            0,
            -1,
        );

        if self.current_player == self.first_player {
            self.current_player = 1 - self.first_player;
            self.phase = Phase::Active;
        } else {
            self.phase = Phase::LiveSet;
            self.current_player = self.first_player;
        }
    }
}
impl ResponseController for GameState {
    fn handle_response(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        let (execution_id, ctx_res) = {
            let pi = if let Some(p) = self.interaction_stack.last() {
                p
            } else {
                return Ok(());
            };
            (pi.execution_id, pi.ctx.clone())
        };

        let choice_idx = match ActionFactory::parse_action(action) {
            DecodedAction::Pass => 99,
            DecodedAction::SelectMode { mode_idx } => mode_idx,
            DecodedAction::PlayMember { hand_idx, .. } => hand_idx as i32,
            DecodedAction::SelectChoice { choice_idx } => choice_idx,
            DecodedAction::SelectColor { color_idx } => color_idx,
            DecodedAction::SelectEnergy { energy_idx } => energy_idx as i32,
            DecodedAction::SelectStageSlot { slot_idx } => slot_idx as i32,
            _ => -1,
        };

        self.ui.current_execution_id = if execution_id > 0 {
            Some(execution_id)
        } else {
            None
        };

        let slot_idx = ctx_res.area_idx as usize;
        let ab_idx_call = if ctx_res.ability_index < 0 {
            0
        } else {
            ctx_res.ability_index as usize
        };
        let target_slot = ctx_res.target_slot as i32;

        self.activate_ability_with_choice(db, slot_idx, ab_idx_call, choice_idx, target_slot)?;

        self.clear_execution_id();
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
            Some("Rule 7.7.2.2"),
            true,
        );

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
        let p_idx = self.current_player as usize;
        if self.phase == Phase::Response {
            let (cid, ctx, orig_phase, orig_cp) = if let Some(pi) = self.interaction_stack.last() {
                let mut c = pi.ctx.clone();
                c.choice_index = choice_idx as i16;
                c.original_phase = Some(pi.original_phase);
                if target_slot >= 0 {
                    c.target_slot = target_slot as i16;
                }
                (pi.card_id, c, pi.original_phase, pi.original_current_player)
            } else {
                return Err("No pending interaction".to_string());
            };

            let (_card_name, bytecode) = if cid == -1 {
                let pi = self.interaction_stack.last().unwrap();
                let virtual_bc = vec![
                    pi.effect_opcode,
                    pi.ctx.v_remaining as i32,
                    (pi.filter_attr & 0xFFFFFFFF) as i32,
                    (pi.filter_attr >> 32) as i32,
                    0, // raw_s
                    O_RETURN,
                    0,
                    0,
                    0,
                    0,
                ];
                ("System".to_string(), virtual_bc)
            } else if let Some(mem) = db.get_member(cid) {
                let ab = mem.abilities.get(ab_idx).ok_or("Ability not found")?;
                (mem.name.clone(), ab.bytecode.clone())
            } else if let Some(live) = db.get_live(cid) {
                let ab = live.abilities.get(ab_idx).ok_or("Ability not found")?;
                (live.name.clone(), ab.bytecode.clone())
            } else {
                return Err("Card not found".to_string());
            };

            // SYSTEMIC FIX: If this is an optional effect and the user chose PASS (99),
            // and we are NOT using the ability bytecode (cid == -1, virtual BC),
            // ensure we pop it properly. Actually, even for cid != -1, if it's an optional
            // discard cost inside bytecode, the PASS action (99) should jump past it.
            // If the interpreter returns without suspending, we need to restore phase.

            // For virtual bytecode (pi.card_id == -1), we must pop.
            // For actual ability bytecode, we pop because resolve_bytecode will use ctx.choice_index
            // to jump or skip, and if it doesn't suspend again, we restore the phase below.
            self.interaction_stack.pop();

            self.resolve_bytecode(db, std::sync::Arc::new(bytecode), &ctx);
            self.process_rule_checks(db);

            // Restore phase only if no new suspension occurred
            if self.interaction_stack.is_empty() {
                if self.debug.debug_mode {
                    println!("[DEBUG_RES] Restoring phase. orig_phase={:?}, stack_len={}", orig_phase, self.interaction_stack.len());
                }
                self.phase = if orig_phase == Phase::Response || orig_phase == Phase::Setup {
                    Phase::Main
                } else {
                    orig_phase
                };
                self.current_player = orig_cp;
            }
            return Ok(());
        }

        let cid = if slot_idx < 3 {
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
        if target_slot >= 0 {
            ctx.target_slot = target_slot as i16;
        }
        let source_type = if slot_idx < 3 { 0 } else { 1 }; // 0=Stage, 1=Other

        // ENFORCEMENT PHASE: Check conditions and costs
        if !self.debug.debug_ignore_conditions {
            if self.core.players[p_idx].prevent_activate > 0 {
                return Err("Cannot activate abilities due to restriction".to_string());
            }

            if ab.is_once_per_turn {
                if !self.check_once_per_turn(p_idx, source_type, cid as u32, ab_idx) {
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
            if !costs::pay_costs_transactional(self, db, &ab.costs, &ctx) {
                return Err("Cannot afford costs".to_string());
            }

            if ab.is_once_per_turn {
                self.consume_once_per_turn(p_idx, source_type, cid as u32, ab_idx);
            }
        }

        self.resolve_bytecode(db, std::sync::Arc::new(ab.bytecode.clone()), &ctx);
        self.process_rule_checks(db);
        Ok(())
    }
}

impl TurnPhaseController for GameState {
    fn do_active_phase(&mut self, db: &CardDatabase) {
        if self.phase != Phase::Active {
            return;
        }
        let p_idx = self.current_player as usize;
        self.setup_turn_log();

        let skip = self.core.players[p_idx].skip_next_activate;
        if skip {
            if !self.ui.silent {
                self.log(format!(
                    "Rule 7.4.1: [Active Phase] SKIPPED (untapping skipped) for Player {}.",
                    p_idx
                ));
            }
            self.core.players[p_idx].skip_next_activate = false;
        } else {
            if !self.ui.silent {
                self.log(format!(
                    "Rule 7.4.1: [Active Phase] Untapping all cards for Player {}.",
                    p_idx
                ));
            }
        }

        self.core.players[p_idx].untap_all(skip);
        let ctx = AbilityContext {
            source_card_id: -1,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: -1,
            ..Default::default()
        };
        self.trigger_abilities(db, TriggerType::TurnStart, &ctx);
        if self.phase == Phase::Active {
            self.phase = Phase::Energy;
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
                    "Rule 7.5.2: Player {} placed Energy from Energy Deck",
                    p_idx
                ));
            }
            let idx = self.core.players[p_idx].energy_zone.len();
            self.core.players[p_idx].energy_zone.push(card_id);
            self.core.players[p_idx].set_energy_tapped(idx, false);
        }
        self.phase = Phase::Draw;
    }

    fn do_draw_phase(&mut self, db: &CardDatabase) {
        let p_idx = self.current_player as usize;
        let ctx = AbilityContext {
            source_card_id: -1,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: -1,
            ..Default::default()
        };
        self.trigger_abilities(db, TriggerType::TurnStart, &ctx);

        if self.phase != Phase::Draw {
            return;
        }
        if !self.ui.silent {
            self.log(format!("Rule 7.6.2: Player {} draws a card.", p_idx));
        }
        self.draw_cards(p_idx, 1);
        self.phase = Phase::Main;
    }
}

// Extracted helpers that remain in GameState impl but in this file
impl GameState {
    fn resume_play_member(
        &mut self,
        db: &CardDatabase,
        choice_idx: i32,
        start_ab_idx: usize,
    ) -> Result<(), String> {
        let (card_id, ctx, orig_phase) = if let Some(pi) = self.interaction_stack.last() {
            let mut c = pi.ctx.clone();
            c.choice_index = choice_idx as i16;
            c.original_phase = Some(pi.original_phase);
            (pi.card_id, c, pi.original_phase)
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

        self.phase = orig_phase;
        if self.phase == Phase::Response || self.phase == Phase::Setup {
            self.phase = Phase::Main;
        }
        self.interaction_stack.pop();

        self.trigger_event(
            db,
            TriggerType::OnPlay,
            ctx.player_id as usize,
            card_id as i32,
            ctx.area_idx,
            start_ab_idx,
            ctx.choice_index,
        );
        self.process_rule_checks(db);
        Ok(())
    }

    fn check_play_legality(
        &self,
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
        if (player.prevent_play_to_slot_mask & (1 << slot_idx)) != 0 && player.stage[slot_idx] >= 0 {
            return Err("Cannot play to this slot due to restriction".to_string());
        }
        if player.is_moved(slot_idx) {
            return Err("Already played/moved to this slot this turn".to_string());
        }

        let old_card_id = player.stage[slot_idx];
        if old_card_id >= 0 {
            if player.baton_touch_count >= player.baton_touch_limit {
                return Err("Baton touch limit reached".to_string());
            }
            if player.prevent_baton_touch > 0 {
                return Err("Baton Touch is restricted".to_string());
            }
            if GameState::has_restriction(self, p_idx, slot_idx, O_PREVENT_BATON_TOUCH, db) {
                return Err("Baton Touch is not allowed for this member".to_string());
            }
        }

        if secondary_slot_idx >= 0 {
            let s_idx = secondary_slot_idx as usize;
            if s_idx >= 3 || player.stage[s_idx] < 0 || player.is_moved(s_idx) {
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
            self.core.players[p_idx].baton_touch_count += 1;
            self.core.players[p_idx].baton_source_ids.push(old_card_id);
            self.core.players[p_idx].baton_source_slots.push(slot_idx);
        }
        if secondary_slot_idx >= 0 {
            self.core.players[p_idx].baton_touch_count += 1;
            let s_idx = secondary_slot_idx as usize;
            let secondary_old_id = self.core.players[p_idx].stage[s_idx];
            if secondary_old_id >= 0 {
                self.core.players[p_idx].baton_source_ids.push(secondary_old_id);
                self.core.players[p_idx].baton_source_slots.push(s_idx);
            }
            if let Some(old) = self.handle_member_leaves_stage(
                p_idx,
                s_idx,
                db,
                &AbilityContext {
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: s_idx as i16,
                    ..Default::default()
                },
            ) {
                self.core.players[p_idx].discard.push(old);
            }
            self.core.players[p_idx].set_moved(s_idx, true);
        }

        self.core.players[p_idx].hand.remove(hand_idx);
        if hand_idx < self.core.players[p_idx].hand_added_turn.len() {
            self.core.players[p_idx].hand_added_turn.remove(hand_idx);
        }

        if old_card_id >= 0 {
            if let Some(old) = self.handle_member_leaves_stage(
                p_idx,
                slot_idx,
                db,
                &AbilityContext {
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: slot_idx as i16,
                    ..Default::default()
                },
            ) {
                self.core.players[p_idx].discard.push(old);
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
