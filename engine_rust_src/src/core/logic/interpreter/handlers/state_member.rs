use crate::core::logic::models::AbilityFrame;

use crate::core::logic::interpreter::handlers::HandlerResult;

use crate::core::enums::*;

use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::logging;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

use crate::core::logic::interpreter::suspension::resolve_target_player;

use crate::core::models::interpreter::resolve_target_slot;

#[path = "state_member_play.rs"]
mod state_member_play;

#[path = "state_member_position.rs"]
mod state_member_position;

#[path = "state_member_tap.rs"]
mod state_member_tap;

pub fn handle_member_state(
    state: &mut GameState,

    db: &CardDatabase,

    ctx: &mut AbilityContext,

    frame: impl Into<AbilityFrame>,

    frame_idx: usize,
) -> HandlerResult {
    let frame: AbilityFrame = frame.into();
    let frame_data = frame.components();

    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    #[allow(unused_variables)]
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;

    let slot_info = frame_data.slot;

    let target_slot = slot_info.target_slot as i32;

    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_ACTIVATE_MEMBER => {
            return state_member_tap::handle_activate_member(
                state,
                db,
                ctx,
                p_idx,
                resolved_slot,
                target_slot,
                v,
                a,
            );
        }

        O_SET_TAPPED => {
            let resolved_slot = if resolved_slot == 4 && ctx.area_idx >= 0 && ctx.area_idx < 3 {
                ctx.area_idx as i32
            } else {
                resolved_slot
            };

            return state_member_tap::handle_set_tapped(
                state,
                db,
                ctx,
                &frame,
                frame_idx,
                p_idx,
                resolved_slot,
            );
        }

        O_TAP_MEMBER => {
            let mut resolved_slot = resolve_target_slot(target_slot, ctx);
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
            let ability_filter_attr = db
                .get_member(ctx.source_card_id)
                .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
                .or_else(|| {
                    db.get_live(ctx.source_card_id)
                        .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
                })
                .and_then(|ability| {
                    ability
                        .effects
                        .iter()
                        .find(|effect| effect.runtime_opcode == O_TAP_MEMBER)
                        .and_then(|effect| filter_attr_from_params(Some(&effect.params)))
                })
                .unwrap_or(0);
            let frame_filter_attr = frame_data.filter.to_attr();

            if resolved_slot == 4 && ctx.area_idx >= 0 && ctx.area_idx < 3 {
                resolved_slot = ctx.area_idx as usize;
            }

            let filter_attr = if ability_filter_attr != 0 {
                ability_filter_attr
            } else if frame_filter_attr != 0 {
                frame_filter_attr
            } else {
                a as u64
            };
            let filter_target = (filter_attr & 0x3) as u8;
            if state.debug.debug_mode && ctx.source_card_id == 4196 {
                eprintln!(
                    "[STATE_TAP] filter_target={} resolved_slot={} {}",
                    filter_target,
                    resolved_slot,
                    logging::describe_frame_semantics(&frame_data, ctx, db)
                );
            }

            let mut target_p_idx =
                resolve_target_player(slot_info, filter_attr, ctx.player_id as usize);

            if filter_target != 2 && filter_target != 3 {
                if let Some(&selected_cid) = ctx.selected_cards.last() {
                    for candidate_p_idx in 0..=1 {
                        if let Some(slot) = state.players[candidate_p_idx]
                            .stage
                            .iter()
                            .position(|&cid| cid == selected_cid)
                        {
                            target_p_idx = candidate_p_idx;
                            resolved_slot = slot;
                            break;
                        }
                    }
                }
            }

            if state.debug.debug_mode && ctx.source_card_id == 4196 {
                eprintln!(
                    "[STATE_TAP] target_p_idx={} stage={:?} tapped={:?} {}",
                    target_p_idx,
                    state.players[target_p_idx].stage,
                    [
                        state.players[target_p_idx].is_tapped(0),
                        state.players[target_p_idx].is_tapped(1),
                        state.players[target_p_idx].is_tapped(2),
                    ],
                    logging::describe_context(ctx)
                );
            }

            if ctx.source_card_id == 4196 {
                eprintln!(
                    "[STATE_TAP_SEL] cond={} {}",
                    target_slot == 4
                        && (is_select_member_choice || ability_filter_attr != 0)
                        && a & 0x02 == 0
                        && (a & 0x01 != 0 || a & 0x80 != 0 || is_select_member_choice),
                    logging::describe_frame_semantics(&frame_data, ctx, db)
                );
            }

            if target_slot == 4
                && (is_select_member_choice || ability_filter_attr != 0)
                && a & 0x02 == 0
                && (a & 0x01 != 0 || a & 0x80 != 0 || is_select_member_choice)
            {
                if matches!(
                    suspend_choice(
                        state,
                        db,
                        ctx,
                        ctx,
                        frame_idx,
                        O_TAP_MEMBER,
                        0,
                        ChoiceType::TapMSelect,
                        ability_filter_attr,
                        v as i16,
                    ),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }

            return state_member_tap::handle_tap_member(
                state,
                db,
                ctx,
                &frame,
                frame_idx,
                target_p_idx,
                a,
                resolved_slot as i32,
            );
        }

        O_TAP_OPPONENT => {
            return state_member_tap::handle_tap_opponent(state, db, ctx, &frame, frame_idx, a, v);
        }

        O_MOVE_MEMBER => {
            return state_member_position::handle_move_member(
                state,
                db,
                ctx,
                &frame,
                frame_idx,
                p_idx,
                a,
                s,
                resolved_slot,
                slot_info,
            );
        }

        O_FORMATION_CHANGE => {
            return state_member_position::handle_formation_change(
                state,
                db,
                ctx,
                &frame,
                frame_idx,
                p_idx,
                a,
                s,
                resolved_slot,
            );
        }

        O_PLACE_UNDER => {
            return state_member_position::handle_place_under(
                state,
                db,
                ctx,
                p_idx,
                a,
                resolved_slot,
            );
        }

        O_ADD_STAGE_ENERGY => {
            return state_member_position::handle_add_stage_energy(state, p_idx, v, resolved_slot);
        }

        O_GRANT_ABILITY => {
            return state_member_position::handle_grant_ability(
                state,
                p_idx,
                ctx.source_card_id,
                v,
                target_slot,
                resolved_slot,
            );
        }

        O_PLAY_MEMBER_FROM_HAND => {
            return state_member_play::handle_play_member_from_hand(
                state, db, ctx, &frame, frame_idx, p_idx, v, a, s,
            );
        }

        O_PLAY_MEMBER_FROM_DISCARD => {
            return state_member_play::handle_play_member_from_discard(
                state, db, ctx, &frame, frame_idx, v, a, s,
            );
        }

        O_INCREASE_COST => {
            state.players[p_idx].cost_modifiers.push((
                crate::core::logic::Condition {
                    condition_type: ConditionType::None,

                    value: 0,

                    attr: 0,

                    target_slot: 0,

                    is_negated: false,

                    params: serde_json::Value::Null,
                },
                v,
            ));
        }

        _ => return HandlerResult::Continue,
    }

    HandlerResult::Continue
}
