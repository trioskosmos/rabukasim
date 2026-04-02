use crate::core::*;

use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn update_live_score_snapshot(
    state: &mut GameState,

    player_idx: usize,

    source_card_id: i32,

    area_idx: i16,

    new_score: i32,
) -> bool {
    let score_value = serde_json::Value::from(new_score.max(0));

    for results in [
        &mut state.ui.performance_results,
        &mut state.ui.last_performance_results,
    ] {
        let Some(serde_json::Value::Object(map)) = results.get_mut(&(player_idx as u8)) else {
            continue;
        };

        let Some(serde_json::Value::Array(lives)) = map.get_mut("lives") else {
            continue;
        };

        let mut updated = false;

        for live_res in lives.iter_mut() {
            let Some(live_map) = live_res.as_object_mut() else {
                continue;
            };

            let card_matches = live_map
                .get("card_id")
                .and_then(|value| value.as_i64())
                .map(|value| value as i32 == source_card_id)
                .unwrap_or(false);

            let slot_matches = live_map
                .get("slot_idx")
                .and_then(|value| value.as_i64())
                .map(|value| value as i16 == area_idx)
                .unwrap_or(false);

            if card_matches || slot_matches {
                live_map.insert("score".to_string(), score_value.clone());

                updated = true;
            }
        }

        if updated {
            return true;
        }
    }

    false
}

pub fn inline_value_ge_threshold(db: &CardDatabase, ctx: &AbilityContext) -> Option<i32> {
    let abilities = if let Some(card) = db.get_live(ctx.source_card_id) {
        card.abilities.as_slice()
    } else {
        db.get_member(ctx.source_card_id)?.abilities.as_slice()
    };

    let ability = usize::try_from(ctx.ability_index)
        .ok()
        .and_then(|ability_index| abilities.get(ability_index))
        .or_else(|| {
            abilities
                .iter()
                .find(|ability| ability.raw_text.contains("VALUE_GE("))
        })?;

    let has_structured_branching = ability.frames().iter().any(|frame| {
        let opcode = frame.opcode();
        opcode == O_JUMP_IF_FALSE
            || opcode == O_JUMP
            || crate::core::logic::interpreter::is_condition_opcode(opcode)
    });
    if has_structured_branching {
        return None;
    }

    let raw_text = ability.raw_text.as_str();
    let marker = "VALUE_GE(";
    let start = raw_text.find(marker)? + marker.len();
    let tail = &raw_text[start..];
    let comma = tail.find(',')?;
    let close = tail[comma + 1..].find(')')? + comma + 1;

    tail[comma + 1..close].trim().parse::<i32>().ok()
}

pub fn source_ability<'a>(
    db: &'a CardDatabase,
    ctx: &AbilityContext,
) -> Option<&'a crate::core::logic::Ability> {
    let ability_index = usize::try_from(ctx.ability_index).ok()?;
    db.get_member(ctx.source_card_id)
        .and_then(|card| card.abilities.get(ability_index))
        .or_else(|| {
            db.get_live(ctx.source_card_id)
                .and_then(|card| card.abilities.get(ability_index))
        })
}

pub fn tap_opponent_chooser_player(db: &CardDatabase, ctx: &AbilityContext) -> u8 {
    let _chooser_is_activator = source_ability(db, ctx)
        .map(|ability| {
            let mut saw_tap_member = false;

            if let Some(program) = &ability.frame_program {
                for frame in &program.frames {
                    match frame.opcode() {
                        O_TAP_MEMBER | O_MOVE_MEMBER => {
                            saw_tap_member = true
                        }
                        O_TAP_OPPONENT if saw_tap_member => return true,
                        _ => {}
                    }
                }
            }

            false
        })
        .unwrap_or(false);
    ctx.activator_id
}
