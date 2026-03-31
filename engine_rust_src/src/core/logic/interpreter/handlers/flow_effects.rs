use crate::core::logic::models::AbilityFrameComponents;
use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::flow_helpers::current_effect_from_data;

#[path = "flow_meta_rule.rs"]
mod flow_meta_rule;

pub fn handle_trigger_remote(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    v: i32,
    p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
) -> HandlerResult {
    let effect = current_effect_from_data(db, ctx, frame_data);
    let from_discard = effect
        .and_then(|e| e.params.get("from"))
        .and_then(|v: &serde_json::Value| v.as_str())
        .map(|s| s.eq_ignore_ascii_case("DISCARD"))
        .unwrap_or(false);
    let filter_attr = effect.map(|e| e.runtime_attr).unwrap_or(0);

    let mut target_cid = -1;
    let mut target_area = -1;

    if from_discard {
        let matching: Vec<(usize, i32)> = state.players[p_idx]
            .discard
            .iter()
            .copied()
            .enumerate()
            .filter(|(_, cid)| *cid >= 0 && state.card_matches_filter(db, *cid, filter_attr))
            .collect();

        if matching.is_empty() {
            return HandlerResult::Continue;
        }

        if matching.len() == 1 {
            target_cid = matching[0].1;
        } else if ctx.choice_index == -1 {
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_TRIGGER_REMOTE, 0, ChoiceType::SelectDiscard, filter_attr, -1),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
            return HandlerResult::Continue;
        } else if let Some(&chosen) = state.players[p_idx].discard.get(ctx.choice_index as usize) {
            if state.card_matches_filter(db, chosen, filter_attr) {
                target_cid = chosen;
            }
        }
    } else if slot_info.target_slot < 3 {
        target_cid = state.players[p_idx].stage[slot_info.target_slot as usize];
        target_area = slot_info.target_slot as i32;
    }

    if target_cid >= 0 {
        if let Some(m) = db.get_member(target_cid as i32) {
            if (v as usize) < m.abilities.len() {
                ctx.source_card_id = target_cid;
                ctx.ability_index = v as i16;
                ctx.area_idx = target_area as i16;
                return HandlerResult::BranchToFrames(std::sync::Arc::new(
                    m.abilities[v as usize]
                        .frame_program
                        .as_ref()
                        .map(|p| p.frames.clone())
                        .unwrap_or_default(),
                ));
            }
        }
    }
    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn handle_meta_rule(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    a: i64,
    v: i32,
    p_idx: usize,
    base_p: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    target_slot: i32,
) -> HandlerResult {
    flow_meta_rule::handle_meta_rule(state, db, ctx, frame_data, frame_idx, a, v, p_idx, base_p, slot_info, target_slot)
}

/// Simplified version that extracts values from frame_data
pub fn handle_trigger_remote_simple(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    handle_trigger_remote(
        state,
        db,
        ctx,
        frame_data,
        frame_idx,
        frame_data.value,
        ctx.player_id as usize,
        frame_data.slot,
    )
}

/// Simplified version that extracts values from frame_data
pub fn handle_meta_rule_simple(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    handle_meta_rule(
        state,
        db,
        ctx,
        frame_data,
        frame_idx,
        frame_data.raw_attr as i64,
        frame_data.value,
        ctx.player_id as usize,
        ctx.activator_id as usize,
        frame_data.slot,
        frame_data.slot.target_slot as i32,
    )
}
