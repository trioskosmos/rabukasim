use crate::core::enums::*;
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

pub fn pending_live_ability<'a>(db: &'a CardDatabase, pi: &PendingInteraction) -> Option<&'a Ability> {
    fn ability_matches_pending(ability: &Ability, pi: &PendingInteraction) -> bool {
        if pi.choice_type == ChoiceType::SelectMode && is_distinct_optional_mode_live_ability(ability) {
            return true;
        }

        ability.effects.iter().any(|effect| {
            effect.runtime_opcode == pi.effect_opcode
                || (pi.choice_type == ChoiceType::SelectMember && effect.runtime_opcode == O_SELECT_MEMBER)
                || (pi.choice_type == ChoiceType::SelectMode && effect.runtime_opcode == O_SELECT_MODE)
        })
    }

    for live_card_id in [pi.card_id, pi.ctx.source_card_id] {
        let Some(card) = db.get_live(live_card_id) else {
            continue;
        };

        if let Ok(ability_index) = usize::try_from(pi.ability_index) {
            if let Some(ability) = card.abilities.get(ability_index) {
                if ability_matches_pending(ability, pi) {
                    return Some(ability);
                }
            }
        }

        if let Some(ability) = card
            .abilities
            .iter()
            .find(|ability| ability_matches_pending(ability, pi))
        {
            return Some(ability);
        }
    }

    None
}

pub fn pending_member_ability<'a>(db: &'a CardDatabase, source_card_id: i32, ability_index: i16) -> Option<&'a Ability> {
    let ability_index = usize::try_from(ability_index).ok()?;
    db.get_member(source_card_id)?.abilities.get(ability_index)
}

fn is_wait_energy_effect(effect: &crate::core::logic::Effect) -> bool {
    effect.runtime_opcode == O_ENERGY_CHARGE
        && effect
            .params
            .get("wait")
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
}

fn is_recover_member_from_discard(effect: &crate::core::logic::Effect) -> bool {
    effect.runtime_opcode == O_RECOVER_MEMBER
        && effect
            .params
            .get("source")
            .and_then(|value| value.as_str())
            .map(|value| value.eq_ignore_ascii_case("discard"))
            .unwrap_or(false)
}

pub fn is_distinct_optional_mode_live_ability(ability: &Ability) -> bool {
    ability.trigger == TriggerType::OnLiveSuccess
        && ability.effects.len() == 2
        && ability.effects.iter().all(|effect| effect.is_optional)
        && is_wait_energy_effect(&ability.effects[0])
        && is_recover_member_from_discard(&ability.effects[1])
}

pub fn pending_optional_mode_mask(db: &CardDatabase, pi: &PendingInteraction) -> Option<i16> {
    let ability = pending_live_ability(db, pi)?;
    if !is_distinct_optional_mode_live_ability(ability) {
        return None;
    }

    if let Some(mask) = decode_optional_mode_mask(pi.ctx.v_accumulated) {
        return Some(mask);
    }

    let is_initial_optional_effect = ability
        .effects
        .iter()
        .any(|effect| effect.runtime_opcode == pi.effect_opcode);
    if is_initial_optional_effect {
        Some((1i16 << ability.effects.len()) - 1)
    } else {
        None
    }
}

pub fn optional_mode_effect<'a>(ability: &'a Ability, mask: i16, choice_idx: i32) -> Option<(&'a crate::core::logic::Effect, i16)> {
    let effect_index = usize::try_from(choice_idx).ok()?;
    let selected_bit = 1i16.checked_shl(choice_idx as u32)?;
    if (mask & selected_bit) == 0 {
        return None;
    }

    let effect = ability.effects.get(effect_index)?;
    Some((effect, mask & !selected_bit))
}

pub fn pending_targeted_live_heart_bonus(db: &CardDatabase, pi: &PendingInteraction) -> Option<(u64, u8)> {
    let ability = pending_live_ability(db, pi)?;
    if ability.trigger != TriggerType::OnLiveStart
        || ability.effects.len() != 5
        || ability.effects.iter().filter(|effect| effect.runtime_opcode == O_SELECT_MEMBER).count() != 1
        || ability.effects.iter().filter(|effect| effect.runtime_opcode == O_ADD_HEARTS).count() != 1
        || ability.effects.get(0).map(|effect| effect.runtime_opcode) != Some(O_DRAW)
        || ability.effects.get(1).map(|effect| effect.runtime_opcode) != Some(O_MOVE_TO_DISCARD)
        || ability.effects.get(4).map(|effect| effect.runtime_opcode) != Some(O_BOOST_SCORE)
    {
        return None;
    }

    let is_target_selection_step = pi.effect_opcode == O_SELECT_MEMBER
        || pi.choice_type == ChoiceType::SelectMember
        || (pi.filter_attr & !0x3) == ability.effects.get(2)?.runtime_attr;
    let is_vacuous_discard_step = pi.effect_opcode == O_MOVE_TO_DISCARD
        && pi.choice_type == ChoiceType::SelectHandDiscard;
    if !is_target_selection_step && !is_vacuous_discard_step {
        return None;
    }

    let select_effect = ability.effects.get(2)?;
    let follow_up = ability.effects.get(3)?;
    Some((select_effect.runtime_attr, follow_up.runtime_attr as u8))
}

pub fn is_optional_live_start_discard_count_ability(ability: &Ability) -> bool {
    ability.trigger == TriggerType::OnLiveStart
        && ability
            .bytecode
            .chunks(5)
            .next()
            .map(|chunk| chunk.first().copied() == Some(O_SELECT_CARDS) && chunk.get(1).copied() == Some(99))
            .unwrap_or(false)
        && ability.effects.iter().any(|effect| {
            effect.runtime_opcode == O_ADD_BLADES
                && effect
                    .params
                    .get("per_card")
                    .and_then(|value| value.as_str())
                    == Some("DISCARD_COUNT")
        })
}

pub fn should_skip_inline_live_precheck(ability: &Ability) -> bool {
    if is_distinct_optional_mode_live_ability(ability) {
        return true;
    }

    let condition_blocks = ability.raw_text.matches("CONDITION:").count();
    ability.trigger == TriggerType::OnLiveStart && condition_blocks > ability.conditions.len().max(1)
}