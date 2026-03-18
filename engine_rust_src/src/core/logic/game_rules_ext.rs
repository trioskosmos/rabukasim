use crate::core::enums::*;
use crate::core::models::LiveCard;
use super::state::GameState;
use super::card_db::CardDatabase;
use super::models::AbilityContext;
use crate::core::hearts::HeartBoard;
use super::filter::CardFilter;
use rand::seq::SliceRandom;
// use rand::SeedableRng;
use rand_pcg::Pcg64;

impl GameState {
    // Rule 10.2: [リフレッシュ (Refresh)]
    // Rule 10.2.1: Refresh can happen any time condition is met
    // Rule 10.2.2.1: Empty deck and non-empty discard triggers refresh
    // Rule 10.2.3: Shuffle discard and move to bottom of deck
    pub fn resolve_deck_refresh(&mut self, player_idx: usize) {
        if !self.ui.silent {
            self.log(format!("Rule 10.2.3: Player {}'s main deck is empty. Refreshing from discard.", player_idx));
        }
        
        // Use current state to seed the shuffle for deterministic replay if needed
        let player = &mut self.core.players[player_idx];
        let mut discard_cards: Vec<i32> = player.discard.drain(..).collect();
        
        // Rule 10.2.3: [控え室のカードを非公開状態にしてシャッフル (Shuffle discard)]
        // Rule 5.5: [シャッフルする (Shuffle)]
        // Rule 5.5.1: [非公開状態にして、並び順をランダムな状態にします (Randomize order)]
        // Rule 5.5.1.1: [指示を受けたプレイヤーがシャッフルを行います。対戦相手は、その後にその領域をシャッフルしたり、カットしたりすることを求めることができます (Non-turn player can cut/shuffle)]
        use rand::SeedableRng;
        let mut rng = Pcg64::seed_from_u64(self.core.turn as u64 * 1000 + player_idx as u64);
        discard_cards.shuffle(&mut rng);
        
        // Rule 10.2.3: [メインデッキ置き場のカードの下に移動 (Place at bottom of deck)]
        // Insert at bottom (index 0) to preserve top cards
        for cid in discard_cards {
            player.deck.insert(0, cid);
        }

        // Safety cap: Never exceed 60 cards in total deck (prevents unintended growth)
        if player.deck.len() > 60 {
            player.deck.truncate(60);
        }
        
        player.set_flag(crate::core::logic::player::PlayerState::FLAG_DECK_REFRESHED, true);
    }

    // Rule 1.2: [ゲームの勝敗 (Game Win/Loss)]
    // Rule 1.2.1: Game ends when victory/defeat is determined
    // Rule 10.3: [勝利処理 (Victory Processing)]
    // Rule 10.3.1: 3 or more success lives wins the game
    pub fn check_win_condition(&mut self) {
        if self.phase == Phase::Terminal {
            return;
        }

        let p0_win = self.core.players[0].success_lives.len() >= 3;
        let p1_win = self.core.players[1].success_lives.len() >= 3;

        if p0_win || p1_win {
            self.phase = Phase::Terminal;
            // Rule 10.1.2: [勝利・敗北判定 (Win/Loss Determination)]
            // Rule 10.1.3: [同時勝利・敗北 (Simultaneous Win/Loss)] (Rule 1.2.1.2)
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

    // Rule 10: [ルール処理 (Rule Processing / SBA)]
    // Rule 10.1: [ルール処理の基本 (SBA Basics)]
    pub fn perform_rule_processing(&mut self, db: &CardDatabase) {
        for i in 0..2 {
            // Rule 10.1.1: [ルール処理のチェックタイミング (SBA Check Timing)]
            // Rule 10.2: [リフレッシュ (Deck Refresh)]
            if self.core.players[i].deck.is_empty() && !self.core.players[i].discard.is_empty() {
                if self.core.players[i].get_flag(super::player::PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH) {
                    self.core.players[i].set_flag(super::player::PlayerState::FLAG_SUPPRESS_AUTO_DECK_REFRESH, false);
                } else {
                    // Rule 10.2.2: [リフレッシュの条件 (Refresh condition)]
                    self.resolve_deck_refresh(i);
                }
            }

            // Rule 10.5: [不正カード処理 (Processing of Unnecessary Cards/Energy)]
            // Rule 10.5.3: [上に重なっているメンバーの無いエネルギーカードをエネルギーデッキに戻す]
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
                    for cid in reclaimed {
                        // Rule 10.5.4: [控え室に置くカードがエネルギーカードである場合、エネルギーデッキ置き場に置く]
                        self.core.players[i].energy_deck.push(cid);
                    }
                    self.core.players[i].stage_energy_count[slot_idx] = 0;

                    // Energy deck is unordered; shuffle to maintain randomness.
                    use rand::SeedableRng;
                    let mut rng = Pcg64::seed_from_u64(
                        self.core.turn as u64 * 31 + i as u64 * 7 + slot_idx as u64,
                    );
                    self.core.players[i].energy_deck.shuffle(&mut rng);
                }
            }

            // Rule 9.6: [能力の解決 (Ability Resolution)]
            // Eagerly synchronize constant modifiers
            self.sync_stat_caches(i, db);
        }
        // Rule 1.2: [ゲームの勝敗 (Check Win Condition)]
        self.check_win_condition();
    }

