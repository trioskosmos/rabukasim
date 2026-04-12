use super::HandlerResult;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::filter::merge_filter_attr_with_params;
use crate::core::logic::interpreter::conditions::get_condition_count;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::flow_helpers::{
    discard_current_yell_pile,
};
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::performance::do_yell;
use crate::core::logic::Phase;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

fn get_param_case_insensitive<'a>(
    params: &'a serde_json::Map<String, serde_json::Value>,
    key: &str,
) -> Option<&'a serde_json::Value> {
    params.get(key).or_else(|| params.get(&key.to_uppercase()))
}

fn target_player_for_meta_rule(base_p: usize, slot_info: crate::core::logic::interpreter::instruction::DecodedSlot, target_slot: i32) -> usize {
    if slot_info.is_opponent || target_slot == 2 {
        1 - base_p
    } else {
        base_p
    }
}

#[allow(clippy::too_many_arguments)]
pub fn handle_meta_rule(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let a = frame_data.raw_attr as i64;
    let v = frame_data.value;
    let p_idx = ctx.player_id as usize;
    let base_p = ctx.activator_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = frame_data.slot.target_slot as i32;
    let target_p_idx = target_player_for_meta_rule(base_p, slot_info, target_slot);
    let raw_effect = frame_data
        .params
        .and_then(|p| p.get("raw_effect"))
        .and_then(|value: &serde_json::Value| value.as_str());
    let rule_type = frame_data
        .params
        .and_then(|p| p.as_object())
        .and_then(|obj| get_param_case_insensitive(obj, "type"))
        .and_then(|value| value.as_str())
        .map(|value| value.to_ascii_uppercase());
    let rule_name = frame_data
        .params
        .and_then(|p| p.as_object())
        .and_then(|obj| get_param_case_insensitive(obj, "rule"))
        .and_then(|value| value.as_str())
        .map(|value| value.to_ascii_uppercase());

    if matches!(raw_effect, Some("COUNT_MEMBER")) {
        let filter_attr = merge_filter_attr_with_params(frame_data.raw_attr, frame_data.params);
        ctx.v_accumulated = get_condition_count(state, db, C_COUNT_STAGE, filter_attr, ctx) as i16;
    } else if matches!(raw_effect, Some("DISCARD_YELL_PILE")) {
        if (a as u64 & FILTER_IS_OPTIONAL) != 0 && ctx.choice_index == -1 {
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_META_RULE, 0, ChoiceType::Optional, a as u64, -1),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if ctx.choice_index == 99 {
            ctx.v_accumulated = state.players[p_idx].yell_cards.len() as i16;
            return HandlerResult::Continue;
        } else {
            ctx.v_accumulated = discard_current_yell_pile(state, p_idx) as i16;
        }
    } else if matches!(raw_effect, Some("RE_YELL")) {
        let yell_count = if ctx.v_accumulated > 0 {
            ctx.v_accumulated as u32
        } else {
            state.players[p_idx].yell_cards.len() as u32
        };

        state.players[p_idx].yell_heart_bonus = [HeartBoard::default(); 3];
        state.players[p_idx].yell_blade_bonus = [0; 3];
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
    } else if matches!(raw_effect, Some("SET_SOURCE_COST_FROM_SELECTED_MINUS")) {
        let delta = frame_data
            .params
            .and_then(|params| params.as_object())
            .and_then(|obj| get_param_case_insensitive(obj, "offset"))
            .and_then(|value| value.as_i64())
            .unwrap_or(1) as i32;
        let Some(selected_cid) = ctx.selected_cards.last().copied() else {
            return HandlerResult::Continue;
        };
        let Some(selected_member) = db.get_member(selected_cid) else {
            return HandlerResult::Continue;
        };
        let Some(source_member) = db.get_member(ctx.source_card_id) else {
            return HandlerResult::Continue;
        };

        let amount = (selected_member.cost as i32 - delta) - source_member.cost as i32;
        let condition = crate::core::logic::Condition {
            condition_type: crate::core::enums::ConditionType::None,
            value: ctx.source_card_id,
            attr: 0,
            target_slot: 0,
            is_negated: false,
            params: serde_json::json!({
                "raw_cond": "SOURCE_CARD_ID_EQUALS",
                "card_id": ctx.source_card_id,
            }),
        };
        state.players[p_idx].cost_modifiers.push((condition, amount));
        if let Some(source_slot) = state.players[p_idx]
            .stage
            .iter()
            .position(|&cid| cid == ctx.source_card_id)
            .filter(|&slot| slot < 3)
        {
            ctx.area_idx = source_slot as i16;
            ctx.target_slot = source_slot as i16;
        }
        ctx.v_accumulated = (selected_member.cost as i32 - delta) as i16;
    } else if matches!(rule_name.as_deref(), Some("ALL_ENERGY_ACTIVE"))
        || (v == 1 && matches!(rule_type.as_deref(), Some("SCORE_RULE")))
    {
        let all_active = state.players[p_idx].tapped_energy_count() == 0;
        return HandlerResult::SetCond(all_active);
    } else if frame_data.opcode == O_META_RULE && v == 1 && frame_data.filter.card_type == 2 {
        let all_active = state.players[p_idx].tapped_energy_count() == 0;
        return HandlerResult::SetCond(all_active);
    }

    let is_cheer_mod = frame_data.opcode == O_META_RULE
        && (matches!(rule_type.as_deref(), Some("CHEER_MOD"))
            || matches!(rule_name.as_deref(), Some("CHEER_MOD"))
            || matches!(raw_effect, Some("CHEER_MOD"))
            || a == 0
            || a == 10);

    if is_cheer_mod {
        state.players[target_p_idx].cheer_mod_count = state.players[target_p_idx]
            .cheer_mod_count
            .saturating_add(v as u16);
        return HandlerResult::Continue;
    }

    if frame_data.opcode == O_META_RULE
        && rule_type.is_none()
        && rule_name.is_none()
        && raw_effect.is_none()
    {
        state.players[target_p_idx].cheer_mod_count = state.players[target_p_idx]
            .cheer_mod_count
            .saturating_add(v as u16);
        return HandlerResult::Continue;
    }

    HandlerResult::Continue
}
