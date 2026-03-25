use super::*;
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::interaction_zone::{
    collect_zone_cards, normalized_source_zone, remove_card_from_zone,
};
use crate::core::logic::models::AbilityFrame;
use crate::core::models::Zone;

pub fn resolve_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    real_op: i32,
) -> HandlerResult {
    let frame_data = frame.components();
    let v = frame_data.value;
    let a = filter_attr_from_params(frame_data.params).unwrap_or(frame_data.raw_attr) as i64;
    let _s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let source_zone = normalized_source_zone(slot_info.source_zone);
    let zone_cards = collect_zone_cards(state, p_idx, source_zone);

    let looked_cards_match_zone = state.players[p_idx]
        .looked_cards
        .iter()
        .any(|cid| zone_cards.contains(cid));

    if state.players[p_idx].looked_cards.is_empty() || !looked_cards_match_zone {
        state.players[p_idx].looked_cards.clear();
        for cid in &zone_cards {
            let type_matches = if real_op == O_RECOVER_LIVE {
                db.get_live(*cid).is_some()
            } else {
                db.get_member(*cid).is_some()
            };
            if type_matches
                && (a == 0 || state.card_matches_filter_with_ctx(db, *cid, a as u64, ctx))
            {
                state.players[p_idx].looked_cards.push(*cid);
            }
        }
        if state.players[p_idx].looked_cards.is_empty() {
            if real_op == O_RECOVER_MEMBER {
                if let Some(&sacrificed_cid) = ctx.selected_cards.first() {
                    let _ =
                        remove_card_from_zone(state, db, ctx, p_idx, Zone::Stage, sacrificed_cid);
                }
            }
            return HandlerResult::Continue;
        }
    }

    let active_recovery_prompt = state
        .interaction_stack
        .last()
        .map(|interaction| {
            matches!(
                interaction.choice_type,
                ChoiceType::RecovL | ChoiceType::RecovM
            )
        })
        .unwrap_or(false);

    if ctx.choice_index == -1 {
        if real_op == O_RECOVER_LIVE && state.players[p_idx].looked_cards.len() == 1 {
            ctx.choice_index = 0;
        } else {
            let choice_type = if real_op == O_RECOVER_LIVE {
                ChoiceType::RecovL
            } else {
                ChoiceType::RecovM
            };
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    real_op,
                    0,
                    choice_type,
                    0,
                    -1,
                ),
                HandlerResult::Suspend
            ) {
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
                if matches!(
                    suspend_choice(
                        state,
                        db,
                        ctx,
                        ctx,
                        frame_idx,
                        real_op,
                        0,
                        choice_type,
                        0,
                        remaining,
                    ),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }
    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}
