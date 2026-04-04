use super::card_db::CardDatabase;
use super::models::AbilityContext;
use super::state::GameState;
use crate::core::enums::{ConditionType, TriggerType};
use crate::core::generated_constants::{
    C_COUNT_BLADES, C_COUNT_HEARTS, O_COLOR_SELECT, O_LOOK_AND_CHOOSE, O_SELECT_CARDS,
    O_SELECT_LIVE, O_SELECT_MEMBER, O_SELECT_MODE, O_SELECT_PLAYER, O_TAP_MEMBER,
    O_TAP_OPPONENT, O_TRIGGER_REMOTE,
};
use crate::core::logic::ability_patterns::should_skip_inline_live_precheck;
use crate::core::logic::Ability;
use crate::core::logic::interpreter::uses_paired_keyword_effect_conditions;

fn should_precheck_trigger_condition(cond: &crate::core::logic::Condition) -> bool {
    !matches!(
        cond.condition_type,
        ConditionType::SumValue | ConditionType::DiscardedCards
    )
}

fn should_defer_trigger_condition_precheck(
    ability: &Ability,
    cond: &crate::core::logic::Condition,
) -> bool {
    let condition_opcode = match cond.condition_type {
        ConditionType::CountBlades => C_COUNT_BLADES,
        ConditionType::CountHearts => C_COUNT_HEARTS,
        _ => return false,
    };

    let mut saw_interactive_prompt = false;
    for frame in ability.resolved_frames().iter() {
        match frame.opcode() {
            O_SELECT_MEMBER
            | O_SELECT_LIVE
            | O_SELECT_PLAYER
            | O_SELECT_MODE
            | O_SELECT_CARDS
            | O_LOOK_AND_CHOOSE
            | O_COLOR_SELECT
            | O_TAP_MEMBER
            | O_TAP_OPPONENT
            | O_TRIGGER_REMOTE => saw_interactive_prompt = true,
            _ => {}
        }

        if frame.opcode() == condition_opcode {
            return saw_interactive_prompt;
        }
    }

    false
}

fn parse_resolution_trigger_subtype(raw_text: &str) -> Option<TriggerType> {
    let type_start = raw_text.find("TYPE=\"")? + 6;
    let type_end = raw_text[type_start..].find('"')? + type_start;
    match &raw_text[type_start..type_end] {
        "ON_LIVE_START" => Some(TriggerType::OnLiveStart),
        "ON_LIVE_SUCCESS" => Some(TriggerType::OnLiveSuccess),
        "ON_PLAY" => Some(TriggerType::OnPlay),
        _ => None,
    }
}

pub(super) fn resolution_trigger_matches_context(
    trigger: TriggerType,
    raw_text: &str,
    ctx_trigger_type: TriggerType,
) -> bool {
    if trigger != TriggerType::OnAbilityResolve && trigger != TriggerType::OnAbilitySuccess {
        return true;
    }

    parse_resolution_trigger_subtype(raw_text)
        .map(|required| required == ctx_trigger_type)
        .unwrap_or(true)
}

fn build_trigger_context(
    state: &GameState,
    p_idx: usize,
    source_cid: i32,
    slot: i16,
    trigger: TriggerType,
    choice: i16,
) -> AbilityContext {
    let mut ctx = AbilityContext {
        player_id: p_idx as u8,
        activator_id: p_idx as u8,
        source_card_id: source_cid,
        area_idx: slot,
        trigger_type: trigger,
        choice_index: choice,
        auto_pick: false,
        ..Default::default()
    };
    let (origin_phase, origin_current_player) = super::interpreter::capture_response_origin(state);
    ctx.capture_state_raw(origin_phase, origin_current_player);
    ctx
}

fn ability_from_db<'a>(
    db: &'a CardDatabase,
    cid: i32,
    is_live: bool,
    ab_idx: usize,
) -> Option<&'a super::models::Ability> {
    if is_live {
        db.get_live(cid)?.abilities.get(ab_idx)
    } else {
        db.get_member(cid)?.abilities.get(ab_idx)
    }
}

