use super::card_db::CardDatabase;
use super::models::AbilityContext;
use super::state::{ActionReceiver, GameState};
use crate::core::enums::*;
// use crate::core::hearts::HeartBoard;
use super::action_factory::ActionFactory;
use super::ai_encoding::GameStateEncoding;
use super::handlers::{
    MainPhaseController, MulliganController, ResponseController, TurnController,
};
use crate::core::heuristics::OriginalHeuristic;
use crate::core::mcts::{SearchHorizon, MCTS};
use crate::core::logic::profiling::{env_flag_enabled, env_threshold_us};
use std::time::Instant;

impl GameState {
    pub fn step(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        if self.debug.debug_mode {
            self.log(format!(
                "[STEP] Action: {} ({})",
                action,
                ActionFactory::get_action_label(action)
            ));
        }
        self.prev_phase = self.phase;
        self.step_internal(db, action)?;
        self.auto_step(db);
        // Skip sync during LiveSet - no board changes that affect auras
        if !matches!(self.phase, Phase::LiveSet) {
            self.sync_all_stats(db);
        }
        Ok(())
    }

    pub fn step_internal(&mut self, db: &CardDatabase, action: i32) -> Result<(), String> {
        match self.phase {
            Phase::Rps => self.handle_rps(action)?,
            Phase::TurnChoice => self.handle_turn_choice(action)?,
            Phase::MulliganP1 | Phase::MulliganP2 => self.handle_mulligan(action)?,
            Phase::Active => self.do_active_phase(db),
            Phase::Energy => self.do_energy_phase(),
            Phase::Draw => self.do_draw_phase(db),
            Phase::Main => self.handle_main(db, action)?,
            Phase::LiveSet => self.handle_liveset(action)?,
            Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Terminal => {}
            Phase::LiveResult => self.handle_liveresult(db, action)?,
            Phase::Response => self.handle_response(db, action)?,
            Phase::Setup => {
                self.phase = Phase::MulliganP1;
            }
        }
        Ok(())
    }

    pub fn auto_step(&mut self, db: &CardDatabase) {
        // Fast path: no triggers to process and not in auto-advance phase
        // OPTIMIZATION: Include LiveSet in fast-path since it doesn't auto-advance
        if self.core.trigger_queue.is_empty() 
            && !matches!(self.phase, Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Energy | Phase::Draw | Phase::Active | Phase::LiveSet) {
            return;
        }
        
        let mut loop_count = 0;
        while loop_count < 40 {
            self.check_win_condition();

            if self.phase == Phase::Terminal || self.phase == Phase::Response {
                break;
            }
            if !self.interaction_stack.is_empty() {
                break;
            }

            if !self.core.trigger_queue.is_empty() {
                self.process_trigger_queue(db);
                if self.phase == Phase::Response {
                    break;
                }
                continue;
            }

            let old_phase = self.phase;
            match self.phase {
                Phase::Active => self.do_active_phase(db),
                Phase::Energy => self.do_energy_phase(),
                Phase::Draw => self.do_draw_phase(db),
                Phase::PerformanceP1 | Phase::PerformanceP2 => {
                    self.do_performance_phase(db);
                }
                Phase::LiveResult => {
                    if self.live_result_selection_pending {
                        break;
                    } else {
                        let _ = self.handle_liveresult(db, 0);
                    }
                }
                _ => {}
            }

            // Early exit optimization: if phase didn't change and no triggers, break
            if self.phase == old_phase && self.core.trigger_queue.is_empty() {
                // Only sync stats if we actually did work AND we're not in LiveSet
                // LiveSet doesn't change board state, so aura recalculation is wasteful
                if loop_count > 0 && !matches!(self.phase, Phase::LiveSet) {
                    self.sync_all_stats(db);
                }
                break;
            }
            loop_count += 1;
        }
    }

