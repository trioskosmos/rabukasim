use super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::filter::map_filter_string_to_attr;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::flow_helpers::discard_current_yell_pile;
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
    let target_p_idx = if slot_info.is_opponent || target_slot == 2 { 1 - base_p } else { base_p };
    
    // Single effect lookup - get the effect at frame_idx from the ability
    let ab_idx = usize::try_from(ctx.ability_index).ok();
    let effect = ab_idx.and_then(|idx| {
        db.get_live(ctx.source_card_id)
            .and_then(|c| c.abilities.get(idx))
            .or_else(|| db.get_member(ctx.source_card_id).and_then(|c| c.abilities.get(idx)))
            .and_then(|a| a.effects.get(frame_idx))
    });

    let raw_effect = effect.and_then(|e| e.params.get("raw_effect").and_then(|v| v.as_str()));
    let rule_type = effect.and_then(|e| e.params.get("type").or(e.params.get("TYPE"))).and_then(|v| v.as_str());
    let rule_name = effect.and_then(|e| e.params.get("rule").or(e.params.get("RULE"))).and_then(|v| v.as_str());

    if matches!(raw_effect, Some("COUNT_MEMBER")) {
        let filter_attr = effect
            .and_then(|e| e.params.get("filter"))
            .and_then(|v| v.as_str())
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
                    -1
                ),
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
    } else if let Some(_) = effect {
        if matches!(rule_name, Some("ALL_ENERGY_ACTIVE"))
            || (v == 1 && matches!(rule_type, Some("SCORE_RULE")))
        {
            let all_active = state.players[p_idx].tapped_energy_count() == 0;
            return HandlerResult::SetCond(all_active);
        }
    } else if frame.opcode() == O_META_RULE && v == 1 && frame.components().filter.card_type == 2 {
        let all_active = state.players[p_idx].tapped_energy_count() == 0;
        return HandlerResult::SetCond(all_active);
    }

    let is_cheer_mod = frame.opcode() == O_META_RULE
        && (matches!(rule_type, Some("CHEER_MOD"))
            || matches!(rule_name, Some("CHEER_MOD"))
            || matches!(raw_effect, Some("CHEER_MOD"))
            || a == 0
            || a == 10);

    if is_cheer_mod || (frame.opcode() == O_META_RULE && rule_type.is_none() && rule_name.is_none() && raw_effect.is_none()) {
        state.players[target_p_idx].cheer_mod_count = state.players[target_p_idx]
            .cheer_mod_count
            .saturating_add(v as u16);
        return HandlerResult::Continue;
    }

    HandlerResult::Continue
}
