use super::constants::*;
use super::models::{Ability, AbilityContext, CanonicalAbilityProgram};
use super::{CardDatabase, GameState};
use crate::core::enums::{AbilityCostType, ConditionType, EffectType, TriggerType};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum CanonicalTrigger {
    None,
    Metadata(TriggerType),
    Unknown(String),
}

impl CanonicalTrigger {
    pub fn from_metadata_key(key: &str) -> Self {
        if key.is_empty() {
            return Self::None;
        }

        match TriggerType::from_metadata_key(key) {
            Some(trigger_type) => Self::Metadata(trigger_type),
            None => Self::Unknown(key.to_string()),
        }
    }

    pub fn metadata_trigger_type(&self) -> Option<TriggerType> {
        match self {
            Self::None => Some(TriggerType::None),
            Self::Metadata(trigger_type) => Some(*trigger_type),
            Self::Unknown(_) => None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum CanonicalConditionOp {
    Metadata(ConditionType),
    ValueGE,
    ValueLE,
    Or,
    And,
    Unknown(String),
}

impl CanonicalConditionOp {
    pub fn from_metadata_key(key: &str) -> Self {
        match key {
            "HEARTS_COUNT" => Self::Metadata(ConditionType::CountHearts),
            "VALUE_GE" => Self::ValueGE,
            "VALUE_LE" => Self::ValueLE,
            "OR" => Self::Or,
            "AND" => Self::And,
            _ => match ConditionType::from_metadata_key(key) {
                Some(condition_type) => Self::Metadata(condition_type),
                None => Self::Unknown(key.to_string()),
            },
        }
    }

    pub fn metadata_condition_type(&self) -> Option<ConditionType> {
        match self {
            Self::Metadata(condition_type) => Some(*condition_type),
            _ => None,
        }
    }

    pub fn is_directly_executable(&self) -> bool {
        matches!(self, Self::ValueGE | Self::ValueLE | Self::Or | Self::And)
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum CanonicalCostOp {
    Metadata(AbilityCostType),
    Unknown(String),
}

impl CanonicalCostOp {
    pub fn from_metadata_key(key: &str) -> Self {
        match AbilityCostType::from_metadata_key(key) {
            Some(cost_type) => Self::Metadata(cost_type),
            None => Self::Unknown(key.to_string()),
        }
    }

    pub fn metadata_cost_type(&self) -> Option<AbilityCostType> {
        match self {
            Self::Metadata(cost_type) => Some(*cost_type),
            Self::Unknown(_) => None,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum CanonicalEffectOp {
    Draw,
    DrawUntil,
    AddToHand,
    ActivateEnergy,
    Metadata(EffectType),
    Unknown(String),
}

impl CanonicalEffectOp {
    pub fn from_metadata_key(key: &str) -> Self {
        match key {
            "DRAW" => Self::Draw,
            "DRAW_UNTIL" => Self::DrawUntil,
            "ADD_TO_HAND" => Self::AddToHand,
            "ACTIVATE_ENERGY" => Self::ActivateEnergy,
            _ => match EffectType::from_metadata_key(key) {
                Some(effect_type) => Self::Metadata(effect_type),
                None => Self::Unknown(key.to_string()),
            },
        }
    }

    pub fn metadata_effect_type(&self) -> Option<EffectType> {
        match self {
            Self::Draw => Some(EffectType::Draw),
            Self::DrawUntil => Some(EffectType::DrawUntil),
            Self::AddToHand => Some(EffectType::AddToHand),
            Self::ActivateEnergy => Some(EffectType::ActivateEnergy),
            Self::Metadata(effect_type) => Some(*effect_type),
            Self::Unknown(_) => None,
        }
    }

    pub fn is_directly_executable(&self) -> bool {
        matches!(
            self,
            Self::Draw | Self::DrawUntil | Self::AddToHand | Self::ActivateEnergy
        )
    }
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct CanonicalDerivedMetadata {
    pub effect_mask: u64,
    pub ability_flags: u64,
    pub choice_flags: u8,
    pub choice_count: u8,
    pub opcodes_mask: u128,
    pub has_unflagged_logic: bool,
}

fn effect_mask_for_effect_type(effect_type: EffectType) -> u64 {
    match effect_type {
        EffectType::AddBlades | EffectType::SetBlades | EffectType::BuffPower | EffectType::TransformBlades => EFFECT_MASK_BLADE,
        EffectType::AddHearts | EffectType::SetHearts | EffectType::TransformHeart => EFFECT_MASK_HEART,
        EffectType::ReduceCost | EffectType::IncreaseCost | EffectType::CalcSumCost => EFFECT_MASK_COST,
        EffectType::ReduceHeartReq | EffectType::SetHeartCost | EffectType::IncreaseHeartCost | EffectType::ReduceLiveSetLimit => EFFECT_MASK_REQ,
        EffectType::GrantAbility => EFFECT_MASK_GRANT,
        EffectType::MetaRule
        | EffectType::Restriction
        | EffectType::PreventPlayToSlot
        | EffectType::PreventSetToSuccessPile
        | EffectType::PreventActivate
        | EffectType::PreventBatonTouch => EFFECT_MASK_RULE,
        EffectType::BoostScore | EffectType::SetScore | EffectType::ReduceScore | EffectType::ModifyScoreRule => EFFECT_MASK_SCORE,
        EffectType::Draw
        | EffectType::LookDeck
        | EffectType::SearchDeck
        | EffectType::LookAndChoose
        | EffectType::AddToHand
        | EffectType::DrawUntil
        | EffectType::RevealUntil => EFFECT_MASK_DRAW,
        _ => 0,
    }
}

fn ability_flags_for_effect_type(effect_type: EffectType) -> u64 {
    match effect_type {
        EffectType::Return | EffectType::LookAndChoose => FLAG_DRAW as u64,
        EffectType::SearchDeck => FLAG_SEARCH as u64,
        EffectType::RecoverLive | EffectType::RecoverMember => FLAG_RECOVER as u64,
        EffectType::AddBlades | EffectType::AddHearts => FLAG_BUFF as u64,
        EffectType::MoveMember | EffectType::SwapCards | EffectType::SwapArea => FLAG_MOVE as u64,
        EffectType::TapOpponent | EffectType::TapMember => FLAG_TAP as u64,
        EffectType::EnergyCharge => FLAG_CHARGE as u64,
        EffectType::ActivateMember | EffectType::SetTapped | EffectType::ActivateEnergy => FLAG_TEMPO as u64,
        EffectType::ReduceCost => FLAG_REDUCE as u64,
        EffectType::BoostScore | EffectType::ModifyScoreRule | EffectType::ReduceScore => FLAG_BOOST as u64,
        EffectType::TransformColor | EffectType::TransformHeart => FLAG_TRANSFORM as u64,
        EffectType::ReduceHeartReq => FLAG_WIN_COND as u64,
        _ => 0,
    }
}

pub fn derive_metadata(program: &CanonicalAbilityProgram) -> CanonicalDerivedMetadata {
    let mut metadata = CanonicalDerivedMetadata::default();

    for step in &program.effects {
        let effect_op = CanonicalEffectOp::from_metadata_key(&step.op);
        let Some(effect_type) = effect_op.metadata_effect_type() else {
            if !step.op.is_empty() {
                metadata.has_unflagged_logic = true;
            }
            continue;
        };

        metadata.effect_mask |= effect_mask_for_effect_type(effect_type);
        metadata.ability_flags |= ability_flags_for_effect_type(effect_type);
        metadata.opcodes_mask |= 1u128 << (effect_type as u32 % 128);

        match effect_type {
            EffectType::LookAndChoose => {
                metadata.choice_flags |= CHOICE_FLAG_LOOK;
                if metadata.choice_count == 0 {
                    metadata.choice_count = step.count.unwrap_or(3).max(1) as u8;
                }
            }
            EffectType::SelectMode => {
                metadata.choice_flags |= CHOICE_FLAG_MODE;
                if metadata.choice_count == 0 {
                    metadata.choice_count = step.count.unwrap_or(1).max(1) as u8;
                }
            }
            EffectType::ColorSelect => {
                metadata.choice_flags |= CHOICE_FLAG_COLOR;
                if metadata.choice_count == 0 {
                    metadata.choice_count = 6;
                }
            }
            EffectType::OrderDeck => {
                metadata.choice_flags |= CHOICE_FLAG_ORDER;
                if metadata.choice_count == 0 {
                    metadata.choice_count = step.count.unwrap_or(3).max(1) as u8;
                }
            }
            _ => {}
        }
    }

    metadata
}

pub fn derive_metadata_for_ability(ability: &Ability) -> Option<CanonicalDerivedMetadata> {
    ability.canonical_program.as_ref().map(derive_metadata)
}

fn synthesized_canonical_effects(ability: &Ability) -> Vec<crate::core::models::CanonicalStep> {
    ability
        .effects
        .iter()
        .map(|effect| crate::core::models::CanonicalStep {
            kind: "effect".to_string(),
            op: effect.effect_type.as_metadata_key().to_string(),
            count: Some(effect.value),
            value: Some(effect.value),
            is_optional: effect.is_optional,
            params: effect.params.clone(),
            ..Default::default()
        })
        .collect()
}

fn expanded_canonical_program(
    ability: &Ability,
    program: &CanonicalAbilityProgram,
) -> CanonicalAbilityProgram {
    if ability.effects.len() > program.effects.len() {
        let mut expanded = program.clone();
        expanded.effects = synthesized_canonical_effects(ability);
        return expanded;
    }

    program.clone()
}

fn canonical_step_count(step: &super::models::CanonicalStep, default_count: i32) -> i32 {
    step.count.or(step.value).unwrap_or(default_count).max(0)
}

fn canonical_target_slot(step: &crate::core::models::CanonicalStep, ctx: &AbilityContext) -> Option<usize> {
    if ctx.target_slot >= 0 {
        let slot = ctx.target_slot as usize;
        if slot < 3 {
            return Some(slot);
        }
    }

    step.target
        .as_ref()
        .and_then(|target| target.parse::<usize>().ok())
        .filter(|slot| *slot < 3)
}

fn canonical_heart_color(step: &crate::core::models::CanonicalStep) -> usize {
    let heart_type = step
        .params
        .get("heart_type")
        .and_then(|value| value.as_str())
        .unwrap_or("");

    match heart_type {
        "PINK" => 0,
        "RED" => 1,
        "YELLOW" => 2,
        "GREEN" => 3,
        "BLUE" => 4,
        "PURPLE" => 5,
        "ANY" => 6,
        _ => step
            .params
            .get("heart_color")
            .and_then(|value| value.as_u64())
            .map(|value| value as usize)
            .unwrap_or(0),
    }
}

fn canonical_filter_attr(
    ability: &Ability,
    program: &CanonicalAbilityProgram,
    effect_idx: usize,
    runtime_opcode: i32,
) -> u64 {
    if let Some(effect) = ability.effects.get(effect_idx) {
        if effect.runtime_opcode == runtime_opcode {
            return effect.runtime_attr;
        }
    }

    let occurrence = program.effects[..=effect_idx]
        .iter()
        .filter(|step| CanonicalEffectOp::from_metadata_key(&step.op).metadata_effect_type().map(|effect_type| effect_type as i32) == Some(runtime_opcode))
        .count();

    ability
        .effects
        .iter()
        .filter(|effect| effect.runtime_opcode == runtime_opcode)
        .nth(occurrence.saturating_sub(1))
        .map(|effect| effect.runtime_attr)
        .unwrap_or(0)
}

pub fn can_execute_directly(program: &CanonicalAbilityProgram) -> bool {
    // Check Costs
    for step in &program.costs {
        if CanonicalCostOp::from_metadata_key(&step.op).metadata_cost_type().is_none() {
            println!("[CANONICAL] Rejected: Unknown cost op {}", step.op);
            return false;
        }
    }

    true
}

fn resolve_canonical_condition(
    state: &mut GameState,
    db: &CardDatabase,
    step: &crate::core::models::CanonicalStep,
    ctx: &AbilityContext,
    p_idx: usize,
    op: &CanonicalConditionOp,
    depth: u32,
) -> bool {
    if depth > 10 {
        return false;
    }
    match op {
        CanonicalConditionOp::Metadata(ct) => {
            state.check_condition(db, p_idx, &crate::core::models::Condition {
                condition_type: *ct,
                value: canonical_step_count(step, 0),
                attr: step.params.get("attr").and_then(|v| v.as_u64()).unwrap_or(0),
                target_slot: step.params.get("target_slot").and_then(|v| v.as_u64()).map(|v| v as u8).unwrap_or(0),
                is_negated: step.params.get("is_negated").and_then(|v| v.as_bool()).unwrap_or(false),
                ..Default::default()
            }, ctx, 0)
        }
        CanonicalConditionOp::ValueGE => {
            let val = canonical_step_count(step, 0);
            let threshold = step.params.get("threshold").and_then(|v| v.as_i64()).map(|v| v as i32).unwrap_or(0);
            val >= threshold
        }
        CanonicalConditionOp::ValueLE => {
            let val = canonical_step_count(step, 0);
            let threshold = step.params.get("threshold").and_then(|v| v.as_i64()).map(|v| v as i32).unwrap_or(0);
            val <= threshold
        }
        CanonicalConditionOp::Or => {
            if let Some(conds_val) = step.extra.get("conditions") {
                if let Ok(nested) = serde_json::from_value::<Vec<crate::core::models::CanonicalStep>>(conds_val.clone()) {
                    for n_step in nested {
                        let n_op = CanonicalConditionOp::from_metadata_key(&n_step.op);
                        if resolve_canonical_condition(state, db, &n_step, ctx, p_idx, &n_op, depth + 1) {
                            return true;
                        }
                    }
                }
            }
            false
        }
        CanonicalConditionOp::And => {
            if let Some(conds_val) = step.extra.get("conditions") {
                if let Ok(nested) = serde_json::from_value::<Vec<crate::core::models::CanonicalStep>>(conds_val.clone()) {
                    for n_step in nested {
                        let n_op = CanonicalConditionOp::from_metadata_key(&n_step.op);
                        if !resolve_canonical_condition(state, db, &n_step, ctx, p_idx, &n_op, depth + 1) {
                            return false;
                        }
                    }
                    return true;
                }
            }
            true
        }
        _ => false,
    }
}

fn execute_canonical_effect_step(
    state: &mut GameState,
    _db: &CardDatabase,
    step: &crate::core::models::CanonicalStep,
    ctx_in: &AbilityContext,
    p_idx: usize,
    depth: u32,
) -> bool {
    if depth > 10 {
        return true;
    }
    let op = CanonicalEffectOp::from_metadata_key(&step.op);
    
    // Handle Direct Ops
    match op {
        CanonicalEffectOp::Draw => {
            state.draw_cards(p_idx, canonical_step_count(step, 1) as u32);
            return true;
        }
        CanonicalEffectOp::DrawUntil => {
            let target_hand_size = canonical_step_count(step, 0) as usize;
            let current_hand_size = state.players[p_idx].hand.len();
            if current_hand_size < target_hand_size {
                state.draw_cards(p_idx, (target_hand_size - current_hand_size) as u32);
            }
            return true;
        }
        CanonicalEffectOp::AddToHand => {
            let count = canonical_step_count(step, 1) as usize;
            if !state.players[p_idx].looked_cards.is_empty() {
                for _ in 0..count {
                    if state.players[p_idx].looked_cards.is_empty() { break; }
                    let cid = state.players[p_idx].looked_cards.remove(0);
                    state.players[p_idx].gain_hand_card(cid);
                }
            } else {
                state.draw_cards(p_idx, count as u32);
            }
            return true;
        }
        CanonicalEffectOp::ActivateEnergy => {
            state.activate_energy(p_idx, canonical_step_count(step, 1));
            return true;
        }
        _ => {}
    }

    // Handle Structural Ops
    if step.kind == "if" {
        let mut condition_met = true;
        if !step.op.is_empty() {
            let cond_op = CanonicalConditionOp::from_metadata_key(&step.op);
            condition_met = resolve_canonical_condition(state, _db, step, ctx_in, p_idx, &cond_op, depth + 1);
        }

        let branch = if condition_met { "then" } else { "else" };
        if let Some(steps_val) = step.extra.get(branch) {
            if let Some(nested_steps) = steps_val.as_array() {
                for n_val in nested_steps {
                    if let Ok(n_step) = serde_json::from_value::<crate::core::models::CanonicalStep>(n_val.clone()) {
                        execute_canonical_effect_step(state, _db, &n_step, ctx_in, p_idx, depth + 1);
                    }
                }
            }
        }
        return true;
    }

    // Handle Metadata Ops
    if let CanonicalEffectOp::Metadata(et) = op {
        match et {
            EffectType::RecoverMember => {
                let count = canonical_step_count(step, 1) as usize;
                for _ in 0..count {
                    if let Some(cid) = state.players[p_idx].pop_discard_card() {
                        state.players[p_idx].gain_hand_card(cid);
                    }
                }
            }
            EffectType::RecoverLive => {
                let count = canonical_step_count(step, 1) as usize;
                for _ in 0..count {
                    if let Some(cid) = state.players[p_idx].pop_discard_card() {
                        state.players[p_idx].live_deck.push(cid);
                    }
                }
            }
            EffectType::BoostScore => {
                state.players[p_idx].score += canonical_step_count(step, 0) as u32;
            }
            EffectType::EnergyCharge => {
                state.draw_energy_cards(p_idx, canonical_step_count(step, 1));
            }
            EffectType::Return => {
                let count = canonical_step_count(step, 1) as usize;
                for _ in 0..count {
                    if state.players[p_idx].looked_cards.is_empty() { break; }
                    let cid = state.players[p_idx].looked_cards.remove(0);
                    state.players[p_idx].gain_hand_card(cid);
                }
            }
            EffectType::AddBlades => {
                if let Some(slot) = canonical_target_slot(step, ctx_in) {
                    state.players[p_idx].blade_buffs[slot] += canonical_step_count(step, 0) as i16;
                }
            }
            EffectType::AddHearts => {
                if let Some(slot) = canonical_target_slot(step, ctx_in) {
                    state.players[p_idx].heart_buffs[slot]
                        .add_to_color(canonical_heart_color(step), canonical_step_count(step, 0));
                }
            }
            EffectType::ReduceYellCount => {
                state.players[p_idx].yell_count_reduction += canonical_step_count(step, 0) as i16;
            }
            EffectType::MoveToDeck => {
                let count = canonical_step_count(step, 1) as usize;
                for _ in 0..count {
                    if let Some(cid) = state.players[p_idx].pop_discard_card() {
                        state.players[p_idx].deck.insert(0, cid);
                    }
                }
            }
            EffectType::ReduceCost => {
                state.players[p_idx].cost_reduction += canonical_step_count(step, 0) as i16;
            }
            _ => { return false; }
        }
        return true;
    }

    false
}

fn resolve_effect_via_runtime(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    effect: &crate::core::logic::Effect,
    auto_pick: bool,
) {
    let mut runtime_ctx = ctx.clone();
    runtime_ctx.auto_pick = auto_pick;
    let virtual_bc = vec![
        effect.runtime_opcode,
        effect.runtime_value,
        (effect.runtime_attr & 0xFFFFFFFF) as i32,
        (effect.runtime_attr >> 32) as i32,
        effect.runtime_slot,
        O_RETURN,
        0,
        0,
        0,
        0,
    ];
    super::interpreter::resolve_bytecode(state, db, std::sync::Arc::new(virtual_bc), &runtime_ctx);
}

pub fn try_resolve_ability(
    state: &mut GameState,
    _db: &CardDatabase,
    ability: &Ability,
    ctx_in: &AbilityContext,
) -> bool {
    let Some(program_ref) = ability.canonical_program.as_ref() else {
        return false;
    };
    let program = expanded_canonical_program(ability, program_ref);

    let mut ctx = ctx_in.clone();

    let mut is_resuming_cost = false;
    let mut is_resuming_effect = false;
    let mut current_cost_idx = 0;
    let mut current_eff_idx = 0;

    if ctx.program_counter >= 1000 && ctx.program_counter < 2000 {
        is_resuming_cost = true;
        current_cost_idx = (ctx.program_counter - 1000) as usize;
    } else if ctx.program_counter >= 2000 && ctx.program_counter < 3000 {
        is_resuming_effect = true;
        current_eff_idx = (ctx.program_counter - 2000) as usize;
    }

    println!("[CANONICAL] Trying resolution for card {}...", ctx.source_card_id);

    if !can_execute_directly(&program) {
        println!("[CANONICAL] Rejected: Operations not supported directly.");
        return false;
    }

    if program.effects.is_empty() && program.costs.is_empty() {
        println!("[CANONICAL] Rejected: Empty program");
        return false;
    }

    let _trigger = CanonicalTrigger::from_metadata_key(&program.trigger);
    let _id = if state.ui.current_execution_id.is_none() && ctx.program_counter == 0 {
        Some(state.generate_execution_id())
    } else {
        None
    };

    let p_idx = ctx.player_id as usize;

    // 1. Resolve Conditions
    if !is_resuming_cost && !is_resuming_effect {
        for (index, step) in program.conditions.iter().enumerate() {
            let op = CanonicalConditionOp::from_metadata_key(&step.op);
            if let Some(ct) = op.metadata_condition_type() {
                let passed = super::interpreter::check_condition_opcode(
                    state, _db, ct as i32, 
                    step.value.unwrap_or(0), 
                    0, // attr
                    step.target.as_ref().map(|t| t.parse::<i32>().unwrap_or(0)).unwrap_or(0), 
                    &ctx, 0
                );
                if !passed { 
                    if _id.is_some() { state.clear_execution_id(); }
                    return true; 
                } 
            } else if let Some(condition) = ability.conditions.get(index) {
                if !state.check_condition(_db, p_idx, condition, &ctx, 0) {
                    if _id.is_some() { state.clear_execution_id(); }
                    return true;
                }
            } else {
                if _id.is_some() { state.clear_execution_id(); }
                return false;
            }
        }
    }

    // 2. Resolve Costs
    if !is_resuming_effect {
        for (i, step) in program.costs.iter().enumerate().skip(current_cost_idx) {
            let op = CanonicalCostOp::from_metadata_key(&step.op);
            if let Some(ct) = op.metadata_cost_type() {
                let cost = super::models::Cost {
                    cost_type: ct.clone(),
                    value: step.value.unwrap_or(0),
                    is_optional: step.is_optional,
                    ..Default::default()
                };
                
                if is_resuming_cost && i == current_cost_idx {
                    // We just came back from a suspension for this cost!
                    if ctx.choice_index == 99 { // 99 is usually Pass/Decline
                        if _id.is_some() { state.clear_execution_id(); }
                        return true; // Cancelled
                    }
                    if ctx.choice_index == 0 { // Accepted Optional Cost
                        // Bypass the normal check_cost and deduct directly if possible
                        // For canonical, optional Pay Energy just needs to deduct the energy.
                        if ct == crate::core::enums::AbilityCostType::Energy {
                            let mut forced_cost = cost.clone();
                            forced_cost.is_optional = false;
                            if !super::interpreter::pay_cost(state, _db, p_idx, &forced_cost, &ctx) {
                                if _id.is_some() { state.clear_execution_id(); }
                                return true;
                            }
                        } else {
                            // If it's a discard selection or other cost requiring full choices, 
                            // we need dedicated handling.
                            // For simplicity on initial implementation, let pay_cost attempt to handle it:
                            let mut forced_cost = cost.clone();
                            forced_cost.is_optional = false;
                            super::interpreter::pay_cost(state, _db, p_idx, &forced_cost, &ctx);
                        }
                    }
                    is_resuming_cost = false; // Finished resuming this cost
                    continue;
                }

                if step.is_optional {
                    // Time to suspend for optional cost!
                    let fake_op = match ct {
                        crate::core::enums::AbilityCostType::Energy => crate::core::logic::constants::O_PAY_ENERGY,
                        crate::core::enums::AbilityCostType::DiscardHand => crate::core::logic::constants::O_MOVE_TO_DISCARD,
                        _ => 0,
                    };
                    let choice_type = match ct {
                        crate::core::enums::AbilityCostType::Energy => crate::core::enums::ChoiceType::PayEnergy,
                        crate::core::enums::AbilityCostType::DiscardHand => crate::core::enums::ChoiceType::SelectHandDiscard,
                        _ => crate::core::enums::ChoiceType::Optional,
                    };

                    crate::core::logic::interpreter::suspend_interaction(
                        state, _db, &ctx, 1000 + i, fake_op, -1, choice_type,
                        "Pay optional cost?", 0, cost.value as i16
                    );
                    return true;
                }

                if !super::interpreter::pay_cost(state, _db, p_idx, &cost, &ctx) {
                    if _id.is_some() { state.clear_execution_id(); }
                    return true; // Cost payment failed, stop execution but return true (resolved as empty)
                }
            } else { 
                if _id.is_some() { state.clear_execution_id(); }
                return false; 
            }
        }
    }

    // 3. Resolve Effects
    for (i, step) in program.effects.iter().enumerate().skip(current_eff_idx) {
        if !(is_resuming_effect && i == current_eff_idx) {
            ctx.choice_index = -1;
        }

        let op = CanonicalEffectOp::from_metadata_key(&step.op);

        if let CanonicalEffectOp::Metadata(et) = op {
            if matches!(et, EffectType::RecoverMember | EffectType::RecoverLive) {
                if let Some(effect) = ability.effects.get(i) {
                    resolve_effect_via_runtime(state, _db, &ctx, effect, false);
                    if state.phase == crate::core::enums::Phase::Response {
                        return true;
                    }
                    continue;
                }
            }
        }
        
        // Target Selection / Suspension Ops
        if let CanonicalEffectOp::Metadata(et) = op {
            match et {
                EffectType::LookAndChoose | EffectType::SelectMember | EffectType::TapOpponent | EffectType::TapMember | EffectType::PlayMemberFromDiscard | EffectType::MoveToDiscard => {
                    if et == EffectType::LookAndChoose {
                        if let Some(effect) = ability.effects.get(i) {
                            resolve_effect_via_runtime(state, _db, &ctx, effect, false);
                            if state.phase == crate::core::enums::Phase::Response {
                                return true;
                            }
                            continue;
                        }
                    }

                    if et == EffectType::MoveToDiscard && !step.is_optional {
                        if let Some(effect) = ability.effects.get(i) {
                            if effect.runtime_opcode == O_MOVE_TO_DISCARD {
                                let move_count = effect.runtime_value.max(0) as usize;
                                let source_zone = super::interpreter::instruction::BytecodeInstruction::new(
                                    effect.runtime_opcode,
                                    effect.runtime_value,
                                    effect.runtime_attr as i64,
                                    effect.runtime_slot,
                                )
                                .slot()
                                .source_zone;

                                if matches!(
                                    source_zone,
                                    crate::core::enums::Zone::Deck
                                        | crate::core::enums::Zone::DeckTop
                                        | crate::core::enums::Zone::DeckBottom
                                        | crate::core::enums::Zone::Default
                                ) {
                                    for _ in 0..move_count.min(state.players[p_idx].deck.len()) {
                                        if let Some(card_id) = state.players[p_idx].pop_deck_card() {
                                            state.players[p_idx].push_discard_card(card_id);
                                        }
                                    }
                                    continue;
                                }

                                let mut direct_ctx = ctx.clone();
                                direct_ctx.auto_pick = source_zone != crate::core::enums::Zone::Hand;
                                let virtual_bc = vec![
                                    effect.runtime_opcode,
                                    effect.runtime_value,
                                    (effect.runtime_attr & 0xFFFFFFFF) as i32,
                                    (effect.runtime_attr >> 32) as i32,
                                    effect.runtime_slot,
                                    O_RETURN,
                                    0,
                                    0,
                                    0,
                                    0,
                                ];
                                super::interpreter::resolve_bytecode(
                                    state,
                                    _db,
                                    std::sync::Arc::new(virtual_bc),
                                    &direct_ctx,
                                );
                                if state.phase == crate::core::enums::Phase::Response {
                                    return true;
                                }
                                continue;
                            }
                        }
                    }

                    if is_resuming_effect && i == current_eff_idx {
                        if ctx.choice_index == CHOICE_DONE as i16 {
                            if _id.is_some() { state.clear_execution_id(); }
                            return true; // Cancelled
                        }
                        
                        let slot = ctx.choice_index as usize;
                        ctx.target_slot = slot as i16;
                        ctx.area_idx = slot as i16;
                        if slot < 3 {
                            if let Some(&selected_cid) = state.players[p_idx].stage.get(slot) {
                                if selected_cid >= 0 {
                                    ctx.target_card_id = selected_cid;
                                    if !ctx.selected_cards.contains(&selected_cid) {
                                        ctx.selected_cards.push(selected_cid);
                                    }
                                }
                            }

                            if et == EffectType::TapOpponent {
                                state.players[p_idx].set_tapped(slot, true);
                            } else if et == EffectType::TapMember {
                                state.players[p_idx].set_tapped(slot, true);
                            }
                        }
                        is_resuming_effect = false;
                        // For non-structural steps, we skip. For IF blocks, we would need 
                        // to know if we're inside. Since IF blocks don't use this branch yet,
                        // this is safe for now.
                        continue;
                    }

                    let mut suspend_ctx = ctx.clone();
                    suspend_ctx.program_counter = (2000 + i) as u16;
                    if et == EffectType::TapOpponent {
                        suspend_ctx.player_id = (1 - p_idx) as u8;
                        suspend_ctx.activator_id = ctx.activator_id;
                    }

                    let fake_op = match et {
                        EffectType::LookAndChoose => O_LOOK_AND_CHOOSE,
                        EffectType::SelectMember => O_SELECT_MEMBER,
                        EffectType::TapOpponent => O_TAP_OPPONENT,
                        EffectType::TapMember => O_TAP_MEMBER,
                        EffectType::PlayMemberFromDiscard => O_PLAY_MEMBER_FROM_DISCARD,
                        EffectType::MoveToDiscard => O_MOVE_TO_DISCARD,
                        _ => 0,
                    };
                    
                    let choice_type = match et {
                        EffectType::LookAndChoose => crate::core::enums::ChoiceType::LookAndChoose,
                        EffectType::SelectMember => crate::core::enums::ChoiceType::SelectMember,
                        EffectType::TapOpponent => crate::core::enums::ChoiceType::TapO,
                        EffectType::TapMember => crate::core::enums::ChoiceType::TapMSelect,
                        EffectType::PlayMemberFromDiscard => crate::core::enums::ChoiceType::SelectDiscardPlay,
                        EffectType::MoveToDiscard => crate::core::enums::ChoiceType::SelectDiscard,
                        _ => crate::core::enums::ChoiceType::None,
                    };

                    crate::core::logic::interpreter::suspend_interaction(
                        state, _db, &suspend_ctx, suspend_ctx.program_counter as usize, fake_op, -1, choice_type,
                        "Select target", canonical_filter_attr(ability, &program, i, fake_op), canonical_step_count(step, 1).max(1) as i16
                    );
                    return true;
                }
                _ => {}
            }
        }

        if !execute_canonical_effect_step(state, _db, step, &ctx, p_idx, 0) {
            if let Some(effect) = ability.effects.get(i) {
                resolve_effect_via_runtime(state, _db, &ctx, effect, false);
                if state.phase == crate::core::enums::Phase::Response {
                    return true;
                }
                continue;
            }

            if state.debug.debug_mode {
                println!("[CANONICAL] Unhandled Effect Op: {:?}", op);
            }
            if _id.is_some() { state.clear_execution_id(); }
            return false;
        }
    }

    state.players[p_idx].revealed_cards.clear();

    if _id.is_some() {
        state.clear_execution_id();
    }

    true
}