    pub fn handle_member_leaves_stage(
        &mut self,
        p_idx: usize,
        slot: usize,
        db: &CardDatabase,
        ctx: &AbilityContext,
    ) -> Option<i32> {
        let profile_enabled = env_flag_enabled("BENCH_PROFILE_PLAY_MEMBER");
        let profile_start = if profile_enabled {
            Some(Instant::now())
        } else {
            None
        };
        if slot >= 3 {
            return None;
        }
        let cid = self.core.players[p_idx].stage[slot];
        if cid < 0 {
            return None;
        }

        if !self.ui.silent {
            self.log(format!("Rule 4.5.4 (4.1.3, 4.5.1): Member card ID {} leaves Stage Slot {}.", cid, slot + 1));
        }

        let mut leave_ctx = ctx.clone();
        leave_ctx.source_card_id = cid;
        leave_ctx.area_idx = slot as i16;

        let t_trigger = if profile_enabled {
            Some(Instant::now())
        } else {
            None
        };
        self.trigger_abilities(db, TriggerType::OnLeaves, &leave_ctx);
        let trigger_us = t_trigger
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        let t_mutate = if profile_enabled {
            Some(Instant::now())
        } else {
            None
        };
        self.core.players[p_idx]
            .granted_abilities
            .retain(|(target_cid, _, _)| *target_cid != cid);

        self.core.players[p_idx].clear_stage_card(slot);
        self.core.players[p_idx].blade_buffs[slot] = 0;
        self.core.players[p_idx].blade_overrides[slot] = -1;
        self.core.players[p_idx].heart_buffs[slot] = crate::core::hearts::HeartBoard::default();

        self.core.players[p_idx].set_tapped(slot, false);
        self.core.players[p_idx].set_moved(slot, false);
        self.mark_stats_dirty(p_idx);
        let mutate_us = t_mutate
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        if let Some(profile_start) = profile_start {
            let total_us = profile_start.elapsed().as_nanos() as u64 / 1000;
            if total_us >= env_threshold_us("BENCH_PROFILE_STEP_THRESHOLD_US", 2000)
                && !self.ui.silent
                && self.debug.debug_mode
            {
                println!(
                    "[PROFILE] MemberLeaves total_us={} trigger_us={} mutate_us={} p={} slot={} cid={}",
                    total_us,
                    trigger_us,
                    mutate_us,
                    p_idx,
                    slot,
                    cid
                );
            }
        }

        Some(cid as i32)
    }

    pub fn trigger_move_to_discard(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        ctx: &AbilityContext,
        moved_cards: &[i32],
    ) {
        if moved_cards.is_empty() {
            return;
        }

        if !self.ui.silent {
            self.log(format!("Rule 4.11.2: Moving {} cards to Discard for Player {}.", moved_cards.len(), p_idx));
        }

        let mut discard_ctx = ctx.clone();
        discard_ctx.player_id = p_idx as u8;
        discard_ctx.activator_id = p_idx as u8;
        discard_ctx.trigger_type = TriggerType::OnMoveToDiscard;
        discard_ctx.selected_cards = smallvec::SmallVec::from_slice(moved_cards);
        if discard_ctx.source_card_id < 0 {
            discard_ctx.source_card_id = moved_cards[0];
        }

        self.trigger_abilities(db, TriggerType::OnMoveToDiscard, &discard_ctx);
    }

    pub fn get_observation(&self, db: &CardDatabase) -> Vec<f32> {
        self.encode_state(db)
    }

    pub fn write_observation(&self, db: &CardDatabase, out: &mut [f32]) {
        let obs = self.encode_state(db);
        let len = obs.len().min(out.len());
        out[..len].copy_from_slice(&obs[..len]);
    }

    pub fn generate_legal_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        receiver: &mut R,
    ) {
        crate::core::logic::action_gen::ActionGeneratorFactory::generate_actions(
            self, db, p_idx, receiver,
        );
    }

    pub fn integrated_step(
        &mut self,
        db: &CardDatabase,
        action: i32,
        opp_mode: u8,
        mcts_sims: usize,
        enable_rollout: bool,
    ) -> (f32, bool) {
        let prev_score = self.core.players[0].score as f32;

        if self.current_player == 0 && self.phase.is_interactive() {
            let _ = self.step(db, action);
        } else {
            let _ = self.step(db, 0);
        }

        while self.phase != Phase::Terminal {
            let is_int = match self.phase {
                Phase::Main
                | Phase::LiveSet
                | Phase::MulliganP1
                | Phase::MulliganP2
                | Phase::Response
                | Phase::LiveResult
                | Phase::Energy => true,
                _ => false,
            };

            if self.current_player == 0 && is_int {
                break;
            }

            if is_int {
                if opp_mode == 1 {
                    let sims = if mcts_sims > 0 { mcts_sims } else { 1000 };
                    let mut mcts = MCTS::new();
                    let heuristic = OriginalHeuristic::default();
                    let (stats, _): (Vec<(i32, f32, u32)>, _) = mcts.search_custom(
                        self,
                        db,
                        sims,
                        0.0,
                        SearchHorizon::TurnEnd(),
                        &heuristic,
                        false,
                        enable_rollout,
                    );
                    let best_action = if !stats.is_empty() { stats[0].0 } else { 0 };
                    let _ = self.step(db, best_action);
                } else {
                    self.step_opponent(db);
                }
            } else {
                let _ = self.step(db, 0);
            }
        }

        let current_score = self.core.players[0].score as f32;
        let reward = current_score - prev_score;

        (reward, self.phase == Phase::Terminal)
    }

    pub fn get_verbose_action_label(&self, action_id: i32, db: &CardDatabase) -> String {
        ActionFactory::get_verbose_action_label(action_id, self, db)
    }
}
