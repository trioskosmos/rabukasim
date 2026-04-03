use super::*;
use crate::core::logic::constants::{CHOICE_DONE, TARGET_SLOT_STAGE, ZONE_DISCARD, ZONE_HAND};
use crate::core::enums::Zone;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::suspension::resolve_target_player;
use crate::core::models::AbilityContext;

fn selected_target_key(source_zone: Zone, slot_idx: i32) -> i32 {
    ((source_zone as i32) << 8) | slot_idx
}

fn cards_for_source_zone(state: &GameState, target_player: usize, source_zone: Zone) -> Vec<i32> {
    match source_zone {
        Zone::Hand => state.players[target_player].hand.to_vec(),
        Zone::Discard => state.players[target_player].discard.to_vec(),
        _ => state.players[target_player].stage.to_vec(),
    }
}

fn selection_source_zone(raw_zone: u8) -> Zone {
    match raw_zone {
        x if x == ZONE_HAND as u8 => Zone::Hand,
        x if x == ZONE_DISCARD as u8 => Zone::Discard,
        _ => Zone::Stage,
    }
}

fn count_selected_targets(cards: &[i32], source_zone: u8, keys: &[i32]) -> usize {
    let source_zone = selection_source_zone(source_zone);
    cards
        .iter()
        .enumerate()
        .filter(|(idx, cid)| {
            **cid >= 0 && keys.contains(&selected_target_key(source_zone, *idx as i32))
        })
        .count()
}

fn count_remaining_targets(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    cards: &[i32],
    source_zone: u8,
    keys: &[i32],
    filter_attr: u64,
) -> usize {
    let source_zone = selection_source_zone(source_zone);
    cards
        .iter()
        .enumerate()
        .filter(|(idx, cid)| {
            **cid >= 0
                && !keys.contains(&selected_target_key(source_zone, *idx as i32))
                && state.card_matches_filter_with_ctx(db, **cid, filter_attr, ctx)
        })
        .count()
}

fn recover_select_filter_attr(db: &CardDatabase, ctx: &AbilityContext, current: u64) -> u64 {
    let Ok(ab_idx) = usize::try_from(ctx.ability_index) else {
        return current;
    };

    let abilities = db
        .get_live(ctx.source_card_id)
        .map(|card| &card.abilities)
        .or_else(|| {
            db.get_member(ctx.source_card_id)
                .map(|card| &card.abilities)
        });
    let Some(abilities) = abilities else {
        return current;
    };

    let ability = abilities.get(ab_idx).or_else(|| {
        abilities.iter().find(|ability| {
            ability
                .resolved_frames()
                .iter()
                .any(|frame| frame.opcode() == O_SELECT_MEMBER)
        })
    });
    let Some(ability) = ability else {
        return current;
    };

    ability
        .resolved_frames()
        .iter()
        .find(|frame| frame.opcode() == O_SELECT_MEMBER)
        .map(|frame| frame.attr())
        .map(|attr| current | attr)
        .unwrap_or(current)
}

