use crate::core::enums::ChoiceType;
use crate::core::enums::*;
// use crate::core::generated_constants::*;

pub fn get_opcode_log(op: i32, v: i32, a: i64, _s: i32, result_count: i32) -> Option<String> {
    match op {
        O_DRAW => Some(format!("Draw {} card(s)", v)),
        O_ADD_HEARTS => {
            let color_str = match a {
                0 => "HEART_PINK",
                1 => "HEART_RED",
                2 => "HEART_YELLOW",
                3 => "HEART_GREEN",
                4 => "HEART_BLUE",
                5 => "HEART_PURPLE",
                6 => "HEART_ANY",
                _ => "HEART_UNKNOWN",
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
        O_REDUCE_HEART_REQ => {
            let color_str = match _s {
                0 => "PINK", 1 => "RED", 2 => "YELLOW", 3 => "GREEN", 4 => "BLUE", 5 => "PURPLE", 6 => "ANY",
                _ => "UNKNOWN",
            };
            Some(format!("Reduced {} heart requirement by {}", color_str, v))
        }
        O_TRANSFORM_HEART => {
            let src_str = match a {
                0 => "PINK", 1 => "RED", 2 => "YELLOW", 3 => "GREEN", 4 => "BLUE", 5 => "PURPLE", 6 => "ANY",
                _ => "UNKNOWN",
            };
            let dst_str = match _s {
                0 => "PINK", 1 => "RED", 2 => "YELLOW", 3 => "GREEN", 4 => "BLUE", 5 => "PURPLE", 6 => "ANY",
                _ => "UNKNOWN",
            };
            Some(format!("Transformed {} required hearts to {} (qty={})", src_str, dst_str, v))
        }
        O_INCREASE_HEART_COST => {
            let color_str = match _s {
                0 => "PINK", 1 => "RED", 2 => "YELLOW", 3 => "GREEN", 4 => "BLUE", 5 => "PURPLE", 6 => "ANY",
                _ => "UNKNOWN",
            };
            Some(format!("Increased {} heart requirement by {}", color_str, v))
        }
        O_TRANSFORM_COLOR => {
            let dst_str = match v {
                0 => "PINK", 1 => "RED", 2 => "YELLOW", 3 => "GREEN", 4 => "BLUE", 5 => "PURPLE", 6 => "ANY",
                _ => "UNKNOWN",
            };
            Some(format!("All hearts transform to {}", dst_str))
        }
        _ => None,
    }
}

pub fn get_opcode_name(op: i32) -> &'static str {
    match op {
        O_DRAW => "DRAW",
        O_ADD_HEARTS => "ADD_HEARTS",
        O_ADD_BLADES => "ADD_BLADES",
        O_MOVE_TO_DISCARD => "MOVE_TO_DISCARD",
        O_LOOK_AND_CHOOSE => ChoiceType::LookAndChoose.as_str(),
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
        O_ORDER_DECK => ChoiceType::OrderDeck.as_str(),
        O_REVEAL_UNTIL => "REVEAL_UNTIL",
        O_PAY_ENERGY => ChoiceType::PayEnergy.as_str(),
        O_SELECT_MEMBER => ChoiceType::SelectMember.as_str(),
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
        306 => ChoiceType::SelectMember.as_str(),
        307 => "SUCCESS_PILE_COUNT",
        308 => "IS_SELF_MOVE",
        309 => "DISCARDED_CARDS",
        310 => "YELL_REVEALED_UNIQUE_COLORS",
        311 => "SYNC_COST",
        312 => "SUM_VALUE",
        313 => "IS_WAIT",
        314 => "ON_ABILITY_RESOLVE",
        315 => "TARGET_MEMBER_HAS_NO_HEARTS",
        O_TRANSFORM_BLADES => "TRANSFORM_BLADES",
        O_SET_HEART_COST => "SET_HEART_COST",
        O_REDUCE_HEART_REQ => "REDUCE_HEART_REQ",
        O_INCREASE_HEART_COST => "INCREASE_HEART_COST",
        O_TRANSFORM_HEART => "TRANSFORM_HEART",
        O_TRANSFORM_COLOR => "TRANSFORM_COLOR",
        O_ADD_TO_HAND => "ADD_TO_HAND",
        O_SELECT_CARDS => "SELECT_CARDS",
        O_SELECT_PLAYER => "SELECT_PLAYER",
        O_SELECT_LIVE => "SELECT_LIVE",
        O_REVEAL_CARDS => "REVEAL_CARDS",
        O_BATON_TOUCH_MOD => "BATON_TOUCH_MOD",
        O_SET_SCORE => "SET_SCORE",
        O_REDUCE_SCORE => "REDUCE_SCORE",
        O_LOSE_EXCESS_HEARTS => "LOSE_EXCESS_HEARTS",
        O_SKIP_ACTIVATE_PHASE => "SKIP_ACTIVATE_PHASE",
        _ => if op == 127 { "TRANSFORM_BLADES" } else { ChoiceType::None.as_str() },
    }
}

pub fn describe_bytecode(op: i32, v: i32, a: i64, s: i32) -> String {
    let base_name = get_opcode_name(op);
    let mut details = String::new();

    // Standard human description if available
    if let Some(desc) = get_opcode_log(op, v, a, s, 0) {
        details = format!(" ({})", desc);
    }

    let a_hex = if a != 0 { format!("0x{:012X}", a) } else { "0".to_string() };

    // Check if the opcode might have a target slot in `s`
    let slot = crate::core::logic::interpreter::instruction::DecodedSlot::decode(s);
    let s_desc = format!("S:{:?}/{} -> D:{:?}/{}", slot.source_zone, slot.target_slot, slot.dest_zone, slot.area_idx);

    // Filter decoding if 'a' is large (likely a filter)
    let a_desc = if a > 10000 {
        let f = crate::core::logic::filter::CardFilter::from_attr(a);
        let mut f_parts = Vec::new();
        if f.char_id_1 > 0 { f_parts.push(format!("Char:{}", f.char_id_1)); }
        if f.group_enabled { f_parts.push(format!("Group:{}", f.group_id)); }
        if f.unit_enabled { f_parts.push(format!("Unit:{}", f.unit_id)); }
        if f.value_enabled { f_parts.push(format!("V{}{}", if f.is_le { "<=" } else { ">=" }, f.value_threshold)); }
        if f.color_mask > 0 { f_parts.push(format!("Color:0x{:X}", f.color_mask)); }
        format!("[{}]", f_parts.join(","))
    } else {
        a_hex
    };

    format!(
        "{:<15} | v:{:<4} a:{:<25} s:{:<15}{}",
        base_name, v, a_desc, s_desc, details
    )
}

pub fn trigger_as_str(t: TriggerType) -> &'static str {
    match t {
        TriggerType::None => "None",
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
        TriggerType::OnAbilityResolve => "OnAbilityResolve",
        TriggerType::OnAbilitySuccess => "OnAbilitySuccess",
        TriggerType::OnMoveToDiscard => "OnMoveToDiscard",
        TriggerType::OnMemberTap => "OnMemberTap",
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
        314 => "Ability resolved on member".to_string(),
        315 => "Member has no hearts".to_string(),
        _ => format!("Condition {} (val={})", op, val),
    }
}
