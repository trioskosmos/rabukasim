// --- Merged Handlers ---
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::interpreter::constants::{
    CHOICE_ALL, CHOICE_DONE, FILTER_IS_OPTIONAL, FILTER_MASK_LOWER, FLAG_REVEAL_UNTIL_IS_LIVE,
    FLAG_TARGET_OPPONENT, DYNAMIC_VALUE,
};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState, TriggerType};
use crate::core::models::interpreter::{resolve_target_slot, get_choice_text, check_condition_opcode};
use crate::core::models::suspend_interaction;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::logging;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

/// Result of an opcode handler execution
#[derive(Debug)]
pub enum HandlerResult {
    /// Continue to next opcode
    Continue,
    /// Set the interpreter's condition flag
    SetCond(bool),
    /// Suspend execution for user choice
    Suspend,
    /// Return from current execution frame
    Return,
    /// Branch to a specific program counter
    Branch(usize),
    /// Branch to a completely new piece of bytecode (e.g. for TRIGGER_REMOTE)
    BranchToBytecode(std::sync::Arc<Vec<i32>>),
}

/// A registry that dispatches opcodes to their respective handlers.
pub struct HandlerRegistry;

impl HandlerRegistry {
    pub fn new() -> Self {
        Self
    }

    /// Dispatches an opcode to its implementation.
    /// Returns a HandlerResult indicating how execution should proceed.
    pub fn dispatch(
        &self,
        state: &mut GameState,
        db: &CardDatabase,
        ctx: &mut AbilityContext,
        op: i32,
        v: i32,
        a: i64,
        s: i32,
        instr_ip: usize,
        bytecode: &[i32],
    ) -> HandlerResult {
        // Centralized Dispatch Match
        match op {
            O_SELECT_MODE => {
                match handle_select_mode(state, db, ctx, v, a, s, instr_ip, bytecode) {
                    Some(new_ip) => HandlerResult::Branch(new_ip),
                    None => HandlerResult::Suspend,
                }
            }
            // 1. Meta / Control Handlers
            O_NEGATE_EFFECT
            | O_REDUCE_YELL_COUNT
            | O_RESTRICTION
            | O_SELECT_MEMBER
            | O_SELECT_LIVE
            | O_SELECT_PLAYER
            | O_OPPONENT_CHOOSE
            | O_PREVENT_ACTIVATE
            | O_PREVENT_BATON_TOUCH
            | O_PREVENT_SET_TO_SUCCESS_PILE
            | O_PREVENT_PLAY_TO_SLOT
            | O_TRIGGER_REMOTE
            | O_REDUCE_LIVE_SET_LIMIT
            | O_META_RULE
            | O_BATON_TOUCH_MOD
            | O_IMMUNITY
            | O_COLOR_SELECT
            | O_SWAP_AREA
            | O_REPEAT_ABILITY
            | O_SET_TARGET_SELF
            | O_SET_TARGET_OPPONENT => handle_meta_control(state, db, ctx, op, v, a, s, instr_ip)
                .unwrap_or(HandlerResult::Continue),
            // 2. Draw / Hand
            O_DRAW | O_DRAW_UNTIL | O_ADD_TO_HAND => {
                handle_draw(state, db, ctx, op, v, a, s).unwrap_or(HandlerResult::Continue)
            }
            // 3. Member State
            O_ACTIVATE_MEMBER
            | O_SET_TAPPED
            | O_TAP_MEMBER
            | O_TAP_OPPONENT
            | O_MOVE_MEMBER
            | O_FORMATION_CHANGE
            | O_PLACE_UNDER
            | O_ADD_STAGE_ENERGY
            | O_GRANT_ABILITY
            | O_PLAY_MEMBER_FROM_HAND
            | O_PLAY_MEMBER_FROM_DISCARD
            | O_INCREASE_COST => handle_member_state(state, db, ctx, op, v, a, s, instr_ip)
                .unwrap_or(HandlerResult::Continue),
            // 4. Energy
            O_ENERGY_CHARGE
            | O_PAY_ENERGY
            | O_ACTIVATE_ENERGY
            | O_PAY_ENERGY_DYNAMIC
            | O_PLACE_ENERGY_UNDER_MEMBER => handle_energy(state, db, ctx, op, v, a, s, instr_ip)
                .unwrap_or(HandlerResult::Continue),
            // 5. Deck / Zones
            O_SEARCH_DECK
            | O_ORDER_DECK
            | O_MOVE_TO_DECK
            | O_SWAP_CARDS
            | O_REVEAL_UNTIL
            | O_LOOK_DECK
            | O_REVEAL_CARDS
            | O_CHEER_REVEAL
            | O_LOOK_DECK_DYNAMIC
            | O_MOVE_TO_DISCARD
            | O_LOOK_AND_CHOOSE
            | O_RECOVER_LIVE
            | O_RECOVER_MEMBER
            | O_PLAY_LIVE_FROM_DISCARD
            | O_SELECT_CARDS
            | O_LOOK_REORDER_DISCARD
            | O_SWAP_ZONE => handle_deck_zones(state, db, ctx, op, v, a, s, instr_ip)
                .unwrap_or(HandlerResult::Continue),
            // 6. Score / Hearts
            O_BOOST_SCORE
            | O_REDUCE_COST
            | O_SET_SCORE
            | O_ADD_BLADES
            | O_BUFF_POWER
            | O_SET_BLADES
            | O_ADD_HEARTS
            | O_SET_HEARTS
            | O_TRANSFORM_COLOR
            | O_REDUCE_HEART_REQ
            | O_TRANSFORM_HEART
            | O_INCREASE_HEART_COST
            | O_SET_HEART_COST
            | O_REDUCE_SCORE
            | O_LOSE_EXCESS_HEARTS
            | O_DIV_VALUE
            | O_SKIP_ACTIVATE_PHASE => {
                handle_score_hearts(state, db, ctx, op, v, a, s).unwrap_or(HandlerResult::Continue)
            }
            _ => {
                if state.debug.debug_mode {
                    println!(
                        "[WARN] Unhandled opcode: {} (v={}, a={}, s={}) at IP {}",
                        op, v, a, s, instr_ip
                    );
                }
                HandlerResult::Continue
            }
        }
    }
}

pub fn handle_select_mode(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    _a: i64,
    _s: i32,
    instr_ip: usize,
    bc: &[i32],
) -> Option<usize> {
    use super::suspension::{get_choice_text, suspend_interaction};
    if ctx.choice_index == -1 {
        let is_opponent = (_s & (1 << 24)) != 0 || (_s & 0xFF) == 2;
        let choice_type = if is_opponent {
            "OPPONENT_CHOOSE"
        } else {
            "SELECT_MODE"
        };
        let choice_text = get_choice_text(db, ctx);

        let mut flip_ctx = ctx.clone();
        if is_opponent {
            flip_ctx.player_id = 1 - (ctx.player_id as u8);
        }

        let old_cp = state.current_player;
        if is_opponent {
            state.current_player = 1 - ctx.player_id;
        }

        let suspended = suspend_interaction(
            state,
            db,
            if is_opponent { &flip_ctx } else { ctx },
            instr_ip,
            crate::core::enums::O_SELECT_MODE,
            0,
            choice_type,
            &choice_text,
            0,
            v as i16,
        );

        if is_opponent {
            state.current_player = old_cp;
        }

        if suspended {
            return None;
        }
        return Some(instr_ip + 5);
    }

    let choice = ctx.choice_index as usize;
    if choice >= v as usize {
        return Some(instr_ip + 5 + ((v as usize).saturating_sub(1)) * 5);
    }

    let jump_instr_offset = instr_ip + 5 + (choice * 5);
    let target = jump_instr_offset as i32 + 5 + (bc[jump_instr_offset + 1] * 5);

    Some(target as usize)
}

// use super::super::conditions::get_condition_count;

