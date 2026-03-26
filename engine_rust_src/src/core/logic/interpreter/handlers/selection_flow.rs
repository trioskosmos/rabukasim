use super::*;
use crate::core::enums::ChoiceType;
use crate::core::logic::interpreter::suspension::finish_pending_interaction;

pub fn cards_for_zone(
    state: &GameState,
    player_idx: usize,
    zone: u8,
) -> &[i32] {
    match zone {
        6 => state.players[player_idx].hand.as_slice(),
        7 => state.players[player_idx].discard.as_slice(),
        _ => state.players[player_idx].stage.as_slice(),
    }
}

pub fn choice_type_for_zone(zone: u8) -> ChoiceType {
    match zone {
        6 => ChoiceType::SelectHandDiscard,
        7 => ChoiceType::SelectDiscardPlay,
        _ => ChoiceType::LookAndChoose,
    }
}

pub fn start_optional_skip(state: &mut GameState) {
    if let Some(execution_id) = state.ui.current_execution_id {
        state.ui.cancelled_execution_ids.insert(execution_id);
    }
    let p_idx = state.current_player as usize;
    state.players[p_idx].looked_cards.clear();
    finish_pending_interaction(state);
}

