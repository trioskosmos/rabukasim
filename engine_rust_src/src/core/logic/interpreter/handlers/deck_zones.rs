use crate::core::logic::{GameState, CardDatabase, AbilityContext, TriggerType, player::PlayerState, interpreter::constants::*};
use crate::core::enums::*;
use super::HandlerResult;
use super::super::suspension::{suspend_interaction, resolve_target_slot, get_choice_text};
use super::super::logging;
// use super::super::conditions::get_condition_count;
use rand_pcg::Pcg64;
use rand::seq::SliceRandom;
use rand::SeedableRng;

pub fn handle_deck_zones(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, a: i32, s: i32, instr_ip: usize) -> HandlerResult {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let resolved_slot = if target_slot == 10 { ctx.target_slot as i32 } else { resolve_target_slot(target_slot, ctx) as i32 };

    match op {
        O_SEARCH_DECK => {
            let search_target = ctx.target_slot as usize;
            if search_target < state.core.players[p_idx].deck.len() {
                let cid = state.core.players[p_idx].deck.remove(search_target);
                match s {
                    4 => {
                        let slot = a as usize;
                        if slot < 3 {
                            if let Some(old) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                                state.core.players[p_idx].discard.push(old);
                            }
                            state.core.players[p_idx].stage[slot] = cid;
                            state.core.players[p_idx].set_tapped(slot, false);
                            state.core.players[p_idx].set_moved(slot, true);
                            state.register_played_member(p_idx, cid, db);
                            let new_ctx = AbilityContext { source_card_id: cid, player_id: p_idx as u8, area_idx: slot as i16, ..Default::default() };
                            state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        } else {
                            state.core.players[p_idx].hand.push(cid);
                            state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1);
                        }
                    },
                    13 => {
                        state.core.players[p_idx].success_lives.push(cid);
                    },
                    _ => {
                        state.core.players[p_idx].hand.push(cid);
                        state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1);
                    }
                }
                let mut rng = Pcg64::from_os_rng();
                state.core.players[p_idx].deck.shuffle(&mut rng);
            }
        },
        O_ORDER_DECK => {
            if state.core.players[p_idx].looked_cards.is_empty() && v > 0 {
                if state.core.players[p_idx].deck.len() < v as usize { state.resolve_deck_refresh(p_idx); }
                for _ in 0..(v as usize).min(state.core.players[p_idx].deck.len()) {
                    if let Some(cid) = state.core.players[p_idx].deck.pop() { state.core.players[p_idx].looked_cards.push(cid); }
                }
            }
            if !state.core.players[p_idx].looked_cards.is_empty() {
                if ctx.choice_index == -1 {
                     let choice_text = get_choice_text(db, ctx);
                     if suspend_interaction(state, db, ctx, instr_ip, O_ORDER_DECK, 0, "ORDER_DECK", &choice_text, 0, -1) {
                         return HandlerResult::Suspend;
                     }
                }
                let choice = ctx.choice_index;
                if choice >= 0 && (choice as usize) < state.core.players[p_idx].looked_cards.len() {
                     let cid = state.core.players[p_idx].looked_cards.remove(choice as usize);
                     state.core.players[p_idx].deck.push(cid);
                    if !state.core.players[p_idx].looked_cards.is_empty() {
                        if suspend_interaction(state, db, ctx, instr_ip, O_ORDER_DECK, 0, "ORDER_DECK", "", 0, -1) {
                            return HandlerResult::Suspend;
                        }
                    }
                } else {
                    let remainder_mode = a as u8;
                    let looked = std::mem::take(&mut state.core.players[p_idx].looked_cards);
                    if remainder_mode == 1 { state.core.players[p_idx].deck.extend(looked); }
                    else if remainder_mode == 2 { for cid in looked { state.core.players[p_idx].deck.insert(0, cid); } }
                    else { state.core.players[p_idx].discard.extend(looked); }
                }
            }
        },
        O_MOVE_TO_DECK => {
            for _ in 0..(v as usize) {
                match a {
                    1 => if let Some(cid) = state.core.players[p_idx].discard.pop() { state.core.players[p_idx].deck.push(cid); },
                    4 => {
                        let slot = ctx.area_idx as usize;
                        if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                            state.core.players[p_idx].deck.push(cid);
                        }
                    },
                    13 => {
                        if let Some(cid) = state.core.players[p_idx].success_lives.pop() {
                            state.core.players[p_idx].deck.push(cid);
                        }
                    },
                    _ => if let Some(cid) = state.core.players[p_idx].hand.pop() { state.core.players[p_idx].deck.push(cid); }
                }
            }
            let mut rng = Pcg64::from_os_rng();
            state.core.players[p_idx].deck.shuffle(&mut rng);
        },
        O_SWAP_CARDS => {
            for _ in 0..(v as usize) {
                if state.core.players[p_idx].deck.is_empty() { state.resolve_deck_refresh(p_idx); }
                if let Some(cid) = state.core.players[p_idx].deck.pop() {
                    match resolved_slot {
                        7 => state.core.players[p_idx].discard.push(cid),
                        8 => state.core.players[p_idx].deck.push(cid),
                        6 => { state.core.players[p_idx].hand.push(cid); state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1); },
                        _ => state.core.players[p_idx].discard.push(cid),
                    }
                }
            }
        },
        O_REVEAL_UNTIL => {
            let mut found = false;
            let mut revealed_count = 0;
            while !found && !state.core.players[p_idx].deck.is_empty() {
                if revealed_count > 60 { break; } 
                if let Some(cid) = state.core.players[p_idx].deck.pop() {
                    revealed_count += 1;
                    let mut new_ctx = ctx.clone(); new_ctx.source_card_id = cid;
                    state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
                    let mut matches = false;
                    match v {
                        C_TYPE_CHECK => { // TYPE_CHECK
                            if db.get_live(cid as i32).is_some() { if (a & 1) == 1 { matches = true; } } 
                        },
                        C_COST_CHECK => { // COST_GE / COST_CHECK
                            if let Some(member) = db.get_member(cid) { if member.cost >= ((a & 0x3F) >> 1) as u32 { matches = true; } }
                        },
                        _ => {}
                    }
                    if matches {
                        if resolved_slot == 6 {
                            state.core.players[p_idx].hand.push(cid);
                            state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1);
                        } else if resolved_slot == 7 {
                            state.core.players[p_idx].discard.push(cid);
                        }
                        found = true;
                    } else { state.core.players[p_idx].discard.push(cid); }
                }
            }
        },
        O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL => {
            let count = v as usize;
            if resolved_slot == 6 {
                if ctx.choice_index == -1 {
                    if suspend_interaction(state, db, ctx, instr_ip, op, 0, "REVEAL_HAND", "", (a as u32) as u64, v as i16) {
                        return HandlerResult::Suspend;
                    }
                }
                let choice = ctx.choice_index as usize;
                if choice != CHOICE_DONE as usize && choice != CHOICE_ALL as usize && choice < state.core.players[p_idx].hand.len() {
                    let cid = state.core.players[p_idx].hand[choice];
                    if !state.core.players[p_idx].looked_cards.contains(&cid) {
                        state.core.players[p_idx].looked_cards.push(cid);
                    }
                }
                if ctx.choice_index == CHOICE_DONE || ctx.choice_index == CHOICE_ALL || (v > 0 && ctx.v_remaining == 1) {
                    // Done
                } else {
                    let next_v = if v > 0 { (if ctx.v_remaining > 0 { ctx.v_remaining } else { v as i16 }) - 1 } else { 0 };
                    if next_v > 0 || v == 0 {
                        ctx.v_remaining = next_v;
                        if suspend_interaction(state, db, ctx, instr_ip, op, 0, "REVEAL_HAND", "", (a as u32) as u64, next_v) {
                            return HandlerResult::Suspend;
                        }
                    }
                }
            } else {
                if state.core.players[p_idx].deck.len() < count { state.resolve_deck_refresh(p_idx); }
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
                        let mut new_ctx = ctx.clone(); new_ctx.source_card_id = cid;
                        state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
                    }
                }
            }
        },
        O_MOVE_TO_DISCARD => {
            return match handle_move_to_discard(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => HandlerResult::SetCond(success),
                None => HandlerResult::Suspend,
            }
        },
        O_LOOK_AND_CHOOSE => {
            return match handle_look_and_choose(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => HandlerResult::SetCond(success),
                None => HandlerResult::Suspend,
            }
        },
        O_RECOVER_LIVE | O_RECOVER_MEMBER => {
            return match handle_recovery(state, db, ctx, v, a, s, instr_ip, op) {
                Some(success) => HandlerResult::SetCond(success),
                None => HandlerResult::Suspend,
            }
        },
        O_PLAY_LIVE_FROM_DISCARD => {
            return match handle_play_live_from_discard(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => HandlerResult::SetCond(success),
                None => HandlerResult::Suspend,
            }
        },
        O_SELECT_CARDS => {
            return match handle_select_cards(state, db, ctx, v, a, s, instr_ip) {
                Some(success) => HandlerResult::SetCond(success),
                None => HandlerResult::Suspend,
            }
        },
        O_SWAP_ZONE => {
            match handle_swap_zone(state, db, ctx, v, a, s, instr_ip) {
                Some(_) => {},
                None => return HandlerResult::Suspend,
            }
        },
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}

