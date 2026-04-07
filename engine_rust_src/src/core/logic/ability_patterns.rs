use crate::core::enums::*;
use crate::core::logic::heart_semantics::{decode_heart_type_from_params, decode_heart_type_from_text};
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{Ability, CardDatabase, PendingInteraction};

fn ability_uses_opcode(ability: &Ability, opcode: i32) -> bool {
    ability
        .resolved_frames()
        .iter()
        .any(|frame| frame.opcode() == opcode)
}

fn modal_option_has_opcode(ability: &Ability, option_idx: usize, opcode: i32) -> bool {
    ability
        .get_modal_option_frames(option_idx)
        .map(|frames| frames.iter().any(|frame| frame.opcode() == opcode))
        .unwrap_or(false)
}

fn structured_targeted_live_heart_bonus_signature(ability: &Ability) -> Option<(u64, u8)> {
    if ability.trigger != TriggerType::OnLiveStart {
        return None;
    }

    let frames = ability.resolved_frames();
    if frames.iter().any(|frame| frame.opcode() == O_SELECT_MODE) {
        return None;
    }

    let select_idx = frames.iter().position(|frame| frame.opcode() == O_SELECT_MEMBER)?;
    let (heart_idx, heart_frame) = frames
        .iter()
        .enumerate()
        .skip(select_idx + 1)
        .find(|(_, frame)| frame.opcode() == O_ADD_HEARTS)?;

    if !frames
        .iter()
        .skip(heart_idx + 1)
        .any(|frame| frame.opcode() == O_BOOST_SCORE)
    {
        return None;
    }

    let select_frame = &frames[select_idx];
    let heart_components = heart_frame.components();
    let heart_color = decode_heart_type_from_params(heart_components.params)
        .map(|color| color as u8)
        .or_else(|| match heart_components.resolved_filter_attr() {
            0..=6 => Some(heart_components.resolved_filter_attr() as u8),
            7 => Some(6),
            _ => decode_heart_type_from_text(&ability.raw_text).map(|color| color as u8),
        })?;

    Some((select_frame.attr(), heart_color))
}

fn source_group_backfilled_filter_attr(
    db: &CardDatabase,
    live_card_id: i32,
    filter_attr: u64,
) -> u64 {
    if filter_attr == 0 {
        return filter_attr;
    }

    let mut filter = crate::core::logic::filter::structured_filter_from_attr(filter_attr);
    if !filter.group_enabled || filter.group_id != 0 || filter.unit_enabled {
        return filter_attr;
    }

    let Some(live) = db.get_live(live_card_id) else {
        return filter_attr;
    };
    if live.groups.len() != 1 {
        return filter_attr;
    }

    let passthrough = crate::core::logic::filter::passthrough_filter_attr(filter_attr);
    filter.group_id = live.groups[0];
    filter.to_attr() | passthrough
}

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

