use crate::core::enums::ChoiceType;
use crate::core::logic::constants::{CHOICE_DONE, FILTER_IS_OPTIONAL};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;
use crate::core::{O_SELECT_CARDS};

pub fn handle_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
    let optional_prompt_marker = -((v as i16) + 2);

    let slot_info = instr.slot();
    let source_zone = slot_info.source_zone as u8;
    let ts = slot_info.target_slot;
    let effective_zone = if source_zone != 0 {
        source_zone
    } else if ts != 0 {
        ts
    } else {
        7
    };

    if is_optional && v == 99 && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_SELECT_CARDS,
            0,
            ChoiceType::Optional,
            &choice_text,
            a as u64,
            optional_prompt_marker,
        ) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional && v == 99 && ctx.v_remaining == optional_prompt_marker {
        if ctx.choice_index == 1 || ctx.choice_index == CHOICE_DONE {
            if let Some(execution_id) = state.ui.current_execution_id {
                state.ui.cancelled_execution_ids.insert(execution_id);
            }
            return HandlerResult::Continue;
        }

        if ctx.choice_index == 0 {
            ctx.choice_index = -1;
            ctx.v_remaining = v as i16;
        }
    }

    if ctx.choice_index == -1 {
        state.players[p_idx].looked_cards.clear();
        let cards_to_filter = match effective_zone {
            6 => state.players[p_idx].hand.to_vec(),
            7 => state.players[p_idx].discard.to_vec(),
            4 => state.players[p_idx]
                .stage
                .iter()
                .cloned()
                .filter(|&c| c >= 0)
                .collect(),
            _ => state.players[p_idx].discard.to_vec(),
        };

        let filter_attr = a as u64;
        for cid in cards_to_filter {
            if state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                state.players[p_idx].looked_cards.push(cid);
            }
        }

        if state.players[p_idx].looked_cards.is_empty() && !is_optional {
            return HandlerResult::Continue;
        }

        let choice_type = match effective_zone {
            6 => ChoiceType::SelectHandDiscard,
            7 => ChoiceType::SelectDiscardPlay,
            _ => ChoiceType::LookAndChoose,
        };
        let choice_text = get_choice_text(db, ctx);
        if suspend_interaction(
            state,
            db,
            ctx,
            instr_ip,
            O_SELECT_CARDS,
            0,
            choice_type,
            &choice_text,
            a as u64,
            if ctx.v_remaining >= 0 {
                ctx.v_remaining
            } else {
                v as i16
            },
        ) {
            return HandlerResult::Suspend;
        }
    }

    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 && (a as u64 & FILTER_IS_OPTIONAL) != 0 {
        return HandlerResult::Continue;
    }

    if choice != CHOICE_DONE as i32
        && choice >= 0
        && (choice as usize) < state.players[p_idx].looked_cards.len()
    {
        let chosen = state.players[p_idx].looked_cards[choice as usize];
        ctx.selected_cards.push(chosen);

        let dest_zone = slot_info.dest_zone as u8;
        if dest_zone != 0 {
            let source_zone = slot_info.source_zone as u8;
            let actual_source = if source_zone != 0 { source_zone } else { 7 };

            let mut found = false;
            match actual_source {
                6 => {
                    if let Some(pos) = state.players[p_idx].hand.iter().position(|&c| c == chosen) {
                        state.players[p_idx].remove_hand_card(pos);
                        found = true;
                    }
                }
                7 => {
                    if let Some(pos) = state.players[p_idx]
                        .discard
                        .iter()
                        .position(|&c| c == chosen)
                    {
                        state.players[p_idx].remove_discard_card(pos);
                        found = true;
                    }
                }
                4 => {
                    for i in 0..3 {
                        if state.players[p_idx].stage[i] == chosen {
                            state.handle_member_leaves_stage(p_idx, i, db, ctx);
                            found = true;
                            break;
                        }
                    }
                }
                _ => {}
            }

            if found {
                match dest_zone {
                    6 => {
                        state.players[p_idx].gain_hand_card(chosen);
                    }
                    7 => {
                        state.players[p_idx].push_discard_card(chosen);
                    }
                    8 | 0 => {
                        state.players[p_idx].push_deck_card(chosen);
                    }
                    13 => {
                        state.players[p_idx].success_lives.push(chosen);
                    }
                    _ => {
                        state.players[p_idx].push_hand_card(chosen);
                    }
                }
            }
        }

        let rem = if ctx.v_remaining > 0 {
            ctx.v_remaining - 1
        } else {
            (v as i16).saturating_sub(1)
        };
        if rem > 0 {
            state.players[p_idx].looked_cards.remove(choice as usize);
            ctx.v_remaining = rem;
            ctx.choice_index = -1;
            let choice_type = match effective_zone {
                6 => ChoiceType::SelectHandDiscard,
                7 => ChoiceType::SelectDiscardPlay,
                _ => ChoiceType::LookAndChoose,
            };
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                s,
                choice_type,
                &choice_text,
                a as u64,
                rem,
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    HandlerResult::Continue
}