// Logic for these helper functions is migrated from interpreter_legacy.rs
fn handle_move_to_discard(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, v: i32, a: i32, s: i32, instr_ip: usize) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    let mut source_zone = (a >> 12) & 0x0F;
    if source_zone == 0 {
        if s == 4 || s == 6 || s == 13 { source_zone = s; } else { source_zone = 6; }
    }
    let count = if v == 0 { 1 } else { v };
    let target_player_idx = if (a & 0x10) != 0 { 1 - p_idx } else { p_idx }; 
    if target_player_idx != p_idx && state.core.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY) { 
        if state.debug.debug_mode { println!("[DEBUG] handle_move_to_discard: Target has IMMUNITY, skipping"); }
        return Some(false); 
    }
    
    if state.debug.debug_mode {
        println!("[DEBUG] handle_move_to_discard: player={}, source_zone={}, count={}, hand_len={}, choice={}", 
            p_idx, source_zone, count, state.core.players[p_idx].hand.len(), ctx.choice_index);
    }
    
    // Mask out source zone bits (12-15) for filter matching
    let filter_attr = (a as u32 as u64) & 0xFFFFFFFFFFFF0FFF;

    // OPTIONAL Handling: Check if we have enough cards to pay if it's an optional cost
    let is_optional = (a & 0x02) != 0;
    
    if is_optional && ctx.choice_index == -1 && !state.ui.silent {
        // Check if we have enough cards to pay
        let available_count = match source_zone {
            6 => state.core.players[target_player_idx].hand.len() as i32,
            4 => state.core.players[target_player_idx].stage.iter().filter(|&&c| c >= 0).count() as i32,
            13 => state.core.players[target_player_idx].energy_zone.len() as i32,
            _ => 99,
        };
        // If not enough cards, auto-decline the optional cost
        if available_count < v { return Some(false); }
    }
    
    let mut next_ctx = ctx.clone();
    // Resumption logic for Yes/No is removed as we go straight to selection.
    
    let choice_type = if source_zone == 6 { "SELECT_HAND_DISCARD" } else { "SELECT_DISCARD" };

    if source_zone == 4 && next_ctx.choice_index == -1 && count == 1 {
        let slot = if next_ctx.area_idx >= 0 { next_ctx.area_idx as usize } else { 0 };
        if slot < 3 && state.core.players[p_idx].stage[slot] == ctx.source_card_id { next_ctx.choice_index = slot as i16; }
    }

    if next_ctx.choice_index == -1 && count > 0 && source_zone != 0 && !state.ui.silent {
         if suspend_interaction(state, db, &next_ctx, instr_ip, O_MOVE_TO_DISCARD, s, choice_type, "", filter_attr, count as i16) { return None; }
    }
    
    if next_ctx.choice_index != -1 {
        // Choice 99 or 0 during selection counts as "Decline" for optional costs
        if is_optional && (next_ctx.choice_index == CHOICE_DONE || next_ctx.choice_index == 0) {
            return Some(false);
        }
        
        let idx = next_ctx.choice_index as usize;
        let mut removed_cid = -1;
        match source_zone {
            6 => if idx < state.core.players[p_idx].hand.len() {
                removed_cid = state.core.players[p_idx].hand[idx];
                if removed_cid != -1 { state.core.players[p_idx].hand[idx] = -1; }
            },
            4 => {
                let slot = if idx < 3 { idx } else if next_ctx.area_idx >= 0 { next_ctx.area_idx as usize } else { 0 };
                if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, &next_ctx) { removed_cid = cid; }
            },
            13 => if !state.core.players[p_idx].success_lives.is_empty() { removed_cid = state.core.players[p_idx].success_lives.pop().unwrap() as i32; },
            0 => if !state.core.players[p_idx].deck.is_empty() { removed_cid = state.core.players[p_idx].deck.pop().unwrap() as i32; },
            3 => if !state.core.players[p_idx].energy_zone.is_empty() { removed_cid = state.core.players[p_idx].energy_zone.pop().unwrap() as i32; },
            _ => {}
        }
        if removed_cid >= 0 {
            state.core.players[p_idx].discard.push(removed_cid as i32);
            next_ctx.v_remaining = if next_ctx.v_remaining > 0 { next_ctx.v_remaining - 1 } else { (count as i16) - 1 };
            if next_ctx.v_remaining > 0 {
                next_ctx.choice_index = -1;
                if suspend_interaction(state, db, &next_ctx, instr_ip, O_MOVE_TO_DISCARD, s, choice_type, "", filter_attr, next_ctx.v_remaining) { return None; }
            }
        }
    } else {
        for _ in 0..count {
            match source_zone {
                6 => if let Some(cid) = state.core.players[p_idx].hand.pop() { state.core.players[p_idx].discard.push(cid); },
                4 => {
                    let slot = if next_ctx.area_idx >= 0 { next_ctx.area_idx as usize } else { 0 };
                    if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, &next_ctx) { state.core.players[p_idx].discard.push(cid as i32); }
                },
                13 => if let Some(cid) = state.core.players[p_idx].success_lives.pop() { state.core.players[p_idx].discard.push(cid); },
                0 => if let Some(cid) = state.core.players[p_idx].deck.pop() { state.core.players[p_idx].discard.push(cid); },
                3 => if let Some(cid) = state.core.players[p_idx].energy_zone.pop() { state.core.players[p_idx].discard.push(cid); },
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

fn handle_play_live_from_discard(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, v: i32, a: i32, _s: i32, instr_ip: usize) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    let remaining = if ctx.v_remaining == -1 { v as i16 * 2 } else { ctx.v_remaining };
    if remaining <= 0 { return Some(true); }

    if remaining % 2 == 0 {
        if ctx.choice_index == -1 {
            state.core.players[p_idx].looked_cards.clear();
            let filter_attr = a as u64;
            for &cid in &state.core.players[p_idx].discard {
                if db.get_live(cid).is_some() && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr)) {
                    state.core.players[p_idx].looked_cards.push(cid);
                }
            }
            if state.core.players[p_idx].looked_cards.is_empty() { return Some(true); }
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(state, db, ctx, instr_ip, O_PLAY_LIVE_FROM_DISCARD, 0, "SELECT_DISCARD_PLAY", &choice_text, a as u64, remaining) {
                return None;
            }
        }
        
        let choice = ctx.choice_index as usize;
        if choice < state.core.players[p_idx].looked_cards.len() {
            let cid = state.core.players[p_idx].looked_cards[choice];
            state.core.players[p_idx].looked_cards.clear();
            state.core.players[p_idx].looked_cards.push(cid);
            
            ctx.v_remaining = remaining - 1;
            ctx.choice_index = -1;
            if suspend_interaction(state, db, ctx, instr_ip, O_PLAY_LIVE_FROM_DISCARD, 0, "SELECT_LIVE_SLOT", "", a as u64, ctx.v_remaining) {
                return None;
            }
        }
    } else {
        if state.core.players[p_idx].looked_cards.is_empty() { return Some(true); }
        let card_id = state.core.players[p_idx].looked_cards.remove(0);
        let slot_idx = ctx.choice_index as usize;
        
        if let Some(pos) = state.core.players[p_idx].discard.iter().position(|&cid| cid == card_id) {
            state.core.players[p_idx].discard.remove(pos);
            if slot_idx < 3 {
                let old = state.core.players[p_idx].live_zone[slot_idx];
                if old >= 0 { state.core.players[p_idx].discard.push(old); }
                state.core.players[p_idx].live_zone[slot_idx] = card_id;
                state.core.players[p_idx].set_revealed(slot_idx, true);
            }
        }
        
        ctx.v_remaining = remaining - 1;
        if ctx.v_remaining > 0 && !state.core.players[p_idx].discard.is_empty() {
            ctx.choice_index = -1;
            return handle_play_live_from_discard(state, db, ctx, v, a, _s, instr_ip);
        }
    }
    Some(true)
}

