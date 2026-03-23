use crate::core::enums::*;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn resolve_source_zone(slot: &DecodedSlot) -> Zone {
    if slot.source_zone != Zone::Default {
        return slot.source_zone;
    }

    let ts = slot.target_slot;
    if ts == SLOT_CONTEXT as u8 {
        Zone::Stage
    } else if ts == SLOT_HAND as u8 {
        Zone::Hand
    } else if (SLOT_LIVE_0 as u8..=SLOT_LIVE_2 as u8).contains(&ts) {
        Zone::LiveSet
    } else {
        Zone::Deck
    }
}

pub fn zone_card_count(state: &GameState, player_idx: usize, zone: Zone) -> i32 {
    match zone {
        Zone::Hand => state.players[player_idx].hand.len() as i32,
        Zone::Stage => state.players[player_idx]
            .stage
            .iter()
            .filter(|&&c| c >= 0)
            .count() as i32,
        Zone::LiveSet | Zone::SuccessPile => state.players[player_idx].success_lives.len() as i32,
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
            state.players[player_idx].deck.len() as i32
        }
        Zone::Energy => state.players[player_idx].energy_zone.len() as i32,
        _ => 0,
    }
}

pub fn zone_available_count(state: &GameState, player_idx: usize, zone: Zone) -> i32 {
    match zone {
        Zone::Hand => state.players[player_idx].hand.len() as i32,
        Zone::Stage => state.players[player_idx]
            .stage
            .iter()
            .filter(|&&c| c >= 0)
            .count() as i32,
        Zone::LiveSet | Zone::SuccessPile => state.players[player_idx].success_lives.len() as i32,
        Zone::Energy => state.players[player_idx].energy_zone.len() as i32,
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => {
            state.players[player_idx].deck.len() as i32
        }
        _ => 99,
    }
}

pub fn remove_card_by_index(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    player_idx: usize,
    zone: Zone,
    idx: usize,
    area_idx: i32,
    accumulate_cost: bool,
) -> Option<i32> {
    match zone {
        Zone::Hand => {
            if idx < state.players[player_idx].hand.len() {
                let removed_cid = state.players[player_idx].hand[idx];
                if removed_cid != -1 {
                    if accumulate_cost {
                        if let Some(m) = db.get_member(removed_cid) {
                            ctx.v_accumulated = m.cost as i16;
                        }
                    }
                    state.players[player_idx].hand[idx] = -1;
                    state.players[player_idx].hand.retain(|c| *c != -1);
                    return Some(removed_cid);
                }
            }
            None
        }
        Zone::Stage => {
            let slot = if idx < 3 {
                idx
            } else if area_idx >= 0 {
                area_idx as usize
            } else {
                0
            };
            if let Some(cid) = state.handle_member_leaves_stage(player_idx, slot, db, ctx) {
                if let Some(member) = db.get_member(cid) {
                    ctx.v_accumulated = member.cost as i16;
                }
                return Some(cid);
            }
            None
        }
        Zone::LiveSet | Zone::SuccessPile => state.players[player_idx]
            .success_lives
            .pop()
            .map(|cid| cid as i32),
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => state.players[player_idx]
            .pop_deck_card()
            .map(|cid| cid as i32),
        Zone::Energy => state.players[player_idx]
            .pop_energy_card()
            .map(|cid| cid as i32),
        _ => None,
    }
}

pub fn pop_card_from_zone(
    state: &mut GameState,
    player_idx: usize,
    zone: Zone,
    area_idx: i32,
    db: &CardDatabase,
    ctx: &AbilityContext,
) -> Option<i32> {
    match zone {
        Zone::Hand => state.players[player_idx].pop_hand_card(),
        Zone::Stage => {
            let slot = if area_idx >= 0 { area_idx as usize } else { 0 };
            state.handle_member_leaves_stage(player_idx, slot, db, ctx)
        }
        Zone::LiveSet | Zone::SuccessPile => state.players[player_idx]
            .success_lives
            .pop()
            .map(|cid| cid as i32),
        Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default => state.players[player_idx]
            .pop_deck_card()
            .map(|cid| cid as i32),
        Zone::Energy => state.players[player_idx]
            .pop_energy_card()
            .map(|cid| cid as i32),
        _ => None,
    }
}
