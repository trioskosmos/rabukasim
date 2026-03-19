use crate::core::enums::ChoiceType;
use crate::core::logic::constants::*;
use crate::core::logic::constants::{CHOICE_DONE, STAGE_SLOT_COUNT};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;

pub fn handle_play_live_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let slot_info = instr.slot();
    let target_p_idx = if slot_info.is_opponent {
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
        return HandlerResult::Continue;
    }

    if remaining % 2 == 0 {
        if ctx.choice_index == -1 {
            state.players[target_p_idx].looked_cards.clear();
            let filter_attr = a as u64;
            let matched_ids: Vec<i32> = state.players[target_p_idx]
                .discard
                .iter()
                .filter(|&&cid| {
                    db.get_live(cid).is_some()
                        && (filter_attr == 0
                            || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
                })
                .cloned()
                .collect();
            state.players[target_p_idx].looked_cards.extend(matched_ids);
            if state.players[target_p_idx].looked_cards.is_empty() {
                return HandlerResult::Continue;
            }
            let mut target_ctx = ctx.clone();
            target_ctx.player_id = target_p_idx as u8;
            if matches!(suspend_choice(
                state,
                db,
                &target_ctx,
                &target_ctx,
                instr_ip,
                O_PLAY_LIVE_FROM_DISCARD,
                s,
                ChoiceType::SelectDiscardPlay,
                a as u64,
                remaining,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }

        let choice = ctx.choice_index as i32;
        if choice == CHOICE_DONE as i32 {
            state.players[target_p_idx].looked_cards.clear();
            return HandlerResult::Continue;
        }
        let real_idx =
            if choice >= 0 && (choice as usize) < state.players[target_p_idx].looked_cards.len() {
                Some(choice as usize)
            } else {
                None
            };

        if let Some(idx) = real_idx {
            let chosen = state.players[target_p_idx].looked_cards[idx];
            if chosen != -1 {
                state.players[target_p_idx].looked_cards[idx] = -1;
                state.players[target_p_idx].looked_cards.clear();
                state.players[target_p_idx].looked_cards.push(chosen);

                remaining -= 1;
                let mut target_ctx = ctx.clone();
                target_ctx.player_id = target_p_idx as u8;
                if matches!(suspend_choice(
                    state,
                    db,
                    &target_ctx,
                    &target_ctx,
                    instr_ip,
                    O_PLAY_LIVE_FROM_DISCARD,
                    s,
                    ChoiceType::SelectLiveSlot,
                    a as u64,
                    remaining,
                ), HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            }
        }
    } else {
        if state.players[target_p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
        let card_id = state.players[target_p_idx].looked_cards.remove(0);
        let slot_idx = ctx.choice_index as usize;

        if let Some(pos) = state.players[target_p_idx]
            .discard
            .iter()
            .position(|&cid| cid == card_id)
        {
            state.players[target_p_idx].remove_discard_card(pos);
            if slot_idx < STAGE_SLOT_COUNT {
                let old = state.players[target_p_idx].live_zone[slot_idx];
                if old >= 0 {
                    state.players[target_p_idx].push_discard_card(old);
                }
                state.players[target_p_idx].live_zone[slot_idx] = card_id;
                state.players[target_p_idx].set_revealed(slot_idx, true);
            }
        }

        remaining -= 1;
        if remaining > 0 && !state.players[target_p_idx].discard.is_empty() {
            ctx.choice_index = -1;
            ctx.v_remaining = remaining;
            return handle_play_live_from_discard(state, db, ctx, instr, instr_ip);
        }
    }
    HandlerResult::Continue
}