fn card_name_from_db<'a>(db: &'a CardDatabase, cid: i32, is_live: bool) -> Option<&'a str> {
    if is_live {
        db.get_live(cid).map(|card| card.name.as_str())
    } else {
        db.get_member(cid).map(|card| card.name.as_str())
    }
}

impl GameState {
    pub fn process_trigger_queue(&mut self, db: &CardDatabase) {
        if self.core.trigger_depth > 0 {
            return;
        }

        self.core.trigger_depth += 1;

        super::interpreter::process_trigger_queue(self, db);

        self.core.trigger_depth -= 1;
    }

    pub fn check_once_per_turn(
        &self,
        p_idx: usize,
        source_type: u8,
        instance_key: u8,
        id: u32,
        ab_idx: usize,
    ) -> bool {
        super::interpreter::check_once_per_turn(self, p_idx, source_type, instance_key, id, ab_idx)
    }

    pub fn consume_once_per_turn(
        &mut self,
        p_idx: usize,
        source_type: u8,
        instance_key: u8,
        id: u32,
        ab_idx: usize,
    ) {
        super::interpreter::consume_once_per_turn(
            self,
            p_idx,
            source_type,
            instance_key,
            id,
            ab_idx,
        );
    }

    pub fn get_once_per_turn_instance_key(
        &self,
        p_idx: usize,
        source_type: u8,
        area_idx: i16,
        card_id: i32,
    ) -> u8 {
        if source_type != 0 {
            return if area_idx >= 0 {
                (area_idx as u8) & 0x0F
            } else {
                0x0F
            };
        }

        let matching_stage_count = self.core.players[p_idx]
            .stage
            .iter()
            .filter(|&&cid| cid == card_id)
            .count();

        if matching_stage_count <= 1 {
            0
        } else if area_idx >= 0 {
            (area_idx as u8) & 0x0F
        } else {
            0x0F
        }
    }

    pub fn is_trigger_negated(&self, p_idx: usize, cid: i32, trigger_type: TriggerType) -> bool {
        let negated = self.core.players[p_idx]
            .negated_triggers
            .iter()
            .find(|entry| entry.0 == cid && entry.1 == trigger_type)
            .map(|entry| entry.2)
            .unwrap_or_default()
            > 0;
        negated
    }

    pub fn trigger_abilities(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
    ) {
        self.trigger_abilities_from(db, trigger, ctx, 0);
    }

    /// PHASE 3: Queues a specific ability for execution.
    pub fn enqueue_trigger(
        &mut self,
        cid: i32,
        ability_card_id: i32,
        ab_idx: u16,
        ctx: AbilityContext,
        is_live: bool,
        trigger: TriggerType,
    ) {
        if !self.ui.silent {
            self.log(format!(
                "Rule 9.7.3: Automatic ability wait state: Trigger {:?} queued for cid={}, ab_idx={}",
                trigger, cid, ab_idx
            ));
        }
        self.core
            .trigger_queue
            .push_back((cid, ability_card_id, ab_idx, ctx, is_live, trigger));
    }

    /// Unified trigger entry point to reduce boilerplate
    pub fn trigger_event(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        p_idx: usize,
        source_cid: i32,
        slot: i16,
        start_ab_idx: usize,
        choice: i16,
    ) {
        let ctx = build_trigger_context(self, p_idx, source_cid, slot, trigger, choice);
        self.trigger_abilities_from(db, trigger, &ctx, start_ab_idx);
    }

    pub fn trigger_global_event(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        source_cid: i32,
        slot: i16,
        start_ab_idx: usize,
        choice: i16,
    ) {
        let cp = self.current_player as usize;
        for i in 0..2 {
            let p_idx = (cp + i) % 2;
            let ctx = build_trigger_context(self, p_idx, source_cid, slot, trigger, choice);
            self.trigger_abilities_from(db, trigger, &ctx, start_ab_idx);
        }
    }

