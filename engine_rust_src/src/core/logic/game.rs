//! # LovecaSim Game State and Orchestration
//!
//! This module defines the `GameState` struct, which is the heart of the engine.
//! It manages players, zones (Hand, Deck, Stage, Energy, Discard), and the turn cycle.
//!
//! ## Key Roles:
//! - **State Management**: Holds 100% of the data needed to represent a point in time in a game.
//! - **Turn Orchestration**: Manages `Phase` transitions (Main, Live, End) and turn switching.
//! - **Rule Enforcement**: Implements high-level game rules (e.g., Playing a member,
//!   starting a Live performance, checking for Live success).
//! - **Rule 10.5.3 (Cleanup)**: Implements the "State Check" logic
//!   (`process_rule_checks`) which handles automatic energy cleanup and score updates.
//!
//! ## State-Action Integrity:
//! The `GameState` is designed to be highly serializable. It works in tandem with
//! the `interpreter` to resolve complex card effects while maintaining state consistency.

// use rand::SeedableRng;
// use rand::rngs::SmallRng;
// use rand::seq::SliceRandom;
// use rand_pcg::Pcg64;
// use smallvec::SmallVec;

// use crate::core::*; // UNUSED
use super::card_db::*;
// use super::filter::CardFilter;
use super::models::*;
// use super::player::*;
use crate::core::enums::*;
// use super::rules::*;
use crate::core::hearts::*;
use crate::core::heuristics::{EvalMode, Heuristic};
// use crate::core::logic::ai_encoding::GameStateEncoding;
use crate::core::logic::handlers::{
    MainPhaseController, MulliganController, ResponseController,
    TurnPhaseController,
};
// use crate::core::logic::game_trigger::resolution_trigger_matches_context;
// use crate::core::logic::ActionFactory;
// use crate::core::mcts::{SearchHorizon, MCTS};

pub use super::state::*;

impl GameState {
    pub(crate) const ACTION_TURN_CHOICE_FIRST: i32 = ACTION_BASE_TURN_ORDER_FIRST;
    pub(crate) const ACTION_TURN_CHOICE_SECOND: i32 = ACTION_BASE_TURN_ORDER_FIRST + 1;

    // Helper to calculate other slot index for Double Baton (offset 3-8)
    pub fn safe_set_mask(&self, mask: &mut [bool], aid: usize) {
        if aid < mask.len() {
            mask[aid] = true;
        } else {
            panic!(
                "[ACTION_OOB] Action ID {} exceeds mask len {} in phase {:?}",
                aid,
                mask.len(),
                self.phase
            );
        }
    }

    pub fn generate_execution_id(&mut self) -> u32 {
        let id = self.ui.next_execution_id;
        self.ui.next_execution_id = self.ui.next_execution_id.wrapping_add(1);
        self.ui.cancelled_execution_ids.remove(&id);
        self.ui.current_execution_id = Some(id);
        id
    }

    pub fn sync_cached_stats(&mut self, db: &CardDatabase, p_idx: usize) {
        let mut total_hearts = HeartBoard::default();
        let mut total_blades = 0;
        let mut slot_blades = [0u32; 3];
        let mut slot_hearts = [HeartBoard::default(), HeartBoard::default(), HeartBoard::default()];
        
        for i in 0..3 {
            let sb = self.get_effective_blades(p_idx, i, db, 1);
            let sh = self.get_effective_hearts(p_idx, i, db, 1);
            
            slot_blades[i] = sb;
            slot_hearts[i] = sh;
            
            total_blades += sb;
            total_hearts.add(sh);
        }
        
        let p = &mut self.core.players[p_idx];
        p.cached_slot_blades = slot_blades;
        p.cached_slot_hearts = slot_hearts;
        p.cached_total_hearts = total_hearts;
        p.cached_total_blades = total_blades;
        
        // Initial deck stats sync if needed
        if p.cached_deck_stats.count == 0.0 && !p.deck.is_empty() {
            p.cached_deck_stats = crate::core::heuristics::calculate_deck_expectations(&p.deck, db);
        }
    }

    pub fn sync_all_stats(&mut self, db: &CardDatabase) {
        self.sync_cached_stats(db, 0);
        self.sync_cached_stats(db, 1);
    }

    pub fn clear_execution_id(&mut self) {
        self.ui.current_execution_id = None;
    }

    pub fn draw_cards(&mut self, player_idx: usize, count: u32) {
        let t = self.turn as i32;
        for _ in 0..count {
            if self.core.players[player_idx].deck.is_empty() {
                self.resolve_deck_refresh(player_idx);
            }
            if let Some(card_id) = self.core.players[player_idx].pop_deck_card() {
                self.core.players[player_idx].draw_hand_card(card_id, t);
            }
        }
    }

    pub fn draw_energy_cards(&mut self, player_idx: usize, count: i32) {
        for _ in 0..count {
            if let Some(cid) = self.core.players[player_idx].energy_deck.pop() {
                self.core.players[player_idx].push_energy_card(cid, false);
            }
        }
    }

