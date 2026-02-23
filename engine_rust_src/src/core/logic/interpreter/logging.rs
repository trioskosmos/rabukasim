use crate::core::generated_constants::*;
use crate::core::enums::*;

pub fn get_opcode_log(op: i32, v: i32, a: i32, _s: i32, result_count: i32) -> Option<String> {
    match op {
        O_DRAW => Some(format!("Draw {} card(s)", v)),
        O_ADD_HEARTS => {
            let color_str = match a {
                1 => "HEART_RED",
                2 => "HEART_YELLOW",
                3 => "HEART_GREEN",
                4 => "HEART_BLUE",
                5 => "HEART_PURPLE",
                6 => "HEART_PINK",
                _ => "HEART_WILD",
            };
            Some(format!("Added +{} {}", v, color_str))
        },
        O_ADD_BLADES => Some(format!("Added +{} BLADE", v)),
        O_MOVE_TO_DISCARD => {
            let count = if result_count > 0 { result_count } else { v };
            let source = match (a >> 12) & 0x0F {
                6 => "Hand",
                0 => "Deck",
                4 => "Stage",
                13 => "Success Live",
                3 => "Energy Zone",
                _ => "Zone",
            };
            Some(format!("Moved {} card(s) from {} to Discard", count, source))
        },
        O_LOOK_AND_CHOOSE => {
             let pick_count = (v >> 8) & 0xFF;
             Some(format!("Looked at cards and chose {}", pick_count))
        },
        O_RECOVER_MEMBER => Some(format!("Recovered {} member(s) from Discard", v)),
        O_RECOVER_LIVE => Some(format!("Recovered {} live card(s) from Discard", v)),
        O_ENERGY_CHARGE => Some(format!("Charge {} Energy", v)),
        O_TAP_MEMBER => Some("Tapped member".to_string()),
        O_TAP_OPPONENT => Some("Tapped opponent member".to_string()),
        O_ACTIVATE_MEMBER => Some("Activated member/energy".to_string()),
        O_BOOST_SCORE => Some(format!("Score +{}", v)),
        O_MOVE_MEMBER | O_FORMATION_CHANGE => Some("Moved member/Changed formation".to_string()),
        O_PLACE_UNDER => Some("Placed card under member (Energy)".to_string()),
        O_ADD_STAGE_ENERGY => Some(format!("Added {} energy to stage slot", v)),
        O_GRANT_ABILITY => Some("Granted ability to member(s)".to_string()),
        O_PLAY_MEMBER_FROM_HAND => Some("Played member from hand via effect".to_string()),
        O_SET_TAPPED => Some(format!("Set member tapped state to {}", v != 0)),
        O_ORDER_DECK => Some(format!("Reordered top {} cards of deck", v)),
        O_REVEAL_UNTIL => Some("Revealed cards until condition met".to_string()),
        _ => None,
    }
}

pub fn trigger_as_str(t: TriggerType) -> &'static str {
    match t {
        TriggerType::None => "NONE",
        TriggerType::OnPlay => "OnPlay",
        TriggerType::OnLiveStart => "OnLiveStart",
        TriggerType::OnLiveSuccess => "OnLiveSuccess",
        TriggerType::TurnStart => "TurnStart",
        TriggerType::TurnEnd => "TurnEnd",
        TriggerType::Constant => "Constant",
        TriggerType::Activated => "Activated",
        TriggerType::OnLeaves => "OnLeaves",
        TriggerType::OnReveal => "OnReveal",
        TriggerType::OnPositionChange => "OnPositionChange",
    }
}

pub fn describe_condition(op: i32, val: i32, _attr: u64) -> String {
    match op {
        C_TURN_1 => "Turn is 1".to_string(),
        C_HAS_MEMBER => "Has specific member".to_string(),
        C_COUNT_STAGE => format!("Need {} member(s) on Stage", val),
        C_COUNT_HAND => format!("Need {} card(s) in Hand", val),
        C_COUNT_ENERGY => format!("Need {} Energy", val),
        C_IS_TAPPED => "Member must be Tapped".to_string(),
        C_IS_ACTIVE => "Member must be Active (not Tapped)".to_string(),
        C_LIVE_PERFORMED => "Live has been performed".to_string(),
        C_IS_PLAYER => "Is Player's turn".to_string(),
        C_IS_OPPONENT => "Is Opponent's turn".to_string(),
        C_COUNT_BLADES => format!("Need {} Blade(s)", val),
        C_COUNT_HEARTS => format!("Need {} Heart(s)", val),
        _ => format!("Condition {} (val={}) not met", op, val),
    }
}
