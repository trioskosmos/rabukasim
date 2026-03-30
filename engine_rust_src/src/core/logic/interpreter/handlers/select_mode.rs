use crate::core::logic::constants::FLAG_REVEAL_UNTIL_IS_LIVE;
use crate::core::logic::models::AbilityFrame;

use super::HandlerResult;

use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

use crate::core::enums::ChoiceType;

use crate::core::logic::{AbilityContext, CardDatabase, GameState};

#[allow(clippy::too_many_arguments)]
pub fn handle_select_mode(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    frames: &[AbilityFrame],
) -> HandlerResult {
    let v = frame.value();
    let frame_data = frame.components();
    println!(
        "[SELECT_MODE_DBG] src={} choice={} v={} phase={:?}",
        ctx.source_card_id,
        ctx.choice_index,
        ctx.v_remaining,
        state.phase
    );

    if ctx.choice_index == -1 {
        if ctx.auto_pick && v == 1 {
            ctx.choice_index = 0;
        } else {
            let slot = frame.dslot();
            let filter = frame.filter();
            let is_opponent =
                frame_data.slot.is_opponent
                    || frame_data.filter.target_player == 2
                    || slot.is_opponent
                    || slot.target_slot == 2
                    || filter.target_player == 2
                    || ctx.source_card_id == 461;
            let choice_type = if is_opponent {
                ChoiceType::OpponentChoose
            } else {
                ChoiceType::SelectMode
            };

            let mut flip_ctx = ctx.clone();
            if is_opponent {
                flip_ctx.player_id = 1 - (ctx.player_id as u8);
            }

            let choice_ctx: &AbilityContext = if is_opponent { &flip_ctx } else { &*ctx };
            let options = if !is_opponent {
                crate::core::logic::ActionFactory::infer_all_select_mode_options(
                    db,
                    ctx.source_card_id,
                    ctx.ability_index,
                    v as i16,
                )
            } else {
                Vec::new()
            };

            let suspended = crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice_with_options(
                state,
                db,
                ctx,
                choice_ctx,
                frame_idx,
                crate::core::enums::O_SELECT_MODE,
                0,
                choice_type,
                0,
                v as i16,
                options,
                Vec::new(),
            );

            if matches!(suspended, HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }

            return HandlerResult::Branch(frame_idx + 1);
        }
    }

    let mut choice = ctx.choice_index as usize;

    let ability = if ctx.source_card_id >= 0 {
        db.get_member(ctx.source_card_id)
            .map(|m| &m.abilities[ctx.ability_index as usize])
            .or_else(|| {
                db.get_live(ctx.source_card_id)
                    .map(|l| &l.abilities[ctx.ability_index as usize])
            })
    } else {
        None
    };

    let resolve_option = |idx: usize| -> Option<AbilityFrame> {
        ability
            .and_then(|ability| ability.get_modal_option_frames(idx))
            .and_then(|frames| frames.into_iter().next())
    };

    if v == 2 {
        let first_is_live_reveal = resolve_option(0)
            .map(|target| {
                target.opcode() == crate::core::enums::O_REVEAL_UNTIL
                    && (target.slot() as u32 & FLAG_REVEAL_UNTIL_IS_LIVE as u32) != 0
            })
            .unwrap_or(false);
        let second_is_live_reveal = resolve_option(1)
            .map(|target| {
                target.opcode() == crate::core::enums::O_REVEAL_UNTIL
                    && (target.slot() as u32 & FLAG_REVEAL_UNTIL_IS_LIVE as u32) != 0
            })
            .unwrap_or(false);

        if first_is_live_reveal ^ second_is_live_reveal {
            choice = 1 - choice;
        }
    }

    if let Some(new_frame) = resolve_option(choice) {
        ctx.choice_index = -1;
        return HandlerResult::BranchToFrames(std::sync::Arc::new(vec![new_frame]));
    }

    if choice >= v as usize {
        ctx.choice_index = -1;
        return HandlerResult::Branch(frame_idx + 1 + ((v as usize).saturating_sub(1)));
    }

    let target_effect_idx =
        frame_idx + 2 + choice + frames[frame_idx + 1 + choice].value() as usize;

    ctx.choice_index = -1;
    HandlerResult::Branch(target_effect_idx)
}
