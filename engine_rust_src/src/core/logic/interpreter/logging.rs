use crate::core::enums::*;
// use crate::core::generated_constants::*;

pub fn get_opcode_log(op: i32, v: i32, a: i64, _s: i32, result_count: i32) -> Option<String> {
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
        }
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
            Some(format!(
                "Moved {} card(s) from {} to Discard",
                count, source
            ))
        }
        O_LOOK_AND_CHOOSE => {
            let pick_count = (v >> 8) & 0xFF;
            Some(format!("Looked at cards and chose {}", pick_count))
        }
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

pub fn get_opcode_name(op: i32) -> &'static str {
    match op {
        O_DRAW => "DRAW",
        O_ADD_HEARTS => "ADD_HEARTS",
        O_ADD_BLADES => "ADD_BLADES",
        O_MOVE_TO_DISCARD => "MOVE_TO_DISCARD",
        O_LOOK_AND_CHOOSE => "LOOK_AND_CHOOSE",
        O_RECOVER_MEMBER => "RECOVER_MEMBER",
        O_RECOVER_LIVE => "RECOVER_LIVE",
        O_ENERGY_CHARGE => "ENERGY_CHARGE",
        O_TAP_MEMBER => "TAP_MEMBER",
        O_TAP_OPPONENT => "TAP_OPPONENT",
        O_ACTIVATE_MEMBER => "ACTIVATE_MEMBER",
        O_BOOST_SCORE => "BOOST_SCORE",
        O_MOVE_MEMBER => "MOVE_MEMBER",
        O_FORMATION_CHANGE => "FORMATION_CHANGE",
        O_PLACE_UNDER => "PLACE_UNDER",
        O_ADD_STAGE_ENERGY => "ADD_STAGE_ENERGY",
        O_GRANT_ABILITY => "GRANT_ABILITY",
        O_PLAY_MEMBER_FROM_HAND => "PLAY_MEMBER_FROM_HAND",
        O_SET_TAPPED => "SET_TAPPED",
        O_ORDER_DECK => "ORDER_DECK",
        O_REVEAL_UNTIL => "REVEAL_UNTIL",
        O_PAY_ENERGY => "PAY_ENERGY",
        O_SELECT_MEMBER => "SELECT_MEMBER",
        O_META_RULE => "META_RULE",
        O_PLAY_MEMBER_FROM_DISCARD => "PLAY_MEMBER_FROM_DISCARD",
        O_JUMP => "JUMP",
        O_JUMP_IF_FALSE => "JUMP_IF_FALSE",
        O_RETURN => "RETURN",
        O_NOP => "NOP",
        // Condition opcodes
        203 => "COUNT_STAGE",
        204 => "COUNT_HAND",
        208 => "COUNT_GROUP",
        209 => "GROUP_FILTER",
        213 => "COUNT_ENERGY",
        220 => "SCORE_COMPARE",
        226 => "HAS_KEYWORD",
        305 => "MAIN_PHASE",
        306 => "SELECT_MEMBER",
        307 => "SUCCESS_PILE_COUNT",
        308 => "IS_SELF_MOVE",
        309 => "DISCARDED_CARDS",
        310 => "YELL_REVEALED_UNIQUE_COLORS",
        311 => "SYNC_COST",
        312 => "SUM_VALUE",
        313 => "IS_WAIT",
        _ => "UNKNOWN",
    }
}

pub fn describe_bytecode(op: i32, v: i32, a: i64, s: i32) -> String {
    let base_name = get_opcode_name(op);
    let mut details = String::new();

    // Standard human description if available
    if let Some(desc) = get_opcode_log(op, v, a, s, 0) {
        details = format!(" ({})", desc);
    }

    format!(
        "{:<15} | v:{:<4} a:{:<10} s:{:<4}{}",
        base_name, v, a, s, details
    )
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
        C_GROUP_FILTER => "Group Filter".to_string(),
        C_SCORE_TOTAL_CHECK => format!("Score Total >= {}", val),
        305 => "Is Main Phase".to_string(),
        306 => "Target must match filter".to_string(),
        307 => format!("Need {} Success Live card(s)", val),
        308 => "Is Self Move activation".to_string(),
        309 => format!("Discarded {} card(s) this turn", val),
        310 => format!("Need {} unique colors in Yell zone", val),
        311 => format!("Relative Cost comparison (val={})", val),
        312 => format!("Sum Value check (val={})", val),
        313 => "Member is Tapped (WAIT)".to_string(),
        _ => format!("Condition {} (val={})", op, val),
    }
}
