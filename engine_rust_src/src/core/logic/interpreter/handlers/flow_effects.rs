use super::*;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::logic::Phase;

#[allow(clippy::too_many_arguments)]
pub fn handle_trigger_remote(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    v: i32,
    p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
) -> HandlerResult {
    let effect = current_effect(db, ctx, instr);
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
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_TRIGGER_REMOTE,
                0,
                ChoiceType::SelectDiscard,
                &choice_text,
                filter_attr,
                -1,
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
                return HandlerResult::BranchToBytecode(std::sync::Arc::new(
                    m.abilities[v as usize].bytecode.clone(),
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
    instr: &BytecodeInstruction,
    instr_ip: usize,
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
    let raw_effect = current_effect(db, ctx, instr)
        .and_then(|effect| effect.params.get("raw_effect"))
        .and_then(|value: &serde_json::Value| value.as_str());

    if matches!(raw_effect, Some("COUNT_MEMBER")) {
        let effect = current_effect(db, ctx, instr);
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
            .filter(|&cid| cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
            .count() as i16;
    } else if matches!(raw_effect, Some("DISCARD_YELL_PILE")) {
        if (a as u64 & FILTER_IS_OPTIONAL) != 0 && ctx.choice_index == -1 {
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_META_RULE,
                0,
                ChoiceType::Optional,
                &get_choice_text(db, ctx),
                a as u64,
                -1,
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
            crate::core::logic::performance::do_yell(state, db, yell_count);
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
    } else if a == 0 || a == 10 {
        state.players[target_p_idx].cheer_mod_count = state.players[target_p_idx]
            .cheer_mod_count
            .saturating_add(v as u16);
    } else if a == 8 {
        if v == 1 {
            let all_active = state.players[p_idx].tapped_energy_count() == 0;
            return HandlerResult::SetCond(all_active);
        }
    }

    HandlerResult::Continue
}
