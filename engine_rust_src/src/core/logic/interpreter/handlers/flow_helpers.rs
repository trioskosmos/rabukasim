use crate::core::logic::models::{Ability, AbilityFrame};
use crate::core::logic::{AbilityContext, CardDatabase, Effect, GameState};

fn find_effect_in_abilities<'a, F>(
    abilities: &'a [Ability],
    ab_idx: usize,
    matches_frame: &F,
) -> Option<&'a Effect>
where
    F: Fn(&Effect) -> bool,
{
    abilities
        .get(ab_idx)
        .and_then(|ability| ability.effects.iter().find(|effect| matches_frame(effect)))
        .or_else(|| {
            abilities
                .iter()
                .find_map(|ability| ability.effects.iter().find(|effect| matches_frame(effect)))
        })
}

pub fn current_effect<'a>(
    db: &'a CardDatabase,
    ctx: &AbilityContext,
    frame: &AbilityFrame,
) -> Option<&'a Effect> {
    let ab_idx = usize::try_from(ctx.ability_index).ok()?;
    let matches_frame = |effect: &Effect| {
        effect.runtime_opcode == frame.opcode()
            && effect.runtime_value == frame.value()
            && effect.runtime_attr == frame.attr()
            && effect.runtime_slot == frame.slot()
    };

    db.get_live(ctx.source_card_id)
        .and_then(|card| find_effect_in_abilities(&card.abilities, ab_idx, &matches_frame))
        .or_else(|| {
            db.get_member(ctx.source_card_id)
                .and_then(|card| find_effect_in_abilities(&card.abilities, ab_idx, &matches_frame))
        })
}

pub fn current_effect_by_frame_index<'a>(
    db: &'a CardDatabase,
    ctx: &AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
) -> Option<&'a Effect> {
    let matches_frame = |candidate: &AbilityFrame| {
        candidate.opcode() == frame.opcode()
            && candidate.value() == frame.value()
            && candidate.attr() == frame.attr()
            && candidate.slot() == frame.slot()
    };

    let find_from_card = |abilities: &'a [Ability]| {
        abilities.iter().find_map(|ability| {
            let program = ability.frame_program.as_ref()?;
            let candidate = program.frames.get(frame_idx)?;
            if matches_frame(candidate) {
                ability.effects.get(frame_idx)
            } else {
                None
            }
        })
    };

    db.get_live(ctx.source_card_id)
        .and_then(|card| find_from_card(&card.abilities))
        .or_else(|| {
            db.get_member(ctx.source_card_id)
                .and_then(|card| find_from_card(&card.abilities))
        })
}

pub fn discard_current_yell_pile(state: &mut GameState, p_idx: usize) -> usize {
    let current_yell = std::mem::take(&mut state.players[p_idx].yell_cards);
    let removed_count = current_yell.len();
    for cid in current_yell {
        for slot in 0..3 {
            if let Some(pos) = state.players[p_idx].stage_energy[slot]
                .iter()
                .position(|&energy_cid| energy_cid == cid)
            {
                state.players[p_idx].stage_energy[slot].remove(pos);
                state.players[p_idx].sync_stage_energy_count(slot);
                break;
            }
        }
        state.players[p_idx].push_discard_card(cid);
    }
    removed_count
}