fn handle_select_cards(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, v: i32, a: i32, s: i32, instr_ip: usize) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 {
        let source_zone = (a >> 12) & 0x0F;
        let effective_zone = if source_zone != 0 { source_zone } else if s != 0 { s } else { 7 }; // Default to Discard
        
        state.core.players[p_idx].looked_cards.clear();
        let cards_to_filter = match effective_zone {
            6 => state.core.players[p_idx].hand.to_vec(),
            7 => state.core.players[p_idx].discard.to_vec(),
            4 => state.core.players[p_idx].stage.iter().cloned().filter(|&c| c >= 0).collect(),
            _ => state.core.players[p_idx].discard.to_vec(),
        };

        let filter_attr = (a as u64) & 0x00000000FFFFFFFF;
        for cid in cards_to_filter {
            if state.card_matches_filter(db, cid, filter_attr) {
                state.core.players[p_idx].looked_cards.push(cid);
            }
        }

        if state.core.players[p_idx].looked_cards.is_empty() { return Some(true); }
        
        let choice_type = match effective_zone {
            6 => "SELECT_HAND_DISCARD",
            7 => "SELECT_DISCARD_PLAY",
            _ => "LOOK_AND_CHOOSE",
        };
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(state, db, ctx, instr_ip, O_SELECT_CARDS, 0, choice_type, &choice_text, a as u64, v as i16) {
            return None;
        }
    }
    
    let choice = ctx.choice_index;
    if choice == CHOICE_DONE && (a & 0x02) != 0 {
        return Some(false);
    }

    if choice != CHOICE_DONE && choice >= 0 && (choice as usize) < state.core.players[p_idx].looked_cards.len() {
        let _chosen = state.core.players[p_idx].looked_cards[choice as usize];
        // For O_SELECT_CARDS, we just keep the selection in looked_cards for the next opcode to consume
        // or we could put it in a specific 'selected' list if we had one.
        // For now, let's just keep looked_cards as the buffer.
        let rem = if ctx.v_remaining > 0 { ctx.v_remaining - 1 } else { (v as i16).saturating_sub(1) };
        if rem > 0 {
            // Remove the chosen card from the available pool in looked_cards so it can't be picked twice
            state.core.players[p_idx].looked_cards.remove(choice as usize);
            ctx.v_remaining = rem;
            ctx.choice_index = -1;
            if suspend_interaction(state, db, ctx, instr_ip, O_SELECT_CARDS, 0, "LOOK_AND_CHOOSE", "", a as u64, rem) {
                return None;
            }
        } else {
            // Done picking. The next opcode (e.g. OPPONENT_CHOOSE) will see the cards in looked_cards?
            // Actually, if we picked multiple cards, they should all be in looked_cards.
            // But the current looked_cards contains the *available* pool.
            // We need a way to store the *choices*.
            
            // Re-think: O_SELECT_CARDS (v=count)
            // It selects 'v' cards.
            // I'll modify handle_select_cards to move chosen cards to a temporary list or similar.
            // Actually, let's look at how other opcodes consume choices.
        }
    }
    
    Some(true)
}

