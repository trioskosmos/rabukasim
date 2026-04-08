use super::card_db::CardDatabase;
use super::filter::CardFilter;
use super::models::AbilityContext;
use super::state::GameState;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::models::LiveCard;
use rand::seq::SliceRandom;
// use rand::SeedableRng;
use super::models::DeckStats;
use rand_pcg::Pcg64;
use std::time::Instant;
use std::cell::RefCell;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, Hash, PartialEq, Eq)]
struct FilterCacheKey {
    cid: i32,
    filter_attr: u64,
    checked_player: u8,
    checked_area: i16,
    player_id: u8,
    activator_id: u8,
    source_card_id: i32,
    area_idx: i16,
    trigger_type: i32,
    choice_index: i16,
    program_counter: u16,
    is_static_eval: bool,
    auto_pick: bool,
}

thread_local! {
    static ACTIVE_FILTER_MATCH_CACHE: RefCell<Option<HashMap<FilterCacheKey, bool>>> =
        const { RefCell::new(None) };
}

pub struct FilterMatchCacheScope;

impl FilterMatchCacheScope {
    pub fn activate() -> Self {
        ACTIVE_FILTER_MATCH_CACHE.with(|cache| {
            *cache.borrow_mut() = Some(HashMap::new());
        });
        Self
    }
}

impl Drop for FilterMatchCacheScope {
    fn drop(&mut self) {
        ACTIVE_FILTER_MATCH_CACHE.with(|cache| {
            *cache.borrow_mut() = None;
        });
    }
}

impl GameState {
    fn filter_cache_lookup(
        &self,
        cid: i32,
        filter_attr: u64,
        checked_slot: Option<(u8, i16)>,
        ctx: &AbilityContext,
    ) -> Option<bool> {
        let (checked_player, checked_area) = checked_slot.unwrap_or((u8::MAX, i16::MIN));
        let key = FilterCacheKey {
            cid,
            filter_attr,
            checked_player,
            checked_area,
            player_id: ctx.player_id,
            activator_id: ctx.activator_id,
            source_card_id: ctx.source_card_id,
            area_idx: ctx.area_idx,
            trigger_type: ctx.trigger_type as i32,
            choice_index: ctx.choice_index,
            program_counter: ctx.program_counter,
            is_static_eval: ctx.is_static_eval,
            auto_pick: ctx.auto_pick,
        };

        ACTIVE_FILTER_MATCH_CACHE.with(|cache| {
            cache
                .borrow()
                .as_ref()
                .and_then(|map| map.get(&key).copied())
        })
    }

    fn filter_cache_store(
        &self,
        cid: i32,
        filter_attr: u64,
        checked_slot: Option<(u8, i16)>,
        ctx: &AbilityContext,
        value: bool,
    ) {
        let (checked_player, checked_area) = checked_slot.unwrap_or((u8::MAX, i16::MIN));
        let key = FilterCacheKey {
            cid,
            filter_attr,
            checked_player,
            checked_area,
            player_id: ctx.player_id,
            activator_id: ctx.activator_id,
            source_card_id: ctx.source_card_id,
            area_idx: ctx.area_idx,
            trigger_type: ctx.trigger_type as i32,
            choice_index: ctx.choice_index,
            program_counter: ctx.program_counter,
            is_static_eval: ctx.is_static_eval,
            auto_pick: ctx.auto_pick,
        };

        ACTIVE_FILTER_MATCH_CACHE.with(|cache| {
            if let Some(map) = cache.borrow_mut().as_mut() {
                map.insert(key, value);
            }
        });
    }

    fn rule_profile_enabled() -> bool {
        std::env::var("BENCH_PROFILE_RULE_CHECKS")
            .ok()
            .map(|value| {
                let value = value.trim();
                !matches!(value, "0" | "false" | "FALSE" | "off" | "OFF")
            })
            .unwrap_or(false)
    }

    pub fn resolve_deck_refresh(&mut self, player_idx: usize) {
        if !self.ui.silent {
            self.log(format!(
                "Rule 4.4.2: Player {}'s main deck is empty. Refreshing from discard.",
                player_idx
            ));
        }

        // Use current state to seed the shuffle for deterministic replay if needed
        let player = &mut self.core.players[player_idx];
        player.cached_deck_stats = DeckStats::default();
        let mut discard_cards: Vec<i32> = player.discard.drain(..).collect();

        // Shuffle discard
        use rand::SeedableRng;
        let mut rng = Pcg64::seed_from_u64(self.core.turn as u64 * 1000 + player_idx as u64);
        discard_cards.shuffle(&mut rng);

        // Main deck's new cards go AFTER any remaining cards (Rule 10.2.3).
        // Deck top is the vector end, so refreshed cards belong at the front.
        let mut refreshed = smallvec::SmallVec::<[i32; 60]>::new();
        refreshed.extend(discard_cards.into_iter().rev());
        refreshed.extend(player.deck.drain(..));
        player.deck = refreshed;

        // Safety cap: Never exceed 60 cards in total deck (prevents unintended growth)
        if player.deck.len() > 60 {
            player.deck.truncate(60);
        }

        player.set_flag(
            crate::core::logic::player::PlayerState::FLAG_DECK_REFRESHED,
            true,
        );
    }

