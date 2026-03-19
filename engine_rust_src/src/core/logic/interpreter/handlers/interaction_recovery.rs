use crate::core::enums::{ChoiceType, Zone};
use crate::core::logic::constants::{CHOICE_ALL, FILTER_IS_OPTIONAL};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::{O_RECOVER_LIVE, O_RECOVER_MEMBER};

pub fn handle_recovery(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    real_op: i32,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let _s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let slot_info = instr.slot();
    let mut source_zone = slot_info.source_zone;
    if source_zone == Zone::Default {
        source_zone = Zone::Discard;
    }

    if ctx.choice_index == -1 && !state.players[p_idx].looked_cards.is_empty() {
        state.players[p_idx].looked_cards.clear();
    }

    if state.players[p_idx].looked_cards.is_empty() {
        let source_ids: Vec<i32> = match source_zone {
            Zone::Yell => state.players[p_idx].yell_cards.iter().copied().collect(),
            Zone::Hand => state.players[p_idx].hand.iter().copied().collect(),
            Zone::Deck => state.players[p_idx].deck.iter().copied().collect(),
            _ => state.players[p_idx].discard.iter().copied().collect(),
        };

        for cid in source_ids {
            let type_matches = if real_op == O_RECOVER_LIVE {
                db.get_live(cid).is_some()
            } else {
                db.get_member(cid).is_some()
            };
            if type_matches
                && (a == 0 || state.card_matches_filter_with_ctx(db, cid, a as u64, ctx))
            {
                state.players[p_idx].looked_cards.push(cid);
            }
        }
        if state.players[p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
    }

    if ctx.choice_index == -1 {
        let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
        let is_single_choice_auto_pick = !is_optional
            && state.players[p_idx].looked_cards.len() == 1
            && real_op != O_RECOVER_MEMBER;

        if is_single_choice_auto_pick {
            ctx.choice_index = 0;
        } else {
            let choice_type = if real_op == O_RECOVER_LIVE {
                ChoiceType::RecovL
            } else {
                ChoiceType::RecovM
            };
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                real_op,
                0,
                choice_type,
                &choice_text,
                0,
                -1,
            ) {
                return HandlerResult::Suspend;
            }
        }
    }

    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 {
        state.players[p_idx].looked_cards.clear();
        return HandlerResult::Continue;
    }
    let real_idx = if choice >= 0 && (choice as usize) < state.players[p_idx].looked_cards.len() {
        Some(choice as usize)
    } else {
        None
    };

    if let Some(idx) = real_idx {
        let cid = state.players[p_idx].looked_cards[idx];
        if cid != -1 {
            state.players[p_idx].looked_cards[idx] = -1;
            state.players[p_idx].gain_hand_card(cid);
            ctx.selected_cards.push(cid);

            let slot_info = instr.slot();
            let mut source_zone = slot_info.source_zone;
            if source_zone == Zone::Default {
                source_zone = Zone::Discard;
            }
            match source_zone {
                Zone::Yell => {
                    if let Some(pos) = state.players[p_idx]
                        .yell_cards
                        .iter()
                        .position(|&x| x == cid)
                    {
                        state.players[p_idx].yell_cards.remove(pos);
                    }
                }
                Zone::Hand => {
                    if let Some(pos) = state.players[p_idx].hand.iter().position(|&x| x == cid) {
                        state.players[p_idx].remove_hand_card(pos);
                    }
                }
                Zone::Deck => {
                    if let Some(pos) = state.players[p_idx].deck.iter().position(|&x| x == cid) {
                        state.players[p_idx].remove_deck_card(pos);
                    }
                }
                _ => {
                    if let Some(pos) = state.players[p_idx].discard.iter().position(|&x| x == cid) {
                        state.players[p_idx].remove_discard_card(pos);
                    }
                }
            }
            let remaining = if ctx.v_remaining == -1 {
                v as i16 - 1
            } else {
                ctx.v_remaining - 1
            };
            if remaining > 0
                && choice != CHOICE_ALL as i32
                && state.players[p_idx].looked_cards.iter().any(|&c| c != -1)
            {
                let choice_type = if real_op == O_RECOVER_LIVE {
                    ChoiceType::RecovL
                } else {
                    ChoiceType::RecovM
                };
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    real_op,
                    0,
                    choice_type,
                    &choice_text,
                    0,
                    remaining,
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }
    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}
