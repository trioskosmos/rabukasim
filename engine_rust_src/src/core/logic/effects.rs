//! Modern Effect System - Structured effect representation for card abilities
//!
//! This module provides a type-safe, structured representation of card abilities
//! that replaces the bit-packed bytecode approach. Each effect variant contains
//! all necessary parameters as named fields.
//!
//! ## Migration Path
//! 1. AbilityFrame (JSON) -> Effect (structured) -> execute_effect()
//! 2. Eventually: Effect can be serialized directly to/from cards_compiled.json

use crate::core::enums::{EffectType, TargetType, Zone};
use crate::core::logic::filter::CardFilter;
use crate::core::logic::models::AbilityFrame;
use serde::{Deserialize, Serialize};

/// A structured, semantic representation of a single effect.
/// 
/// This enum replaces the bit-packed `AbilityFrame::Semantic` with type-safe
/// variants that have named fields for all parameters.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum Effect {
    /// No operation
    Nop,
    
    /// Early return from ability
    Return,
    
    /// Jump to another effect index
    Jump { offset: i32 },
    
    /// Jump if condition is false
    JumpIfFalse { offset: i32 },
    
    /// Draw cards
    Draw {
        count: i32,
        from: Zone,
        to: Zone,
        target: TargetType,
    },
    
    /// Draw until hand has N cards
    DrawUntil {
        target_hand_size: i32,
        target: TargetType,
    },
    
    /// Add blade tokens
    AddBlades {
        count: i32,
        target: TargetType,
    },
    
    /// Set blade count
    SetBlades {
        count: i32,
        target: TargetType,
    },
    
    /// Add hearts
    AddHearts {
        count: i32,
        target: TargetType,
    },
    
    /// Set heart count
    SetHearts {
        count: i32,
        target: TargetType,
    },
    
    /// Recover live cards from discard
    RecoverLive {
        count: i32,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Recover member cards
    RecoverMember {
        count: i32,
        from: Zone,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Look at top N cards and optionally choose
    LookAndChoose {
        look_count: i32,
        choose_count: i32,
        from: Zone,
        reveal: bool,
        remainder_to: Zone,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Look at top N cards of deck
    LookDeck {
        count: i32,
        target: TargetType,
    },
    
    /// Reveal cards until condition met
    RevealUntil {
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Search deck for cards matching filter
    SearchDeck {
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Order top cards of deck
    OrderDeck {
        count: i32,
        target: TargetType,
    },
    
    /// Move cards between zones
    MoveToDeck {
        count: i32,
        from: Zone,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Move cards to discard
    MoveToDiscard {
        count: i32,
        from: Zone,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Select member cards
    SelectMember {
        count: i32,
        from: Zone,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Select live cards
    SelectLive {
        count: i32,
        from: Zone,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Move member on stage
    MoveMember {
        from_slot: i32,
        to_slot: i32,
        target: TargetType,
    },
    
    /// Formation change
    FormationChange {
        target: TargetType,
    },
    
    /// Tap member
    TapMember {
        slot: i32,
        filter: CardFilter,
        is_cost: bool,
        target: TargetType,
    },
    
    /// Set tapped state
    SetTapped {
        slot: i32,
        tapped: bool,
        target: TargetType,
    },
    
    /// Activate member (untap)
    ActivateMember {
        slot: i32,
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Tap opponent member
    TapOpponent {
        count: i32,
        filter: CardFilter,
    },
    
    /// Charge energy
    EnergyCharge {
        count: i32,
        target: TargetType,
        is_wait: bool,
    },
    
    /// Pay energy cost
    PayEnergy {
        count: i32,
        target: TargetType,
    },
    
    /// Activate energy (convert waiting to active)
    ActivateEnergy {
        count: i32,
        target: TargetType,
    },
    
    /// Add stage energy
    AddStageEnergy {
        count: i32,
        target: TargetType,
    },
    
    /// Boost score
    BoostScore {
        amount: i32,
        target: TargetType,
    },
    
    /// Reduce cost
    ReduceCost {
        amount: i32,
        target: TargetType,
    },
    
    /// Set score
    SetScore {
        value: i32,
        target: TargetType,
    },
    
    /// Buff power
    BuffPower {
        amount: i32,
        target: TargetType,
    },
    
    /// Transform heart color
    TransformHeart {
        from_color: u8,
        to_color: u8,
        target: TargetType,
    },
    
    /// Transform color
    TransformColor {
        from_color: u8,
        to_color: u8,
        target: TargetType,
    },
    
    /// Reduce heart requirement
    ReduceHeartReq {
        amount: i32,
        target: TargetType,
    },
    
    /// Set heart cost
    SetHeartCost {
        cost: i32,
        target: TargetType,
    },
    
    /// Negate effect
    NegateEffect {
        trigger_type: i32,
        count: i32,
        target: TargetType,
    },
    
    /// Meta rule
    MetaRule {
        rule_type: i32,
        target: TargetType,
    },
    
    /// Select mode (modal choice)
    SelectMode {
        option_count: i32,
    },
    
    /// Opponent choice
    OpponentChoose {
        choice_type: i32,
        filter: CardFilter,
    },
    
    /// Play member from hand
    PlayMemberFromHand {
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Play member from discard
    PlayMemberFromDiscard {
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Play live from discard
    PlayLiveFromDiscard {
        filter: CardFilter,
        target: TargetType,
    },
    
    /// Grant ability
    GrantAbility {
        ability_id: i32,
        target: TargetType,
    },
    
    /// Place under member
    PlaceUnder {
        source: Zone,
        target: TargetType,
    },
    
    /// Swap cards
    SwapCards {
        target: TargetType,
    },
    
    /// Swap zones
    SwapZone {
        zone1: Zone,
        zone2: Zone,
        target: TargetType,
    },
    
    /// Swap area
    SwapArea {
        target: TargetType,
    },
    
    /// Reveal cards
    RevealCards {
        count: i32,
        from: Zone,
        target: TargetType,
    },
    
    /// Cheer reveal
    CheerReveal {
        count: i32,
        target: TargetType,
    },
    
    /// Color select
    ColorSelect {
        target: TargetType,
    },
    
    /// Trigger remote ability
    TriggerRemote {
        ability_id: i32,
        target: TargetType,
    },
    
    /// Reduce yell count
    ReduceYellCount {
        amount: i32,
    },
    
    /// Increase cost
    IncreaseCost {
        amount: i32,
        target: TargetType,
    },
    
    /// Increase heart cost
    IncreaseHeartCost {
        amount: i32,
        target: TargetType,
    },
    
    /// Reduce score
    ReduceScore {
        amount: i32,
        target: TargetType,
    },
    
    /// Transform blades
    TransformBlades {
        target: TargetType,
    },
    
    /// Lose excess hearts
    LoseExcessHearts {
        target: TargetType,
    },
    
    /// Skip activate phase
    SkipActivatePhase,
    
    /// Prevent activation
    PreventActivate {
        target: TargetType,
    },
    
    /// Prevent baton touch
    PreventBatonTouch {
        target: TargetType,
    },
    
    /// Prevent play to slot
    PreventPlayToSlot {
        target: TargetType,
    },
    
    /// Prevent set to success pile
    PreventSetToSuccessPile {
        target: TargetType,
    },
    
    /// Reduce live set limit
    ReduceLiveSetLimit {
        amount: i32,
    },
    
    /// Immunity
    Immunity {
        target: TargetType,
    },
    
    /// Baton touch mod
    BatonTouchMod {
        target: TargetType,
    },
    
    /// Calc sum cost
    CalcSumCost,
    
    /// Div value
    DivValue,
    
    /// Repeat ability
    RepeatAbility {
        count: i32,
    },
    
    /// Set target self
    SetTargetSelf,
    
    /// Set target opponent
    SetTargetOpponent,
    
    /// Look reorder discard
    LookReorderDiscard {
        count: i32,
    },
    
    /// Look deck dynamic
    LookDeckDynamic,
    
    /// Pay energy dynamic
    PayEnergyDynamic,
    
    /// Place energy under member
    PlaceEnergyUnderMember,
    
    /// Restriction
    Restriction {
        restriction_type: i32,
    },
}

impl Effect {
    /// Get the EffectType for this effect
    pub fn effect_type(&self) -> EffectType {
        match self {
            Effect::Nop => EffectType::Nop,
            Effect::Return => EffectType::Return,
            Effect::Jump { .. } => EffectType::Jump,
            Effect::JumpIfFalse { .. } => EffectType::JumpIfFalse,
            Effect::Draw { .. } => EffectType::Draw,
            Effect::DrawUntil { .. } => EffectType::DrawUntil,
            Effect::AddBlades { .. } => EffectType::AddBlades,
            Effect::SetBlades { .. } => EffectType::SetBlades,
            Effect::AddHearts { .. } => EffectType::AddHearts,
            Effect::SetHearts { .. } => EffectType::SetHearts,
            Effect::RecoverLive { .. } => EffectType::RecoverLive,
            Effect::RecoverMember { .. } => EffectType::RecoverMember,
            Effect::LookAndChoose { .. } => EffectType::LookAndChoose,
            Effect::LookDeck { .. } => EffectType::LookDeck,
            Effect::RevealUntil { .. } => EffectType::RevealUntil,
            Effect::SearchDeck { .. } => EffectType::SearchDeck,
            Effect::OrderDeck { .. } => EffectType::OrderDeck,
            Effect::MoveToDeck { .. } => EffectType::MoveToDeck,
            Effect::MoveToDiscard { .. } => EffectType::MoveToDiscard,
            Effect::SelectMember { .. } => EffectType::SelectMember,
            Effect::SelectLive { .. } => EffectType::SelectLive,
            Effect::MoveMember { .. } => EffectType::MoveMember,
            Effect::FormationChange { .. } => EffectType::FormationChange,
            Effect::TapMember { .. } => EffectType::TapMember,
            Effect::SetTapped { .. } => EffectType::SetTapped,
            Effect::ActivateMember { .. } => EffectType::ActivateMember,
            Effect::TapOpponent { .. } => EffectType::TapOpponent,
            Effect::EnergyCharge { .. } => EffectType::EnergyCharge,
            Effect::PayEnergy { .. } => EffectType::PayEnergy,
            Effect::ActivateEnergy { .. } => EffectType::ActivateEnergy,
            Effect::AddStageEnergy { .. } => EffectType::AddStageEnergy,
            Effect::BoostScore { .. } => EffectType::BoostScore,
            Effect::ReduceCost { .. } => EffectType::ReduceCost,
            Effect::SetScore { .. } => EffectType::SetScore,
            Effect::BuffPower { .. } => EffectType::BuffPower,
            Effect::TransformHeart { .. } => EffectType::TransformHeart,
            Effect::TransformColor { .. } => EffectType::TransformColor,
            Effect::ReduceHeartReq { .. } => EffectType::ReduceHeartReq,
            Effect::SetHeartCost { .. } => EffectType::SetHeartCost,
            Effect::NegateEffect { .. } => EffectType::NegateEffect,
            Effect::MetaRule { .. } => EffectType::MetaRule,
            Effect::SelectMode { .. } => EffectType::SelectMode,
            Effect::OpponentChoose { .. } => EffectType::OpponentChoose,
            Effect::PlayMemberFromHand { .. } => EffectType::PlayMemberFromHand,
            Effect::PlayMemberFromDiscard { .. } => EffectType::PlayMemberFromDiscard,
            Effect::PlayLiveFromDiscard { .. } => EffectType::PlayLiveFromDiscard,
            Effect::GrantAbility { .. } => EffectType::GrantAbility,
            Effect::PlaceUnder { .. } => EffectType::PlaceUnder,
            Effect::SwapCards { .. } => EffectType::SwapCards,
            Effect::SwapZone { .. } => EffectType::SwapZone,
            Effect::SwapArea { .. } => EffectType::SwapArea,
            Effect::RevealCards { .. } => EffectType::RevealCards,
            Effect::CheerReveal { .. } => EffectType::CheerReveal,
            Effect::ColorSelect { .. } => EffectType::ColorSelect,
            Effect::TriggerRemote { .. } => EffectType::TriggerRemote,
            Effect::ReduceYellCount { .. } => EffectType::ReduceYellCount,
            Effect::IncreaseCost { .. } => EffectType::IncreaseCost,
            Effect::IncreaseHeartCost { .. } => EffectType::IncreaseHeartCost,
            Effect::ReduceScore { .. } => EffectType::ReduceScore,
            Effect::TransformBlades { .. } => EffectType::TransformBlades,
            Effect::LoseExcessHearts { .. } => EffectType::LoseExcessHearts,
            Effect::SkipActivatePhase => EffectType::SkipActivatePhase,
            Effect::PreventActivate { .. } => EffectType::PreventActivate,
            Effect::PreventBatonTouch { .. } => EffectType::PreventBatonTouch,
            Effect::PreventPlayToSlot { .. } => EffectType::PreventPlayToSlot,
            Effect::PreventSetToSuccessPile { .. } => EffectType::PreventSetToSuccessPile,
            Effect::ReduceLiveSetLimit { .. } => EffectType::ReduceLiveSetLimit,
            Effect::Immunity { .. } => EffectType::Immunity,
            Effect::BatonTouchMod { .. } => EffectType::BatonTouchMod,
            Effect::CalcSumCost => EffectType::CalcSumCost,
            Effect::DivValue => EffectType::DivValue,
            Effect::RepeatAbility { .. } => EffectType::RepeatAbility,
            Effect::SetTargetSelf => EffectType::SetTargetSelf,
            Effect::SetTargetOpponent => EffectType::SetTargetOpponent,
            Effect::LookReorderDiscard { .. } => EffectType::LookReorderDiscard,
            Effect::LookDeckDynamic => EffectType::LookDeckDynamic,
            Effect::PayEnergyDynamic => EffectType::PayEnergyDynamic,
            Effect::PlaceEnergyUnderMember => EffectType::PlaceEnergyUnderMember,
            Effect::Restriction { .. } => EffectType::Restriction,
        }
    }
    
    /// Check if this effect is a cost
    pub fn is_cost(&self) -> bool {
        match self {
            Effect::TapMember { is_cost, .. } => *is_cost,
            Effect::PayEnergy { .. } => true,
            Effect::PayEnergyDynamic => true,
            _ => false,
        }
    }
}

/// Convert from AbilityFrame to structured Effect
/// 
/// This provides a migration path from the old frame system to the new
/// structured effect system.
pub fn frame_to_effect(frame: &AbilityFrame) -> Option<Effect> {
    use crate::core::enums::*;
    
    match frame {
        AbilityFrame::Return => Some(Effect::Return),
        
        AbilityFrame::Draw { count, slot, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            Some(Effect::Draw {
                count: *count,
                from: Zone::Deck,
                to: Zone::Hand,
                target,
            })
        }
        
        AbilityFrame::RecoverLive { count, filter, slot, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            Some(Effect::RecoverLive {
                count: *count,
                filter: *filter,
                target,
            })
        }
        
        AbilityFrame::RecoverMember { count, filter, slot, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            Some(Effect::RecoverMember {
                count: *count,
                from: Zone::Discard,
                filter: *filter,
                target,
            })
        }
        
        AbilityFrame::LookAndChoose { count, choose_count, reveal, dest_discard, filter, slot, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            let remainder_to = if *dest_discard { Zone::Discard } else { Zone::Deck };
            Some(Effect::LookAndChoose {
                look_count: *count,
                choose_count: *choose_count,
                from: Zone::Deck,
                reveal: *reveal,
                remainder_to,
                filter: *filter,
                target,
            })
        }
        
        AbilityFrame::SelectMember { count, filter, slot, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            Some(Effect::SelectMember {
                count: *count,
                from: Zone::Deck,
                filter: *filter,
                target,
            })
        }
        
        AbilityFrame::MoveMember { filter, slot, from_slot, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            Some(Effect::MoveMember {
                from_slot: *from_slot,
                to_slot: slot.target_slot as i32,
                target,
            })
        }
        
        AbilityFrame::MetaRule { rule_type, filter, slot, .. } => {
            let _target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            Some(Effect::MetaRule {
                rule_type: *rule_type,
                target: TargetType::Player,
            })
        }
        
        AbilityFrame::Semantic { opcode, value, filter, slot, is_cost, .. } => {
            let target = if slot.is_opponent { TargetType::Opponent } else { TargetType::Player };
            
            // Convert semantic frames based on opcode
            match *opcode {
                O_DRAW => Some(Effect::Draw {
                    count: *value,
                    from: Zone::Deck,
                    to: Zone::Hand,
                    target,
                }),
                O_DRAW_UNTIL => Some(Effect::DrawUntil {
                    target_hand_size: *value,
                    target,
                }),
                O_RECOVER_LIVE => Some(Effect::RecoverLive {
                    count: *value,
                    filter: *filter,
                    target,
                }),
                O_RECOVER_MEMBER => Some(Effect::RecoverMember {
                    count: *value,
                    from: slot.source_zone.into(),
                    filter: *filter,
                    target,
                }),
                O_LOOK_AND_CHOOSE => Some(Effect::LookAndChoose {
                    look_count: *value,
                    choose_count: 1, // Default, would need frame data
                    from: Zone::Deck,
                    reveal: false,
                    remainder_to: Zone::Deck,
                    filter: *filter,
                    target,
                }),
                O_TAP_MEMBER => Some(Effect::TapMember {
                    slot: slot.target_slot as i32,
                    filter: *filter,
                    is_cost: *is_cost,
                    target,
                }),
                O_SET_TAPPED => Some(Effect::SetTapped {
                    slot: slot.target_slot as i32,
                    tapped: *value != 0,
                    target,
                }),
                O_ACTIVATE_MEMBER => Some(Effect::ActivateMember {
                    slot: slot.target_slot as i32,
                    filter: *filter,
                    target,
                }),
                O_ENERGY_CHARGE => Some(Effect::EnergyCharge {
                    count: *value,
                    target,
                    is_wait: false,
                }),
                O_PAY_ENERGY => Some(Effect::PayEnergy {
                    count: *value,
                    target,
                }),
                O_BOOST_SCORE => Some(Effect::BoostScore {
                    amount: *value,
                    target,
                }),
                O_REDUCE_COST => Some(Effect::ReduceCost {
                    amount: *value,
                    target,
                }),
                O_SET_SCORE => Some(Effect::SetScore {
                    value: *value,
                    target,
                }),
                O_SELECT_MODE => Some(Effect::SelectMode {
                    option_count: *value,
                }),
                _ => None, // Unknown semantic frame
            }
        }
        
        AbilityFrame::Raw { .. } => None, // Can't convert raw frames without more context
    }
}

/// A program of effects - the modern replacement for FrameProgram
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct EffectProgram {
    pub effects: Vec<Effect>,
}

impl EffectProgram {
    /// Create from a slice of AbilityFrames (migration helper)
    pub fn from_frames(frames: &[AbilityFrame]) -> Self {
        let effects: Vec<Effect> = frames
            .iter()
            .filter_map(frame_to_effect)
            .collect();
        Self { effects }
    }
    
    /// Get effect at index
    pub fn get(&self, idx: usize) -> Option<&Effect> {
        self.effects.get(idx)
    }
    
    /// Number of effects
    pub fn len(&self) -> usize {
        self.effects.len()
    }
    
    pub fn is_empty(&self) -> bool {
        self.effects.is_empty()
    }
}