pub fn handle_deck_zones(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_SEARCH_DECK => {
            let search_target = ctx.target_slot as usize;
            if search_target < state.core.players[p_idx].deck.len() {
                let cid = state.core.players[p_idx].deck.remove(search_target);
                match s {
                    4 => {
                        let slot = (a as u64 & FILTER_MASK_LOWER) as usize;
                        if slot < 3 {
                            if let Some(old) =
                                state.handle_member_leaves_stage(p_idx, slot, db, ctx)
                            {
                                state.core.players[p_idx].discard.push(old);
                            }
                            state.core.players[p_idx].stage[slot] = cid;
                            state.core.players[p_idx].set_tapped(slot, false);
                            state.core.players[p_idx].set_moved(slot, true);
                            state.register_played_member(p_idx, cid, db);
                            let new_ctx = AbilityContext {
                                source_card_id: cid,
                                player_id: p_idx as u8,
                                activator_id: p_idx as u8,
                                area_idx: slot as i16,
                                ..Default::default()
                            };
                            state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        } else {
                            state.core.players[p_idx].hand.push(cid);
                            state.core.players[p_idx].hand_increased_this_turn = state.core.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        }
                    }
                    13 => {
                        state.core.players[p_idx].success_lives.push(cid);
                    }
                    _ => {
                        state.core.players[p_idx].hand.push(cid);
                        state.core.players[p_idx].hand_increased_this_turn = state.core.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                }
                let mut rng = Pcg64::from_os_rng();
                state.core.players[p_idx].deck.shuffle(&mut rng);
            }
        }
        O_ORDER_DECK => {
            if state.core.players[p_idx].looked_cards.is_empty() && v > 0 {
                if state.core.players[p_idx].deck.len() < v as usize {
                    state.resolve_deck_refresh(p_idx);
                }
                for _ in 0..(v as usize).min(state.core.players[p_idx].deck.len()) {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            if !state.core.players[p_idx].looked_cards.is_empty() {
                if ctx.choice_index == -1 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_ORDER_DECK,
                        0,
                        "ORDER_DECK",
                        &choice_text,
                        0,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                let choice = ctx.choice_index as i32;
                let real_idx = if choice >= 0
                    && (choice as usize) < state.core.players[p_idx].looked_cards.len()
                {
                    Some(choice as usize)
                } else {
                    None
                };

                if let Some(idx) = real_idx {
                    let cid = state.core.players[p_idx].looked_cards.remove(idx);
                    state.core.players[p_idx].deck.push(cid);
                    if !state.core.players[p_idx].looked_cards.is_empty() {
                        if suspend_interaction(
                            state,
                            db,
                            ctx,
                            instr_ip,
                            O_ORDER_DECK,
                            0,
                            "ORDER_DECK",
                            "",
                            0,
                            -1,
                        ) {
                            return Some(HandlerResult::Suspend);
                        }
                    }
                    let remainder_mode = (a as u64 & FILTER_MASK_LOWER) as u8;
                    let looked = std::mem::take(&mut state.core.players[p_idx].looked_cards);
                    if remainder_mode == 1 {
                        state.core.players[p_idx].deck.extend(looked);
                    } else if remainder_mode == 2 {
                        for cid in looked {
                            state.core.players[p_idx].deck.insert(0, cid);
                        }
                    } else {
                        state.core.players[p_idx].discard.extend(looked);
                    }
                }
            }
        }
        O_LOOK_REORDER_DISCARD => {
            if state.core.players[p_idx].looked_cards.is_empty() && v > 0 {
                for _ in 0..(v as usize).min(state.core.players[p_idx].deck.len()) {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            if !state.core.players[p_idx].looked_cards.is_empty() {
                if ctx.choice_index == -1 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_LOOK_REORDER_DISCARD,
                        0,
                        "SELECT_CARDS_ORDER",
                        &choice_text,
                        0,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let choice = ctx.choice_index as i32;
                if choice == 99 {
                    // Done - move rest of looked cards to top in current order
                    let looked = std::mem::take(&mut state.core.players[p_idx].looked_cards);
                    for &cid in looked.iter() {
                        state.core.players[p_idx].deck.push(cid);
                    }
                    return Some(HandlerResult::Continue);
                }

                if choice >= 0 && (choice as usize) < state.core.players[p_idx].looked_cards.len() {
                    let cid = state.core.players[p_idx].looked_cards.remove(choice as usize);
                    state.core.players[p_idx].deck.push(cid);

                    if !state.core.players[p_idx].looked_cards.is_empty() {
                        if suspend_interaction(
                            state,
                            db,
                            ctx,
                            instr_ip,
                            O_LOOK_REORDER_DISCARD,
                            0,
                            "SELECT_CARDS_ORDER",
                            "",
                            0,
                            -1,
                        ) {
                            return Some(HandlerResult::Suspend);
                        }
                    } else {
                        return Some(HandlerResult::Continue);
                    }
                }
            }
        }
        O_MOVE_TO_DECK => {
            for _ in 0..(v as usize) {
                match a as u64 & FILTER_MASK_LOWER {
                    1 => {
                        if let Some(cid) = state.core.players[p_idx].discard.pop() {
                            state.core.players[p_idx].deck.push(cid);
                        }
                    }
                    4 => {
                        let slot = ctx.area_idx as usize;
                        if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                            state.core.players[p_idx].deck.push(cid);
                        }
                    }
                    13 => {
                        if let Some(cid) = state.core.players[p_idx].success_lives.pop() {
                            state.core.players[p_idx].deck.push(cid);
                        }
                    }
                    _ => {
                        if let Some(cid) = state.core.players[p_idx].hand.pop() {
                            state.core.players[p_idx].deck.push(cid);
                        }
                    }
                }
            }
            let mut rng = Pcg64::from_os_rng();
            state.core.players[p_idx].deck.shuffle(&mut rng);
        }
        O_SWAP_CARDS => {
            for _ in 0..(v as usize) {
                if state.core.players[p_idx].deck.is_empty() {
                    state.resolve_deck_refresh(p_idx);
                }
                if let Some(cid) = state.core.players[p_idx].deck.pop() {
                    match resolved_slot {
                        7 => state.core.players[p_idx].discard.push(cid),
                        8 => state.core.players[p_idx].deck.push(cid),
                        6 => {
                            state.core.players[p_idx].hand.push(cid);
                            state.core.players[p_idx].hand_increased_this_turn = state.core.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        }
                        _ => state.core.players[p_idx].discard.push(cid),
                    }
                }
            }
        }
        O_REVEAL_UNTIL => {
            let mut found = false;
            let mut revealed_count = 0;
            while !found && !state.core.players[p_idx].deck.is_empty() {
                if revealed_count > 60 {
                    break;
                }
                if let Some(cid) = state.core.players[p_idx].deck.pop() {
                    revealed_count += 1;
                    let mut new_ctx = ctx.clone();
                    new_ctx.source_card_id = cid;
                    state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);

                    let is_live_only = (s as u32 & FLAG_REVEAL_UNTIL_IS_LIVE as u32) != 0;
                    let matches = if is_live_only {
                        db.get_live(cid).is_some()
                    } else if v == 0 {
                        state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)
                    } else {
                        check_condition_opcode(state, db, v, a as i32, a as u64, s, &new_ctx, 0)
                    };

                    if state.debug.debug_mode {
                        println!("[DEBUG] REVEAL_UNTIL: cid={}, matches={}", cid, matches);
                    }

                    if matches {
                        let dest_slot = resolved_slot & 0x0F;
                        if dest_slot == 6 {
                            state.core.players[p_idx].hand.push(cid);
                            state.core.players[p_idx].hand_increased_this_turn = state.core.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        } else if dest_slot == 7 {
                            state.core.players[p_idx].discard.push(cid);
                        }
                        found = true;
                    } else {
                        state.core.players[p_idx].discard.push(cid);
                    }
                }
            }
        }
        O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL => {
            let count = v as usize;
            if resolved_slot == 6 {
                if ctx.choice_index == -1 {
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        op,
                        0,
                        "REVEAL_HAND",
                        "",
                        (a as u32) as u64,
                        v as i16,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                let choice = ctx.choice_index as usize;
                if choice != CHOICE_DONE as usize
                    && choice != CHOICE_ALL as usize
                    && choice < state.core.players[p_idx].hand.len()
                {
                    let cid = state.core.players[p_idx].hand[choice];
                    if !state.core.players[p_idx].looked_cards.contains(&cid) {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
                if ctx.choice_index == CHOICE_DONE
                    || ctx.choice_index == CHOICE_ALL
                    || (v > 0 && ctx.v_remaining == 1)
                {
                    // Done
                } else {
                    let next_v = if v > 0 {
                        (if ctx.v_remaining > 0 {
                            ctx.v_remaining
                        } else {
                            v as i16
                        }) - 1
                    } else {
                        0
                    };
                    if next_v > 0 || v == 0 {
                        ctx.v_remaining = next_v;
                        if suspend_interaction(
                            state,
                            db,
                            ctx,
                            instr_ip,
                            op,
                            0,
                            "REVEAL_HAND",
                            "",
                            (a as u32) as u64,
                            next_v,
                        ) {
                            return Some(HandlerResult::Suspend);
                        }
                    }
                }
            } else {
                if state.core.players[p_idx].deck.len() < count {
                    state.resolve_deck_refresh(p_idx);
                }
                let deck_len = state.core.players[p_idx].deck.len();
                let mut revealed_cids = Vec::new();
                for _ in 0..count.min(deck_len) {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                        revealed_cids.push(cid);
                    }
                }
                if op != O_LOOK_DECK {
                    for cid in revealed_cids {
                        let mut new_ctx = ctx.clone();
                        new_ctx.source_card_id = cid;
                        state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
                    }
                }
            }
        }
        O_LOOK_DECK_DYNAMIC => {
            // Look at cards from deck equal to live score + v
            // Used by cards like PL!-bp5-001-AR: "look at cards equal to live score + 2"

            // Refinement: Use performance score if available (e.g. for ON_LIVE_SUCCESS triggers)
            let mut total_score = 0;
            if let Some(res) = state.ui.performance_results.get(&(p_idx as u8)) {
                total_score = res.get("total_score").and_then(|v| v.as_u64()).unwrap_or(0) as i32;
            } else if let Some(res) = state.ui.last_performance_results.get(&(p_idx as u8)) {
                total_score = res.get("total_score").and_then(|v| v.as_u64()).unwrap_or(0) as i32;
            }

            // Fallback to cumulative score if performance score is not yet set or 0
            if total_score == 0 {
                total_score = (state.core.players[p_idx].score as i32)
                    + state.core.players[p_idx].live_score_bonus;
            }

            let count = (total_score + v) as usize;

            if state.debug.debug_mode {
                // println!("[DEBUG] O_LOOK_DECK_DYNAMIC: total_score={}, v={}, count={}", total_score, v, count);
            }

            if count > 0 {
                if state.core.players[p_idx].deck.len() < count {
                    state.resolve_deck_refresh(p_idx);
                }
                let deck_len = state.core.players[p_idx].deck.len();
                for _ in 0..count.min(deck_len) {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
        }
        O_MOVE_TO_DISCARD => {
            return match handle_move_to_discard(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_LOOK_AND_CHOOSE => {
            return match handle_look_and_choose(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_RECOVER_LIVE | O_RECOVER_MEMBER => {
            return match handle_recovery(state, db, ctx, v, a, s, instr_ip, op) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_PLAY_LIVE_FROM_DISCARD => {
            return match handle_play_live_from_discard(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_SELECT_CARDS => {
            return match handle_select_cards(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => Some(HandlerResult::SetCond(success)),
                None => Some(HandlerResult::Suspend),
            }
        }
        O_SWAP_ZONE => match handle_swap_zone(state, db, ctx, v, a, s, instr_ip) {
            Some(_) => {}
            None => return Some(HandlerResult::Suspend),
        },
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

// Logic for these helper functions is migrated from interpreter_legacy.rs
pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<bool> {
    let base_p = ctx.activator_id as usize;
    let p_idx = ctx.player_id as usize;
    // Zone bits are now in the 's' word: Bits 16-23 Source, Bits 8-15 Destination.
    let mut source_zone = (s >> 16) & 0xFF;
    if source_zone == 0 {
        let ts = s & 0xFF; // target_slot
        if ts == 4 || ts == 6 || ts == 13 {
            source_zone = ts;
        } else {
            source_zone = 8;
        }
    }
    let target_player_idx = if (s & (FLAG_TARGET_OPPONENT as i32)) != 0 {
        1 - base_p
    } else {
        base_p
    };

    // UNTIL_SIZE operation: v is target size, count is calculated
    let count = if (v as u32 & (1 << 31)) != 0 {
        let target_size = v & 0x7FFFFFFF;
        let current_size = match source_zone {
            6 => state.core.players[target_player_idx].hand.len() as i32,
            4 => state.core.players[target_player_idx]
                .stage
                .iter()
                .filter(|&&c| c >= 0)
                .count() as i32,
            13 => state.core.players[target_player_idx].success_lives.len() as i32,
            8 | 0 => state.core.players[target_player_idx].deck.len() as i32,
            3 => state.core.players[target_player_idx].energy_zone.len() as i32,
            _ => 0,
        };
        (current_size - target_size).max(0)
    } else {
        v
    };
    if target_player_idx != p_idx
        && state.core.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY)
    {
        if state.debug.debug_mode {
            println!("[DEBUG] handle_move_to_discard: Target has IMMUNITY, skipping");
        }
        return Some(false);
    }

    if state.debug.debug_mode {
        // println!("[DEBUG] handle_move_to_discard: player={}, source_zone={}, count={}, hand_len={}, choice={}",
        //    p_idx, source_zone, count, state.core.players[p_idx].hand.len(), ctx.choice_index);
    }

    // Mask out source zone bits (12-15) for filter matching
    let filter_attr = (a as u64) & 0xFFFFFFFFFFFF0FFF;

    // OPTIONAL Handling: Check if we have enough cards to pay if it's an optional cost
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;

    if is_optional && ctx.choice_index == -1 {
        // Check if we have enough cards to pay
        let available_count = match source_zone {
            6 => state.core.players[target_player_idx].hand.len() as i32,
            4 => state.core.players[target_player_idx]
                .stage
                .iter()
                .filter(|&&c| c >= 0)
                .count() as i32,
            13 => state.core.players[target_player_idx].energy_zone.len() as i32,
            8 | 0 => state.core.players[target_player_idx].deck.len() as i32,
            _ => 99,
        };
        // If not enough cards, auto-decline the optional cost
        if available_count < v {
            return Some(false);
        }
    }

    let mut next_ctx = ctx.clone();
    // Resumption logic for Yes/No is removed as we go straight to selection.

    let choice_type = if source_zone == 6 {
        "SELECT_HAND_DISCARD"
    } else {
        "SELECT_DISCARD"
    };

    if source_zone == 4 && next_ctx.choice_index == -1 && count == 1 {
        let slot = if next_ctx.area_idx >= 0 {
            next_ctx.area_idx as usize
        } else {
            0
        };
        if slot < 3 && state.core.players[p_idx].stage[slot] == ctx.source_card_id {
            next_ctx.choice_index = slot as i16;
        }
    }

    if next_ctx.choice_index == -1 && count > 0 && source_zone != 0 && source_zone != 8 {
        if suspend_interaction(
            state,
            db,
            &next_ctx,
            instr_ip,
            O_MOVE_TO_DISCARD,
            s,
            choice_type,
            "",
            filter_attr,
            count as i16,
        ) {
            return None;
        }
    }

    if next_ctx.choice_index != -1 {
        // Choice 99 counts as "Decline" for optional costs
        // Note: choice_index == 0 means "select first card", NOT decline
        if next_ctx.choice_index == CHOICE_DONE {
            if is_optional {
                return Some(false);
            } else {
                // Mandatory effect: if we still have cards to discard, we shouldn't allow 'DONE'
                // unless v_remaining is 0.
                if (next_ctx.v_remaining > 0) || (next_ctx.v_remaining == -1 && count > 0) {
                    // Re-suspend or ignore the choice if mandatory
                    if suspend_interaction(
                        state,
                        db,
                        &next_ctx,
                        instr_ip,
                        O_MOVE_TO_DISCARD,
                        s,
                        choice_type,
                        "You must select more cards",
                        filter_attr,
                        if next_ctx.v_remaining > 0 {
                            next_ctx.v_remaining
                        } else {
                            count as i16
                        },
                    ) {
                        return None;
                    }
                    return Some(true); // Should not happen if suspend returns true
                }
            }
        }

        let idx = next_ctx.choice_index as usize;
        let mut removed_cid = -1;
        match source_zone {
            6 => {
                if idx < state.core.players[p_idx].hand.len() {
                    removed_cid = state.core.players[p_idx].hand[idx];
                    if removed_cid != -1 {
                        // Capture cost if Bit 25 of slot is set
                        if (s & (1 << 25)) != 0 {
                            if let Some(m) = db.get_member(removed_cid) {
                                ctx.v_accumulated = m.cost as i16;
                            }
                        }
                        state.core.players[p_idx].hand[idx] = -1;
                        // Immediately remove -1 placeholders from hand
                        state.core.players[p_idx].hand.retain(|c| *c != -1);
                    }
                }
            }
            4 => {
                let slot = if idx < 3 {
                    idx
                } else if next_ctx.area_idx >= 0 {
                    next_ctx.area_idx as usize
                } else {
                    0
                };
                if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, &next_ctx) {
                    removed_cid = cid;
                }
            }
            13 => {
                if !state.core.players[p_idx].success_lives.is_empty() {
                    removed_cid = state.core.players[p_idx].success_lives.pop().unwrap() as i32;
                }
            }
            8 | 0 => {
                if !state.core.players[p_idx].deck.is_empty() {
                    removed_cid = state.core.players[p_idx].deck.pop().unwrap() as i32;
                }
            }
            3 => {
                if !state.core.players[p_idx].energy_zone.is_empty() {
                    removed_cid = state.core.players[p_idx].energy_zone.pop().unwrap() as i32;
                }
            }
            _ => {}
        }
        if removed_cid >= 0 {
            state.core.players[p_idx].discard.push(removed_cid as i32);
            next_ctx.v_remaining = if next_ctx.v_remaining > 0 {
                next_ctx.v_remaining - 1
            } else {
                (count as i16) - 1
            };
            if next_ctx.v_remaining > 0 {
                next_ctx.choice_index = -1;
                if suspend_interaction(
                    state,
                    db,
                    &next_ctx,
                    instr_ip,
                    O_MOVE_TO_DISCARD,
                    s,
                    choice_type,
                    "",
                    filter_attr,
                    next_ctx.v_remaining,
                ) {
                    return None;
                }
            }
        }
    } else {
        for _ in 0..count {
            match source_zone {
                6 => {
                    if let Some(cid) = state.core.players[p_idx].hand.pop() {
                        state.core.players[p_idx].discard.push(cid);
                    }
                }
                4 => {
                    let slot = if next_ctx.area_idx >= 0 {
                        next_ctx.area_idx as usize
                    } else {
                        0
                    };
                    if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, &next_ctx)
                    {
                        state.core.players[p_idx].discard.push(cid as i32);
                    }
                }
                13 => {
                    if let Some(cid) = state.core.players[p_idx].success_lives.pop() {
                        state.core.players[p_idx].discard.push(cid);
                    }
                }
                8 | 0 => {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() {
                        state.core.players[p_idx].discard.push(cid);
                    }
                }
                3 => {
                    if let Some(cid) = state.core.players[p_idx].energy_zone.pop() {
                        state.core.players[p_idx].discard.push(cid);
                    }
                }
                _ => {}
            }
        }
    }

    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_MOVE_TO_DISCARD, v, a, s, 0) {
            state.log(msg);
        }
    }

    state.core.players[p_idx].hand.retain(|c| *c != -1);
    Some(true)
}

pub fn handle_play_live_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<bool> {
    let opponent_bit = (s >> 24) & 1;
    let target_p_idx = if opponent_bit != 0 {
        1 - (ctx.activator_id as usize)
    } else {
        ctx.activator_id as usize
    };

    let mut remaining = if ctx.v_remaining == -1 {
        v as i16 * 2
    } else {
        ctx.v_remaining
    };
    if remaining <= 0 {
        return Some(true);
    }

    if remaining % 2 == 0 {
        if ctx.choice_index == -1 {
            state.core.players[target_p_idx].looked_cards.clear();
            let filter_attr = a as u64;
            for &cid in &state.core.players[target_p_idx].discard {
                if db.get_live(cid).is_some()
                    && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
                {
                    state.core.players[target_p_idx].looked_cards.push(cid);
                }
            }
            if state.core.players[target_p_idx].looked_cards.is_empty() {
                return Some(true);
            }
            let mut target_ctx = ctx.clone();
            target_ctx.player_id = target_p_idx as u8;
            let choice_text = get_choice_text(db, &target_ctx);
            if suspend_interaction(
                state,
                db,
                &target_ctx,
                instr_ip,
                O_PLAY_LIVE_FROM_DISCARD,
                s,
                "SELECT_DISCARD_PLAY",
                &choice_text,
                a as u64,
                remaining,
            ) {
                return None;
            }
        }

        let choice = ctx.choice_index as i32;
        let real_idx = if choice >= 0
            && (choice as usize) < state.core.players[target_p_idx].looked_cards.len()
        {
            Some(choice as usize)
        } else {
            None
        };

        if let Some(idx) = real_idx {
            let chosen = state.core.players[target_p_idx].looked_cards[idx];
            if chosen != -1 {
                state.core.players[target_p_idx].looked_cards[idx] = -1;
                state.core.players[target_p_idx].looked_cards.clear(); // Clear all looked cards
                state.core.players[target_p_idx].looked_cards.push(chosen); // Push only the chosen one

                remaining -= 1;
                let mut target_ctx = ctx.clone();
                target_ctx.player_id = target_p_idx as u8;
                if suspend_interaction(
                    state,
                    db,
                    &target_ctx,
                    instr_ip,
                    O_PLAY_LIVE_FROM_DISCARD,
                    s,
                    "SELECT_LIVE_SLOT",
                    "",
                    a as u64,
                    remaining,
                ) {
                    return None;
                }
            }
        }
    } else {
        if state.core.players[target_p_idx].looked_cards.is_empty() {
            return Some(true);
        }
        let card_id = state.core.players[target_p_idx].looked_cards.remove(0);
        let slot_idx = ctx.choice_index as usize;

        if let Some(pos) = state.core.players[target_p_idx]
            .discard
            .iter()
            .position(|&cid| cid == card_id)
        {
            state.core.players[target_p_idx].discard.remove(pos);
            if slot_idx < 3 {
                let old = state.core.players[target_p_idx].live_zone[slot_idx];
                if old >= 0 {
                    state.core.players[target_p_idx].discard.push(old);
                }
                state.core.players[target_p_idx].live_zone[slot_idx] = card_id;
                state.core.players[target_p_idx].set_revealed(slot_idx, true);
            }
        }

        remaining -= 1;
        if remaining > 0 && !state.core.players[target_p_idx].discard.is_empty() {
            ctx.choice_index = -1;
            ctx.v_remaining = remaining;
            return handle_play_live_from_discard(state, db, ctx, v, a, s, instr_ip);
        }
    }
    Some(true)
}

pub fn handle_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 {
        let source_zone = (s >> 16) & 0xFF;
        let ts = s & 0xFF;
        let effective_zone = if source_zone != 0 {
            source_zone
        } else if ts != 0 {
            ts
        } else {
            7
        }; // Default to Discard

        state.core.players[p_idx].looked_cards.clear();
        let cards_to_filter = match effective_zone {
            6 => state.core.players[p_idx].hand.to_vec(),
            7 => state.core.players[p_idx].discard.to_vec(),
            4 => state.core.players[p_idx]
                .stage
                .iter()
                .cloned()
                .filter(|&c| c >= 0)
                .collect(),
            _ => state.core.players[p_idx].discard.to_vec(),
        };

        let filter_attr = (a as u64) & 0x00000000FFFFFFFF;
        for cid in cards_to_filter {
            if state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                state.core.players[p_idx].looked_cards.push(cid);
            }
        }

        if state.core.players[p_idx].looked_cards.is_empty() {
            return Some(true);
        }

        if state.debug.debug_mode {
            println!("[DEBUG] handle_select_cards: p_idx={}, effective_zone={}, filter_attr={:X}", p_idx, effective_zone, filter_attr);
        }
        let choice_type = match effective_zone {
            6 => "SELECT_HAND_DISCARD",
            7 => "SELECT_DISCARD_PLAY",
            _ => "LOOK_AND_CHOOSE",
        };
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_SELECT_CARDS,
            0,
            choice_type,
            &choice_text,
            a as u64,
            v as i16,
        ) {
            return None;
        }
    }

    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 && (a as u64 & FILTER_IS_OPTIONAL) != 0 {
        return Some(false);
    }

    if choice != CHOICE_DONE as i32
        && choice >= 0
        && (choice as usize) < state.core.players[p_idx].looked_cards.len()
    {
        let chosen = state.core.players[p_idx].looked_cards[choice as usize];
        ctx.selected_cards.push(chosen);

        // Consumption Logic: Move the card to the destination zone
        let dest_zone = (s >> 8) & 0xFF;
        if dest_zone != 0 {
            // Find where it was in the source zone and remove it
            let source_zone = (s >> 16) & 0xFF;
            let actual_source = if source_zone != 0 { source_zone } else { 7 };

            let mut found = false;
            match actual_source {
                6 => {
                    if let Some(pos) = state.core.players[p_idx]
                        .hand
                        .iter()
                        .position(|&c| c == chosen)
                    {
                        state.core.players[p_idx].hand.remove(pos);
                        found = true;
                    }
                }
                7 => {
                    if let Some(pos) = state.core.players[p_idx]
                        .discard
                        .iter()
                        .position(|&c| c == chosen)
                    {
                        state.core.players[p_idx].discard.remove(pos);
                        found = true;
                    }
                }
                4 => {
                    for i in 0..3 {
                        if state.core.players[p_idx].stage[i] == chosen {
                            state.handle_member_leaves_stage(p_idx, i, db, ctx);
                            found = true;
                            break;
                        }
                    }
                }
                _ => {}
            }

            if found {
                match dest_zone {
                    6 => {
                        state.core.players[p_idx].hand.push(chosen);
                        state.core.players[p_idx].hand_increased_this_turn = state.core.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                    7 => {
                        state.core.players[p_idx].discard.push(chosen);
                    }
                    8 | 0 => {
                        state.core.players[p_idx].deck.push(chosen);
                    } // Shuffle handled by caller if needed, or simple push
                    13 => {
                        state.core.players[p_idx].success_lives.push(chosen);
                    }
                    _ => {
                        state.core.players[p_idx].hand.push(chosen);
                    }
                }
            }
        }

        let rem = if ctx.v_remaining > 0 {
            ctx.v_remaining - 1
        } else {
            (v as i16).saturating_sub(1)
        };
        if rem > 0 {
            state.core.players[p_idx]
                .looked_cards
                .remove(choice as usize);
            ctx.v_remaining = rem;
            ctx.choice_index = -1;
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                s,
                "LOOK_AND_CHOOSE",
                "",
                a as u64,
                rem,
            ) {
                return None;
            }
        }
    }

    Some(true)
}

pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let rem_dest = (s >> 8) & 0xFF;
    let source_zone = (s >> 16) & 0xFF;
    let source_zone = if source_zone == 0 {
        8
    } else {
        source_zone as i32
    };
    let look_count = (v & 0xFF) as usize;
    let pick_count_raw = ((v >> 8) & 0xFF) as usize;
    let reveal_flag = (v & (1 << 30)) != 0;

    if state.core.players[p_idx].looked_cards.is_empty() {
        let reveal_count = if source_zone == 6 {
            state.core.players[p_idx].hand.len()
        } else if source_zone == 7 {
            state.core.players[p_idx].discard.len()
        } else if source_zone == 15 {
            state.core.players[p_idx].yell_cards.len()
        } else {
            look_count
        };
        match source_zone {
            6 => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.core.players[p_idx].hand.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            7 => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.core.players[p_idx].discard.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            15 => {
                let y = std::mem::take(&mut state.core.players[p_idx].yell_cards);
                state.core.players[p_idx].looked_cards.extend(y);
            }
            _ => {
                if state.core.players[p_idx].deck.len() < reveal_count {
                    state.resolve_deck_refresh(p_idx);
                }
                for _ in 0..reveal_count.min(state.core.players[p_idx].deck.len()) {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
        }
    }

    if ctx.choice_index == -1 {
        let choice_type = if source_zone == 6 {
            "SELECT_HAND_DISCARD"
        } else {
            "LOOK_AND_CHOOSE"
        };
        let choice_text = get_choice_text(db, ctx);
        let pick_count = ((v >> 8) & 0xFF) as i16;
        let v_rem = if pick_count > 0 { pick_count } else { 1 };
        let mut filter_attr = a as u64;
        if ((v >> 16) & 0x7F) > 0 {
            filter_attr |= 1u64 << 42;
            filter_attr |= (((v >> 16) & 0x7F) as u64) << 31;
        }
        if ((v >> 23) & 0x7F) > 0 {
            filter_attr |= 1u64 << 31;
            filter_attr |= (((v >> 23) & 0x7F) as u64) << 32;
        }
        let is_optional =
            (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_LOOK_AND_CHOOSE,
            s,
            choice_type,
            &choice_text,
            filter_attr,
            v_rem,
        ) {
            if is_optional && ctx.choice_index == CHOICE_DONE {
                state.core.players[p_idx]
                    .deck
                    .extend(state.core.players[p_idx].looked_cards.drain(..).rev());
                return Some(false);
            }
            return None;
        }
    }

    let choice = ctx.choice_index as i32;
    let mut revealed = std::mem::take(&mut state.core.players[p_idx].looked_cards);
    let _is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
    if choice == CHOICE_DONE as i32 {
        state.core.players[p_idx].looked_cards.retain(|c| *c != -1);
        return Some(true);
    }

    if choice != CHOICE_DONE as i32 {
        if choice >= 0 && (choice as usize) < revealed.len() && choice != CHOICE_ALL as i32 {
            let chosen = revealed[choice as usize];
            if chosen != -1 {
                revealed[choice as usize] = -1;
                // Destination logic cleanup:
                // 1. target_slot (s & 0xFF) is the PRIMARY destination (usually Hand=6 or Stage=4)
                let destination = if target_slot > 0 {
                    target_slot as i32
                } else {
                    6
                };
                match destination {
                    7 => {
                        state.core.players[p_idx].discard.push(chosen);
                    }
                    8 => {
                        state.core.players[p_idx].deck.push(chosen);
                    }
                    4 => {
                        let slot = s as usize;
                        if slot < 3 {
                            if let Some(cid) =
                                state.handle_member_leaves_stage(p_idx, slot, db, ctx)
                            {
                                state.core.players[p_idx].discard.push(cid as i32);
                            }
                            state.core.players[p_idx].stage[slot] = chosen;
                            state.core.players[p_idx].set_tapped(slot, false);
                            state.core.players[p_idx].set_moved(slot, true);
                            state.register_played_member(p_idx, chosen, db);
                            let new_ctx = AbilityContext {
                                source_card_id: chosen,
                                player_id: p_idx as u8,
                                activator_id: p_idx as u8,
                                area_idx: slot as i16,
                                ..Default::default()
                            };
                            state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        } else {
                            state.core.players[p_idx].hand.push(chosen);
                            state.core.players[p_idx].hand_increased_this_turn = state.core.players
                                [p_idx]
                                .hand_increased_this_turn
                                .saturating_add(1);
                        }
                    }
                    13 => {
                        state.core.players[p_idx].success_lives.push(chosen);
                    }
                    _ => {
                        state.core.players[p_idx].hand.push(chosen);
                        state.core.players[p_idx].hand_increased_this_turn = state.core.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                }
                if reveal_flag {
                    let new_ctx = AbilityContext {
                        source_card_id: chosen,
                        player_id: p_idx as u8,
                        activator_id: p_idx as u8,
                        ..Default::default()
                    };
                    state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
                }
                if source_zone == 15 {
                    for slot in 0..3 {
                        if let Some(pos) = state.core.players[p_idx].stage_energy[slot]
                            .iter()
                            .position(|&c| c == chosen)
                        {
                            state.core.players[p_idx].stage_energy[slot].remove(pos);
                            state.core.players[p_idx].sync_stage_energy_count(slot);
                            break;
                        }
                    }
                }
                let effective_pick_count = if pick_count_raw > 0 {
                    pick_count_raw
                } else {
                    look_count
                };
                let rem = if ctx.v_remaining > 0 {
                    ctx.v_remaining - 1
                } else {
                    (effective_pick_count as i16).saturating_sub(1)
                };
                if rem > 0 && revealed.iter().any(|&c| c != -1) {
                    state.core.players[p_idx].looked_cards = revealed.clone();
                    let choice_type = if source_zone == 6 {
                        "SELECT_HAND_DISCARD"
                    } else {
                        "LOOK_AND_CHOOSE"
                    };
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_LOOK_AND_CHOOSE,
                        s,
                        choice_type,
                        "",
                        a as u64,
                        rem,
                    ) {
                        return None;
                    }
                }
            }
        }
    }
    revealed.retain(|c| *c != -1);
    if !revealed.is_empty() {
        let dest = if rem_dest > 0 {
            rem_dest
        } else {
            source_zone as i32
        };
        match dest {
            6 => state.core.players[p_idx].hand.extend(revealed),
            7 => state.core.players[p_idx].discard.extend(revealed),
            15 => state.core.players[p_idx].yell_cards.extend(revealed),
            0 | 8 => {
                state.core.players[p_idx].deck.extend(revealed);
                let mut rng = Pcg64::from_os_rng();
                state.core.players[p_idx].deck.shuffle(&mut rng);
            }
            1 => state.core.players[p_idx].deck.extend(revealed),
            2 => {
                for c in revealed.iter().rev() {
                    state.core.players[p_idx].deck.insert(0, *c);
                }
            }
            _ => state.core.players[p_idx].discard.extend(revealed),
        }
    }
    Some(true)
}

pub fn handle_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
    real_op: i32,
) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    /*
    if state.debug.debug_mode {
        println!(
            "[DEBUG] handle_recovery: Start. choice={}, s={}, a={}",
            ctx.choice_index, s, a
        );
    }
    */

    // Determine source zone
    let mut source_zone = (s >> 16) & 0xFF;
    if source_zone == 0 {
        source_zone = 7;
    } // Default recovery to discard

    // Populate looked_cards if empty (first call OR resumed call where looked_cards were cleared)
    if state.core.players[p_idx].looked_cards.is_empty() {
        let source_ids: Vec<i32> = if source_zone == 15 {
            state.core.players[p_idx]
                .yell_cards
                .iter()
                .copied()
                .collect()
        } else {
            state.core.players[p_idx].discard.iter().copied().collect()
        };

        for cid in source_ids {
            let type_matches = if real_op == O_RECOVER_LIVE {
                db.get_live(cid).is_some()
            } else {
                db.get_member(cid).is_some()
            };
            /*
            if state.debug.debug_mode {
                println!(
                    "[DEBUG] handle_recovery scan: cid={}, type_matches={}, attr={}",
                    cid, type_matches, a
                );
            }
            */
            if type_matches && (a == 0 || state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)) {
                state.core.players[p_idx].looked_cards.push(cid);
            }
        }
        /*
        if state.debug.debug_mode {
            println!(
                "[DEBUG] handle_recovery: populated looked_cards with {} cards",
                state.core.players[p_idx].looked_cards.len()
            );
        }
        */
        if state.core.players[p_idx].looked_cards.is_empty() {
            return Some(true);
        }
    }

    if ctx.choice_index == -1 {
        let choice_type = if real_op == O_RECOVER_LIVE {
            "RECOV_L"
        } else {
            "RECOV_M"
        };
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            real_op,
            0,
            choice_type,
            &choice_text,
            0,
            -1,
        ) {
            return None;
        }
    }

    let choice = ctx.choice_index as i32;
    let real_idx =
        if choice >= 0 && (choice as usize) < state.core.players[p_idx].looked_cards.len() {
            Some(choice as usize)
        } else {
            None
        };
    /*
    if state.debug.debug_mode {
        println!(
            "[DEBUG] handle_recovery: resolving choice={}, real_idx={:?}, looked_cards={:?}",
            choice, real_idx, state.core.players[p_idx].looked_cards
        );
    }
    */

    if let Some(idx) = real_idx {
        let cid = state.core.players[p_idx].looked_cards[idx];
        if cid != -1 {
            /*
            if state.debug.debug_mode {
                println!("[DEBUG] handle_recovery: chosen card {}", cid);
            }
            */
            state.core.players[p_idx].looked_cards[idx] = -1;
            state.core.players[p_idx].hand.push(cid);
            state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx]
                .hand_increased_this_turn
                .saturating_add(1);
            ctx.selected_cards.push(cid);

            let mut source_zone = (s >> 16) & 0xFF;
            if source_zone == 0 {
                source_zone = 7;
            }
            if source_zone == 15 {
                if let Some(pos) = state.core.players[p_idx]
                    .yell_cards
                    .iter()
                    .position(|&x| x == cid)
                {
                    state.core.players[p_idx].yell_cards.remove(pos);
                }
            } else {
                if let Some(pos) = state.core.players[p_idx]
                    .discard
                    .iter()
                    .position(|&x| x == cid)
                {
                    state.core.players[p_idx].discard.remove(pos);
                }
            }
            let remaining = if ctx.v_remaining == -1 {
                v as i16 - 1
            } else {
                ctx.v_remaining - 1
            };
            if remaining > 0
                && choice != CHOICE_ALL as i32
                && state.core.players[p_idx]
                    .looked_cards
                    .iter()
                    .any(|&c| c != -1)
            {
                let choice_type = if real_op == O_RECOVER_LIVE {
                    "RECOV_L"
                } else {
                    "RECOV_M"
                };
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    real_op,
                    0,
                    choice_type,
                    &choice_text,
                    0,
                    remaining,
                ) {
                    return None;
                }
            }
        }
    }
    state.core.players[p_idx].looked_cards.clear();
    Some(true)
}

pub fn handle_swap_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _v: i32,
    _a: i64,
    _s: i32,
    instr_ip: usize,
) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 && ctx.v_remaining == -1 {
        let cards = state.core.players[p_idx].success_lives.clone();
        if cards.is_empty() {
            return Some(true);
        }
        state.core.players[p_idx].looked_cards.clear();
        state.core.players[p_idx].looked_cards.extend(cards);
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_SWAP_ZONE,
            0,
            "SELECT_SWAP_SOURCE",
            &choice_text,
            0,
            1,
        ) {
            return None;
        }
    }
    if ctx.v_remaining == 1 {
        let picked_idx = ctx.choice_index as usize;
        if picked_idx < state.core.players[p_idx].looked_cards.len() {
            let cid = state.core.players[p_idx].looked_cards[picked_idx];
            state.core.players[p_idx].looked_cards.clear();
            state.core.players[p_idx].looked_cards.push(cid);
            let mut next_ctx = ctx.clone();
            next_ctx.choice_index = -1;
            next_ctx.v_remaining = 0;
            if suspend_interaction(
                state,
                db,
                &next_ctx,
                instr_ip,
                O_SWAP_ZONE,
                0,
                "SELECT_HAND_PLAY",
                "",
                0,
                1,
            ) {
                return None;
            }
        }
    } else if ctx.v_remaining == 0 {
        let hand_idx = ctx.choice_index as usize;
        if hand_idx < state.core.players[p_idx].hand.len()
            && !state.core.players[p_idx].looked_cards.is_empty()
        {
            let hand_cid = state.core.players[p_idx].hand.remove(hand_idx);
            let success_cid = state.core.players[p_idx].looked_cards.remove(0);
            if let Some(pos) = state.core.players[p_idx]
                .success_lives
                .iter()
                .position(|&x| x == success_cid)
            {
                state.core.players[p_idx].success_lives[pos] = hand_cid;
                state.core.players[p_idx].hand.push(success_cid);
                state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx]
                    .hand_increased_this_turn
                    .saturating_add(1);
            }
        }
    }
    state.core.players[p_idx].looked_cards.clear();
    Some(true)
}