    pub fn process_rule_checks(&mut self, db: &CardDatabase) {
        // Rule 10.1: [ルール処理 (Rule Processing)]
        self.perform_rule_processing(db);
        // Rule 9.1: [チェックタイミング (Check Timing / Trigger Processing)]
        self.process_trigger_queue(db);
    }


    pub fn sync_stat_caches(&mut self, p_idx: usize, db: &CardDatabase) {
        use crate::core::logic::rules::{calculate_board_aura, get_effective_blades, get_effective_hearts};
        
        // 1. Calculate and cache the BoardAura (single pass over constant abilities)
        let aura = calculate_board_aura(self, p_idx, db);
        self.core.players[p_idx].board_aura = aura.clone();
        
        // 2. Synchronize legacy cost modifiers (legacy compatibility)
        self.core.players[p_idx].slot_cost_modifiers = aura.slot_cost_modifiers;
        self.core.players[p_idx].heart_req_reductions = aura.heart_req_reductions;
        self.core.players[p_idx].heart_req_additions = aura.heart_req_additions;
        for &(_, color_idx, amount) in &self.core.players[p_idx].heart_req_addition_logs {
            self.core.players[p_idx]
                .heart_req_additions
                .add_to_color(color_idx as usize, amount as i32);
        }

        // 3. Calculate effective stats (now O(1) inside because they use board_aura)
        let mut total_blades = 0u32;
        let mut total_hearts = HeartBoard::default();
        let mut slot_blades = [0u32; 3];
        let mut slot_hearts = [HeartBoard::default(); 3];
        
        for slot_idx in 0..3 {
            let b = get_effective_blades(self, p_idx, slot_idx, db, 1);
            slot_blades[slot_idx] = b;
            total_blades += b;
            
            let h = get_effective_hearts(self, p_idx, slot_idx, db, 1);
            slot_hearts[slot_idx] = h;
            total_hearts.add(h);
        }
        
        let player = &mut self.core.players[p_idx];
        player.cached_total_blades = total_blades;
        player.cached_total_hearts = total_hearts;
        player.cached_slot_blades = slot_blades;
        player.cached_slot_hearts = slot_hearts;
    }

    // Rule 12.1: [繧｢繝薙fa繧｣繝・ぅ縺ｮ菴ｿ逕ｨ (Ability Usage)]
    // Rule 12.1.1.2: Order of resolution (LIFO on stack / Queue)
    pub fn card_matches_filter(&self, db: &CardDatabase, cid: i32, filter_attr: u64) -> bool {
        self.card_matches_filter_with_ctx(db, cid, filter_attr, &AbilityContext::default())
    }

    pub fn card_matches_filter_with_ctx(&self, db: &CardDatabase, cid: i32, filter_attr: u64, ctx: &AbilityContext) -> bool {
        self.card_matches_filter_with_ctx_internal(db, cid, filter_attr, ctx, false)
    }

    pub fn card_matches_filter_with_ctx_logs(&self, db: &CardDatabase, cid: i32, filter_attr: u64, ctx: &AbilityContext) -> bool {
        self.card_matches_filter_with_ctx_internal(db, cid, filter_attr, ctx, true)
    }

    pub fn card_matches_filter_with_ctx_internal(&self, db: &CardDatabase, cid: i32, filter_attr: u64, ctx: &AbilityContext, debug: bool) -> bool {
        // Rule 1.3.2: Impossible actions (If card doesn't exist, it doesn't match)
        // Rule 1.3.2.4: [繝励Ξ繧､繝､繝ｼ縺ｮ驕ｸ謚・ (Selection of player)]
        if cid == -1 { return false; }
        if filter_attr == 0 { return true; }

        let filter = CardFilter::from_attr(filter_attr as i64);
        let needs_dynamic_hearts = filter.color_mask != 0;

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
                        filter.matches_with_logs(db, self, cid, ctx, Some((p_idx, s_idx)), tapped, Some(&h_arr))
                    } else {
                        filter.matches(self, db, cid, Some((p_idx, s_idx)), tapped, Some(&h_arr), ctx)
                    };
                    if res {
                        return true;
                    }
                }
            }
        }

        if debug {
            filter.matches_with_logs(db, self, cid, ctx, None, false, None)
        } else {
            filter.matches(self, db, cid, None, false, None, ctx)
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
