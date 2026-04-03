use crate::core::enums::ChoiceType;
use crate::core::*;
use crate::core::enums::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, PendingInteraction};
use serde_json::Value;
// use crate::core::generated_constants::*;

pub fn get_opcode_log(op: i32, v: i32, a: i64, _s: i32, result_count: i32) -> Option<String> {
    match op {
        O_DRAW => Some(format!("Draw {} card(s)", v)),
        O_ADD_HEARTS => {
            let color_str = match a {
                0 => "Pink Heart",
                1 => "Red Heart",
                2 => "Yellow Heart",
                3 => "Green Heart",
                4 => "Blue Heart",
                5 => "Purple Heart",
                6 => "Any Heart",
                _ => "Unknown Heart",
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
                0 => "Pink",
                1 => "Red",
                2 => "Yellow",
                3 => "Green",
                4 => "Blue",
                5 => "Purple",
                6 => "Any",
                _ => "Unknown",
            };
            Some(format!("Reduced {} heart requirement by {}", color_str, v))
        }
        O_TRANSFORM_HEART => {
            let src_str = match a {
                0 => "Pink",
                1 => "Red",
                2 => "Yellow",
                3 => "Green",
                4 => "Blue",
                5 => "Purple",
                6 => "Any",
                _ => "Unknown",
            };
            let dst_str = match _s {
                0 => "Pink",
                1 => "Red",
                2 => "Yellow",
                3 => "Green",
                4 => "Blue",
                5 => "Purple",
                6 => "Any",
                _ => "Unknown",
            };
            Some(format!(
                "Transformed {} required hearts to {} (qty={})",
                src_str, dst_str, v
            ))
        }
        O_INCREASE_HEART_COST => {
            let color_str = match _s {
                0 => "Pink",
                1 => "Red",
                2 => "Yellow",
                3 => "Green",
                4 => "Blue",
                5 => "Purple",
                6 => "Any",
                _ => "Unknown",
            };
            Some(format!(
                "Increased {} heart requirement by {}",
                color_str, v
            ))
        }
        O_TRANSFORM_COLOR => {
            let dst_str = match v {
                0 => "Pink",
                1 => "Red",
                2 => "Yellow",
                3 => "Green",
                4 => "Blue",
                5 => "Purple",
                6 => "Any",
                _ => "Unknown",
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
        _ => {
            if op == 127 {
                "TRANSFORM_BLADES"
            } else {
                ChoiceType::None.as_str()
            }
        }
    }
}

pub fn describe_frame_words(op: i32, v: i32, a: i64, s: i32) -> String {
    let base_name = get_opcode_name(op);
    let mut details = String::new();

    // Standard human description if available
    if let Some(desc) = get_opcode_log(op, v, a, s, 0) {
        details = format!(" ({})", desc);
    }

    let a_desc = if a != 0 && op != O_NOP as i32 && op != O_RETURN as i32 {
        let attr_desc = describe_filter_attr(CardFilter::from_attr_legacy(a));
        if attr_desc == "-" {
            "-".to_string()
        } else {
            format!("[{}]", attr_desc)
        }
    } else {
        "-".to_string()
    };

    // Check if the opcode might have a target slot in `s`
    let slot = crate::core::logic::interpreter::instruction::DecodedSlot::decode(s);
    let s_desc = format!(
        "S:{:?}/{} -> D:{:?}/{}",
        slot.source_zone, slot.target_slot, slot.dest_zone, slot.area_idx
    );

    format!(
        "{:<15} | v:{:<4} a:{:<25} s:{:<15}{}",
        base_name, v, a_desc, s_desc, details
    )
}

pub fn describe_words(op: i32, v: i32, a: i64, s: i32) -> String {
    describe_frame_words(op, v, a, s)
}

pub fn describe_bytecode(op: i32, v: i32, a: i64, s: i32) -> String {
    describe_words(op, v, a, s)
}

pub fn describe_trace_step(op: i32, v: i32, a: i64, s: i32, is_negated: bool) -> String {
    let name = get_opcode_name(op);
    let prefix = if is_condition_opcode(op) { "IF" } else { "DO" };
    let body = if is_condition_opcode(op) {
        describe_condition(op, v, a as u64)
    } else if let Some(desc) = get_opcode_log(op, v, a, s, 0) {
        desc
    } else {
        describe_frame_words(op, v, a, s)
    };

    if is_negated {
        format!("{} NOT {} [{}]", prefix, body, name)
    } else {
        format!("{} {} [{}]", prefix, body, name)
    }
}

pub fn describe_frame_step(frame: &AbilityFrameComponents<'_>) -> String {
    describe_trace_step(
        frame.opcode,
        frame.value,
        frame.resolved_filter_attr() as i64,
        frame.slot.to_raw(),
        frame.is_negated,
    )
}

pub fn describe_frame_condition(frame: &AbilityFrameComponents<'_>) -> String {
    describe_condition(frame.opcode, frame.value, frame.resolved_filter_attr())
}

fn truncate_text(text: String, max_len: usize) -> String {
    if text.len() <= max_len {
        text
    } else {
        text.chars()
            .take(max_len.saturating_sub(1))
            .collect::<String>()
            + "…"
    }
}

fn join_parts(parts: Vec<String>) -> String {
    if parts.is_empty() {
        "-".to_string()
    } else {
        parts.join(", ")
    }
}

fn describe_card_texts(db: &CardDatabase, card_id: i32) -> String {
    let card_texts = db
        .get_member(card_id)
        .map(|card| {
            (
                card.original_text.as_str(),
                card.ability_text.as_str(),
                card.original_text_en.as_str(),
            )
        })
        .or_else(|| {
            db.get_live(card_id).map(|card| {
                (
                    card.original_text.as_str(),
                    card.ability_text.as_str(),
                    card.original_text_en.as_str(),
                )
            })
        });

    let Some((jp, ability, en)) = card_texts else {
        return "text=-".to_string();
    };

    let mut parts = Vec::new();
    if !jp.is_empty() {
        parts.push(format!("jp={}", truncate_text(jp.to_string(), 160)));
    }
    if !ability.is_empty() {
        parts.push(format!(
            "ability={}",
            truncate_text(ability.to_string(), 160)
        ));
    }
    if !en.is_empty() {
        parts.push(format!("en={}", truncate_text(en.to_string(), 160)));
    }

    join_parts(parts)
}

pub fn describe_filter_attr(filter: CardFilter) -> String {
    let mut parts = Vec::new();

    if filter.target_player != 0 {
        parts.push(format!("target_player={}", filter.target_player));
    }
    if filter.card_type != 0 {
        parts.push(format!("card_type={}", filter.card_type));
    }
    if filter.group_enabled {
        parts.push(format!(
            "group={}({})",
            filter.group_id,
            get_group_name(filter.group_id, "en")
        ));
    }
    if filter.unit_enabled {
        parts.push(format!(
            "unit={}({})",
            filter.unit_id,
            get_unit_name(filter.unit_id, "en")
        ));
    }
    if filter.char_id_1 != 0 {
        parts.push(format!("char_1={}", filter.char_id_1));
    }
    if filter.char_id_2 != 0 {
        parts.push(format!("char_2={}", filter.char_id_2));
    }
    if filter.char_id_3 != 0 {
        parts.push(format!("char_3={}", filter.char_id_3));
    }
    if filter.zone_mask != 0 {
        parts.push(format!("zone=0x{:X}", filter.zone_mask));
    }
    if filter.color_mask != 0 {
        parts.push(format!("color=0x{:X}", filter.color_mask));
    }
    if filter.is_tapped {
        parts.push("tapped".to_string());
    }
    if filter.has_blade_heart {
        parts.push("has_blade".to_string());
    }
    if filter.not_has_blade_heart {
        parts.push("no_blade".to_string());
    }
    if filter.unique_names {
        parts.push("unique_names".to_string());
    }
    if filter.value_enabled {
        parts.push(format!(
            "value{}{}",
            if filter.is_le { "<=" } else { ">=" },
            filter.value_threshold
        ));
    }
    if filter.special_id != 0 {
        parts.push(format!("special={}", filter.special_id));
    }
    if filter.is_setsuna {
        parts.push("setsuna".to_string());
    }
    if filter.compare_accumulated {
        parts.push("compare_accumulated".to_string());
    }
    if filter.is_optional {
        parts.push("optional".to_string());
    }
    if filter.keyword_energy {
        parts.push("keyword_energy".to_string());
    }
    if filter.keyword_member {
        parts.push("keyword_member".to_string());
    }

    join_parts(parts)
}

pub fn describe_filter_bits(attr: u64) -> String {
    describe_filter_attr(CardFilter::from_attr_legacy(attr as i64))
}

pub fn describe_slot(slot: DecodedSlot) -> String {
    let mut parts = vec![
        format!("src={:?}", slot.source_zone),
        format!("dst={:?}", slot.dest_zone),
        format!("target={}", slot.target_slot),
        format!("area={}", slot.area_idx),
    ];

    if slot.is_opponent {
        parts.push("opponent".to_string());
    }
    if slot.is_reveal_until_live {
        parts.push("reveal_until_live".to_string());
    }
    if slot.is_baton_slot {
        parts.push("baton".to_string());
    }
    if slot.is_empty_slot {
        parts.push("empty".to_string());
    }
    if slot.is_wait {
        parts.push("wait".to_string());
    }
    if slot.is_dynamic {
        parts.push("dynamic".to_string());
    }

    join_parts(parts)
}

pub fn describe_params(params: Option<&Value>) -> String {
    match params {
        Some(value) if value.is_object() || value.is_array() => truncate_text(
            serde_json::to_string(value).unwrap_or_else(|_| "<invalid-json>".into()),
            240,
        ),
        Some(value) => truncate_text(value.to_string(), 240),
        None => "-".to_string(),
    }
}

pub fn describe_context(ctx: &AbilityContext) -> String {
    format!(
        "ctx[p={},a={},src={},ab={},pc={},choice={},v_acc={},v_rem={},slot={},area={},color={},trigger={:?}]",
        ctx.player_id,
        ctx.activator_id,
        ctx.source_card_id,
        ctx.ability_index,
        ctx.program_counter,
        ctx.choice_index,
        ctx.v_accumulated,
        ctx.v_remaining,
        ctx.target_slot,
        ctx.area_idx,
        ctx.selected_color,
        ctx.trigger_type
    )
}

pub fn describe_frame_semantics(
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
    db: &CardDatabase,
) -> String {
    let card_name = db
        .get_member(ctx.source_card_id)
        .map(|c| c.name.as_str())
        .or_else(|| db.get_live(ctx.source_card_id).map(|c| c.name.as_str()))
        .unwrap_or("System");

    let trace_step = frame.to_trace_step();
    let trace_json = truncate_text(
        serde_json::to_string(&trace_step).unwrap_or_else(|_| "<trace-step-error>".to_string()),
        320,
    );

    format!(
        "card={} trace={} filter=[{}] slot=[{}] params=[{}] {} {}",
        card_name,
        trace_json,
        describe_filter_attr(frame.filter),
        describe_slot(frame.slot),
        describe_params(frame.params),
        describe_card_texts(db, ctx.source_card_id),
        describe_context(ctx)
    )
}

pub fn describe_pending_interaction(pi: &PendingInteraction) -> String {
    format!(
        "pending[op={},choice={},card={},ab={},v={},filter=[{}],slot={},phase={:?},cp={},exec={},actions={},options={},{}]",
        get_opcode_name(pi.effect_opcode),
        pi.choice_type.as_str(),
        pi.card_id,
        pi.ability_index,
        pi.v_remaining,
        describe_filter_bits(pi.filter_attr),
        pi.target_slot,
        pi.original_phase,
        pi.original_current_player,
        pi.execution_id,
        pi.actions.len(),
        pi.options.len(),
        describe_context(&pi.ctx)
    )
}

pub fn is_condition_opcode(op: i32) -> bool {
    (203..=255).contains(&op) || (301..=399).contains(&op)
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