#[allow(clippy::too_many_arguments)]
pub fn resolve_select_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr_ip: usize,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    _p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    supports_partial_completion: bool,
    partial_selection_prompt: i16,
    is_move_member_follow_up: bool,
) -> HandlerResult {
    let choice = ctx.choice_index as i32;
    let source_zone = slot_info.source_zone as u8;
    let filter_attr = recover_select_filter_attr(
        db,
        ctx,
        state
            .interaction_stack
            .last()
            .map(|interaction| interaction.filter_attr)
            .unwrap_or(a as u64),
    );
    let is_targeted_select_member_cost = state
        .interaction_stack
        .last()
        .map(|interaction| {
            crate::core::logic::interpreter::instruction::DecodedSlot::decode(
                interaction.target_slot,
            )
            .target_slot
                == TARGET_SLOT_STAGE
                && (interaction.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK)
                    != 0
        })
        .unwrap_or(false);
    let is_tap_member_selection = state
        .interaction_stack
        .last()
        .map(|interaction| interaction.choice_type == ChoiceType::TapMSelect)
        .unwrap_or(false);
    let is_optional_set_tapped = state
        .interaction_stack
        .last()
        .map(|interaction| {
            interaction.choice_type == ChoiceType::Optional
                && interaction.effect_opcode == crate::core::O_SET_TAPPED
        })
        .unwrap_or(false);

    if supports_partial_completion && choice == CHOICE_DONE as i32 {
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
        return HandlerResult::Continue;
    }

    let target_player = if is_targeted_select_member_cost {
        ctx.player_id as usize
    } else {
        resolve_target_player(slot_info, filter_attr, ctx.player_id as usize)
    };
    let source_zone_enum = selection_source_zone(source_zone);
    let selected_cid = {
        let source_cards = cards_for_source_zone(state, target_player, source_zone_enum);
        let idx = if source_zone == ZONE_HAND as u8 || source_zone == ZONE_DISCARD as u8 {
            choice.saturating_sub(1) as usize
        } else {
            choice as usize
        };
        source_cards.get(idx).copied().unwrap_or(-1)
    };
    if source_zone == ZONE_HAND as u8 || source_zone == ZONE_DISCARD as u8 {
        ctx.selected_hand_idx = if choice > 0 { choice - 1 } else { choice } as i16;
        ctx.target_card_id = selected_cid;
    } else {
        ctx.target_slot = choice as i16;
        ctx.area_idx = choice as i16;
    }
    if selected_cid >= 0 && !ctx.selected_cards.contains(&selected_cid) {
        ctx.selected_cards.push(selected_cid);
    }
    if choice >= 0
        && choice < 3
        && (is_targeted_select_member_cost || is_tap_member_selection || is_optional_set_tapped)
    {
        if state.debug.debug_mode && ctx.source_card_id == 4196 {
            eprintln!(
                "[SELECT_RESOLVE_TAP] target_player={} choice={} selected_cid={} before_tapped={}",
                target_player,
                choice,
                selected_cid,
                state.players[target_player].is_tapped(choice as usize)
            );
        }
        state.players[target_player].set_tapped(choice as usize, true);
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
    }
    let selected_key = selected_target_key(source_zone_enum, choice);
    if !ctx.selected_target_keys.contains(&selected_key) {
        ctx.selected_target_keys.push(selected_key);
    }

    if state.debug.debug_mode {
        state.trace_internal(&format!(
            "FRAME_SELECT_RESOLVE: [phase={:?}] choice={} cid={} source_zone={} selected_cards={} remaining={} {}",
            state.phase,
            choice,
            selected_cid,
            source_zone,
            ctx.selected_cards.len(),
            ctx.v_remaining,
            logging::describe_context(ctx)
        ));
    }

    if is_move_member_follow_up {
        ctx.target_slot = choice as i16;
        ctx.choice_index = -1;
        return HandlerResult::Continue;
    }

    if supports_partial_completion && !ctx.selected_cards.is_empty() {
        let current_selection_count = count_selected_targets(
            cards_for_source_zone(state, target_player, source_zone_enum).as_slice(),
            source_zone,
            &ctx.selected_target_keys,
        );
        let remaining_candidates = count_remaining_targets(
            state,
            db,
            ctx,
            cards_for_source_zone(state, target_player, source_zone_enum).as_slice(),
            source_zone,
            &ctx.selected_target_keys,
            filter_attr,
        );

        let remaining_picks = (v as usize).saturating_sub(current_selection_count);

        if remaining_picks > 0 && remaining_candidates > 0 {
            ctx.choice_index = -1;
            ctx.v_remaining = remaining_picks as i16;
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    op,
                    s,
                    ChoiceType::SelectMember,
                    filter_attr,
                    remaining_picks as i16,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if remaining_picks > 0 && current_selection_count == 1 && remaining_candidates > 0 {
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    op,
                    s,
                    ChoiceType::Optional,
                    0,
                    partial_selection_prompt,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if remaining_picks > 0 && remaining_candidates == 0 {
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
        }
    }

    if !supports_partial_completion && !is_move_member_follow_up {
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
    }

    HandlerResult::Continue
}