pub fn handle_draw(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    op: i32,
    v: i32,
    _a: i64,
    s: i32,
) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let count = v as u32;
    let target_p = if s == 2 {
        1 - p_idx
    } else if s == 3 {
        0
    } else {
        p_idx
    };

    match op {
        O_DRAW => {
            if s == 3 {
                state.draw_cards(0, count);
                state.draw_cards(1, count);
            } else {
                state.draw_cards(target_p, count);
            }
            // Unified logging: EFFECT events now go to both turn_history and rule_log
            state.log_event(
                "EFFECT",
                &format!("Draw {} card(s)", count),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_DRAW_UNTIL => {
            let target_hand_size = v as usize;
            let current_hand_size = state.core.players[p_idx].hand.len();
            if current_hand_size < target_hand_size {
                let to_draw = (target_hand_size - current_hand_size) as u32;
                state.draw_cards(p_idx, to_draw);
            }
        }
        O_ADD_TO_HAND => {
            // Special case: Adding from looked cards (s=90 or s=6)
            if s == 90 || s == 6 {
                for _ in 0..v as usize {
                    if !state.core.players[p_idx].looked_cards.is_empty() {
                        let cid = state.core.players[p_idx].looked_cards.remove(0);
                        state.core.players[p_idx].hand.push(cid);
                        state.core.players[p_idx].hand_increased_this_turn = state.core.players
                            [p_idx]
                            .hand_increased_this_turn
                            .saturating_add(1);
                    }
                }
            } else {
                state.draw_cards(p_idx, v as u32);
            }
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

pub fn handle_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;

    match op {
        O_ENERGY_CHARGE => {
            let target_p = if (s & 0xFF) == 2 { 1 - p_idx } else { p_idx };
            // Read "Wait" flag from Slot bit 27 (FLAG_IS_WAIT) instead of Attr bit 31
            let is_wait =
                (s as u64 & crate::core::logic::interpreter::constants::FLAG_IS_WAIT) != 0;
            for _ in 0..v {
                if let Some(cid) = state.core.players[target_p].energy_deck.pop() {
                    state.core.players[target_p].energy_zone.push(cid);
                    let new_idx = state.core.players[target_p].energy_zone.len() - 1;
                    state.core.players[target_p].set_energy_tapped(new_idx, is_wait);
                }
            }
            Some(HandlerResult::Continue)
        }
        O_PAY_ENERGY => {
            let available = (0..state.core.players[p_idx].energy_zone.len())
                .filter(|&i| !state.core.players[p_idx].is_energy_tapped(i))
                .count() as i32;

            let is_optional =
                (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
            if is_optional && ctx.choice_index == -1 {
                if available < v {
                    if state.debug.debug_mode {
                        println!("[DEBUG] O_PAY_ENERGY: cannot afford optional cost.");
                    }
                    return Some(HandlerResult::SetCond(false)); // Can't afford optional -> SetCond(false)
                } else {
                    if state.debug.debug_mode {
                        println!(
                            "[DEBUG] O_PAY_ENERGY: attempting optional suspension (instr_ip={}).",
                            instr_ip
                        );
                    }
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_PAY_ENERGY,
                        0,
                        "OPTIONAL",
                        "",
                        a as u64,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }

            if ctx.choice_index == 99 {
                return Some(HandlerResult::SetCond(false));
            }

            let mut next_ctx = ctx.clone();
            if is_optional && ctx.choice_index != -1 && ctx.v_remaining == -1 {
                if ctx.choice_index == 1 {
                    return Some(HandlerResult::SetCond(false));
                } // Declined -> SetCond(false)
                next_ctx.choice_index = -1;
                next_ctx.v_remaining = v as i16;
            }

            if next_ctx.choice_index == 99 {
                return Some(HandlerResult::SetCond(false));
            } else if available < v {
                return Some(HandlerResult::SetCond(false));
            } else {
                if next_ctx.choice_index != -1 {
                    let idx = next_ctx.choice_index as usize;
                    if idx < state.core.players[p_idx].energy_zone.len()
                        && !state.core.players[p_idx].is_energy_tapped(idx)
                    {
                        state.core.players[p_idx].set_energy_tapped(idx, true);
                        next_ctx.v_remaining -= 1;
                        if next_ctx.v_remaining > 0 {
                            next_ctx.choice_index = -1;
                            if suspend_interaction(
                                state,
                                db,
                                &next_ctx,
                                instr_ip,
                                O_PAY_ENERGY,
                                0,
                                "PAY_ENERGY",
                                "",
                                0,
                                next_ctx.v_remaining,
                            ) {
                                return Some(HandlerResult::Suspend);
                            }
                        }
                    }
                } else {
                    // Auto-pay
                    let mut paid = 0;
                    let player = &mut state.core.players[p_idx];
                    for i in 0..player.energy_zone.len() {
                        if paid >= v {
                            break;
                        }
                        if !player.is_energy_tapped(i) {
                            player.set_energy_tapped(i, true);
                            paid += 1;
                        }
                    }
                }
            }
            Some(HandlerResult::SetCond(true))
        }
        O_ACTIVATE_ENERGY => {
            // Readies up to `v` tapped energy.
            let mut count = 0;
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                if state.debug.debug_mode {
                    println!(
                        "[ENERGY_DEBUG] source_card_id={}, card_no={}, groups={:?}",
                        ctx.source_card_id, card.card_no, card.groups
                    );
                }
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            } else {
                if state.debug.debug_mode {
                    println!(
                        "[ENERGY_DEBUG] card NOT FOUND for id={}",
                        ctx.source_card_id
                    );
                }
            }

            for i in 0..state.core.players[p_idx].energy_zone.len() {
                if count >= v {
                    break;
                }
                if state.core.players[p_idx].is_energy_tapped(i) {
                    state.core.players[p_idx].set_energy_tapped(i, false);
                    state.core.players[p_idx].activated_energy_group_mask |= group_bits;
                    count += 1;
                }
            }
            Some(HandlerResult::Continue)
        }
        O_PAY_ENERGY_DYNAMIC => {
            // Pay energy equal to card score + v
            // Used by cards that have dynamic energy costs based on card properties
            let base_score = state.core.players[p_idx].score as i32;
            let total_cost = (base_score + v) as usize;

            if state.debug.debug_mode {
                println!(
                    "[DEBUG] O_PAY_ENERGY_DYNAMIC: base_score={}, v={}, total_cost={}",
                    base_score, v, total_cost
                );
            }

            let available = (0..state.core.players[p_idx].energy_zone.len())
                .filter(|&i| !state.core.players[p_idx].is_energy_tapped(i))
                .count();

            if available < total_cost {
                return Some(HandlerResult::SetCond(false));
            }

            // Auto-pay the energy
            let mut paid = 0;
            for i in 0..state.core.players[p_idx].energy_zone.len() {
                if paid >= total_cost {
                    break;
                }
                if !state.core.players[p_idx].is_energy_tapped(i) {
                    state.core.players[p_idx].set_energy_tapped(i, true);
                    paid += 1;
                }
            }
            Some(HandlerResult::SetCond(true))
        }
        O_PLACE_ENERGY_UNDER_MEMBER => {
            // Place energy card under a member
            // Source zone shifted to Slot bits 16-23
            let src_zone = (s >> 16) & 0xFF;
            let slot = if ctx.area_idx >= 0 {
                ctx.area_idx as usize
            } else {
                0
            };

            if slot < 3 {
                match src_zone {
                    7 => {
                        // From Discard
                        if let Some(cid) = state.core.players[p_idx].discard.pop() {
                            state.core.players[p_idx].stage_energy[slot].push(cid);
                        }
                    }
                    8 | 0 => {
                        // From Deck (0 default is deck in this context)
                        if let Some(cid) = state.core.players[p_idx].deck.pop() {
                            state.core.players[p_idx].stage_energy[slot].push(cid);
                        }
                    }
                    _ => {
                        // From Energy (Default 1 or other)
                        if !state.core.players[p_idx].energy_zone.is_empty() {
                            // Find an untapped energy to move
                            for i in 0..state.core.players[p_idx].energy_zone.len() {
                                if !state.core.players[p_idx].is_energy_tapped(i) {
                                    let energy_cid =
                                        state.core.players[p_idx].energy_zone.remove(i);
                                    state.core.players[p_idx].stage_energy[slot].push(energy_cid);
                                    break;
                                }
                            }
                        }
                    }
                }
            }
            Some(HandlerResult::Continue)
        }
        _ => None,
    }
}

pub fn handle_member_state(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_ACTIVATE_MEMBER => {
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            }

            if target_slot == 1 {
                for i in 0..3 {
                    if state.core.players[p_idx].is_tapped(i) {
                        state.core.players[p_idx].set_tapped(i, false);
                        state.core.players[p_idx].activated_member_group_mask |= group_bits;
                    }
                }
            } else if resolved_slot < 3 {
                if state.core.players[p_idx].is_tapped(resolved_slot as usize) {
                    state.core.players[p_idx].set_tapped(resolved_slot as usize, false);
                    state.core.players[p_idx].activated_member_group_mask |= group_bits;
                }
            }
        }
        O_SET_TAPPED => {
            if resolved_slot < 3 {
                state.core.players[p_idx].set_tapped(resolved_slot as usize, v != 0);
            }
        }
        O_TAP_MEMBER => {
            let mut resolved_slot = resolve_target_slot(s, ctx);
            let target_p_idx = if s & 0x1000000 != 0 { 1 - ctx.player_id } else { ctx.player_id };

            // Robustness Fix for Q183: If selection is needed (v=0) but missing from bytecode
            if v == 0 && resolved_slot == 4 && a & 0x02 == 0 {
                // If it's an optional cost or clearly multi-target, force selection mode
                if a & 0x01 != 0 || a & 0x80 != 0 {
                    let mod_a = a | 0x02; // Force selection mode bit
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        "TAP_M_SELECT",
                        &choice_text,
                        mod_a as u64,
                        v as i16,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }

            let is_optional =
                (a as u64 & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0;
            if ctx.choice_index == -1 {
                if is_optional || (a & 0x01) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        "OPTIONAL",
                        &choice_text,
                        a as u64,
                        -1,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                if (a & 0x02) != 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        "TAP_M_SELECT",
                        &choice_text,
                        a as u64,
                        v as i16,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                // Only auto-tap if it was NOT an optional handler that just suspended or was bypassed
                if (a & 0x03) == 0 && resolved_slot < 3 {
                    state.core.players[p_idx].set_tapped(resolved_slot as usize, true);
                }
            } else {
                if is_optional || (a & 0x01) != 0 {
                    // 1 and 99 are both mapped to "No" for optional costs
                    if ctx.choice_index == CHOICE_DONE || ctx.choice_index == 1 {
                        return Some(HandlerResult::SetCond(false));
                    }
                    if resolved_slot < 3 {
                        state.core.players[p_idx].set_tapped(resolved_slot as usize, true);
                    }
                    return Some(HandlerResult::SetCond(true));
                } else {
                    let slot = ctx.choice_index as usize;
                    if slot < 3 {
                        state.core.players[p_idx].set_tapped(slot, true);
                    }
                    return Some(HandlerResult::SetCond(true));
                }
            }
        }
        O_TAP_OPPONENT => {
            let target_p_idx = 1 - (ctx.activator_id as usize);
            // println!("[DEBUG] O_TAP_OPPONENT handler: v={}, a={}, s={}", v, a, s);
            let count = if ctx.v_remaining == -1 {
                v as i16
            } else {
                ctx.v_remaining
            };
            if count <= 0 {
                return Some(HandlerResult::Continue);
            }

            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                
                let old_cp = state.current_player;
                
                // [Q189] Create a flipped context so suspend_interaction sets correct current_player
                let mut flip_ctx = ctx.clone();
                flip_ctx.player_id = target_p_idx as u8;
                state.current_player = target_p_idx as u8;
                if state.debug.debug_mode {
                    println!("[DEBUG] O_TAP_OPPONENT: Suspending. Switching CP from {} to {}", old_cp, state.current_player);
                }

                let suspended = suspend_interaction(
                    state,
                    db,
                    &flip_ctx,
                    instr_ip,
                    O_TAP_OPPONENT,
                    0,
                    "TAP_O",
                    &choice_text,
                    a as u64,
                    count,
                );

                if suspended {
                    return Some(HandlerResult::Suspend);
                }

                state.current_player = old_cp;
            } else {
                let slot_idx = ctx.choice_index as usize;
                if slot_idx < 3 {
                    state.core.players[target_p_idx].set_tapped(slot_idx, true);
                    ctx.v_remaining = count - 1;
                    ctx.choice_index = -1;
                    if ctx.v_remaining > 0 {
                        let choice_text = get_choice_text(db, ctx);
                                               // [Q189] Switch to opponent during selection
                                let mut flip_ctx = ctx.clone();
                                flip_ctx.player_id = target_p_idx as u8;

                                let old_cp = state.current_player;
                                state.current_player = target_p_idx as u8;

                        let suspended = suspend_interaction(
                            state,
                            db,
                            &flip_ctx,
                            instr_ip,
                            O_TAP_OPPONENT,
                            0,
                            "TAP_O",
                            &choice_text,
                            a as u64,
                            ctx.v_remaining,
                        );

                        if suspended {
                            return Some(HandlerResult::Suspend);
                        }
                        
                        state.current_player = old_cp;
                    }
                }
            }
        }
        O_MOVE_MEMBER | O_FORMATION_CHANGE => {
            let src_slot = if op == O_FORMATION_CHANGE && target_slot == 4 {
                ctx.area_idx as usize
            } else if op == O_MOVE_MEMBER && ctx.area_idx >= 0 {
                ctx.area_idx as usize
            } else {
                resolved_slot as usize
            };

            if op == O_MOVE_MEMBER && a == 99 && ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_MOVE_MEMBER,
                    s,
                    "MOVE_MEMBER_DEST",
                    &choice_text,
                    0,
                    -1,
                ) {
                    return Some(HandlerResult::Suspend);
                }
            }

            let dst_slot = if op == O_MOVE_MEMBER && a == 99 && ctx.choice_index != -1 {
                let slot = ctx.choice_index as usize;
                ctx.choice_index = -1;
                slot
            } else if ctx.target_slot != -1 && a != 99 {
                ctx.target_slot as usize
            } else {
                a as usize
            };
            if src_slot < 3 && dst_slot < 3 && src_slot != dst_slot {
                state.core.players[p_idx].swap_slot_data(src_slot, dst_slot);
                for &slot in &[src_slot, dst_slot] {
                    let cid = state.core.players[p_idx].stage[slot];
                    if cid >= 0 {
                        let mut pos_ctx = ctx.clone();
                        pos_ctx.source_card_id = cid;
                        pos_ctx.area_idx = slot as i16;
                        state.trigger_abilities(db, TriggerType::OnPositionChange, &pos_ctx);
                    }
                }
            }
        }
        O_PLACE_UNDER => {
            let slot = if ctx.target_slot != -1 {
                ctx.target_slot as usize
            } else {
                resolved_slot as usize
            };
            if slot < 3 {
                if a == 0 && !state.core.players[p_idx].hand.is_empty() {
                    let hand_idx = if ctx.choice_index != -1 {
                        ctx.choice_index as usize
                    } else {
                        state.core.players[p_idx].hand.len() - 1
                    };
                    if hand_idx < state.core.players[p_idx].hand.len() {
                        let cid = state.core.players[p_idx].hand.remove(hand_idx);
                        state.core.players[p_idx].stage_energy[slot].push(cid);
                    }
                } else if a == 1 {
                    if let Some(cid) = state.core.players[p_idx].energy_zone.pop() {
                        state.core.players[p_idx].stage_energy[slot].push(cid);
                    }
                }
                state.core.players[p_idx].stage_energy_count[slot] =
                    state.core.players[p_idx].stage_energy[slot].len() as u8;
            }
        }
        O_ADD_STAGE_ENERGY => {
            if resolved_slot < 3 {
                for _ in 0..v {
                    state.core.players[p_idx].stage_energy[resolved_slot as usize].push(2000);
                }
                state.core.players[p_idx].sync_stage_energy_count(resolved_slot as usize);
            }
        }
        O_GRANT_ABILITY => {
            let ab_idx = v as u16;
            let source_cid = ctx.source_card_id;
            let mut targets = smallvec::SmallVec::<[i32; 3]>::new();
            if target_slot == 4 && resolved_slot < 3 {
                let cid = state.core.players[p_idx].stage[resolved_slot as usize];
                if cid >= 0 {
                    targets.push(cid);
                }
            } else if target_slot == 1 {
                for i in 0..3 {
                    let cid = state.core.players[p_idx].stage[i];
                    if cid >= 0 {
                        targets.push(cid);
                    }
                }
            } else if target_slot >= 0 && target_slot < 3 {
                let cid = state.core.players[p_idx].stage[target_slot as usize];
                if cid >= 0 {
                    targets.push(cid);
                }
            }

            for t_cid in targets {
                state.core.players[p_idx]
                    .granted_abilities
                    .push((t_cid, source_cid, ab_idx));
            }
        }
        O_PLAY_MEMBER_FROM_HAND => {
            let remaining = if ctx.v_remaining == -1 {
                if v == 1 {
                    1
                } else {
                    2
                } // v=1 means card pre-selected, just need slot
            } else {
                ctx.v_remaining
            };

            if state.debug.debug_mode {
                println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: v={}, remaining={}, target_slot={}, choice_index={}", v, remaining, ctx.target_slot, ctx.choice_index);
            }

            if remaining == 2 {
                // Step 1: Select Card from Hand
                if ctx.choice_index == -1 {
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_HAND,
                        0,
                        "SELECT_HAND_PLAY",
                        "",
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
                let h_idx = ctx.choice_index as usize;

                if h_idx < state.core.players[p_idx].hand.len() {
                    ctx.target_slot = h_idx as i16;
                    ctx.v_remaining = 1;
                    ctx.choice_index = -1;
                    if state.debug.debug_mode {
                        println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: Step 1 Done. Selected real hand_idx={}", h_idx);
                    }
                    // Move to Step 2
                    return handle_member_state(state, db, ctx, op, v, a, s, instr_ip);
                }
            } else if remaining == 1 {
                // Step 2: Select Slot
                if ctx.choice_index == -1 {
                    let mut next_ctx = ctx.clone();
                    next_ctx.player_id = p_idx as u8;
                    if suspend_interaction(
                        state,
                        db,
                        &next_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_HAND,
                        s,
                        "SELECT_STAGE",
                        "",
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let slot_idx = ctx.choice_index as usize;
                if state.debug.debug_mode {
                    println!(
                        "[DEBUG] O_PLAY_MEMBER_FROM_HAND: Step 2 Selection. slot_idx={}",
                        slot_idx
                    );
                }

                if slot_idx < 3 {
                    // Execute Play
                    let h_idx = ctx.target_slot as usize;
                    if h_idx < state.core.players[p_idx].hand.len() {
                        let cid = state.core.players[p_idx].hand.remove(h_idx);
                        if state.debug.debug_mode {
                            println!("[DEBUG] O_PLAY_MEMBER_FROM_HAND: Executing Play of cid={} to slot={}", cid, slot_idx);
                        }
                        if let Some(old) =
                            state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx)
                        {
                            state.core.players[p_idx].discard.push(old);
                        }
                        state.core.players[p_idx].stage[slot_idx] = cid;
                        state.core.players[p_idx].set_tapped(slot_idx, false);
                        state.core.players[p_idx].set_moved(slot_idx, true);
                        state.register_played_member(p_idx, cid, db);

                        let new_ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        ctx.choice_index = -1;
                        ctx.v_remaining = 0;
                        return Some(HandlerResult::Continue);
                    }
                }
            }
        }
        O_PLAY_MEMBER_FROM_DISCARD => {
            let opponent_bit = (s >> 24) & 1;
            let target_p_idx = if opponent_bit != 0 {
                1 - (ctx.activator_id as usize)
            } else {
                ctx.activator_id as usize
            };
            let empty_slot_only = ((s as u64)
                & crate::core::logic::interpreter::constants::FLAG_EMPTY_SLOT_ONLY)
                != 0;

            let filter_attr_base = a as u64;
            let is_total_cost = (filter_attr_base
                & crate::core::logic::interpreter::constants::FILTER_TOTAL_COST)
                != 0;

            let mut remaining = if ctx.v_remaining == -1 {
                if is_total_cost {
                    ctx.v_accumulated = ((filter_attr_base
                        >> crate::core::generated_constants::FILTER_COST_SHIFT)
                        & 0x1F) as i16;
                }
                v as i16 * 2
            } else {
                ctx.v_remaining
            };
            if remaining <= 0 {
                return Some(HandlerResult::Continue);
            }

            if remaining % 2 == 0 {
                // Softlock Prevention: If empty_slot_only is set, check if any slot is actually empty
                if empty_slot_only
                    && state.core.players[target_p_idx]
                        .stage
                        .iter()
                        .all(|&c| c >= 0)
                {
                    return Some(HandlerResult::Continue);
                }

                // Step 1: Choose Card
                if state.core.players[target_p_idx].looked_cards.is_empty() {
                    let mut filter_attr = filter_attr_base;
                    if is_total_cost {
                        filter_attr = (filter_attr
                            & !(0x1F << crate::core::generated_constants::FILTER_COST_SHIFT))
                            | ((ctx.v_accumulated as u64)
                                << crate::core::generated_constants::FILTER_COST_SHIFT);
                    }
                    for &cid in &state.core.players[target_p_idx].discard {
                        if db.get_member(cid).is_some()
                            && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
                        {
                            state.core.players[target_p_idx].looked_cards.push(cid);
                        }
                    }
                    if state.core.players[target_p_idx].looked_cards.is_empty() {
                        return Some(HandlerResult::Continue);
                    }

                    // Reset stale choice_index from previous round and re-suspend
                    ctx.choice_index = -1;
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(
                        state,
                        db,
                        &target_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_DISCARD,
                        s,
                        "SELECT_DISCARD_PLAY",
                        &choice_text,
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }

                let idx = ctx.choice_index as usize;
                let cards_len = state.core.players[target_p_idx].looked_cards.len();

                if idx < cards_len {
                    let cid = state.core.players[target_p_idx].looked_cards[idx];
                    state.core.players[target_p_idx].looked_cards.clear();
                    state.core.players[target_p_idx].looked_cards.push(cid);

                    remaining -= 1;
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    let choice_type = if empty_slot_only {
                        "SELECT_STAGE_EMPTY"
                    } else {
                        "SELECT_STAGE"
                    };
                    if suspend_interaction(
                        state,
                        db,
                        &target_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_DISCARD,
                        s,
                        choice_type,
                        "",
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            } else {
                if state.core.players[target_p_idx].looked_cards.is_empty() {
                    return Some(HandlerResult::Continue);
                }
                let card_id = state.core.players[target_p_idx].looked_cards.remove(0);

                // If the player passed the stage selection (choice 99), we stop here and DON'T remove from discard.
                if ctx.choice_index == 99 {
                    return Some(HandlerResult::Continue);
                }

                if let Some(pos) = state.core.players[target_p_idx]
                    .discard
                    .iter()
                    .position(|&cid| cid == card_id)
                {
                    let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 {
                        ctx.choice_index as usize
                    } else {
                        resolved_slot as usize
                    };

                    if slot_idx < 3 {
                        // Validate slot restriction or overlap
                        if (state.core.players[target_p_idx].prevent_play_to_slot_mask
                            & (1 << slot_idx))
                            != 0
                            || (empty_slot_only
                                && state.core.players[target_p_idx].stage[slot_idx] != -1)
                        {
                            // If the slot is locked or occupied (when empty only is req), we abort the play and DON'T remove from discard
                            return Some(HandlerResult::Continue);
                        }

                        if is_total_cost {
                            if let Some(m) = db.get_member(card_id) {
                                ctx.v_accumulated = (ctx.v_accumulated - m.cost as i16).max(0);
                            }
                        }

                        state.core.players[target_p_idx].discard.remove(pos);

                        if let Some(old) =
                            state.handle_member_leaves_stage(target_p_idx, slot_idx, db, ctx)
                        {
                            state.core.players[target_p_idx].discard.push(old);
                        }
                        state.core.players[target_p_idx].stage[slot_idx] = card_id;
                        state.core.players[target_p_idx].set_tapped(slot_idx, true); // WAIT state
                        state.core.players[target_p_idx].set_moved(slot_idx, true);
                        state.register_played_member(target_p_idx, card_id, db);

                        // Rule Check: Slot is locked for the rest of the turn (Q169)
                        state.core.players[target_p_idx].prevent_play_to_slot_mask |= 1 << slot_idx;

                        let mut new_ctx = AbilityContext {
                            source_card_id: card_id,
                            player_id: target_p_idx as u8,
                            activator_id: target_p_idx as u8,
                            area_idx: slot_idx as i16,
                            v_accumulated: ctx.v_accumulated,
                            ..Default::default()
                        };
                        new_ctx.v_remaining = ctx.v_remaining;
                        state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                    }
                }

                remaining -= 1;
                if remaining > 0 {
                    // Start next pair: repopulate looked_cards for the next card selection
                    let mut filter_attr = filter_attr_base;
                    if is_total_cost {
                        filter_attr = (filter_attr
                            & !(0x1F << crate::core::generated_constants::FILTER_COST_SHIFT))
                            | ((ctx.v_accumulated as u64)
                                << crate::core::generated_constants::FILTER_COST_SHIFT);
                    }
                    state.core.players[target_p_idx].looked_cards.clear();
                    for &cid in &state.core.players[target_p_idx].discard {
                        if db.get_member(cid).is_some()
                            && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
                        {
                            state.core.players[target_p_idx].looked_cards.push(cid);
                        }
                    }
                    if state.core.players[target_p_idx].looked_cards.is_empty() {
                        // No more eligible cards in discard
                        return Some(HandlerResult::Continue);
                    }
                    let mut target_ctx = ctx.clone();
                    target_ctx.player_id = target_p_idx as u8;
                    target_ctx.choice_index = -1;
                    let choice_text = get_choice_text(db, &target_ctx);
                    if suspend_interaction(
                        state,
                        db,
                        &target_ctx,
                        instr_ip,
                        O_PLAY_MEMBER_FROM_DISCARD,
                        s,
                        "SELECT_DISCARD_PLAY",
                        &choice_text,
                        a as u64,
                        remaining,
                    ) {
                        return Some(HandlerResult::Suspend);
                    }
                }
            }
        }
        O_INCREASE_COST => {
            state.core.players[p_idx].cost_modifiers.push((
                crate::core::logic::Condition {
                    condition_type: crate::core::enums::ConditionType::None,
                    value: 0,
                    attr: 0,
                    target_slot: 0,
                    is_negated: false,
                    params: serde_json::Value::Null,
                },
                v,
            ));
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

pub fn handle_meta_control(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    instr_ip: usize,
) -> Option<HandlerResult> {
    let base_p = ctx.activator_id as usize;
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let target_p_idx = if (s & (1 << 24)) != 0 || target_slot == 2 {
        1 - base_p
    } else {
        base_p
    };
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_CALC_SUM_COST => {
            let mut sum = 0;
            for &cid in &ctx.selected_cards {
                if cid >= 0 {
                    if let Some(member) = db.get_member(cid) {
                        sum += member.cost as i32;
                    }
                }
            }
            println!("[DEBUG] CALC_SUM_COST: total_sum={}, cards={:?}", sum, ctx.selected_cards);
            ctx.v_accumulated = sum as i16;
        }
        O_NEGATE_EFFECT => {
            let trigger_type = match v {
                1 => TriggerType::OnPlay,
                2 => TriggerType::OnLiveStart,
                3 => TriggerType::OnLiveSuccess,
                4 => TriggerType::TurnStart,
                5 => TriggerType::TurnEnd,
                6 => TriggerType::Constant,
                7 => TriggerType::Activated,
                8 => TriggerType::OnLeaves,
                9 => TriggerType::OnReveal,
                10 => TriggerType::OnPositionChange,
                _ => TriggerType::None,
            };
            if target_slot >= 0 && (target_slot as usize) < 3 {
                let cid = state.core.players[p_idx].stage[target_slot as usize];
                if cid >= 0 {
                    state.core.players[p_idx].negated_triggers.push((
                        cid,
                        trigger_type,
                        (a as u64 & FILTER_MASK_LOWER).max(1) as i32,
                    ));
                }
            }
        }
        O_LOSE_EXCESS_HEARTS => {
            state.core.players[p_idx].excess_hearts = 0;
        }
        O_DIV_VALUE => {
            if v > 1 {
                ctx.v_accumulated /= v as i16;
            }
        }
        O_RESTRICTION => {
            state.core.players[p_idx]
                .restrictions
                .push((a as u64 & FILTER_MASK_LOWER) as u8);
            if (a as u64 & FILTER_MASK_LOWER) == 1 {
                state.core.players[p_idx].set_flag(
                    crate::core::logic::player::PlayerState::FLAG_CANNOT_LIVE,
                    true,
                );
            }
        }
        O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
            // Systemic Fix: If area bits (28-30) are present in the slot parameter, auto-resolve
            let area_val = (s >> 28) & 0x07;
            if area_val >= 1 && area_val <= 3 {
                let auto_slot = (area_val - 1) as i16;
                ctx.choice_index = auto_slot;
                ctx.area_idx = auto_slot;
                if state.debug.debug_mode {
                    println!(
                        "[DEBUG] O_SELECT_MEMBER: Auto-selecting slot {} based on area bits",
                        auto_slot
                    );
                }
            } else if ctx.choice_index == -1 {
                let choice_type = if op == O_SELECT_MEMBER {
                    "SELECT_MEMBER"
                } else if op == O_SELECT_LIVE {
                    "SELECT_LIVE"
                } else if op == O_SELECT_PLAYER {
                    "SELECT_PLAYER"
                } else {
                    "UNKNOWN"
                };
                let mut flip_ctx = ctx.clone();
                if s == 2 {
                    flip_ctx.player_id = 1 - (p_idx as u8);
                } else if s == 3 {
                    flip_ctx.player_id = 1;
                }
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    &flip_ctx,
                    instr_ip,
                    op,
                    s,
                    choice_type,
                    &choice_text,
                    a as u64,
                    -1,
                ) {
                    return Some(HandlerResult::Suspend);
                }
            } else {
                let choice = ctx.choice_index as i32;
                let source_zone = (s >> 16) & 0xFF;

                if source_zone == 6 {
                    // Hand selection: choice IS the index
                    ctx.target_slot = choice as i16;
                } else if source_zone == 7 {
                    // Discard selection: choice IS the index
                    ctx.target_slot = choice as i16;
                } else {
                    // Default to Stage Slot or Live Zone: choice IS the index
                    ctx.target_slot = choice as i16;
                    ctx.area_idx = choice as i16;
                }
            }
        }
        O_OPPONENT_CHOOSE => {
            if ctx.choice_index == -1 {
                let mut flip_ctx = ctx.clone();
                flip_ctx.player_id = 1 - (p_idx as u8);
                let old_cp = state.current_player;
                state.current_player = 1 - ctx.player_id;
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    &flip_ctx,
                    instr_ip,
                    O_OPPONENT_CHOOSE,
                    0,
                    "OPPONENT_CHOOSE",
                    &choice_text,
                    0,
                    -1,
                ) {
                    return Some(HandlerResult::Suspend);
                }
                state.current_player = old_cp;
            }
            // On resumption, ctx.player_id is already flipped (stored as flip_ctx)
            // Subsequent opcodes will use the flipped player_id (opponent's perspective)
        }
        O_PREVENT_ACTIVATE => {
            let target_p_idx = if s == 1 { 1 - base_p } else { base_p };
            state.core.players[target_p_idx].prevent_activate = 1;
        }
        O_PREVENT_BATON_TOUCH => {
            let target_p_idx = if s == 1 { 1 - base_p } else { base_p };
            state.core.players[target_p_idx].prevent_baton_touch = 1;
        }
        O_PREVENT_SET_TO_SUCCESS_PILE => {
            let target_p_idx = if s == 1 { 1 - base_p } else { base_p };
            state.core.players[target_p_idx].prevent_success_pile_set = 1;
        }
        O_PREVENT_PLAY_TO_SLOT => {
            let target_p_idx = if (s as u32 & FLAG_TARGET_OPPONENT as u32) != 0 {
                1 - base_p
            } else {
                base_p
            };
            if resolved_slot >= 0 && resolved_slot < 3 {
                state.core.players[target_p_idx].prevent_play_to_slot_mask |= 1 << resolved_slot;
            }
        }
        O_TRIGGER_REMOTE => {
            let target_cid = if target_slot >= 0 && target_slot < 3 {
                state.core.players[p_idx].stage[target_slot as usize]
            } else {
                -1
            };
            if target_cid >= 0 {
                if let Some(m) = db.get_member(target_cid as i32) {
                    if (v as usize) < m.abilities.len() {
                        return Some(HandlerResult::BranchToBytecode(std::sync::Arc::new(
                            m.abilities[v as usize].bytecode.clone(),
                        )));
                    }
                }
            }
        }
        O_REDUCE_LIVE_SET_LIMIT => {
            state.core.players[p_idx].prevent_success_pile_set = state.core.players[p_idx]
                .prevent_success_pile_set
                .saturating_add(v as u8);
        }
        O_REDUCE_YELL_COUNT => {
            state.core.players[p_idx].yell_count_reduction = state.core.players[p_idx]
                .yell_count_reduction
                .saturating_add(v as i16);
        }
        O_META_RULE => {
            if a == 0 || a == 10 {
                state.core.players[target_p_idx].cheer_mod_count = state.core.players[target_p_idx]
                    .cheer_mod_count
                    .saturating_add(v as u16);
            } else if a == 8 {
                // SCORE_RULE: dynamic conditional rules for scoring
                // v = 1 means "ALL_ENERGY_ACTIVE"
                if v == 1 {
                    let all_active = state.core.players[p_idx].tapped_energy_count() == 0;
                    if state.debug.debug_mode {
                        // println!("[DEBUG] SCORE_RULE: ALL_ENERGY_ACTIVE evaluated to {}", all_active);
                    }
                    return Some(HandlerResult::SetCond(all_active));
                }
            }
        }
        O_BATON_TOUCH_MOD => state.core.players[p_idx].baton_touch_limit = v as u8,
        O_IMMUNITY => state.core.players[p_idx].set_flag(
            crate::core::logic::player::PlayerState::FLAG_IMMUNITY,
            v != 0,
        ),
        O_COLOR_SELECT => {
            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_COLOR_SELECT,
                    0,
                    "COLOR_SELECT",
                    &choice_text,
                    0,
                    -1,
                ) {
                    return Some(HandlerResult::Suspend);
                }
            } else {
                ctx.selected_color = ctx.choice_index;
            }
        }
        O_SWAP_AREA => {
            let p = &mut state.core.players[target_p_idx];
            let temp_stage = p.stage;
            let temp_energy = p.stage_energy_count;
            let temp_tapped = [p.is_tapped(0), p.is_tapped(1), p.is_tapped(2)];
            let temp_moved = [p.is_moved(0), p.is_moved(1), p.is_moved(2)];
            if v == 2 || (a == 1 && s == 0) {
                let src = ctx.area_idx as usize;
                let dst = a as usize;
                if src < 3 && dst < 3 {
                    p.stage[src] = temp_stage[dst];
                    p.stage[dst] = temp_stage[src];
                    p.stage_energy_count[src] = temp_energy[dst];
                    p.stage_energy_count[dst] = temp_energy[src];
                    p.set_tapped(src, temp_tapped[dst]);
                    p.set_tapped(dst, temp_tapped[src]);
                    p.set_moved(src, temp_moved[dst]);
                    p.set_moved(dst, temp_moved[src]);
                }
            } else {
                if s == 4 {
                    // Rotate Left
                    p.stage[0] = temp_stage[1];
                    p.stage[1] = temp_stage[2];
                    p.stage[2] = temp_stage[0];
                    p.stage_energy_count[0] = temp_energy[1];
                    p.stage_energy_count[1] = temp_energy[2];
                    p.stage_energy_count[2] = temp_energy[0];
                    p.set_tapped(0, temp_tapped[1]);
                    p.set_tapped(1, temp_tapped[2]);
                    p.set_tapped(2, temp_tapped[0]);
                    p.set_moved(0, temp_moved[1]);
                    p.set_moved(1, temp_moved[2]);
                    p.set_moved(2, temp_moved[0]);
                } else {
                    // Rotate Right (default)
                    p.stage[0] = temp_stage[2];
                    p.stage[1] = temp_stage[0];
                    p.stage[2] = temp_stage[1];
                    p.stage_energy_count[0] = temp_energy[2];
                    p.stage_energy_count[1] = temp_energy[0];
                    p.stage_energy_count[2] = temp_energy[1];
                    p.set_tapped(0, temp_tapped[2]);
                    p.set_tapped(1, temp_tapped[0]);
                    p.set_tapped(2, temp_tapped[1]);
                    p.set_moved(0, temp_moved[2]);
                    p.set_moved(1, temp_moved[0]);
                    p.set_moved(2, temp_moved[1]);
                }
            }
        }
        O_REPEAT_ABILITY => {
            // v = max repeat count (0 = infinite, N = repeat N more times)
            // Returns Branch(0) to restart ability from beginning, or Continue if limit reached
            let max_repeats = v;
            if max_repeats == 0 || ctx.repeat_count < max_repeats as i16 {
                ctx.repeat_count = ctx.repeat_count.saturating_add(1);
                if state.debug.debug_mode {
                    // println!("[DEBUG] O_REPEAT_ABILITY: repeating ability (count={}/{})", ctx.repeat_count, max_repeats);
                }
                return Some(HandlerResult::Branch(0)); // Jump back to start of ability
            } else {
                if state.debug.debug_mode {
                    // println!("[DEBUG] O_REPEAT_ABILITY: limit reached (count={}/{})", ctx.repeat_count, max_repeats);
                }
            }
        }
        O_SET_TARGET_SELF => {
            ctx.player_id = ctx.activator_id;
        }
        O_SET_TARGET_OPPONENT => {
            ctx.player_id = 1 - ctx.activator_id;
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}

pub fn handle_score_hearts(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
) -> Option<HandlerResult> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_BOOST_SCORE => {
            let mut final_v = v;
            if (a as u64 & DYNAMIC_VALUE) != 0 {
                // slot (s) contains the count opcode
                let count = resolve_count(
                    state,
                    _db,
                    s,
                    a as u64 & !DYNAMIC_VALUE & FILTER_MASK_LOWER,
                    0,
                    ctx,
                    0,
                );
                final_v = v * count;
            }
            state.core.players[p_idx].live_score_bonus += final_v;
            state.core.players[p_idx]
                .live_score_bonus_logs
                .push((ctx.source_card_id, final_v));
            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_BOOST_SCORE, final_v, a, s, 0) {
                    state.log(msg);
                }
            }
        }
        O_REDUCE_COST => state.core.players[p_idx].cost_reduction += v as i16,
        O_SET_SCORE => state.core.players[p_idx].score = v as u32,
        O_ADD_BLADES | O_BUFF_POWER => {
            if target_slot == 1 {
                for t in 0..3 {
                    state.core.players[p_idx].blade_buffs[t] += v as i16;
                    state.core.players[p_idx].blade_buff_logs.push((
                        ctx.source_card_id,
                        v as i16,
                        t as u8,
                    ));
                }
            } else if resolved_slot < 3 {
                state.core.players[p_idx].blade_buffs[resolved_slot as usize] += v as i16;
                state.core.players[p_idx].blade_buff_logs.push((
                    ctx.source_card_id,
                    v as i16,
                    resolved_slot as u8,
                ));
            }
            // Unified logging: EFFECT events now go to both turn_history and rule_log
            state.log_event(
                "EFFECT",
                &format!("+{} Appeal", v),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_SET_BLADES => {
            if target_slot == 4 && ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                state.core.players[p_idx].blade_buffs[ctx.area_idx as usize] = v as i16;
            }
        }
        O_ADD_HEARTS => {
            let mut color = (a as u64 & FILTER_MASK_LOWER) as usize;
            if color == 0 {
                color = ctx.selected_color as usize;
            }
            if color < 7 {
                // DEBUG: Log heart buff application
                if state.debug.debug_mode {
                    // println!("[DEBUG O_ADD_HEARTS] target_slot={}, area_idx={}, color={}, v={}", target_slot, ctx.area_idx, color, v);
                }
                if (target_slot == 4 || target_slot == 0) && ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    state.core.players[p_idx].heart_buffs[ctx.area_idx as usize]
                        .add_to_color(color, v as i32);
                    state.core.players[p_idx].heart_buff_logs.push((
                        ctx.source_card_id,
                        v,
                        color as u8,
                        ctx.area_idx as u8,
                    ));
                } else if target_slot == 1 {
                    for t in 0..3 {
                        state.core.players[p_idx].heart_buffs[t].add_to_color(color, v as i32);
                        state.core.players[p_idx].heart_buff_logs.push((
                            ctx.source_card_id,
                            v,
                            color as u8,
                            t as u8,
                        ));
                    }
                }
            }
            if !state.ui.silent {
                if let Some(msg) = logging::get_opcode_log(O_ADD_HEARTS, v, a, s, 0) {
                    state.log(msg);
                }
            }
            // Unified logging: EFFECT events now go to both turn_history and rule_log
            state.log_event(
                "EFFECT",
                &format!("+{} Heart(s)", v),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_SET_HEARTS => {
            if (a as usize) < 7 {
                let targets = if target_slot == 4 && ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                    vec![ctx.area_idx as usize]
                } else if target_slot == 1 {
                    vec![0, 1, 2]
                } else {
                    vec![]
                };
                for t in targets {
                    state.core.players[p_idx].heart_buffs[t].set_color_count(a as usize, v as u8);
                }
            }
        }
        O_TRANSFORM_COLOR => {
            state.core.players[p_idx]
                .color_transforms
                .push((ctx.source_card_id, 0, v as u8));
        }
        O_REDUCE_HEART_REQ => {
            if (s as usize) < 7 {
                state.core.players[p_idx]
                    .heart_req_reductions
                    .add_to_color(s as usize, v);
                state.core.players[p_idx].heart_req_reduction_logs.push((
                    ctx.source_card_id,
                    s as u8,
                    v as u8,
                ));
            }
        }
        O_TRANSFORM_HEART => {
            let src = a as usize;
            let dst = s as usize;
            if src < 7 && dst < 7 {
                let amt = v.abs();
                if state.core.players[p_idx]
                    .heart_req_reductions
                    .get_color_count(src)
                    >= amt as u8
                {
                    state.core.players[p_idx]
                        .heart_req_reductions
                        .add_to_color(src, -(amt as i32));
                    state.core.players[p_idx]
                        .heart_req_reductions
                        .add_to_color(dst, amt as i32);
                }
            }
        }
        O_INCREASE_HEART_COST => {
            if (s as usize) < 7 {
                state.core.players[p_idx]
                    .heart_req_additions
                    .add_to_color(s as usize, v);
                state.core.players[p_idx].heart_req_addition_logs.push((
                    ctx.source_card_id,
                    s as u8,
                    v as u8,
                ));
            }
        }
        O_SET_HEART_COST => {
            // Set heart cost map override
            // IF v > 15 OR s == -1: Assume packed map (nibbles)
            // ELSE: Treat s as color index and v as value
            let player = &mut state.core.players[p_idx];
            if v > 15 || s == -1 {
                // player.heart_req_additions = HeartBoard::default(); // REMOVED: Don't overwrite, be cumulative for Q115
                // player.heart_req_addition_logs.clear(); 
                for i in 0..7 {
                    let count = ((v >> (i * 4)) & 0xF) as u8;
                    if count > 0 {
                        let old = player.heart_req_additions.get_color_count(i);
                        player.heart_req_additions.set_color_count(i, old.saturating_add(count));
                        player
                            .heart_req_addition_logs
                            .push((ctx.source_card_id, i as u8, count));
                    }
                }
            } else if (s as usize) < 7 {
                player
                    .heart_req_additions
                    .set_color_count(s as usize, v as u8);
                player
                    .heart_req_addition_logs
                    .push((ctx.source_card_id, s as u8, v as u8));
            }
        }
        O_REDUCE_SCORE => {
            // Reduce live score bonus by v
            // Used by cards that penalize the player's live score
            let reduction = v.min(state.core.players[p_idx].live_score_bonus);
            state.core.players[p_idx].live_score_bonus -= reduction;
            if state.debug.debug_mode {
                // println!("[DEBUG] O_REDUCE_SCORE: reduced by {} to {}", reduction, state.core.players[p_idx].live_score_bonus);
            }
        }
        O_LOSE_EXCESS_HEARTS => {
            // Lose excess hearts beyond what's required for the live
            // v = number of excess hearts to lose (0 = lose all excess)
            let player = &mut state.core.players[p_idx];
            let reduction = if v == 0 {
                player.excess_hearts
            } else {
                v as u32
            };
            player.excess_hearts = player.excess_hearts.saturating_sub(reduction);

            if state.debug.debug_mode {
                // println!("[DEBUG] O_LOSE_EXCESS_HEARTS: reduced by {} to {}", reduction, player.excess_hearts);
            }
        }
        O_SKIP_ACTIVATE_PHASE => {
            // Skip the next activate phase
            // Used by cards that prevent member activation
            state.core.players[p_idx].skip_next_activate = true;
            if state.debug.debug_mode {
                // println!("[DEBUG] O_SKIP_ACTIVATE_PHASE: set skip_next_activate=true");
            }
        }
        _ => return None,
    }
    Some(HandlerResult::Continue)
}