    pub fn check_win_condition(&mut self) {
        if self.phase == Phase::Terminal {
            return;
        }

        let p0_win = self.core.players[0].success_lives.len() >= 3;
        let p1_win = self.core.players[1].success_lives.len() >= 3;

        if p0_win || p1_win {
            self.phase = Phase::Terminal;
            let msg = match (p0_win, p1_win) {
                (true, false) => "Rule 1.2.1.1: Player 0 wins by 3 successful lives.",
                (false, true) => "Rule 1.2.1.1: Player 1 wins by 3 successful lives.",
                _ => "Rule 1.2.1.2: Draw (Both players reached 3 successful lives).",
            };
            self.log(msg.to_string());
        }
    }

    pub fn is_terminal(&self) -> bool {
        self.phase == Phase::Terminal
    }

    pub fn process_rule_checks(&mut self, db: &CardDatabase) {
        if !self.ui.silent {
            self.log("Rule 10.1, Rule 10.1.2: Performing check timing (State-Based Actions).".to_string());
        }
        let profile_enabled = Self::rule_profile_enabled();
        let profile_start = if profile_enabled {
            Some(Instant::now())
        } else {
            None
        };
        let mut deck_refresh_us = 0u64;
        let mut energy_reclaim_us = 0u64;
        let mut sync_us = 0u64;
        let win_check_us;
        let trigger_queue_us;
        for i in 0..2 {
            // 1. Deck Refresh (Rule 4.4.2)
            if self.core.players[i].deck.is_empty() && !self.core.players[i].discard.is_empty() {
                if self.core.players[i]
                    .get_flag(super::player::PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH)
                {
                    self.core.players[i].set_flag(
                        super::player::PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH,
                        false,
                    );
                } else {
                    let t = profile_enabled.then(Instant::now);
                    self.resolve_deck_refresh(i);
                    deck_refresh_us += t
                        .map(|t| t.elapsed().as_nanos() as u64 / 1000)
                        .unwrap_or(0);
                }
            }

            // 2. Energy in empty member area -> Energy Deck (Rule 10.5.3)
            let t_energy = profile_enabled.then(Instant::now);
            for slot_idx in 0..3 {
                if self.core.players[i].stage[slot_idx] < 0
                    && self.core.players[i].stage_energy_count[slot_idx] > 0
                {
                    if !self.ui.silent {
                        self.log(format!(
                            "Rule 10.5.3: Reclaiming energy from empty slot {} for player {}.",
                            slot_idx, i
                        ));
                    }
                    let reclaimed: Vec<i32> = self.core.players[i].stage_energy[slot_idx]
                        .drain(..)
                        .collect();
                    self.core.players[i].energy_deck.extend(reclaimed);
                    self.core.players[i].stage_energy_count[slot_idx] = 0;

                    // Energy deck is unordered; shuffle to maintain randomness.
                    use rand::SeedableRng;
                    let mut rng = Pcg64::seed_from_u64(
                        self.core.turn as u64 * 31 + i as u64 * 7 + slot_idx as u64,
                    );
                    self.core.players[i].energy_deck.shuffle(&mut rng);
                }
            }
            energy_reclaim_us += t_energy
                .map(|t| t.elapsed().as_nanos() as u64 / 1000)
                .unwrap_or(0);
        }

        // Only resync players that actually changed. The dirty mask is already
        // maintained by the effect handlers, so there is no reason to rebuild
        // both board auras after every state-based check.
        let t_sync = profile_enabled.then(Instant::now);
        self.sync_all_stats(db);
        sync_us += t_sync
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        let t_win = profile_enabled.then(Instant::now);
        self.check_win_condition();
        win_check_us = t_win
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);
        let t_trigger_queue = profile_enabled.then(Instant::now);
        self.process_trigger_queue(db);
        trigger_queue_us = t_trigger_queue
            .map(|t| t.elapsed().as_nanos() as u64 / 1000)
            .unwrap_or(0);

