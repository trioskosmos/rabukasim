use super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;

fn is_interactive_frame(frame: &AbilityFrame) -> bool {
    matches!(
        frame.opcode(),
        O_SELECT_MEMBER
            | O_SELECT_LIVE
            | O_SELECT_PLAYER
            | O_SELECT_MODE
            | O_SELECT_CARDS
            | O_LOOK_AND_CHOOSE
            | O_OPPONENT_CHOOSE
            | O_COLOR_SELECT
            | O_TAP_MEMBER
            | O_TAP_OPPONENT
            | O_TRIGGER_REMOTE
    )
}

#[allow(clippy::too_many_arguments)]
pub fn handle_optional_nop(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
) -> HandlerResult {
    let frame_data = frame.components();
    let prompt_like = frame_data.filter.is_optional;

    if !prompt_like || ctx.choice_index != -1 || ctx.v_remaining != -1 {
        return HandlerResult::Continue;
    }

    let source_ability = db
        .get_member(ctx.source_card_id)
        .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
        .or_else(|| {
            db.get_live(ctx.source_card_id)
                .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
        });
    let has_future_prompt = source_ability
        .map(|ability| {
            ability
                .frames()
                .iter()
                .skip(frame_idx + 1)
                .any(|next| is_interactive_frame(next) || next.filter().is_optional)
        })
        .unwrap_or(false);

    let choice_type = if is_interactive_frame(frame) {
        if frame_data.slot.target_slot == 4 {
            ChoiceType::SelectStage
        } else if frame_data.slot.source_zone as u8 == 6 || frame_data.filter.target_player != 0 {
            ChoiceType::SelectMember
        } else {
            ChoiceType::Optional
        }
    } else if frame_data.filter.is_optional {
        ChoiceType::Optional
    } else {
        ChoiceType::Optional
    };

    suspend_choice_with_options(
        state,
        db,
        ctx,
        ctx,
        frame_idx,
        frame_data.opcode,
        frame_data.raw_slot,
        choice_type,
        frame_data.raw_attr,
        frame_data.value as i16,
        Vec::new(),
        Vec::new(),
    )
}

#[allow(clippy::too_many_arguments)]
pub fn suspend_choice(
    state: &mut GameState,
    db: &CardDatabase,
    choice_ctx: &AbilityContext,
    suspend_ctx: &AbilityContext,
    frame_idx: usize,
    op: i32,
    s: i32,
    choice_type: ChoiceType,
    attr: u64,
    remaining: i16,
) -> HandlerResult {
    suspend_choice_with_options(
        state,
        db,
        choice_ctx,
        suspend_ctx,
        frame_idx,
        op,
        s,
        choice_type,
        attr,
        remaining,
        Vec::new(),
        Vec::new(),
    )
}

#[allow(clippy::too_many_arguments)]
pub fn suspend_choice_with_options(
    state: &mut GameState,
    db: &CardDatabase,
    choice_ctx: &AbilityContext,
    suspend_ctx: &AbilityContext,
    frame_idx: usize,
    op: i32,
    s: i32,
    choice_type: ChoiceType,
    attr: u64,
    remaining: i16,
    options: Vec<serde_json::Value>,
    actions: Vec<i32>,
) -> HandlerResult {
    let choice_text = get_choice_text(db, choice_ctx);
    if !state.ui.silent {
        let rule_msg = match choice_type {
            ChoiceType::Optional => "Rule 12.2, Rule 12.2.1: Presenting voluntary (optional) choice to player.",
            _ => "Rule 12.2, Rule 12.2.2: Presenting mandatory choice to player.",
        };
        state.log(rule_msg.to_string());
    }
    if suspend_interaction(
        state,
        db,
        suspend_ctx,
        frame_idx,
        op,
        s,
        choice_type,
        &choice_text,
        attr,
        remaining,
        options,
        actions,
    ) {
        HandlerResult::Suspend
    } else {
        HandlerResult::Continue
    }
}
