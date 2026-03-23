use crate::core::logic::models::AbilityFrame;

use super::*;

use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

#[path = "flow_meta_rule.rs"]
mod flow_meta_rule;

#[allow(clippy::too_many_arguments)]

pub fn handle_trigger_remote(
    state: &mut GameState,

    db: &CardDatabase,

    ctx: &mut AbilityContext,

    frame: &AbilityFrame,

    frame_idx: usize,

    v: i32,

    p_idx: usize,

    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
) -> HandlerResult {
    let effect = current_effect(db, ctx, frame);

    let from_discard = effect
        .and_then(|effect| effect.params.get("from"))
        .and_then(|value: &serde_json::Value| value.as_str())
        .map(|value: &str| value.eq_ignore_ascii_case("DISCARD"))
        .unwrap_or(false);

    let filter_attr = effect.map(|effect| effect.runtime_attr).unwrap_or(0);

    let mut target_cid = -1;

    let mut target_area = -1;

    if from_discard {
        let matching_discard: Vec<(usize, i32)> = state.players[p_idx]
            .discard
            .iter()
            .copied()
            .enumerate()
            .filter(|(_, cid)| *cid >= 0 && state.card_matches_filter(db, *cid, filter_attr))
            .collect();

        if matching_discard.is_empty() {
            return HandlerResult::Continue;
        }

        if matching_discard.len() == 1 {
            target_cid = matching_discard[0].1;
        } else if ctx.choice_index == -1 {
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_TRIGGER_REMOTE,
                    0,
                    ChoiceType::SelectDiscard,
                    filter_attr,
                    -1,
                ),
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
                        .map(|program| program.frames.clone())
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

    frame: &AbilityFrame,

    frame_idx: usize,

    a: i64,

    v: i32,

    p_idx: usize,

    base_p: usize,

    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,

    target_slot: i32,
) -> HandlerResult {
    flow_meta_rule::handle_meta_rule(
        state,
        db,
        ctx,
        frame,
        frame_idx,
        a,
        v,
        p_idx,
        base_p,
        slot_info,
        target_slot,
    )
}
