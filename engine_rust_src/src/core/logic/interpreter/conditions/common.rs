use crate::core::logic::AbilityContext;
use crate::core::logic::constants::*;
use crate::core::logic::ConditionType;
use serde_json::Value;
use std::cell::RefCell;
use std::collections::HashMap;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

pub const CONDITION_CHECK_MAX_DEPTH: u32 = 8;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ConditionEvalCacheKey {
    opcode: i32,
    value: i32,
    raw_attr: u64,
    raw_slot: i32,
    p_idx: usize,
    depth: u32,
    ctx_hash: u64,
    params_hash: u64,
}

thread_local! {
    static ACTIVE_CONDITION_EVAL_CACHE: RefCell<Option<HashMap<ConditionEvalCacheKey, bool>>> =
        const { RefCell::new(None) };
}

pub struct ConditionEvalCacheScope;

impl ConditionEvalCacheScope {
    pub fn activate() -> Self {
        ACTIVE_CONDITION_EVAL_CACHE.with(|cache| {
            *cache.borrow_mut() = Some(HashMap::new());
        });
        Self
    }
}

impl Drop for ConditionEvalCacheScope {
    fn drop(&mut self) {
        ACTIVE_CONDITION_EVAL_CACHE.with(|cache| {
            *cache.borrow_mut() = None;
        });
    }
}

#[inline]
fn hash_value<T: Hash>(value: &T) -> u64 {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish()
}

#[inline]
fn hash_params(params: Option<&Value>) -> u64 {
    params.map(hash_value).unwrap_or_default()
}

#[inline]
pub fn condition_eval_cache_key(
    opcode: i32,
    value: i32,
    raw_attr: u64,
    raw_slot: i32,
    p_idx: usize,
    params: Option<&Value>,
    ctx: &AbilityContext,
    depth: u32,
) -> ConditionEvalCacheKey {
    ConditionEvalCacheKey {
        opcode,
        value,
        raw_attr,
        raw_slot,
        p_idx,
        depth,
        ctx_hash: hash_value(ctx),
        params_hash: hash_params(params),
    }
}

#[inline]
pub fn condition_eval_cache_lookup(key: &ConditionEvalCacheKey) -> Option<bool> {
    ACTIVE_CONDITION_EVAL_CACHE.with(|cache| {
        cache
            .borrow()
            .as_ref()
            .and_then(|active| active.get(key).copied())
    })
}

#[inline]
pub fn condition_eval_cache_store(key: ConditionEvalCacheKey, value: bool) {
    ACTIVE_CONDITION_EVAL_CACHE.with(|cache| {
        if let Some(active) = cache.borrow_mut().as_mut() {
            active.insert(key, value);
        }
    });
}

/// Compare an i32 value against a target with optional comparison mode from slot.
/// Slot encoding: 0 = equal, 1 = greater, 2 = less, 3 = greater-or-equal, 4 = less-or-equal
#[inline]
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
