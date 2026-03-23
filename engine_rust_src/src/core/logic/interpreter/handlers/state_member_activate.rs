use super::*;
use crate::core::logic::models::AbilityFrame;

pub fn handle_activate_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    resolved_slot: i32,
    target_slot: i32,
    v: i32,
    a: i64,
) -> HandlerResult {
    let resolved_slot = if resolved_slot == 4 && ctx.area_idx >= 0 && ctx.area_idx < 3 {
        ctx.area_idx as i32
    } else {
        resolved_slot
    };
    let mut group_bits = 0u32;
    if let Some(card) = db.get_member(ctx.source_card_id) {
        for &g in &card.groups {
            if g < 32 {
                group_bits |= 1 << g;
            }
        }
    }

    let activate_all = v == 99 || (a != 0 && resolved_slot >= 3);
    if activate_all {
        for i in 0..3 {
            let cid = state.players[p_idx].stage[i];
            if cid < 0 {
                continue;
            }
            if a != 0 && !state.card_matches_filter_with_ctx(db, cid, a as u64, ctx) {
                continue;
            }
            if state.players[p_idx].is_tapped(i) {
                state.players[p_idx].set_tapped(i, false);
                state.players[p_idx].activated_member_group_mask |= group_bits;
            }
        }
    } else if target_slot == 1 {
        for i in 0..3 {
            if state.players[p_idx].is_tapped(i) {
                state.players[p_idx].set_tapped(i, false);
                state.players[p_idx].activated_member_group_mask |= group_bits;
            }
        }
    } else if resolved_slot < 3 {
        if state.players[p_idx].is_tapped(resolved_slot as usize) {
            state.players[p_idx].set_tapped(resolved_slot as usize, false);
            state.players[p_idx].activated_member_group_mask |= group_bits;
        }
    }

    HandlerResult::Continue
}