    pub fn pay_energy(&mut self, player_idx: usize, count: i32) {
        let mut paid = 0;
        let player = &mut self.core.players[player_idx];
        for i in 0..player.energy_zone.len() {
            if paid >= count {
                break;
            }
            if !player.is_energy_tapped(i) {
                player.set_energy_tapped(i, true);
                paid += 1;
            }
        }
    }

    pub fn activate_energy(&mut self, player_idx: usize, count: i32) {
        let mut activated = 0;
        let player = &mut self.core.players[player_idx];
        for i in 0..player.energy_zone.len() {
            if activated >= count {
                break;
            }
            if player.is_energy_tapped(i) {
                player.set_energy_tapped(i, false);
                activated += 1;
            }
        }
    }

    pub fn get_effective_blades(
        &self,
        player_idx: usize,
        slot_idx: usize,
        db: &CardDatabase,
        depth: u32,
    ) -> u32 {
        super::rules::get_effective_blades(self, player_idx, slot_idx, db, depth)
    }
    pub fn get_effective_hearts(
        &self,
        player_idx: usize,
        slot_idx: usize,
        db: &CardDatabase,
        depth: u32,
    ) -> HeartBoard {
        super::rules::get_effective_hearts(self, player_idx, slot_idx, db, depth)
    }
    pub fn get_total_blades(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
        super::rules::get_total_blades(self, p_idx, db, depth)
    }
    pub fn get_total_hearts(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> HeartBoard {
        super::rules::get_total_hearts(self, p_idx, db, depth)
    }
    pub fn get_total_member_hearts(&self, p_idx: usize, db: &CardDatabase, depth: u32) -> HeartBoard {
        super::rules::get_total_member_hearts(self, p_idx, db, depth)
    }
    pub fn calculate_cost_delta(&self, db: &CardDatabase, card_id: i32, p_idx: usize) -> i32 {
        super::rules::calculate_cost_delta(self, db, card_id, p_idx)
    }
    pub fn get_member_cost(
        &self,
        p_idx: usize,
        card_id: i32,
        slot_idx: i16,
        secondary_slot_idx: i16,
        db: &CardDatabase,
        depth: u32,
    ) -> i32 {
        super::rules::get_member_cost(self, p_idx, card_id, slot_idx, secondary_slot_idx, db, depth)
    }
    pub fn has_restriction(
        &self,
        p_idx: usize,
        slot_idx: usize,
        opcode: i32,
        db: &CardDatabase,
    ) -> bool {
        super::rules::has_restriction(self, p_idx, slot_idx, opcode, db)
    }

    pub fn set_member_tapped(
        &mut self,
        player_idx: usize,
        slot_idx: usize,
        tapped: bool,
        db: &CardDatabase,
    ) {
        let was_tapped = self.core.players[player_idx].is_tapped(slot_idx);
        self.core.players[player_idx].set_tapped(slot_idx, tapped);
        
        // When member becomes tapped (not untapped), trigger ON_MEMBER_TAP abilities on opponent
        if tapped && !was_tapped {
            let other_player = 1 - player_idx;
            let card_id = self.core.players[player_idx].stage[slot_idx];
            
            let ctx = AbilityContext {
                player_id: other_player as u8,
                activator_id: other_player as u8,
                source_card_id: card_id,
                area_idx: slot_idx as i16,
                trigger_type: TriggerType::OnMemberTap,
                target_slot: slot_idx as i16,
                ..Default::default()
            };
            self.trigger_abilities(db, TriggerType::OnMemberTap, &ctx);
        }
    }

    // --- Performance Phase Wrappers ---
    pub fn do_yell(&mut self, db: &CardDatabase, count: u32) -> Vec<i32> {
        super::performance::do_yell(self, db, count)
    }
    pub fn do_performance_phase(&mut self, db: &CardDatabase) {
        super::performance::do_performance_phase(self, db)
    }
    pub fn advance_from_performance(&mut self) {
        super::performance::advance_from_performance(self);
    }

    // --- Phase Methods ---


    pub fn play_member(
        &mut self,
        db: &CardDatabase,
        hand_idx: usize,
        slot_idx: usize,
    ) -> Result<(), String> {
        self.play_member_with_choice(db, hand_idx, slot_idx, -1, -1, 0)
    }

    pub fn end_main_phase(&mut self, db: &CardDatabase) {
        MainPhaseController::end_main_phase(self, db);
    }

    pub fn do_live_result(&mut self, db: &CardDatabase) {
        super::performance::do_live_result(self, db);
    }

    pub fn finalize_live_result(&mut self) {
        super::performance::finalize_live_result(self);
    }

    pub fn activate_ability(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
    ) -> Result<(), String> {
        ResponseController::activate_ability(self, db, slot_idx, ab_idx)
    }

    pub fn activate_ability_with_choice(
        &mut self,
        db: &CardDatabase,
        slot_idx: usize,
        ab_idx: usize,
        choice_idx: i32,
        target_slot: i32,
    ) -> Result<(), String> {
        ResponseController::activate_ability_with_choice(
            self,
            db,
            slot_idx,
            ab_idx,
            choice_idx,
            target_slot,
        )
    }

    pub fn execute_mulligan(&mut self, player_idx: usize, discard_indices: Vec<usize>) {
        MulliganController::execute_mulligan(self, player_idx, discard_indices);
    }

    pub fn do_active_phase(&mut self, db: &CardDatabase) {
        TurnPhaseController::do_active_phase(self, db);
    }

    pub fn do_energy_phase(&mut self) {
        TurnPhaseController::do_energy_phase(self);
    }

    pub fn do_draw_phase(&mut self, db: &CardDatabase) {
        TurnPhaseController::do_draw_phase(self, db);
    }

    pub fn set_live_cards(&mut self, player_idx: usize, card_ids: Vec<u32>) -> Result<(), String> {
        if card_ids.len() > 3 {
            return Err("Too many lives".to_string());
        }
        // For logging purposes, we'd ideally show card names, but for now just count
        if !self.ui.silent {
            self.log(format!(
                "Rule 8.2.2: Player {} sets {} cards to Live Zone.",
                player_idx,
                card_ids.len()
            ));
        }

        for cid in card_ids {
            let mut placed = false;
            for i in 0..3 {
                if self.core.players[player_idx].live_zone[i] == -1 {
                    self.core.players[player_idx].live_zone[i] = cid as i32;
                    self.core.players[player_idx].set_revealed(i, false);
                    // Rule 8.2.2: Draw same number of cards as placed
                    self.draw_cards(player_idx, 1);
                    placed = true;
                    break;
                }
            }
            if !placed {
                return Err("No empty live slots".to_string());
            }
        }
        Ok(())
    }

    // --- INTERPRETER DELEGATION ---
    pub fn resolve_bytecode(
        &mut self,
        db: &CardDatabase,
        bytecode: std::sync::Arc<Vec<i32>>,
        ctx_in: &AbilityContext,
    ) {
        super::interpreter::resolve_bytecode(self, db, bytecode, ctx_in);
    }

    /// Convenience: Accept Vec (takes ownership)
    #[inline]
    pub fn resolve_bytecode_owned(
        &mut self,
        db: &CardDatabase,
        bytecode: Vec<i32>,
        ctx_in: &AbilityContext,
    ) {
        self.resolve_bytecode(db, std::sync::Arc::new(bytecode), ctx_in);
    }

    /// Convenience: Accept &Vec<i32> (clones internally)
    #[inline]
    pub fn resolve_bytecode_cref(
        &mut self,
        db: &CardDatabase,
        bytecode: &Vec<i32>,
        ctx_in: &AbilityContext,
    ) {
        self.resolve_bytecode(db, std::sync::Arc::new(bytecode.clone()), ctx_in);
    }

    /// Convenience: Accept &[i32] slice (copies internally)
    #[inline]
    pub fn resolve_bytecode_slice(
        &mut self,
        db: &CardDatabase,
        bytecode: &[i32],
        ctx_in: &AbilityContext,
    ) {
        self.resolve_bytecode(db, std::sync::Arc::new(bytecode.to_vec()), ctx_in);
    }

    pub fn resolve_ability(
        &mut self,
        db: &CardDatabase,
        ability: &Ability,
        ctx_in: &AbilityContext,
    ) {
        super::interpreter::resolve_ability(self, db, ability, ctx_in);
    }

    pub fn check_condition(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        cond: &Condition,
        ctx: &AbilityContext,
        depth: u32,
    ) -> bool {
        super::interpreter::check_condition(self, db, p_idx, cond, ctx, depth)
    }

    pub fn check_condition_opcode(
        &self,
        db: &CardDatabase,
        op: i32,
        val: i32,
        attr: u64,
        slot: i32,
        ctx: &AbilityContext,
        depth: u32,
    ) -> bool {
        super::interpreter::check_condition_opcode(self, db, op, val, attr, slot, ctx, depth)
    }

    pub fn check_cost(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        cost: &Cost,
        ctx: &AbilityContext,
    ) -> bool {
        super::interpreter::check_cost(self, db, p_idx, cost, ctx)
    }

    pub fn pay_cost(
        &mut self,
        db: &CardDatabase,
        p_idx: usize,
        cost: &Cost,
        ctx: &AbilityContext,
    ) -> bool {
        super::interpreter::pay_cost(self, db, p_idx, cost, ctx)
    }




    pub fn evaluate<H: Heuristic>(
        &self,
        db: &CardDatabase,
        p0_baseline: u32,
        p1_baseline: u32,
        eval_mode: EvalMode,
        heuristic: &H,
    ) -> f32 {
        heuristic.evaluate(self, db, p0_baseline, p1_baseline, eval_mode, None, None)
    }

}