fn handle_look_and_choose(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, v: i32, a: i32, s: i32, instr_ip: usize) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    let target_slot = s & 0xFF;
    let rem_dest = (s >> 8) & 0xFF;
    let source_zone = (a >> 12) & 0x0F;
    let source_zone = if source_zone == 0 { 8 } else { source_zone as i32 };
    let look_count = (v & 0xFF) as usize;
    let pick_count_raw = ((v >> 8) & 0xFF) as usize;

    if state.core.players[p_idx].looked_cards.is_empty() {
        let reveal_count = if source_zone == 6 { state.core.players[p_idx].hand.len() }
                           else if source_zone == 7 { state.core.players[p_idx].discard.len() }
                           else if source_zone == 15 { state.core.players[p_idx].yell_cards.len() }
                           else { look_count };
        match source_zone {
            6 => for _ in 0..reveal_count { if let Some(cid) = state.core.players[p_idx].hand.pop() { state.core.players[p_idx].looked_cards.push(cid); } },
            7 => for _ in 0..reveal_count { if let Some(cid) = state.core.players[p_idx].discard.pop() { state.core.players[p_idx].looked_cards.push(cid); } },
            15 => { let y = std::mem::take(&mut state.core.players[p_idx].yell_cards); state.core.players[p_idx].looked_cards.extend(y); },
            _ => {
                if state.core.players[p_idx].deck.len() < reveal_count { state.resolve_deck_refresh(p_idx); }
                for _ in 0..reveal_count.min(state.core.players[p_idx].deck.len()) { if let Some(cid) = state.core.players[p_idx].deck.pop() { state.core.players[p_idx].looked_cards.push(cid); } }
            }
        }
    }

    if ctx.choice_index == -1 {
         let choice_type = if source_zone == 6 { "SELECT_HAND_DISCARD" } else { "LOOK_AND_CHOOSE" };
         let choice_text = get_choice_text(db, ctx);
         let pick_count = ((v >> 8) & 0xFF) as i16;
         let v_rem = if pick_count > 0 { pick_count } else { 1 };
         let mut filter_attr = (a as u32) as u64;
         if ((v >> 16) & 0x7F) > 0 { filter_attr |= 1u64 << 42; filter_attr |= (((v >> 16) & 0x7F) as u64) << 31; }
         if ((v >> 23) & 0x7F) > 0 { filter_attr |= 1u64 << 31; filter_attr |= (((v >> 23) & 0x7F) as u64) << 32; }
         if suspend_interaction(state, db, ctx, instr_ip, O_LOOK_AND_CHOOSE, s, choice_type, &choice_text, filter_attr, v_rem) { return None; }
     }
     
    let choice = ctx.choice_index;
    let mut revealed = std::mem::take(&mut state.core.players[p_idx].looked_cards);
    if choice != CHOICE_DONE {
        if choice >= 0 && (choice as usize) < revealed.len() && choice != CHOICE_ALL {
            let chosen = revealed[choice as usize];
            if chosen != -1 {
                revealed[choice as usize] = -1;
                let destination = if target_slot > 0 { target_slot } else if (a & 0x01) != 0 { 7 } else if (a & 0x02) != 0 { 8 } else if (a & 0x04) != 0 { 4 } else { 6 };
                match destination {
                    7 => { state.core.players[p_idx].discard.push(chosen); },
                    8 => { state.core.players[p_idx].deck.push(chosen); },
                    4 => {
                        let slot = s as usize;
                        if slot < 3 {
                            if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) { state.core.players[p_idx].discard.push(cid as i32); }
                            state.core.players[p_idx].stage[slot] = chosen; state.core.players[p_idx].set_tapped(slot, false); state.core.players[p_idx].set_moved(slot, true);
                            state.register_played_member(p_idx, chosen, db);
                            let new_ctx = AbilityContext { source_card_id: chosen, player_id: p_idx as u8, area_idx: slot as i16, ..Default::default() };
                            state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                        } else { state.core.players[p_idx].hand.push(chosen); state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1); }
                    },
                    13 => { state.core.players[p_idx].success_lives.push(chosen); },
                    _ => { state.core.players[p_idx].hand.push(chosen); state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1); }
                }
                if source_zone == 15 {
                    for slot in 0..3 { if let Some(pos) = state.core.players[p_idx].stage_energy[slot].iter().position(|&c| c == chosen) { state.core.players[p_idx].stage_energy[slot].remove(pos); state.core.players[p_idx].sync_stage_energy_count(slot); break; } }
                }
                let effective_pick_count = if pick_count_raw > 0 { pick_count_raw } else { look_count };
                let rem = if ctx.v_remaining > 0 { ctx.v_remaining - 1 } else { (effective_pick_count as i16).saturating_sub(1) };
                if rem > 0 && revealed.iter().any(|&c| c != -1) {
                    state.core.players[p_idx].looked_cards = revealed.clone();
                    let choice_type = if source_zone == 6 { "SELECT_HAND_DISCARD" } else { "LOOK_AND_CHOOSE" };
                    if suspend_interaction(state, db, ctx, instr_ip, O_LOOK_AND_CHOOSE, s, choice_type, "", a as u64, rem) { return None; }
                }
            }
         }
    }
    revealed.retain(|c| *c != -1);
    if !revealed.is_empty() {
        let dest = if rem_dest > 0 { rem_dest } else { source_zone as i32 };
        match dest {
            6 => state.core.players[p_idx].hand.extend(revealed),
            7 => state.core.players[p_idx].discard.extend(revealed),
            15 => state.core.players[p_idx].yell_cards.extend(revealed),
            0 | 8 => { state.core.players[p_idx].deck.extend(revealed); let mut rng = Pcg64::from_os_rng(); state.core.players[p_idx].deck.shuffle(&mut rng); },
            1 => state.core.players[p_idx].deck.extend(revealed),
            2 => for c in revealed.iter().rev() { state.core.players[p_idx].deck.insert(0, *c); },
            _ => state.core.players[p_idx].discard.extend(revealed),
        }
    }
    Some(true)
}

