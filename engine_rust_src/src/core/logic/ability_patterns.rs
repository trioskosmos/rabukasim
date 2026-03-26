use crate::core::enums::*;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{Ability, CardDatabase, PendingInteraction};

pub const OPTIONAL_MODE_MASK_BASE: i16 = 1900;

pub fn encode_optional_mode_mask(mask: i16) -> i16 {
    OPTIONAL_MODE_MASK_BASE + mask
}

pub fn decode_optional_mode_mask(value: i16) -> Option<i16> {
    if value >= OPTIONAL_MODE_MASK_BASE {
        Some(value - OPTIONAL_MODE_MASK_BASE)
    } else {
        None
    }
}

fn pending_live_card_ids(pi: &PendingInteraction) -> [i32; 2] {
    [pi.card_id, pi.ctx.source_card_id]
}

fn preferred_ability_index(pi: &PendingInteraction) -> Option<usize> {
    usize::try_from(pi.ability_index).ok()
}

fn find_matching_live_ability<'a, F>(
    db: &'a CardDatabase,
    pi: &PendingInteraction,
    mut matches: F,
) -> Option<&'a Ability>
where
    F: FnMut(&Ability) -> bool,
{
    let ability_index = preferred_ability_index(pi);

    for live_card_id in pending_live_card_ids(pi) {
        let Some(card) = db.get_live(live_card_id) else {
            continue;
        };

        if let Some(index) = ability_index {
            if let Some(ability) = card.abilities.get(index) {
                if matches(ability) {
                    return Some(ability);
                }
            }
        }

        if let Some(ability) = card.abilities.iter().find(|ability| matches(ability)) {
            return Some(ability);
        }
    }

    None
}

pub fn pending_live_ability<'a>(
    db: &'a CardDatabase,
    pi: &PendingInteraction,
) -> Option<&'a Ability> {
    fn ability_uses_opcode(ability: &Ability, opcode: i32) -> bool {
        ability
            .frames()
            .iter()
            .any(|frame| frame.opcode() == opcode)
    }

    fn ability_matches_pending(ability: &Ability, pi: &PendingInteraction) -> bool {
        if pi.choice_type == ChoiceType::SelectMode
            && is_distinct_optional_mode_live_ability(ability)
        {
            return true;
        }

        ability_uses_opcode(ability, pi.effect_opcode)
            || (pi.choice_type == ChoiceType::SelectMember
                && ability_uses_opcode(ability, O_SELECT_MEMBER))
            || (pi.choice_type == ChoiceType::SelectMode
                && ability_uses_opcode(ability, O_SELECT_MODE))
    }

    if matches!(
        pi.choice_type,
        ChoiceType::SelectMode | ChoiceType::RecovM | ChoiceType::RecovL | ChoiceType::Optional
    ) {
        if let Some(ability) =
            find_matching_live_ability(db, pi, is_distinct_optional_mode_live_ability)
        {
            return Some(ability);
        }
    }

    find_matching_live_ability(db, pi, |ability| ability_matches_pending(ability, pi))
}

pub fn pending_member_ability<'a>(
    db: &'a CardDatabase,
    source_card_id: i32,
    ability_index: i16,
) -> Option<&'a Ability> {
    let ability_index = usize::try_from(ability_index).ok()?;
    db.get_member(source_card_id)?.abilities.get(ability_index)
}

pub fn is_distinct_optional_mode_live_ability(ability: &Ability) -> bool {
    let frames = ability.frames();
    let has_select_mode = frames.iter().any(|frame| frame.opcode() == O_SELECT_MODE);
    ability.trigger == TriggerType::OnLiveSuccess
        && frames.iter().any(|frame| frame.opcode() == O_ENERGY_CHARGE)
        && frames
            .iter()
            .any(|frame| frame.opcode() == O_RECOVER_MEMBER)
        && !has_select_mode
}

