use crate::core::enums::{ChoiceType, TriggerType};
use crate::core::logic::constants::{
    CHOICE_ALL, CHOICE_DONE, ZONE_DISCARD, ZONE_HAND, ZONE_YELL,
};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::O_LOOK_AND_CHOOSE;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

#[path = "interaction_look_choose_apply.rs"]
mod interaction_look_choose_apply;
#[path = "interaction_look_choose_finalize.rs"]
mod interaction_look_choose_finalize;
#[path = "interaction_look_choose_resolve.rs"]
mod interaction_look_choose_resolve;

pub fn handle_look_and_choose(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
) -> HandlerResult {
    let frame_data = frame.components();
    let _v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = slot_info.target_slot;
    let rem_dest = slot_info.dest_zone as u8;
    let source_zone_bits = slot_info.source_zone as u8;
    let source_zone = if source_zone_bits == 0 {
        8
    } else {
        source_zone_bits as i32
    };
    let lc = frame.look_choose();
    let look_count = lc.count.max(1) as usize;
    let reveal_flag = lc.reveal;
    let dest_discard_v = lc.dest_discard;
    let compiled_choice_count = frame.look_choose().choose_count.max(1);
    if state.debug.debug_mode {
        println!(
            "[DEBUG_LOOK_FRAME] {} look_count={} choose_count={}",
            logging::describe_frame_semantics(&frame_data, ctx, db),
            look_count,
            compiled_choice_count
        );
    }

    if state.players[p_idx].looked_cards.is_empty() {
        let reveal_count = if source_zone == ZONE_HAND {
            state.players[p_idx].hand.len()
        } else if source_zone == ZONE_DISCARD {
            state.players[p_idx].discard.len()
        } else if source_zone == ZONE_YELL {
            state.players[p_idx].yell_cards.len()
        } else {
            look_count
        };
        match source_zone {
            ZONE_HAND => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].pop_hand_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            ZONE_DISCARD => {
                for _ in 0..reveal_count {
                    if let Some(cid) = state.players[p_idx].pop_discard_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
            ZONE_YELL => {
                let y = std::mem::take(&mut state.players[p_idx].yell_cards);
                state.players[p_idx].looked_cards.extend(y);
            }
            _ => {
                if state.players[p_idx].deck.len() < reveal_count {
                    state.resolve_deck_refresh(p_idx);
                }
                for _ in 0..reveal_count.min(state.players[p_idx].deck.len()) {
                    if let Some(cid) = state.players[p_idx].pop_deck_card() {
                        state.players[p_idx].looked_cards.push(cid);
                    }
                }
            }
        }
    }

    if ctx.choice_index == -1 {
        if state.debug.debug_mode {
            println!(
                "[DEBUG_LOOK] suspend: source_zone={} looked_cards={:?} {}",
                source_zone,
                state.players[p_idx].looked_cards,
                logging::describe_context(ctx)
            );
        }
        let choice_type = if source_zone == ZONE_HAND {
            ChoiceType::SelectHandDiscard
        } else if source_zone == ZONE_DISCARD {
            ChoiceType::SelectDiscardPlay
        } else {
            ChoiceType::LookAndChoose
        };
        let lc = frame.look_choose();

        let mut filter_obj = frame_data.filter;
        filter_obj.char_id_1 = lc.char_id_1;
        filter_obj.char_id_2 = lc.char_id_2;
        filter_obj.char_id_3 = lc.char_id_3;

        let pick_count = i16::from(compiled_choice_count);
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_LOOK_AND_CHOOSE,
                s,
                choice_type,
                filter_obj.to_attr(),
                pick_count,
            ),
            HandlerResult::Suspend
        ) {
            let is_optional = filter_obj.is_optional;
            if is_optional && ctx.choice_index == CHOICE_DONE {
                let cards: Vec<i32> = state.players[p_idx].looked_cards.drain(..).collect();
                state.players[p_idx].deck.extend(cards.into_iter().rev());
                return HandlerResult::Continue;
            }
            return HandlerResult::Suspend;
        }
    }
    if state.debug.debug_mode {
        println!(
            "[DEBUG_LOOK] resolve: choice={} looked_cards={:?} {}",
            ctx.choice_index,
            state.players[p_idx].looked_cards,
            logging::describe_context(ctx)
        );
    }
    interaction_look_choose_resolve::resolve_look_choice(
        state,
        db,
        ctx,
        frame,
        frame_idx,
        p_idx,
        slot_info,
        target_slot,
        rem_dest,
        source_zone,
        reveal_flag,
        dest_discard_v,
        a,
        s,
    )
}
