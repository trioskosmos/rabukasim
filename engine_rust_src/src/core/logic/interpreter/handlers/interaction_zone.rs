use crate::core::enums::Zone;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn normalized_source_zone(zone: Zone) -> Zone {
    if zone == Zone::Default {
        Zone::Discard
    } else {
        zone
    }
}

pub fn collect_zone_cards(state: &GameState, p_idx: usize, source_zone: Zone) -> Vec<i32> {
    match normalized_source_zone(source_zone) {
        Zone::Yell => state.players[p_idx].yell_cards.iter().copied().collect(),
        Zone::Hand => state.players[p_idx].hand.iter().copied().collect(),
        Zone::Deck => state.players[p_idx].deck.iter().copied().collect(),
        _ => state.players[p_idx].discard.iter().copied().collect(),
    }
}

pub fn remove_card_from_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    source_zone: Zone,
    cid: i32,
) -> bool {
    match normalized_source_zone(source_zone) {
        Zone::Yell => {
            if let Some(pos) = state.players[p_idx]
                .yell_cards
                .iter()
                .position(|&x| x == cid)
            {
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
