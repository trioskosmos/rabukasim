use crate::core::logic::ConditionType;
use crate::core::logic::constants::*;

pub const MAX_CONDITION_CHECK_DEPTH: u32 = 8;

/// Compare an i32 value against a target with optional comparison mode from slot.
/// Slot encoding: 0 = equal, 1 = greater, 2 = less, 3 = greater-or-equal, 4 = less-or-equal
pub fn compare_i32(actual: i32, target: i32, slot: i32) -> bool {
    let mode = (slot >> 4) & 0x0F;
    match mode {
        COMP_GT => actual > target,
        COMP_LT => actual < target,
        COMP_GE => actual >= target,
        COMP_LE => actual <= target,
        _ => actual == target, // default: equal (COMP_EQ: 0)
    }
}

pub fn parse_condition_type(value: i32) -> ConditionType {
    match value {
        200 => ConditionType::Turn1,
        201 => ConditionType::HasMember,
        202 => ConditionType::HasColor,
        203 => ConditionType::CountStage,
        204 => ConditionType::CountHand,
        205 => ConditionType::CountDiscard,
        206 => ConditionType::IsCenter,
        207 => ConditionType::LifeLead,
        208 => ConditionType::CountGroup,
        209 => ConditionType::GroupFilter,
        210 => ConditionType::OpponentHas,
        211 => ConditionType::SelfIsGroup,
        212 => ConditionType::ModalAnswer,
        213 => ConditionType::CountEnergy,
        214 => ConditionType::HasLiveCard,
        215 => ConditionType::CostCheck,
        216 => ConditionType::RarityCheck,
        217 => ConditionType::HandHasNoLive,
        218 => ConditionType::CountSuccessLive,
        219 => ConditionType::OpponentHandDiff,
        220 => ConditionType::ScoreCompare,
        221 => ConditionType::HasChoice,
        222 => ConditionType::OpponentChoice,
        223 => ConditionType::CountHearts,
        224 => ConditionType::CountBlades,
        225 => ConditionType::OpponentEnergyDiff,
        226 => ConditionType::HasKeyword,
        227 => ConditionType::DeckRefreshed,
        228 => ConditionType::HasMoved,
        229 => ConditionType::HandIncreased,
        230 => ConditionType::CountLiveZone,
        231 => ConditionType::Baton,
        232 => ConditionType::TypeCheck,
        233 => ConditionType::IsInDiscard,
        234 => ConditionType::AreaCheck,
        235 => ConditionType::CostLead,
        236 => ConditionType::ScoreLead,
        237 => ConditionType::HeartLead,
        238 => ConditionType::HasExcessHeart,
        239 => ConditionType::NotHasExcessHeart,
        240 => ConditionType::TotalBlades,
        241 => ConditionType::CostCompare,
        242 => ConditionType::BladeCompare,
        243 => ConditionType::HeartCompare,
        244 => ConditionType::OpponentHasWait,
        245 => ConditionType::IsTapped,
        246 => ConditionType::IsActive,
        247 => ConditionType::LivePerformed,
        248 => ConditionType::IsPlayer,
        249 => ConditionType::IsOpponent,
        250 => ConditionType::CountUniqueColors,
        301 => ConditionType::CountEnergyExact,
        302 => ConditionType::CountBladeHeartTypes,
        303 => ConditionType::OpponentHasExcessHeart,
        304 => ConditionType::ScoreTotalCheck,
        305 => ConditionType::MainPhase,
        306 => ConditionType::SelectMember,
        307 => ConditionType::SuccessPileCount,
        308 => ConditionType::IsSelfMove,
        309 => ConditionType::DiscardedCards,
        310 => ConditionType::YellRevealedUniqueColors,
        311 => ConditionType::SyncCost,
        312 => ConditionType::SumValue,
        313 => ConditionType::IsWait,
        314 => ConditionType::OnAbilityResolve,
        315 => ConditionType::TargetMemberHasNoHearts,
        _ => ConditionType::None,
    }
}
