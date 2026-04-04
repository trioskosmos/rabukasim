use crate::core::enums::ChoiceType;
use crate::core::logic::constants::{CHOICE_ALL, CHOICE_DONE};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::enums::Zone;
use crate::core::{O_RECOVER_LIVE, O_RECOVER_MEMBER};

fn recovery_uses_same_name_filter(
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> bool {
    recovery_special_id(db, ctx, frame_data, frame_idx) == 4
}

fn recovery_special_id(
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> u8 {
    if frame_data.filter.special_id != 0 {
        return frame_data.filter.special_id;
    }

    let source_card_id = if ctx.ability_card_id >= 0 {
        ctx.ability_card_id
    } else {
        ctx.source_card_id
    };
    let ability_index = ctx.ability_index.max(0) as usize;
    let ability = db
        .get_member(source_card_id)
        .and_then(|member| member.abilities.get(ability_index))
        .or_else(|| db.get_live(source_card_id).and_then(|live| live.abilities.get(ability_index)));
    let Some(ability) = ability else {
        return 0;
    };
    if cfg!(debug_assertions) {
        let _ = (ability.frame_program.is_some(), ability.resolved_frame_source());
    }
    let Some(frame_program) = ability.frame_program.as_ref() else {
        return 0;
    };

    if let Some(frame) = frame_program.frames.get(frame_idx) {
        let program_frame = frame.components();
        if program_frame.opcode == frame_data.opcode {
            return program_frame.filter.special_id;
        }
    }

    frame_program
        .frames
        .iter()
        .map(|frame| frame.components())
        .find(|program_frame| {
            program_frame.opcode == frame_data.opcode
                && program_frame.value == frame_data.value
                && program_frame.raw_slot == frame_data.raw_slot
        })
        .or_else(|| {
            frame_program
                .frames
                .iter()
                .map(|frame| frame.components())
                .find(|program_frame| {
                    program_frame.opcode == frame_data.opcode
                        && program_frame.filter.special_id != 0
                })
        })
        .map(|program_frame| program_frame.filter.special_id)
        .unwrap_or(0)
}

/// Recovery handler - consolidated from interaction_recovery_resolve.rs
pub fn handle_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    op: i32,
) -> HandlerResult {
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let source_zone = if op == O_RECOVER_LIVE || op == O_RECOVER_MEMBER {
        Zone::Discard
    } else {
        normalized_source_zone(slot_info.source_zone)
    };
    let zone_cards = collect_zone_cards(state, p_idx, source_zone);
    let candidate_cards = zone_cards.clone();
    let real_op = if op == O_RECOVER_LIVE || op == O_RECOVER_MEMBER {
        op
    } else {
        frame_data.opcode
    };
    let use_name_filter = recovery_uses_same_name_filter(db, ctx, frame_data, frame_idx);

    // Handle "same name" style recovery when the frame has no explicit filter.
    let mut handled_same_name = false;
    if use_name_filter {
        let source_cards = get_source_cards_for_name_recovery(state, db, ctx, p_idx);
        let revealed_names: Vec<String> = source_cards
            .iter()
            .filter_map(|cid| {
                db.get_live(*cid)
                    .map(|c| c.name.clone())
                    .or_else(|| db.get_member(*cid).map(|c| c.name.clone()))
            })
            .collect();
        handled_same_name = true;

        state.players[p_idx].looked_cards.clear();
        for cid in &candidate_cards {
            if !type_matches(db, *cid, real_op) {
                continue;
            }
            let candidate_name = db.get_live(*cid)
                .map(|c| c.name.clone())
                .or_else(|| db.get_member(*cid).map(|c| c.name.clone()));
            if let Some(name) = candidate_name {
                if revealed_names
                    .iter()
                    .any(|revealed| same_name_recovery_matches(&name, revealed))
                {
                    state.players[p_idx].looked_cards.push(*cid);
                }
            }
        }

        if state.players[p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
    }

    // Populate looked_cards from candidate_cards if not already handled
    if !handled_same_name {
        state.players[p_idx].looked_cards.clear();
        for cid in &candidate_cards {
            if type_matches(db, *cid, real_op)
                && (a == 0 || state.card_matches_filter_with_ctx(db, *cid, a as u64, ctx))
            {
                state.players[p_idx].looked_cards.push(*cid);
            }
        }
        if state.players[p_idx].looked_cards.is_empty()
            && matches!(source_zone, Zone::Discard)
            && (op == O_RECOVER_LIVE || op == O_RECOVER_MEMBER)
        {
            let recent_discards = state.players[p_idx].discard_ids_this_turn.clone();
            for cid in recent_discards {
                if type_matches(db, cid, real_op)
                    && state.players[p_idx].discard.contains(&cid)
                    && !state.players[p_idx].looked_cards.contains(&cid)
                {
                    state.players[p_idx].looked_cards.push(cid);
                }
            }
        }
        if state.players[p_idx].looked_cards.is_empty() {
            // Special case: remove sacrificed member if recovery failed
            if op == O_RECOVER_MEMBER {
                if let Some(&sacrificed_cid) = ctx.selected_cards.first() {
                    remove_card_from_zone(state, db, ctx, p_idx, Zone::Stage, sacrificed_cid);
                }
            }
            return HandlerResult::Continue;
        }
    }

    // Check if already in recovery prompt
    let in_recovery_prompt = state
        .interaction_stack
        .last()
        .map(|i| matches!(i.choice_type, ChoiceType::RecovL | ChoiceType::RecovM))
        .unwrap_or(false);

    // Suspend for player choice if needed
    if ctx.choice_index == -1 && !in_recovery_prompt {
        // Auto-pick if only 1 card for O_RECOVER_LIVE
        if real_op == O_RECOVER_LIVE && state.players[p_idx].looked_cards.len() == 1 {
            ctx.choice_index = 0;
        } else {
            let choice_type = if real_op == O_RECOVER_LIVE {
                ChoiceType::RecovL
            } else {
                ChoiceType::RecovM
            };
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, op, 0, choice_type, 0, -1),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    // Handle player choice
    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 {
        state.players[p_idx].looked_cards.clear();
        return HandlerResult::Continue;
    }

    if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
        let cid = state.players[p_idx].looked_cards[choice as usize];
        if cid != -1 {
            state.players[p_idx].looked_cards[choice as usize] = -1;
            state.players[p_idx].gain_hand_card(cid);
            ctx.selected_cards.push(cid);
            remove_card_from_zone(state, db, ctx, p_idx, source_zone, cid);

            // Handle multi-recovery remainder
            let remaining = if ctx.v_remaining == -1 { v as i16 - 1 } else { ctx.v_remaining - 1 };
            if remaining > 0
                && choice != CHOICE_ALL as i32
                && state.players[p_idx].looked_cards.iter().any(|&c| c != -1)
            {
                let choice_type = if real_op == O_RECOVER_LIVE {
                    ChoiceType::RecovL
                } else {
                    ChoiceType::RecovM
                };
                if matches!(
                    suspend_choice(state, db, ctx, ctx, frame_idx, op, 0, choice_type, 0, remaining),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }

    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}

// === Helper functions (inlined from interaction_zone) ===

fn normalized_source_zone(zone: crate::core::logic::Zone) -> Zone {
    if zone == Zone::Default {
        Zone::Discard
    } else {
        zone
    }
}

fn normalize_same_name(name: &str) -> String {
    name.replace(' ', "")
}

fn same_name_recovery_matches(candidate_name: &str, revealed_name: &str) -> bool {
    let normalized_candidate = normalize_same_name(candidate_name);
    let normalized_revealed = normalize_same_name(revealed_name);
    normalized_candidate.contains(&normalized_revealed)
}

fn collect_zone_cards(state: &GameState, p_idx: usize, zone: Zone) -> Vec<i32> {
    match zone {
        Zone::Yell => state.players[p_idx].yell_cards.iter().copied().collect(),
        Zone::Hand => state.players[p_idx].hand.iter().copied().collect(),
        Zone::Deck => state.players[p_idx].deck.iter().copied().collect(),
        _ => state.players[p_idx].discard.iter().copied().collect(),
    }
}

fn remove_card_from_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    zone: Zone,
    cid: i32,
) -> bool {
    match zone {
        Zone::Yell => {
            if let Some(pos) = state.players[p_idx].yell_cards.iter().position(|&x| x == cid) {
                state.players[p_idx].yell_cards.remove(pos);
                true
            } else {
                false
            }
        }
        Zone::Hand => {
            if let Some(pos) = state.players[p_idx].hand.iter().position(|&x| x == cid) {
                state.players[p_idx].remove_hand_card(pos);
                true
            } else {
                false
            }
        }
        Zone::Deck => {
            if let Some(pos) = state.players[p_idx].deck.iter().position(|&x| x == cid) {
                state.players[p_idx].remove_deck_card(pos);
                true
            } else {
                false
            }
        }
        Zone::Stage => {
            for i in 0..3 {
                if state.players[p_idx].stage[i] == cid {
                    state.handle_member_leaves_stage(p_idx, i, db, ctx);
                    return true;
                }
            }
            false
        }
        _ => {
            if let Some(pos) = state.players[p_idx].discard.iter().position(|&x| x == cid) {
                state.players[p_idx].remove_discard_card(pos);
                true
            } else {
                false
            }
        }
    }
}

fn type_matches(db: &CardDatabase, cid: i32, op: i32) -> bool {
    if op == O_RECOVER_LIVE {
        db.get_live(cid).is_some()
    } else {
        db.get_member(cid).is_some()
    }
}

fn get_source_cards_for_name_recovery(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
) -> Vec<i32> {
    let revealed: Vec<i32> = state.players[p_idx]
        .revealed_cards
        .iter()
        .copied()
        .filter(|cid| db.get_live(*cid).is_some() || db.get_member(*cid).is_some())
        .collect();
    if !revealed.is_empty() {
        return revealed;
    }

    let selected: Vec<i32> = ctx
        .selected_cards
        .iter()
        .copied()
        .filter(|cid| db.get_live(*cid).is_some() || db.get_member(*cid).is_some())
        .collect();
    if !selected.is_empty() {
        return selected;
    }

    let hand: Vec<i32> = state.players[p_idx]
        .hand
        .iter()
        .copied()
        .filter(|cid| db.get_live(*cid).is_some() || db.get_member(*cid).is_some())
        .collect();
    if !hand.is_empty() {
        return hand;
    }

    Vec::new()
}