fn handle_recovery(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, v: i32, _a: i32, _s: i32, instr_ip: usize, real_op: i32) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    if state.debug.debug_mode {
        println!("[DEBUG] handle_recovery: p_idx={}, choice_index={}, v={}, real_op={}", p_idx, ctx.choice_index, v, real_op);
    }
    if ctx.choice_index == -1 {
        state.core.players[p_idx].looked_cards.clear();
        for &cid in &state.core.players[p_idx].discard {
            let matches = if real_op == O_RECOVER_LIVE { db.get_live(cid).is_some() } else { db.get_member(cid).is_some() };
            if matches { state.core.players[p_idx].looked_cards.push(cid); }
        }
        if state.debug.debug_mode {
            println!("[DEBUG] handle_recovery: looked_cards={:?}", state.core.players[p_idx].looked_cards);
        }
        if state.core.players[p_idx].looked_cards.is_empty() { 
            if state.debug.debug_mode { println!("[DEBUG] handle_recovery: No matching cards in discard, returning early"); }
            return Some(true); 
        }
        let choice_type = if real_op == O_RECOVER_LIVE { "RECOV_L" } else { "RECOV_M" };
        let choice_text = get_choice_text(db, ctx);
        if state.debug.debug_mode { println!("[DEBUG] handle_recovery: Suspending with choice_type={}", choice_type); }
        if suspend_interaction(state, db, ctx, instr_ip, real_op, 0, choice_type, &choice_text, 0, -1) { return None; }
    }
    let choice = ctx.choice_index as usize;
    if choice < state.core.players[p_idx].looked_cards.len() {
        let cid = state.core.players[p_idx].looked_cards[choice];
        if cid != -1 {
            state.core.players[p_idx].looked_cards[choice] = -1;
            state.core.players[p_idx].hand.push(cid);
            state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1);
            if let Some(pos) = state.core.players[p_idx].discard.iter().position(|&x| x == cid) { state.core.players[p_idx].discard.remove(pos); }
            let remaining = if ctx.v_remaining == -1 { v as i16 - 1 } else { ctx.v_remaining - 1 };
            if remaining > 0 && choice != CHOICE_ALL as usize && state.core.players[p_idx].looked_cards.iter().any(|&c| c != -1) {
                  let choice_type = if real_op == O_RECOVER_LIVE { "RECOV_L" } else { "RECOV_M" };
                  let choice_text = get_choice_text(db, ctx);
                  if suspend_interaction(state, db, ctx, instr_ip, real_op, 0, choice_type, &choice_text, 0, remaining) { return None; }
            }
        }
    }
    state.core.players[p_idx].looked_cards.clear();
    Some(true)
}

