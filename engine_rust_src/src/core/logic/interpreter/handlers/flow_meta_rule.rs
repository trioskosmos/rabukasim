use super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::filter::map_filter_string_to_attr;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::flow_helpers::current_effect_by_frame_index;
use crate::core::logic::interpreter::handlers::flow_helpers::{
    current_effect, discard_current_yell_pile,
};
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::performance::do_yell;
use crate::core::logic::Phase;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

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
    let target_p_idx = if slot_info.is_opponent || target_slot == 2 {
        1 - base_p
    } else {
        base_p
    };
    let effect_lookup = current_effect_by_frame_index(db, ctx, frame, frame_idx)
        .or_else(|| {
            let ab_idx = usize::try_from(ctx.ability_index).ok();
            ab_idx
                .and_then(|ab_idx| {
                    db.get_live(ctx.source_card_id)
                        .and_then(|card| card.abilities.get(ab_idx))
                        .or_else(|| {
                            db.get_member(ctx.source_card_id)
                                .and_then(|card| card.abilities.get(ab_idx))
                        })
                })
                .and_then(|ability| ability.effects.get(frame_idx))
        })
        .or_else(|| current_effect(db, ctx, frame));
    let raw_effect = effect_lookup
        .and_then(|effect| effect.params.get("raw_effect"))
        .and_then(|value: &serde_json::Value| value.as_str());

    if matches!(raw_effect, Some("COUNT_MEMBER")) {
        let effect = effect_lookup;
        let filter_attr = effect
            .and_then(|effect| effect.params.get("filter"))
            .and_then(|value: &serde_json::Value| value.as_str())
            .map(map_filter_string_to_attr)
            .filter(|&attr| attr != 0)
            .unwrap_or(a as u64);
        let target_player = match (filter_attr & 0x3) as u8 {
            2 => 1 - p_idx,
            3 => 1,
            _ => p_idx,
        };

        ctx.v_accumulated = state.players[target_player]
            .stage
            .iter()
            .copied()
            .filter(|&cid| {
                cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
            })
            .count() as i16;
    } else if matches!(raw_effect, Some("DISCARD_YELL_PILE")) {
        if (a as u64 & FILTER_IS_OPTIONAL) != 0 && ctx.choice_index == -1 {
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_META_RULE,
                    0,
                    ChoiceType::Optional,
                    a as u64,
                    -1,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }

        if ctx.choice_index == 99 {
            ctx.v_accumulated = state.players[p_idx].yell_cards.len() as i16;
            return HandlerResult::Continue;
        }

        ctx.v_accumulated = discard_current_yell_pile(state, p_idx) as i16;
    } else if matches!(raw_effect, Some("RE_YELL")) {
        let yell_count = if ctx.v_accumulated > 0 {
            ctx.v_accumulated as u32
        } else {
            state.players[p_idx].yell_cards.len() as u32
        };

        if !state.players[p_idx].yell_cards.is_empty() {
            state.players[p_idx].yell_cards.clear();
        }

        ctx.v_accumulated = 0;
        if yell_count > 0 {
            do_yell(state, db, yell_count);
            if state.phase == Phase::Response {
                return HandlerResult::Suspend;
            }
        }
    } else if matches!(raw_effect, Some("TAP_SELF")) {
        let slot_idx = if ctx.area_idx >= 0 {
            Some(ctx.area_idx as usize)
        } else {
            state.players[p_idx]
                .stage
                .iter()
                .position(|&cid| cid == ctx.source_card_id)
        };

        if let Some(slot_idx) = slot_idx.filter(|&slot| slot < 3) {
            state.players[p_idx].set_tapped(slot_idx, true);
        }
    } else if let Some(effect) = effect_lookup {
        let rule_type = effect
            .params
            .get("type")
            .or_else(|| effect.params.get("TYPE"))
            .and_then(|value| value.as_str())
            .map(|value| value.to_ascii_uppercase());
        let rule_name = effect
            .params
            .get("rule")
            .or_else(|| effect.params.get("RULE"))
            .and_then(|value| value.as_str())
            .map(|value| value.to_ascii_uppercase());

        if matches!(rule_name.as_deref(), Some("ALL_ENERGY_ACTIVE"))
            || (v == 1 && matches!(rule_type.as_deref(), Some("SCORE_RULE")))
        {
            let all_active = state.players[p_idx].tapped_energy_count() == 0;
            return HandlerResult::SetCond(all_active);
        }
    } else if frame.opcode() == O_META_RULE && v == 1 && frame.components().filter.card_type == 2 {
        let all_active = state.players[p_idx].tapped_energy_count() == 0;
        return HandlerResult::SetCond(all_active);
    }

    if frame.opcode() == O_META_RULE && (a == 0 || a == 10) {
        state.players[target_p_idx].cheer_mod_count = state.players[target_p_idx]
            .cheer_mod_count
            .saturating_add(v as u16);
        return HandlerResult::Continue;
    }

    HandlerResult::Continue
}