pub fn pending_optional_mode_mask(db: &CardDatabase, pi: &PendingInteraction) -> Option<i16> {
    let ability = pending_live_ability(db, pi)?;
    if !is_distinct_optional_mode_live_ability(ability) {
        return None;
    }

    if let Some(mask) = decode_optional_mode_mask(pi.ctx.v_accumulated) {
        return Some(mask);
    }

    if pi.choice_type == ChoiceType::SelectMode && !pi.ctx.selected_cards.is_empty() {
        let option_count = ability.modal_option_count();
        let mut mask = optional_mode_mask_for_count(option_count);
        for &selected in &pi.ctx.selected_cards {
            if selected >= 0 && (selected as usize) < option_count {
                mask &= !(1i16 << selected);
            }
        }
        if mask > 0 {
            return Some(mask);
        }
    }

    let is_initial_optional_effect = ability
        .frames()
        .iter()
        .any(|frame| frame.opcode() == pi.effect_opcode);
    if is_initial_optional_effect {
        Some(optional_mode_mask_for_count(ability.modal_option_count()))
    } else {
        None
    }
}

fn optional_mode_mask_for_count(option_count: usize) -> i16 {
    if option_count >= i16::BITS as usize {
        i16::MAX
    } else {
        (1i16 << option_count) - 1
    }
}

pub fn optional_mode_effect<'a>(
    ability: &'a Ability,
    mask: i16,
    choice_idx: i32,
) -> Option<(AbilityFrame, i16)> {
    let effect_index = usize::try_from(choice_idx).ok()?;
    let selected_bit = 1i16.checked_shl(choice_idx as u32)?;
    if (mask & selected_bit) == 0 {
        return None;
    }

    let frame = ability
        .get_modal_option_frames(effect_index)?
        .into_iter()
        .next()?;
    Some((frame, mask & !selected_bit))
}

pub fn pending_targeted_live_heart_bonus(
    db: &CardDatabase,
    pi: &PendingInteraction,
) -> Option<(u64, u8)> {
    let ability = pending_live_ability(db, pi)?;
    let frames = ability.frames();
    if ability.trigger != TriggerType::OnLiveStart
        || frames.len() != 5
        || frames
            .iter()
            .filter(|frame| frame.opcode() == O_SELECT_MEMBER)
            .count()
            != 1
        || frames
            .iter()
            .filter(|frame| frame.opcode() == O_ADD_HEARTS)
            .count()
            != 1
        || frames.get(0).map(|frame| frame.opcode()) != Some(O_DRAW)
        || frames.get(1).map(|frame| frame.opcode()) != Some(O_MOVE_TO_DISCARD)
        || frames.get(4).map(|frame| frame.opcode()) != Some(O_BOOST_SCORE)
    {
        return None;
    }

    let is_target_selection_step = pi.effect_opcode == O_SELECT_MEMBER
        || pi.choice_type == ChoiceType::SelectMember
        || (pi.filter_attr & !0x3) == frames.get(2)?.attr();
    let is_vacuous_discard_step =
        pi.effect_opcode == O_MOVE_TO_DISCARD && pi.choice_type == ChoiceType::SelectHandDiscard;
    if !is_target_selection_step && !is_vacuous_discard_step {
        return None;
    }

    let select_effect = frames.get(2)?;
    let follow_up = frames.get(3)?;
    Some((select_effect.attr(), follow_up.attr() as u8))
}

pub fn is_optional_live_start_discard_count_ability(ability: &Ability) -> bool {
    let frames = ability.frames();
    ability.trigger == TriggerType::OnLiveStart
        && frames
            .first()
            .map(|frame| frame.opcode() == O_SELECT_CARDS && frame.value() == 99)
            .unwrap_or(false)
        && frames.iter().any(|frame| {
            frame.opcode() == O_ADD_BLADES
                && frame
                    .components()
                    .params
                    .and_then(|params| params.get("per_card"))
                    .and_then(|value| value.as_str())
                    == Some("DISCARD_COUNT")
        })
}

pub fn should_skip_inline_live_precheck(ability: &Ability) -> bool {
    if is_distinct_optional_mode_live_ability(ability) {
        return true;
    }

    let condition_blocks = ability.raw_text.matches("CONDITION:").count();
    ability.trigger == TriggerType::OnLiveStart
        && condition_blocks > ability.conditions.len().max(1)
}