fn handle_swap_zone(state: &mut GameState, db: &CardDatabase, ctx: &mut AbilityContext, _v: i32, _a: i32, _s: i32, instr_ip: usize) -> Option<bool> {
    let p_idx = ctx.player_id as usize;
    if ctx.choice_index == -1 && ctx.v_remaining == -1 {
        let cards = state.core.players[p_idx].success_lives.clone();
        if cards.is_empty() { return Some(true); }
        state.core.players[p_idx].looked_cards.clear(); state.core.players[p_idx].looked_cards.extend(cards);
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(state, db, ctx, instr_ip, O_SWAP_ZONE, 0, "SELECT_SWAP_SOURCE", &choice_text, 0, 1) { return None; }
    }
    if ctx.v_remaining == 1 {
        let picked_idx = ctx.choice_index as usize;
        if picked_idx < state.core.players[p_idx].looked_cards.len() {
            let cid = state.core.players[p_idx].looked_cards[picked_idx];
            state.core.players[p_idx].looked_cards.clear(); state.core.players[p_idx].looked_cards.push(cid);
            let mut next_ctx = ctx.clone(); next_ctx.choice_index = -1; next_ctx.v_remaining = 0;
            if suspend_interaction(state, db, &next_ctx, instr_ip, O_SWAP_ZONE, 0, "SELECT_HAND_PLAY", "", 0, 1) { return None; }
        }
    } else if ctx.v_remaining == 0 {
        let hand_idx = ctx.choice_index as usize;
        if hand_idx < state.core.players[p_idx].hand.len() && !state.core.players[p_idx].looked_cards.is_empty() {
            let hand_cid = state.core.players[p_idx].hand.remove(hand_idx);
            let success_cid = state.core.players[p_idx].looked_cards.remove(0);
            if let Some(pos) = state.core.players[p_idx].success_lives.iter().position(|&x| x == success_cid) {
                state.core.players[p_idx].success_lives[pos] = hand_cid;
                state.core.players[p_idx].hand.push(success_cid);
                state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1);
            }
        }
    }
    state.core.players[p_idx].looked_cards.clear();
    Some(true)
}
