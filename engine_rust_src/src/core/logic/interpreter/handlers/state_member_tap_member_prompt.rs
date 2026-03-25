use super::*;
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;

#[allow(clippy::too_many_arguments)]
pub fn handle_tap_member_prompt(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;
    let is_select_member_choice = frame_data
        .params
        .map(|params| {
            params.get("FILTER").is_some()
                || params.get("filter").is_some()
                || params
                    .get("destination")
                    .and_then(|value| value.as_str())
                    .map(|value| value.eq_ignore_ascii_case("target"))
                    .unwrap_or(false)
                || params
                    .get("cost_type_name")
                    .and_then(|value| value.as_str())
                    .map(|value| value.eq_ignore_ascii_case("SELECT_MEMBER"))
                    .unwrap_or(false)
        })
        .unwrap_or(false);
    let self_source_is_on_stage = ctx.area_idx >= 0 && ctx.area_idx < 3;
    let filter_attr = filter_attr_from_params(frame_data.params)
        .unwrap_or(frame_data.raw_attr.max(frame_data.filter.to_attr()))
        & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let fixed_slot_matches = if resolved_slot >= 0 && resolved_slot < 3 {
        let cid = state.players[p_idx].stage[resolved_slot as usize];
        cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
    } else {
        false
    };
    let needs_selection =
        is_select_member_choice || (a & 0x02) != 0 || (!fixed_slot_matches && filter_attr != 0);
    let active_optional_prompt = state
        .interaction_stack
        .last()
        .map(|interaction| interaction.choice_type == ChoiceType::Optional)
        .unwrap_or(false);

    if ctx.source_card_id == 4196 {
        eprintln!(
            "[TAP_PROMPT] optional={} select_member={} filter={:X} resolved_slot={} choice_index={} v_remaining={} needs_selection={} active_optional={}",
            is_optional,
            is_select_member_choice,
            filter_attr,
            resolved_slot,
            ctx.choice_index,
            ctx.v_remaining,
            needs_selection,
            active_optional_prompt
        );
    }

    if is_optional && ctx.v_remaining != -1 && !active_optional_prompt {
        ctx.v_remaining = -1;
    }

    if !self_source_is_on_stage && resolved_slot == 4 && !needs_selection {
        return HandlerResult::SetCond(false);
    }

    if is_optional && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::Optional,
                filter_attr,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
        return HandlerResult::Continue;
    }

    if needs_selection {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::TapMSelect,
                filter_attr,
                frame_data.value as i16,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
        return HandlerResult::Continue;
    }

    if is_optional || (a & 0x01) != 0 || needs_selection {
        if (a & 0x03) == 0 && resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
            return HandlerResult::SetCond(true);
        }
    } else {
        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    }

    HandlerResult::Continue
}