    pub fn trigger_abilities_from(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
    ) {
        // Fast path: vanilla mode or empty board - skip trigger processing
        if db.is_vanilla {
            return;
        }
        
        // Fast path: no cards on board for this player
        let p_idx = ctx.player_id as usize;
        let has_stage_cards = self.core.players[p_idx].stage.iter().any(|&c| c >= 0);
        let has_live_cards = self.core.players[p_idx].live_zone.iter().any(|&c| c >= 0);
        if !has_stage_cards && !has_live_cards && ctx.source_card_id < 0 {
            // Nothing to trigger from
            return;
        }

        if !self.ui.silent {
            println!(
                "[DEBUG] trigger_abilities_from: {:?} for player {}",
                trigger, ctx.player_id
            );
        }

        use smallvec::SmallVec;
        // Collect all potential triggers
        let mut queue = SmallVec::<[(i32, i32, u16, AbilityContext, bool); 8]>::new();
        let p_idx = ctx.player_id as usize;

        // 1. Stage Members
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            self.collect_triggers_for_card(
                db,
                cid,
                trigger,
                ctx,
                start_ab_idx,
                false,
                &mut queue,
                slot_idx as i16,
            );
        }

        // 2. Performance/Live Cards
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            self.collect_triggers_for_card(
                db,
                cid,
                trigger,
                ctx,
                start_ab_idx,
                true,
                &mut queue,
                slot_idx as i16,
            );
        }

        // 3. Source Card (if not on stage/live)
        let source_cid = ctx.source_card_id;
        let on_stage = self.core.players[p_idx]
            .stage
            .iter()
            .any(|&c| c == source_cid);
        let on_live = self.core.players[p_idx]
            .live_zone
            .iter()
            .any(|&c| c == source_cid);
        if !on_stage && !on_live && source_cid >= 0 {
            self.collect_triggers_for_card(
                db,
                source_cid,
                trigger,
                ctx,
                start_ab_idx,
                false,
                &mut queue,
                -1,
            );
            self.collect_triggers_for_card(
                db,
                source_cid,
                trigger,
                ctx,
                start_ab_idx,
                true,
                &mut queue,
                -1,
            );
        }

        for (cid, def_cid, ab_idx, mut ab_ctx, is_live) in queue {
            ab_ctx.source_card_id = cid;
            ab_ctx.ability_card_id = def_cid;
            ab_ctx.ability_index = ab_idx as i16;

            let Some(ability) = ability_from_db(db, def_cid, is_live, ab_idx as usize) else {
                continue;
            };
            let conditions = &ability.conditions;
            // Unified logging: TRIGGER events now go to both turn_history and rule_log
            let card_name = card_name_from_db(db, cid, is_live).unwrap_or("Unknown");
            let trigger_str = super::interpreter::logging::trigger_as_str(trigger);
            self.log_event(
                "TRIGGER",
                &format!(
                    "Rule 9.7.1 (Q221): [{}] Trigger condition met for {}. (Ability is queued for resolution even if source leaves zone later).",
                    trigger_str, card_name
                ),
                cid,
                ab_idx as i16,
                p_idx as u8,
                None,
                true,
            );

            let costs = &ability.costs;

            let skip_precheck_for_compensation =
                is_live && should_skip_inline_live_precheck(ability);

            // Trigger enqueueing only prechecks top-level authored conditions.
            // Inline frame conditions are branch/control-flow logic and must be
            // evaluated by the interpreter in sequence rather than flattened here.
            let mut all_met = true;
            let mut failed_cond_idx = 0;
            if !skip_precheck_for_compensation {
                if uses_paired_keyword_effect_conditions(ability) {
                    // For OR logic, check if any condition passes
                    let mut any_passed = false;
                    for (i, cond) in conditions.iter().enumerate() {
                        let passed = super::interpreter::conditions::check_condition(
                            self, db, p_idx, cond, &ab_ctx, 1,
                        );
                        if self.debug.debug_mode {
                            eprintln!(
                                "[DEBUG_TRIGGER_COND] idx={}, type={:?}, passed={}",
                                i,
                                cond.condition_type,
                                passed
                            );
                        }
                        if passed {
                            any_passed = true;
                            break;
                        }
                    }
                    if !any_passed {
                        all_met = false;
                        failed_cond_idx = 0;
                    }
                } else {
                    // Normal AND logic
                    for (i, cond) in conditions.iter().enumerate() {
                        if !should_precheck_trigger_condition(cond)
                            || should_defer_trigger_condition_precheck(ability, cond)
                        {
                            continue;
                        }
                        let passed = super::interpreter::conditions::check_condition(
                            self, db, p_idx, cond, &ab_ctx, 1,
                        );
                        if self.debug.debug_mode {
                            eprintln!(
                                "[DEBUG_TRIGGER_COND] idx={}, type={:?}, passed={}",
                                i,
                                cond.condition_type,
                                passed
                            );
                        }
                        if !passed {
                            all_met = false;
                            failed_cond_idx = i;
                            break;
                        }
                    }
                }
            }
            if self.debug.debug_mode {
                eprintln!(
                    "[DEBUG_TRIGGER] After condition checks: all_met={}, failed_cond_idx={}",
                    all_met,
                    failed_cond_idx
                );
            }

            if all_met {
                // Check costs as well before enqueueing
                for cost in costs {
                    if cost.is_optional {
                        continue;
                    } // Skip optional costs for trigger check
                    if !super::interpreter::costs::check_cost(self, db, p_idx, cost, &ab_ctx) {
                        all_met = false;
                        break;
                    }
                }
            }

            if all_met {
                // PHASE 3: Queue instead of immediate resolve to decouple mutations
                if self.debug.debug_mode {
                    eprintln!(
                        "[DEBUG_TRIGGER] Enqueuing ability: cid={}, ab_idx={}, trigger={:?}, conditions={}",
                        cid,
                        ab_idx,
                        trigger,
                        conditions.len()
                    );
                }
                self.enqueue_trigger(cid, def_cid, ab_idx as u16, ab_ctx, is_live, trigger);
            } else {
                if self.debug.debug_mode {
                    eprintln!(
                        "[DEBUG_TRIGGER] NOT enqueuing ability: cid={}, ab_idx={}, all_met={}, conditions={}",
                        cid,
                        ab_idx,
                        all_met,
                        conditions.len()
                    );
                }
                if !self.ui.silent {
                    // Log which condition failed
                    for cond in conditions {
                        if !super::interpreter::conditions::check_condition(
                            self, db, p_idx, cond, &ab_ctx, 1,
                        ) {
                            let cond_desc = super::interpreter::logging::describe_condition(
                                cond.condition_type as i32,
                                cond.value,
                                cond.attr,
                            );
                            let card_name = if is_live {
                                db.get_live(cid).unwrap().name.clone()
                            } else {
                                db.get_member(cid).unwrap().name.clone()
                            };
                            self.log(format!("{}'s ability did not activate because target condition was not met: {}.", card_name, cond_desc));
                            break;
                        }
                    }
                }
            }
        }

        self.process_trigger_queue(db);
    }

    fn collect_triggers_for_card(
        &mut self,
        db: &CardDatabase,
        cid: i32,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
        is_live: bool,
        queue: &mut smallvec::SmallVec<[(i32, i32, u16, AbilityContext, bool); 8]>,
        slot_idx: i16,
    ) {
        if cid < 0 {
            return;
        }

        let abilities = if is_live {
            db.get_live(cid).map(|l| &l.abilities)
        } else {
            db.get_member(cid).map(|m| &m.abilities)
        };

        let p_idx = ctx.player_id as usize;
        if let Some(abs) = abilities {
            let has_distinct_optional_mode = trigger == TriggerType::OnLiveSuccess
                && abs.iter().any(|ability| {
                    super::ability_patterns::is_distinct_optional_mode_live_ability(ability)
                });
            for (ab_idx, ab) in abs.iter().enumerate() {
                if ab.trigger == trigger {
                    if has_distinct_optional_mode
                        && ((ab.choice_flags & crate::core::logic::constants::CHOICE_FLAG_MODE)
                            != 0
                            || ab.get_modal_option_frames(0).is_some()
                            || ab.choice_count > 0)
                    {
                        continue;
                    }
                    if !resolution_trigger_matches_context(trigger, &ab.raw_text, ctx.trigger_type)
                    {
                        continue;
                    }

                    // Filter OnPlay/OnLeaves to only the specific card being moved
                    // UNLESS it is a monitoring ability (has a GroupFilter/Score/etc condition)
                    let is_same_slot_instance =
                        slot_idx >= 0 && ctx.area_idx >= 0 && slot_idx == ctx.area_idx;
                    let is_explicit_source_card = slot_idx < 0 && cid == ctx.source_card_id;
                    let is_same_card_different_slot = slot_idx >= 0
                        && ctx.area_idx >= 0
                        && cid == ctx.source_card_id
                        && slot_idx != ctx.area_idx;
                    if (trigger == TriggerType::OnPlay || trigger == TriggerType::OnLeaves)
                        && !is_same_slot_instance
                        && !is_explicit_source_card
                    {
                        if is_same_card_different_slot {
                            continue;
                        }

                        let has_monitor_cond = ab.conditions.iter().any(|c| {
                            c.condition_type == ConditionType::GroupFilter
                                || c.condition_type == ConditionType::ScoreTotalCheck
                        });
                        if !has_monitor_cond {
                            continue;
                        }
                    }

                    if trigger != ctx.trigger_type || ab_idx >= start_ab_idx {
                        // Check and consume negation
                        let mut negated = false;
                        if let Some(entry) = self.core.players[p_idx]
                            .negated_triggers
                            .iter_mut()
                            .find(|entry| entry.0 == cid && entry.1 == trigger)
                        {
                            if entry.2 > 0 {
                                negated = true;
                                entry.2 -= 1;
                            }
                        }

                        if negated {
                            if !self.ui.silent {
                                self.log(format!(
                                    "Trigger {:?} for card {} is negated.",
                                    trigger, cid
                                ));
                            }
                            continue;
                        }
                        let mut trigger_ctx = ctx.clone();
                        trigger_ctx.source_card_id = cid;
                        if slot_idx >= 0 && trigger_ctx.area_idx == -1 {
                            trigger_ctx.area_idx = slot_idx;
                        }
                        queue.push((cid, cid, ab_idx as u16, trigger_ctx, is_live));
                    }
                }
            }
        }

        // --- PHASE 3: Granted (Triggered) Abilities Audit Fix ---
        if !is_live {
            for &(target_cid, source_cid, ab_idx) in &self.core.players[p_idx].granted_abilities {
                if target_cid != cid {
                    continue;
                }

                if let Some(src_m) = db.get_member(source_cid) {
                    if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                        if ab.trigger == trigger {
                            if !resolution_trigger_matches_context(
                                trigger,
                                &ab.raw_text,
                                ctx.trigger_type,
                            ) {
                                continue;
                            }
                            if (trigger == TriggerType::OnPlay || trigger == TriggerType::OnLeaves)
                                && (!(slot_idx >= 0
                                    && ctx.area_idx >= 0
                                    && slot_idx == ctx.area_idx))
                                && !(slot_idx < 0 && cid == ctx.source_card_id)
                            {
                                if slot_idx >= 0
                                    && ctx.area_idx >= 0
                                    && cid == ctx.source_card_id
                                    && slot_idx != ctx.area_idx
                                {
                                    continue;
                                }
                                continue;
                            }
                            queue.push((cid, source_cid, ab_idx as u16, ctx.clone(), false));
                        }
                    }
                }
            }
        }
    }
}
