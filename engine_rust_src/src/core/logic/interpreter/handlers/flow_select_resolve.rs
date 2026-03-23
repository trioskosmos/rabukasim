use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

#[allow(clippy::too_many_arguments)]
pub fn resolve_select_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr_ip: usize,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    _p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    supports_partial_completion: bool,
    partial_selection_prompt: i16,
    is_move_member_follow_up: bool,
) -> HandlerResult {
    let choice = ctx.choice_index as i32;
    let source_zone = slot_info.source_zone as u8;
    let filter_attr = a as u64;

    if supports_partial_completion && choice == CHOICE_DONE as i32 {
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
        return HandlerResult::Continue;
    }

    if source_zone == 6 || source_zone == 7 {
        ctx.target_slot = choice as i16;
    } else {
        ctx.target_slot = choice as i16;
        ctx.area_idx = choice as i16;
    }

    let target_player = match (filter_attr & 0x3) as u8 {
        2 => 1 - (ctx.player_id as usize),
        3 => 1,
        _ => ctx.player_id as usize,
    };
    let selected_cid = match source_zone {
        6 => state.players[target_player]
            .hand
            .get(choice as usize)
            .copied()
            .unwrap_or(-1),
        7 => state.players[target_player]
            .discard
            .get(choice as usize)
            .copied()
            .unwrap_or(-1),
        _ => state.players[target_player]
            .stage
            .get(choice as usize)
            .copied()
            .unwrap_or(-1),
    };
    if selected_cid >= 0 && !ctx.selected_cards.contains(&selected_cid) {
        ctx.selected_cards.push(selected_cid);
    }

    if is_move_member_follow_up {
        ctx.area_idx = choice as i16;
        ctx.choice_index = -1;
        return HandlerResult::Continue;
    }

    if supports_partial_completion && !ctx.selected_cards.is_empty() {
        let current_selection_count = match source_zone {
            6 => state.players[target_player]
                .hand
                .iter()
                .copied()
                .filter(|cid| *cid >= 0 && ctx.selected_cards.contains(cid))
                .count(),
            7 => state.players[target_player]
                .discard
                .iter()
                .copied()
                .filter(|cid| *cid >= 0 && ctx.selected_cards.contains(cid))
                .count(),
            _ => state.players[target_player]
                .stage
                .iter()
                .copied()
                .filter(|cid| *cid >= 0 && ctx.selected_cards.contains(cid))
                .count(),
        };

        let remaining_candidates = match source_zone {
            6 => state.players[target_player]
                .hand
                .iter()
                .copied()
                .filter(|cid| {
                    *cid >= 0
                        && !ctx.selected_cards.contains(cid)
                        && state.card_matches_filter_with_ctx(db, *cid, filter_attr, ctx)
                })
                .count(),
            7 => state.players[target_player]
                .discard
                .iter()
                .copied()
                .filter(|cid| {
                    *cid >= 0
                        && !ctx.selected_cards.contains(cid)
                        && state.card_matches_filter_with_ctx(db, *cid, filter_attr, ctx)
                })
                .count(),
            _ => state.players[target_player]
                .stage
                .iter()
                .copied()
                .filter(|cid| {
                    *cid >= 0
                        && !ctx.selected_cards.contains(cid)
                        && state.card_matches_filter_with_ctx(db, *cid, filter_attr, ctx)
                })
                .count(),
        };

            let remaining_picks = (v as usize).saturating_sub(current_selection_count);

        if remaining_picks > 0 && remaining_candidates > 0 {
            ctx.choice_index = -1;
            ctx.v_remaining = remaining_picks as i16;
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                op,
                s,
                ChoiceType::SelectMember,
                filter_attr,
                remaining_picks as i16,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        } else if remaining_picks > 0 && current_selection_count == 1 {
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                op,
                s,
                ChoiceType::Optional,
                0,
                partial_selection_prompt,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
    }

    HandlerResult::Continue
}