        if let Some(profile_start) = profile_start {
            let total_us = profile_start.elapsed().as_nanos() as u64 / 1000;
            if total_us >= 1000 && !self.ui.silent && self.debug.debug_mode {
                println!(
                    "[PROFILE] RuleChecks total_us={} deck_refresh_us={} energy_reclaim_us={} sync_us={} win_check_us={} trigger_queue_us={}",
                    total_us,
                    deck_refresh_us,
                    energy_reclaim_us,
                    sync_us,
                    win_check_us,
                    trigger_queue_us
                );
            }
        }
    }

    pub fn sync_stat_caches(&mut self, p_idx: usize, db: &CardDatabase) {
        use crate::core::logic::rules::{
            calculate_board_aura, get_effective_blades_with_aura, get_effective_hearts_with_aura,
        };

        // 1. Calculate and cache the BoardAura (single pass over constant abilities)
        let aura = calculate_board_aura(self, p_idx, db);
        self.core.players[p_idx].board_aura = aura.clone();

        // 2. Synchronize legacy cost modifiers (legacy compatibility)
        self.core.players[p_idx].slot_cost_modifiers = aura.slot_cost_modifiers;
        self.core.players[p_idx].heart_req_reductions = aura.heart_req_reductions;
        self.core.players[p_idx].heart_req_additions = aura.heart_req_additions;
        for &(_, col, val) in &self.core.players[p_idx].heart_req_reduction_logs {
            self.core.players[p_idx]
                .heart_req_reductions
                .add_to_color(col as usize, val as i32);
        }
        for &(_, col, val) in &self.core.players[p_idx].heart_req_addition_logs {
            self.core.players[p_idx]
                .heart_req_additions
                .add_to_color(col as usize, val as i32);
        }

        // 3. Calculate effective stats (O(1) pass using the pre-calculated aura)
        let mut total_blades = 0u32;
        let mut total_hearts = HeartBoard::default();
        let mut slot_blades = [0u32; 3];
        let mut slot_hearts = [HeartBoard::default(); 3];

        for slot_idx in 0..3 {
            let b = get_effective_blades_with_aura(self, p_idx, slot_idx, db, &aura);
            slot_blades[slot_idx] = b;
            total_blades += b;

            let h = get_effective_hearts_with_aura(self, p_idx, slot_idx, db, &aura);
            slot_hearts[slot_idx] = h;
            total_hearts.add(h);
        }

        let player = &mut self.core.players[p_idx];
        player.cached_total_blades = total_blades;
        player.cached_total_hearts = total_hearts;
        player.cached_slot_blades = slot_blades;
        player.cached_slot_hearts = slot_hearts;
    }

    pub fn card_matches_filter(&self, db: &CardDatabase, cid: i32, filter_attr: u64) -> bool {
        self.card_matches_filter_with_ctx(db, cid, filter_attr, &AbilityContext::default())
    }

    pub fn card_matches_filter_with_ctx(
        &self,
        db: &CardDatabase,
        cid: i32,
        filter_attr: u64,
        ctx: &AbilityContext,
    ) -> bool {
        if let Some(hit) = self.filter_cache_lookup(cid, filter_attr, None, ctx) {
            return hit;
        }
        let result =
            self.card_matches_filter_with_ctx_internal(db, cid, filter_attr, None, ctx, false, None);
        self.filter_cache_store(cid, filter_attr, None, ctx, result);
        result
    }

    pub fn card_matches_filter_with_ctx_logs(
        &self,
        db: &CardDatabase,
        cid: i32,
        filter_attr: u64,
        ctx: &AbilityContext,
    ) -> bool {
        self.card_matches_filter_with_ctx_internal(db, cid, filter_attr, None, ctx, true, None)
    }

    pub fn card_matches_filter_with_ctx_at_slot(
        &self,
        db: &CardDatabase,
        cid: i32,
        filter_attr: u64,
        checked_slot: (u8, i16),
        ctx: &AbilityContext,
    ) -> bool {
        if let Some(hit) = self.filter_cache_lookup(cid, filter_attr, Some(checked_slot), ctx) {
            return hit;
        }
        let result = self.card_matches_filter_with_ctx_internal(
            db,
            cid,
            filter_attr,
            None,
            ctx,
            false,
            Some(checked_slot),
        );
        self.filter_cache_store(cid, filter_attr, Some(checked_slot), ctx, result);
        result
    }

    pub fn card_matches_filter_with_struct(
        &self,
        db: &CardDatabase,
        cid: i32,
        checked_slot: Option<(u8, i16)>,
        filter: &CardFilter,
        ctx: &AbilityContext,
    ) -> bool {
        if let Some(hit) = self.filter_cache_lookup(cid, 0, checked_slot, ctx) {
            return hit;
        }
        let result = self.card_matches_filter_with_ctx_internal(
            db,
            cid,
            0,
            Some(filter),
            ctx,
            false,
            checked_slot,
        );
        self.filter_cache_store(cid, 0, checked_slot, ctx, result);
        result
    }

    fn card_matches_filter_with_ctx_internal(
        &self,
        db: &CardDatabase,
        cid: i32,
        filter_attr: u64,
        filter_struct: Option<&CardFilter>,
        ctx: &AbilityContext,
        debug: bool,
        provided_slot: Option<(u8, i16)>,
    ) -> bool {
        if cid == -1 {
            return false;
        }
        if filter_attr == 0 && filter_struct.is_none() {
            return true;
        }

        let filter_storage;
        let filter = if let Some(f) = filter_struct {
            f
        } else {
            filter_storage = CardFilter::from_attr(filter_attr);
            &filter_storage
        };
        let provided_slot = provided_slot.or_else(|| {
            if ctx.source_card_id == cid && ctx.area_idx >= 0 && ctx.area_idx < 3 {
                Some((ctx.player_id, ctx.area_idx))
            } else {
                None
            }
        });

        let needs_dynamic_hearts = filter.color_mask != 0;
        if let Some((p_idx, s_idx)) = provided_slot {
            let p_idx = p_idx as usize;
            let s_idx = s_idx as usize;
            if p_idx < 2 && s_idx < 3 && self.core.players[p_idx].stage[s_idx] == cid {
                let tapped = self.core.players[p_idx].is_tapped(s_idx);
                let h_arr = if needs_dynamic_hearts {
                    self.get_effective_hearts(p_idx, s_idx, db, 0).to_array()
                } else {
                    [0u8; 7]
                };

                return if debug {
                    filter.matches_with_logs(
                        db,
                        self,
                        cid,
                        ctx,
                        Some((p_idx as u8, s_idx as i16)),
                        tapped,
                        Some(&h_arr),
                    )
                } else {
                    filter.matches(
                        self,
                        db,
                        cid,
                        Some((p_idx as u8, s_idx as i16)),
                        tapped,
                        Some(&h_arr),
                        ctx,
                    )
                };
            }
        }

        // Fast Path: If the filter only checks static attributes (ID, Type, Group, Unit, Char)
        // and doesn't require stage-specific state (tapped, hearts, ownership, or NOT_SELF),
        // we can skip the expensive stage scanning loop.
        let requires_stage_scan = needs_dynamic_hearts
            || filter.is_tapped
            || (filter.special_id == 3 && provided_slot.is_none()) // NOT_SELF (only needs scan if slot unknown)
            || filter.keyword_energy
            || filter.keyword_member;

        if requires_stage_scan {
            for p in 0..2 {
                for s in 0..3 {
                    if self.core.players[p].stage[s] == cid {
                        let s_idx = s as i16;
                        let p_idx = p as u8;

                        let tapped = self.core.players[p].is_tapped(s);
                        let h_arr = if needs_dynamic_hearts {
                            self.get_effective_hearts(p, s, db, 0).to_array()
                        } else {
                            [0u8; 7]
                        };

                        let res = if debug {
                            filter.matches_with_logs(
                                db,
                                self,
                                cid,
                                ctx,
                                Some((p_idx, s_idx)),
                                tapped,
                                Some(&h_arr),
                            )
                        } else {
                            filter.matches(
                                self,
                                db,
                                cid,
                                Some((p_idx, s_idx)),
                                tapped,
                                Some(&h_arr),
                                ctx,
                            )
                        };
                        if res {
                            return true;
                        }
                    }
                }
            }
        }

        if debug {
            filter.matches_with_logs(db, self, cid, ctx, provided_slot, false, None)
        } else {
            filter.matches(self, db, cid, provided_slot, false, None, ctx)
        }
    }

    pub fn check_hearts_suitability(&self, have: &[u8; 7], need: &[u8; 7]) -> bool {
        super::performance::check_hearts_suitability(have, need)
    }

    pub fn consume_hearts_from_pool(&self, pool: &mut [u8; 7], need: &[u8; 7]) {
        super::performance::consume_hearts_from_pool(pool, need);
    }

    pub fn get_context_card_id(&self, ctx: &AbilityContext) -> Option<i32> {
        if ctx.source_card_id >= 0 {
            return Some(ctx.source_card_id as i32);
        }
        if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
            let cid = self.core.players[ctx.player_id as usize].stage[ctx.area_idx as usize];
            if cid >= 0 {
                return Some(cid as i32);
            }
        }
        None
    }

    pub fn check_live_success(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        live: &LiveCard,
        total_hearts: &[u8; 7],
    ) -> bool {
        super::performance::check_live_success(self, db, p_idx, live, total_hearts)
    }
}
