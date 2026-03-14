use crate::core::enums::{TriggerType, ConditionType};
use super::state::GameState;
use super::card_db::CardDatabase;
use super::models::AbilityContext;
use super::constants::MAX_CONDITION_CHECK_DEPTH;

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

impl GameState {
    pub fn process_trigger_queue(&mut self, db: &CardDatabase) {
        super::interpreter::process_trigger_queue(self, db);
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
        super::interpreter::consume_once_per_turn(self, p_idx, source_type, instance_key, id, ab_idx);
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
        let player = &self.core.players[p_idx];
        player
            .negated_triggers
            .iter()
            .any(|(t_cid, t_trigger, _)| *t_cid == cid && *t_trigger == trigger_type)
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
        ab_idx: u16,
        ctx: AbilityContext,
        is_live: bool,
        trigger: TriggerType,
    ) {
        self.core
            .trigger_queue
            .push_back((cid, ab_idx, ctx, is_live, trigger));
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
        let ctx = AbilityContext {
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            source_card_id: source_cid,
            area_idx: slot,
            trigger_type: trigger,
            choice_index: choice,
            auto_pick: false,
            ..Default::default()
        };
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
        self.trigger_depth += 1;
        let cp = self.current_player as usize;
        for i in 0..2 {
            let p_idx = (cp + i) % 2;
            let ctx = AbilityContext {
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                source_card_id: source_cid,
                area_idx: slot,
                trigger_type: trigger,
                choice_index: choice,
                ..Default::default()
            };
            self.trigger_abilities_from_internal(db, trigger, &ctx, start_ab_idx);
        }
        self.trigger_depth -= 1;
        if self.trigger_depth == 0 {
            self.process_trigger_queue(db);
        }
    }

