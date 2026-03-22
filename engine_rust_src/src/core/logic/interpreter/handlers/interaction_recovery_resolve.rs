use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::interaction_zone::{
    collect_zone_cards, normalized_source_zone, remove_card_from_zone,
};

pub fn resolve_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    real_op: i32,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let _s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let slot_info = instr.slot();
    let source_zone = normalized_source_zone(slot_info.source_zone);

    if ctx.choice_index == -1 {
        state.players[p_idx].looked_cards.clear();
        for cid in collect_zone_cards(state, p_idx, source_zone) {
            let type_matches = if real_op == O_RECOVER_LIVE {
                db.get_live(cid).is_some()
            } else {
                db.get_member(cid).is_some()
            };
            if type_matches
                && (a == 0 || state.card_matches_filter_with_ctx(db, cid, a as u64, ctx))
            {
                state.players[p_idx].looked_cards.push(cid);
            }
        }
        if state.players[p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
    }

    if ctx.choice_index == -1 {
        let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
        let is_single_choice_auto_pick = !is_optional
            && state.players[p_idx].looked_cards.len() == 1
            && real_op != O_RECOVER_MEMBER;

        if is_single_choice_auto_pick {
            ctx.choice_index = 0;
        } else {
            let choice_type = if real_op == O_RECOVER_LIVE {
                ChoiceType::RecovL
            } else {
                ChoiceType::RecovM
            };
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                real_op,
                0,
                choice_type,
                0,
                -1,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
    }

    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 {
        state.players[p_idx].looked_cards.clear();
        return HandlerResult::Continue;
    }
    let real_idx = if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
        Some(choice as usize)
    } else {
        None
    };

    if let Some(idx) = real_idx {
        let cid = state.players[p_idx].looked_cards[idx];
        if cid != -1 {
            state.players[p_idx].looked_cards[idx] = -1;
            state.players[p_idx].gain_hand_card(cid);
            ctx.selected_cards.push(cid);

            remove_card_from_zone(state, db, ctx, p_idx, source_zone, cid);
            let remaining = if ctx.v_remaining == -1 {
                v as i16 - 1
            } else {
                ctx.v_remaining - 1
            };
            if remaining > 0
                && choice != CHOICE_ALL as i32
                && state.players[p_idx].looked_cards.iter().any(|&c| c != -1)
            {
                let choice_type = if real_op == O_RECOVER_LIVE {
                    ChoiceType::RecovL
                } else {
                    ChoiceType::RecovM
                };
                if matches!(suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    real_op,
                    0,
                    choice_type,
                    0,
                    remaining,
                ), HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }
    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}