fn find_matching_live_ability<'a, F>(
    db: &'a CardDatabase,
    pi: &PendingInteraction,
    mut matches: F,
) -> Option<&'a Ability>
where
    F: FnMut(&Ability) -> bool,
{
    let preferred_index = usize::try_from(pi.ability_index).ok();

    for live_card_id in [
        if pi.ability_card_id >= 0 {
            pi.ability_card_id
        } else {
            pi.card_id
        },
        if pi.ctx.ability_card_id >= 0 {
            pi.ctx.ability_card_id
        } else {
            pi.ctx.source_card_id
        },
    ] {
        let Some(card) = db.get_live(live_card_id) else {
            continue;
        };

        if let Some(index) = preferred_index {
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
    let preferred_index = usize::try_from(pi.ability_index).ok()?;
    for live_card_id in [
        if pi.ability_card_id >= 0 {
            pi.ability_card_id
        } else {
            pi.card_id
        },
        if pi.ctx.ability_card_id >= 0 {
            pi.ctx.ability_card_id
        } else {
            pi.ctx.source_card_id
        },
    ] {
        let Some(card) = db.get_live(live_card_id) else {
            continue;
        };

        if let Some(ability) = card.abilities.get(preferred_index) {
            if matches!(
                pi.choice_type,
                ChoiceType::SelectMode | ChoiceType::RecovM | ChoiceType::RecovL | ChoiceType::Optional
            ) && is_distinct_optional_mode_live_ability(ability)
            {
                return Some(ability);
            }

            if ability_uses_opcode(ability, pi.effect_opcode)
                || (pi.choice_type == ChoiceType::SelectMember
                    && ability_uses_opcode(ability, O_SELECT_MEMBER))
                || (pi.choice_type == ChoiceType::SelectMode
                    && ability_uses_opcode(ability, O_SELECT_MODE))
            {
                return Some(ability);
            }
        }
    }

    if matches!(
        pi.choice_type,
        ChoiceType::SelectMode | ChoiceType::RecovM | ChoiceType::RecovL | ChoiceType::Optional
    ) {
        if let Some(ability) = find_matching_live_ability(db, pi, |ability| {
            is_distinct_optional_mode_live_ability(ability)
                && ability_uses_opcode(ability, pi.effect_opcode)
        }) {
            return Some(ability);
        }
    }

    find_matching_live_ability(db, pi, |ability| {
        ability_uses_opcode(ability, pi.effect_opcode)
            || (pi.choice_type == ChoiceType::SelectMember
                && ability_uses_opcode(ability, O_SELECT_MEMBER))
            || (pi.choice_type == ChoiceType::SelectMode
                && ability_uses_opcode(ability, O_SELECT_MODE))
    })
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
    if ability.trigger == TriggerType::OnLiveSuccess
        && ability.modal_option_count() >= 2
        && modal_option_has_opcode(ability, 0, O_ENERGY_CHARGE)
        && modal_option_has_opcode(ability, 1, O_RECOVER_MEMBER)
    {
        return true;
    }

    let frames = ability.resolved_frames();
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
        let mut mask = if option_count >= i16::BITS as usize {
            i16::MAX
        } else {
            (1i16 << option_count) - 1
        };
        for &selected in &pi.ctx.selected_cards {
            if selected >= 0 && (selected as usize) < option_count {
                mask &= !(1i16 << selected);
            }
        }
        if mask > 0 {
            return Some(mask);
        }
    }

    let is_initial_optional_effect = if ability.trigger == TriggerType::OnLiveSuccess
        && ability.modal_option_count() >= 2
        && modal_option_has_opcode(ability, 0, O_ENERGY_CHARGE)
        && modal_option_has_opcode(ability, 1, O_RECOVER_MEMBER)
    {
        (0..ability.modal_option_count()).any(|option_idx| {
            modal_option_has_opcode(ability, option_idx, pi.effect_opcode)
        })
    } else {
        ability
            .resolved_frames()
            .iter()
            .any(|frame| frame.opcode() == pi.effect_opcode)
    };
    if is_initial_optional_effect {
        Some(if ability.modal_option_count() >= i16::BITS as usize {
            i16::MAX
        } else {
            (1i16 << ability.modal_option_count()) - 1
        })
    } else {
        None
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
    let (filter_attr, heart_color_idx) = structured_targeted_live_heart_bonus_signature(ability)?;
    let live_card_id = [
        if pi.ability_card_id >= 0 {
            pi.ability_card_id
        } else {
            pi.card_id
        },
        if pi.ctx.ability_card_id >= 0 {
            pi.ctx.ability_card_id
        } else {
            pi.ctx.source_card_id
        },
    ]
    .into_iter()
        .find(|cid| db.get_live(*cid).is_some())
        .unwrap_or(pi.card_id);
    let filter_attr = source_group_backfilled_filter_attr(db, live_card_id, filter_attr);

    let current_frame_matches = ability
        .get_frame(pi.ctx.program_counter as usize)
        .map(|frame| {
            frame.opcode() == O_SELECT_MEMBER
                && (frame
                    .components()
                    .normalized_select_member_filter_attr_with_source(db, &pi.ctx)
                    & !0x3)
                    == (filter_attr & !0x3)
        })
        .unwrap_or(false)
        || ability.resolved_frames().iter().any(|frame| {
            frame.opcode() == O_SELECT_MEMBER
                && (frame
                    .components()
                    .normalized_select_member_filter_attr_with_source(db, &pi.ctx)
                    & !0x3)
                    == (filter_attr & !0x3)
        });
    if !(matches!(pi.choice_type, ChoiceType::SelectMember)
        && pi.effect_opcode == O_SELECT_MEMBER
        && current_frame_matches)
    {
        return None;
    }

    Some((filter_attr, heart_color_idx))
}

pub fn is_optional_live_start_discard_count_ability(ability: &Ability) -> bool {
    let frames = ability.resolved_frames();
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
    if is_distinct_optional_mode_live_ability(ability)
        || structured_targeted_live_heart_bonus_signature(ability).is_some()
        || is_optional_live_start_discard_count_ability(ability)
    {
        return true;
    }

    let condition_blocks = ability.raw_text.matches("CONDITION:").count();
    ability.trigger == TriggerType::OnLiveStart
        && condition_blocks > ability.conditions.len().max(1)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::logic::{AbilityContext, Effect, PendingInteraction};
    use serde_json::json;

    #[test]
    fn distinct_optional_live_mode_detects_structured_modal_options() {
        let ability = Ability {
            trigger: TriggerType::OnLiveSuccess,
            effects: vec![Effect {
                modal_options: json!([
                    [{ "effect_type": EffectType::EnergyCharge }],
                    [{ "effect_type": EffectType::RecoverMember }]
                ]),
                ..Default::default()
            }],
            ..Default::default()
        };

        assert!(is_distinct_optional_mode_live_ability(&ability));
    }

    #[test]
    fn pending_optional_mode_mask_uses_structured_modal_option_opcodes() {
        let ability = Ability {
            trigger: TriggerType::OnLiveSuccess,
            effects: vec![Effect {
                modal_options: json!([
                    [{ "effect_type": EffectType::EnergyCharge }],
                    [{ "effect_type": EffectType::RecoverMember }]
                ]),
                ..Default::default()
            }],
            ..Default::default()
        };

        let mut db = CardDatabase::default();
        db.lives.insert(
            9000,
            crate::core::logic::LiveCard {
                card_id: 9000,
                abilities: vec![ability],
                ..Default::default()
            },
        );

        let pi = PendingInteraction {
            card_id: 9000,
            ability_card_id: 9000,
            ability_index: 0,
            effect_opcode: O_ENERGY_CHARGE,
            choice_type: ChoiceType::SelectMode,
            ctx: AbilityContext {
                player_id: 0,
                source_card_id: 9000,
                ability_card_id: 9000,
                ability_index: 0,
                ..Default::default()
            },
            ..Default::default()
        };

        assert_eq!(pending_optional_mode_mask(&db, &pi), Some(3));
    }

    #[test]
    fn pending_optional_mode_mask_does_not_hijack_sibling_select_mode_ability() {
        let structured_optional = Ability {
            trigger: TriggerType::OnLiveSuccess,
            effects: vec![Effect {
                modal_options: json!([
                    [{ "effect_type": EffectType::EnergyCharge }],
                    [{ "effect_type": EffectType::RecoverMember }]
                ]),
                ..Default::default()
            }],
            ..Default::default()
        };

        let explicit_select_mode = Ability {
            trigger: TriggerType::OnLiveSuccess,
            frame_program: Some(crate::core::logic::FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_SELECT_MODE, 2, 0, 0, false),
                    AbilityFrame::new(O_RETURN, 0, 0, 0, false),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let mut db = CardDatabase::default();
        db.lives.insert(
            9001,
            crate::core::logic::LiveCard {
                card_id: 9001,
                abilities: vec![structured_optional, explicit_select_mode],
                ..Default::default()
            },
        );

        let pi = PendingInteraction {
            card_id: 9001,
            ability_card_id: 9001,
            ability_index: 1,
            effect_opcode: O_SELECT_MODE,
            choice_type: ChoiceType::SelectMode,
            ctx: AbilityContext {
                player_id: 0,
                source_card_id: 9001,
                ability_card_id: 9001,
                ability_index: 1,
                ..Default::default()
            },
            ..Default::default()
        };

        assert_eq!(pending_optional_mode_mask(&db, &pi), None);
        assert!(
            pending_live_ability(&db, &pi)
                .map(|ability| ability_uses_opcode(ability, O_SELECT_MODE))
                .unwrap_or(false)
        );
    }

    #[test]
    fn pending_targeted_live_heart_bonus_accepts_structured_ordered_frames() {
        let ability = Ability {
            trigger: TriggerType::OnLiveStart,
            frame_program: Some(crate::core::logic::FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_DRAW, 1, 0, 0, false),
                    AbilityFrame::new(O_SELECT_MEMBER, 1, 0x1234, 0, false),
                    AbilityFrame::new(O_ADD_HEARTS, 1, 5, 0, false),
                    AbilityFrame::new(O_BOOST_SCORE, 1, 0, 0, false),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let mut db = CardDatabase::default();
        db.lives.insert(
            9010,
            crate::core::logic::LiveCard {
                card_id: 9010,
                abilities: vec![ability],
                ..Default::default()
            },
        );

        let pi = PendingInteraction {
            card_id: 9010,
            ability_card_id: 9010,
            ability_index: 0,
            effect_opcode: O_SELECT_MEMBER,
            choice_type: ChoiceType::SelectMember,
            ctx: AbilityContext {
                player_id: 0,
                source_card_id: 9010,
                ability_card_id: 9010,
                ability_index: 0,
                trigger_type: TriggerType::OnLiveStart,
                ..Default::default()
            },
            ..Default::default()
        };

        assert_eq!(pending_targeted_live_heart_bonus(&db, &pi), Some((0x1234, 5)));
    }

    #[test]
    fn skip_inline_live_precheck_for_structured_targeted_bonus() {
        let ability = Ability {
            trigger: TriggerType::OnLiveStart,
            frame_program: Some(crate::core::logic::FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_SELECT_MEMBER, 1, 0x1234, 0, false),
                    AbilityFrame::new(O_ADD_HEARTS, 1, 2, 0, false),
                    AbilityFrame::new(O_BOOST_SCORE, 1, 0, 0, false),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        assert!(should_skip_inline_live_precheck(&ability));
    }
}
