use crate::core::enums::{ChoiceType, Zone};
use crate::core::logic::constants::TARGET_SLOT_STAGE;
use crate::core::logic::filter::{structured_filter_attr, CardFilter};
use crate::core::logic::interpreter::instruction::DecodedSlot;
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

pub fn draw_zone_cards(
    state: &mut GameState,
    p_idx: usize,
    source_zone: Zone,
    count: usize,
) -> Vec<i32> {
    match normalized_source_zone(source_zone) {
        Zone::Hand => {
            let mut cards = Vec::with_capacity(count);
            for _ in 0..count {
                if let Some(cid) = state.players[p_idx].pop_hand_card() {
                    cards.push(cid);
                }
            }
            cards
        }
        Zone::Discard => {
            let mut cards = Vec::with_capacity(count);
            for _ in 0..count {
                if let Some(cid) = state.players[p_idx].pop_discard_card() {
                    cards.push(cid);
                }
            }
            cards
        }
        Zone::Yell => state.players[p_idx].yell_cards.drain(..).collect(),
        _ => {
            if state.players[p_idx].deck.len() < count {
                state.resolve_deck_refresh(p_idx);
            }
            let mut cards = Vec::with_capacity(count);
            for _ in 0..count.min(state.players[p_idx].deck.len()) {
                if let Some(cid) = state.players[p_idx].pop_deck_card() {
                    cards.push(cid);
                }
            }
            cards
        }
    }
}

pub fn cards_for_source_zone(state: &GameState, target_player: usize, source_zone: Zone) -> &[i32] {
    match source_zone {
        Zone::Hand => state.players[target_player].hand.as_slice(),
        Zone::Discard => state.players[target_player].discard.as_slice(),
        _ => state.players[target_player].stage.as_slice(),
    }
}

pub fn selected_target_key(source_zone: Zone, slot_idx: usize) -> i32 {
    ((source_zone as i32) << 8) | slot_idx as i32
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

pub fn resolved_select_cards_zone(slot_info: DecodedSlot) -> u8 {
    let source_zone = slot_info.source_zone as u8;
    if source_zone != 0 {
        return source_zone;
    }

    match slot_info.target_slot as u8 {
        zone if zone == Zone::Hand as u8 => Zone::Hand as u8,
        zone if zone == Zone::Discard as u8 => Zone::Discard as u8,
        zone if zone == Zone::Deck as u8 => Zone::Deck as u8,
        zone if zone == Zone::Yell as u8 => Zone::Yell as u8,
        _ => Zone::Discard as u8,
    }
}

pub fn selection_source_zone(raw_zone: u8) -> Zone {
    match raw_zone {
        x if x == Zone::Hand as u8 => Zone::Hand,
        x if x == Zone::Discard as u8 => Zone::Discard,
        _ => Zone::Stage,
    }
}

pub fn target_slot_destination(target_slot: u8) -> Zone {
    match target_slot {
        TARGET_SLOT_STAGE => Zone::Stage,
        x if x == Zone::Discard as u8 => Zone::Discard,
        x if x == Zone::Deck as u8 => Zone::Deck,
        x if x == Zone::SuccessPile as u8 => Zone::SuccessPile,
        x if x == Zone::Hand as u8 || x == 0 => Zone::Hand,
        _ => Zone::Hand,
    }
}

pub fn choice_type_for_select_cards_zone(effective_zone: u8) -> ChoiceType {
    match effective_zone {
        6 => ChoiceType::SelectHandDiscard,
        7 => ChoiceType::SelectDiscardPlay,
        _ => ChoiceType::LookAndChoose,
    }
}

pub fn source_zone_for_select_cards(source_zone: u8) -> Zone {
    match if source_zone != 0 { source_zone } else { 7 } {
        4 => Zone::Stage,
        6 => Zone::Hand,
        7 => Zone::Discard,
        8 => Zone::Deck,
        15 => Zone::Yell,
        _ => Zone::Discard,
    }
}

pub fn collect_discard_selection_cards<F>(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    target_p_idx: usize,
    filter_attr: u64,
    remaining: Option<i16>,
    mut is_candidate: F,
) -> Vec<i32>
where
    F: FnMut(&crate::core::logic::card_db::CardRef) -> bool,
{
    state.players[target_p_idx]
        .discard
        .iter()
        .enumerate()
        .filter_map(|(idx, &cid)| {
            let card = db.get_card(cid)?;
            let cost_ok = remaining.map_or(true, |limit| match &card {
                crate::core::logic::card_db::CardRef::Member(member) => member.cost as i16 <= limit,
                _ => true,
            });
            let discard_slot = (target_p_idx as u8, 100 + idx as i16);
            if cost_ok
                && is_candidate(&card)
                && (filter_attr == 0
                    || state.card_matches_filter_with_ctx_at_slot(
                        db,
                        cid,
                        filter_attr,
                        discard_slot,
                        ctx,
                    ))
            {
                Some(cid)
            } else {
                None
            }
        })
        .collect()
}

fn is_trivial_live_discard_filter(filter_attr: u64) -> bool {
    let filter = CardFilter::from_attr(structured_filter_attr(filter_attr));

    if !filter.is_enabled {
        return true;
    }

    (filter.card_type == 0
        || filter.card_type == crate::core::generated_constants::CARD_TYPE_LIVE as u8)
        && (filter.zone_mask == 0
            || filter.zone_mask == crate::core::generated_constants::ZONE_DISCARD as u8)
        && !filter.group_enabled
        && !filter.is_tapped
        && !filter.has_blade_heart
        && !filter.not_has_blade_heart
        && !filter.unique_names
        && !filter.unit_enabled
        && !filter.value_enabled
        && filter.color_mask == 0
        && filter.char_id_1 == 0
        && filter.char_id_2 == 0
        && filter.char_id_3 == 0
        && filter.special_id == 0
        && !filter.is_setsuna
        && !filter.compare_accumulated
        && !filter.keyword_energy
        && !filter.keyword_member
}

pub fn collect_live_discard_selection_cards(
    state: &GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    target_p_idx: usize,
    filter_attr: u64,
) -> Vec<i32> {
    if is_trivial_live_discard_filter(filter_attr) {
        return state.players[target_p_idx]
            .discard
            .iter()
            .copied()
            .filter(|&cid| db.get_live(cid).is_some())
            .collect();
    }

    collect_discard_selection_cards(
        state,
        db,
        ctx,
        target_p_idx,
        filter_attr,
        None,
        |card| matches!(card, crate::core::logic::card_db::CardRef::Live(_)),
    )
}