    fn trigger_abilities_from_internal(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
    ) {
        // Collect all potential triggers
        let mut queue = Vec::new();
        let p_idx = ctx.player_id as usize;

        // Stage Members
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, false, &mut queue, slot_idx as i16);
        }

        // Performance/Live Cards
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, true, &mut queue, slot_idx as i16);
        }

        for (cid, _def_cid, ab_idx, mut ab_ctx, is_live) in queue {
            ab_ctx.source_card_id = cid;
            ab_ctx.ability_index = ab_idx as i16;
            self.enqueue_trigger(cid, ab_idx as u16, ab_ctx, is_live, trigger);
        }
    }

    pub fn trigger_abilities_from(
        &mut self,
        db: &CardDatabase,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
    ) {
        // VANILLA OPTIMIZATION: No abilities in vanilla mode
        if db.is_vanilla {
            return;
        }

        if self.trigger_depth as u32 > MAX_CONDITION_CHECK_DEPTH {
            if !self.ui.silent {
                println!("[DEBUG] Trigger depth limit reached for {:?}.", trigger);
            }
            return;
        }
        if !self.ui.silent {
            println!("[DEBUG] trigger_abilities_from: {:?} for player {}", trigger, ctx.player_id);
        }
        self.trigger_depth += 1;

        // Collect all potential triggers
        let mut queue = Vec::new();
        let p_idx = ctx.player_id as usize;

        // 1. Stage Members
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].stage[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, false, &mut queue, slot_idx as i16);
        }

        // 2. Performance/Live Cards
        for slot_idx in 0..3 {
            let cid = self.core.players[p_idx].live_zone[slot_idx];
            self.collect_triggers_for_card(db, cid, trigger, ctx, start_ab_idx, true, &mut queue, slot_idx as i16);
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
            ab_ctx.ability_index = ab_idx as i16;

            let (_bytecode, conditions, _pseudocode) = if is_live {
                let ab = &db.get_live(def_cid).unwrap().abilities[ab_idx as usize];
                (&ab.bytecode, &ab.conditions, &ab.pseudocode)
            } else {
                let ab = &db.get_member(def_cid).unwrap().abilities[ab_idx as usize];
                (&ab.bytecode, &ab.conditions, &ab.pseudocode)
            };

            // Unified logging: TRIGGER events now go to both turn_history and rule_log
            let card_name = if is_live {
                db.get_live(cid).unwrap().name.clone()
            } else {
                db.get_member(cid).unwrap().name.clone()
            };
            let trigger_str = super::interpreter::logging::trigger_as_str(trigger);
            self.log_event(
                "TRIGGER",
                &format!("[{}] Triggered for {}", trigger_str, card_name),
                cid,
                ab_idx as i16,
                p_idx as u8,
                None,
                true, // Also log to rule_log for visibility
            );

            let costs = if is_live {
                &db.get_live(def_cid).unwrap().abilities[ab_idx as usize].costs
            } else {
                &db.get_member(def_cid).unwrap().abilities[ab_idx as usize].costs
            };

            let skip_precheck_for_compensation = if is_live {
                db.get_live(def_cid)
                    .map(|card| {
                        (card.card_no == "PL!-bp5-021-L"
                            && trigger == TriggerType::OnLiveStart
                            && ab_idx == 0)
                            || (card.card_no == "PL!N-bp4-030-L"
                                && trigger == TriggerType::OnLiveSuccess
                                && ab_idx == 0
                                && self.core.players[p_idx]
                                    .success_lives
                                    .iter()
                                    .copied()
                                    .any(|success_cid| self.card_matches_filter(db, success_cid, 80)))
                    })
                    .unwrap_or(false)
            } else {
                false
            };

            // Check conditions before resolving bytecode
            let mut all_met = true;
            if !skip_precheck_for_compensation {
                for cond in conditions {
                    if !super::interpreter::conditions::check_condition(
                        self, db, p_idx, cond, &ab_ctx, 1,
                    ) {
                        all_met = false;
                        break;
                    }
                }
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
                self.enqueue_trigger(cid, ab_idx as u16, ab_ctx, is_live, trigger);
            } else {
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

        self.trigger_depth -= 1;
        if self.trigger_depth == 0 {
            self.process_trigger_queue(db);
        }
    }

    fn collect_triggers_for_card(
        &mut self,
        db: &CardDatabase,
        cid: i32,
        trigger: TriggerType,
        ctx: &AbilityContext,
        start_ab_idx: usize,
        is_live: bool,
        queue: &mut Vec<(i32, i32, u16, AbilityContext, bool)>,
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
            for (ab_idx, ab) in abs.iter().enumerate() {
                if ab.trigger == trigger {
                    if !resolution_trigger_matches_context(trigger, &ab.raw_text, ctx.trigger_type) {
                        continue;
                    }
                    
                    // Filter OnPlay/OnLeaves to only the specific card being moved
                    // UNLESS it is a monitoring ability (has a GroupFilter/Score/etc condition)
                    let is_same_slot_instance = slot_idx >= 0
                        && ctx.area_idx >= 0
                        && slot_idx == ctx.area_idx;
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
                        if let Some(n_idx) = self.core.players[p_idx]
                            .negated_triggers
                            .iter()
                            .position(|&(t_cid, t_trig, count)| {
                                t_cid == cid && t_trig == trigger && count > 0
                            })
                        {
                            self.core.players[p_idx].negated_triggers[n_idx].2 -= 1;
                            negated = true;
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
            for i in 0..self.core.players[p_idx].granted_abilities.len() {
                let (target_cid, source_cid, ab_idx) =
                    self.core.players[p_idx].granted_abilities[i];
                if target_cid == cid {
                    if let Some(src_m) = db.get_member(source_cid) {
                        if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                            if ab.trigger == trigger {
                                if !resolution_trigger_matches_context(trigger, &ab.raw_text, ctx.trigger_type) {
                                    continue;
                                }
                                if (trigger == TriggerType::OnPlay
                                    || trigger == TriggerType::OnLeaves)
                                    && (!(
                                        slot_idx >= 0
                                            && ctx.area_idx >= 0
                                            && slot_idx == ctx.area_idx
                                    ))
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
}