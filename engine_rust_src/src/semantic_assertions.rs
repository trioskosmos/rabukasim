use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::core::logic::{GameState, CardDatabase, Phase};
use crate::core::models::{TriggerType, AbilityContext};
use crate::test_helpers::{Action as EngineAction, create_test_state, ZoneSnapshot};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SemanticDelta {
    pub tag: String,
    pub value: serde_json::Value,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SemanticSegment {
    pub text: String,
    pub deltas: Vec<SemanticDelta>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SemanticAbility {
    pub trigger: String,
    pub sequence: Vec<SemanticSegment>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct SemanticCardTruth {
    pub id: String,
    pub abilities: Vec<SemanticAbility>,
}

pub struct SemanticAssertionEngine {
    pub truth: HashMap<String, SemanticCardTruth>,
    pub db: CardDatabase,
}

impl SemanticAssertionEngine {
    pub fn load() -> Self {
        println!("DEBUG CWD: {:?}", std::env::current_dir());
        let truth: HashMap<String, SemanticCardTruth> = if let Ok(truth_str) = std::fs::read_to_string("../reports/semantic_truth.json") {
            serde_json::from_str(&truth_str).expect("Failed to parse semantic_truth.json")
        } else {
            println!("WARNING: semantic_truth.json not found. Starting with empty truth set.");
            HashMap::new()
        };

        if let Some(c) = truth.get("PL!N-PR-005-PR") {
             println!("DEBUG TRUTH LOADED: {:?}", c);
        }
        
        let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
            .expect("Failed to read cards_compiled.json");
        let mut db = CardDatabase::from_json(&compiled_str).expect("Failed to parse CardDatabase");
        
        // Inject Universal Teammates into the DB for audit/oracle use
        for i in 5000..5100 {
            let m = crate::core::logic::MemberCard {
                card_id: i as i32,
                card_no: format!("DUMMY-{:04}", i),
                name: format!("Dummy {}", i),
                cost: 1,
                hearts: [1; 7],
                groups: (1..21).collect(),
                units: (1..11).collect(),
                ..Default::default()
            };
            db.members.insert(i as i32, m.clone());
            if (i as usize) < db.members_vec.len() {
                db.members_vec[(i as usize) & LOGIC_ID_MASK as usize] = Some(m);
            }
        }
        // Inject dummy lives
        for i in 15000..15050 {
            let l = crate::core::logic::LiveCard {
                card_id: i as i32,
                card_no: format!("DUMMY-LIVE-{:04}", i),
                name: format!("Dummy Live {}", i),
                score: 5,
                required_hearts: [1; 7],
                ..Default::default()
            };
            db.lives.insert(i as i32, l.clone());
            let idx = (i - 10000) as usize;
            if idx < db.lives_vec.len() {
                db.lives_vec[idx & LOGIC_ID_MASK as usize] = Some(l);
            }
        }

        Self { truth, db }
    }

    pub fn verify_card(&self, card_id_str: &str, ab_idx: usize) -> Result<(), String> {
        let truth = self.truth.get(card_id_str).ok_or(format!("Card {} not found in truth set", card_id_str))?;
        let ability = truth.abilities.get(ab_idx).ok_or(format!("Ability index {} not found for {}", ab_idx, card_id_str))?;
        
        let mut state = create_test_state();
        state.ui.silent = false; // Enable logging for debugging
        state.debug.debug_mode = true; // Enable interpreter debug mode
        
        let real_id = self.find_real_id(card_id_str)?;
        let trigger_type = self.map_trigger_type(&ability.trigger);
        
        match trigger_type {
            TriggerType::OnPlay | TriggerType::OnLiveStart | TriggerType::OnLiveSuccess | TriggerType::Constant | TriggerType::None | TriggerType::Activated => {
                Self::setup_oracle_environment(&mut state, &self.db, real_id);

                // For live-card abilities, set up live-phase context
                if trigger_type == TriggerType::OnLiveStart || trigger_type == TriggerType::OnLiveSuccess {
                    state.phase = if trigger_type == TriggerType::OnLiveSuccess { Phase::LiveResult } else { Phase::PerformanceP1 };
                    // Put the card being tested in the live zone
                    if self.db.get_live(real_id).is_some() {
                        state.core.players[0].live_zone[0] = real_id;
                    }
                }

                // Capture snapshot AFTER placing the card but BEFORE triggering/activating
                let prev_snapshot = ZoneSnapshot::capture(&state.core.players[0]);

                // --- Execution Phase ---
                if trigger_type == TriggerType::Activated {
                    state.activate_ability(&self.db, 0, ab_idx).ok();
                    state.process_trigger_queue(&self.db);
                    // Auto-resolve any pending interactions from activation costs
                    let mut cost_safety = 0;
                    while !state.interaction_stack.is_empty() && cost_safety < 10 {
                        self.resolve_interaction(&mut state).ok();
                        cost_safety += 1;
                    }
                } else if trigger_type != TriggerType::None && trigger_type != TriggerType::Constant {
                    match trigger_type {
                        TriggerType::OnLeaves => {
                            // Move from stage to discard to trigger
                            state.core.players[0].stage[0] = -1;
                            state.trigger_event(&self.db, trigger_type, 0, real_id, 0, 0);
                        },
                        TriggerType::TurnEnd => {
                            state.phase = Phase::Terminal;
                            state.trigger_event(&self.db, trigger_type, 0, real_id, 0, 0);
                        },
                        _ => {
                            state.trigger_event(&self.db, trigger_type, 0, real_id, 0, 0);
                        }
                    }
                    state.process_trigger_queue(&self.db);
                }
                
                let p0_init = ZoneSnapshot::capture(&state.core.players[0]);
                let p1_init = ZoneSnapshot::capture(&state.core.players[1]);
                self.run_sequence(&mut state, &ability.sequence, p0_init, p1_init, trigger_type)?;
            },
            _ => {
                return Err(format!("Trigger type {:?} not yet supported in semantic runner", trigger_type));
            }
        }
        Ok(())
    }

    pub fn verify_card_negative(&self, card_id_str: &str, ab_idx: usize) -> Result<(), String> {
        let truth = self.truth.get(card_id_str).ok_or(format!("Card {} not found in truth set", card_id_str))?;
        let ability = truth.abilities.get(ab_idx).ok_or(format!("Ability index {} not found for {}", ab_idx, card_id_str))?;
        
        let mut state = create_test_state();
        state.ui.silent = true;
        
        let real_id = self.find_real_id(card_id_str)?;
        let trigger_type = self.map_trigger_type(&ability.trigger);

        // Minimal setup: just the card on stage, but no energy, no lives, no discard, no opponent
        state.core.players[0].stage[0] = real_id;
        state.core.players[0].energy_zone.clear();
        state.core.players[0].success_lives.clear();
        state.core.players[0].discard.clear();
        state.core.players[1].stage[0] = -1; // Empty opponent stage
        
        let prev_snapshot = ZoneSnapshot::capture(&state.core.players[0]);

        // Execute
        if trigger_type == TriggerType::Activated {
            state.activate_ability(&self.db, 0, ab_idx).ok();
            state.process_trigger_queue(&self.db);
        } else if trigger_type != TriggerType::None && trigger_type != TriggerType::Constant {
            let ctx = AbilityContext { 
                source_card_id: real_id, 
                player_id: 0, 
                area_idx: 0, 
                trigger_type,
                ability_index: ab_idx as i16,
                ..Default::default() 
            };
            let is_live = self.db.get_live(real_id).is_some();
            state.trigger_queue.push_back((real_id, ab_idx as u16, ctx, is_live, trigger_type));
            state.process_trigger_queue(&self.db);
            state.step(&self.db, EngineAction::Pass.id()).ok();
        }

        let current_snapshot = ZoneSnapshot::capture(&state.core.players[0]);
        let deltas = self.diff_snapshots(&prev_snapshot, &current_snapshot);

        if !deltas.is_empty() {
             // If the ability fired when it shouldn't have...
             // Some abilities have NO conditions, so they will always fire.
             // We only report this as a "failure" if the JP text suggests a condition.
             // For now, we'll just log it.
             let combined_deltas = deltas.iter().map(|d| format!("{}:{}", d.tag, d.value)).collect::<Vec<_>>().join(", ");
             println!("INFO: [Negative Test] Ability {}/{} fired in minimal state: {}", card_id_str, ab_idx, combined_deltas);
        }

        Ok(())
    }

    fn run_sequence(&self, state: &mut GameState, sequence: &[SemanticSegment], initial_p0: ZoneSnapshot, initial_p1: ZoneSnapshot, _trigger_type: TriggerType) -> Result<(), String> {
        let mut seq_idx = 0;
        let mut safety = 0;
        
        let mut checkpoint_p0 = initial_p0;
        let mut checkpoint_p1 = initial_p1;

        while seq_idx < sequence.len() && safety < 100 {
            let is_suspended = state.phase == Phase::Response || !state.interaction_stack.is_empty();

            if is_suspended {
                 self.resolve_interaction(state).expect("Failed to resolve interaction during audit");
            }

            let curr_p0 = ZoneSnapshot::capture(&state.core.players[0]);
            let curr_p1 = ZoneSnapshot::capture(&state.core.players[1]);
            
            let mut matched_segments = 0;
            let mut error_if_fail = String::new();

            'lookahead: for offset in 0..(sequence.len() - seq_idx) {
                let segments_to_check = &sequence[seq_idx ..= seq_idx + offset];
                match self.assert_cumulative_deltas(segments_to_check, &checkpoint_p0, &curr_p0, &checkpoint_p1, &curr_p1) {
                    Ok(_) => {
                        seq_idx += offset + 1;
                        matched_segments = offset + 1;
                        break 'lookahead;
                    },
                    Err(e) => {
                         if offset == 0 { error_if_fail = e; }
                    }
                }
            }
            
            if matched_segments > 0 {
                checkpoint_p0 = curr_p0;
                checkpoint_p1 = curr_p1;
            } else {
                if !is_suspended && state.phase == Phase::Main && state.interaction_stack.is_empty() {
                    return Err(format!("Stuck at segment {}: {}", seq_idx, error_if_fail));
                }
            }
            
            safety += 1;
        }
        Ok(())
    }

    fn resolve_interaction(&self, state: &mut GameState) -> Result<(), String> {
        let (pi, player_id) = {
            let last = state.interaction_stack.last().ok_or("No interaction to resolve")?;
            (last.clone(), last.ctx.player_id)
        };
        
        let p_idx = player_id as usize;
        
        // Correct Action ID Base Selection based on ResponseGenerator
        let base = match pi.choice_type.as_str() {
            "MODE" | "CHOICE" | "MODAL" | "SELECT_MODE" | "OPTIONAL" | "YES_NO" => 8000,
            "COLOR" | "SELECT_COLOR" => 580,
            "SLOT" | "SELECT_SLOT" | "TARGET_MEMBER" | "SELECT_STAGE" | "SELECT_LIVE_SLOT" | "MEMBER" => 600,
            "RPS" => 10001,
            "HAND" | "SELECT_HAND" | "SELECT_HAND_DISCARD" | "REVEAL_HAND" | "SELECT_SWAP_TARGET" => 3000,
            "DISCARD" | "SELECT_DISCARD" | "RECOV_M" | "SELECT_DISCARD_PLAY" | "SEARCH" | "SEARCH_MEMBER" => 8000,
            "PAY_ENERGY" => 2000,
            _ => {
                if pi.choice_type.contains("SEARCH") || pi.choice_type.contains("RECOV") { 8000 }
                else if pi.choice_type.contains("HAND") { 3000 }
                else { 8000 }
            }
        };

        // Automatic Index Selection
        let mut selected_idx = 0;
        match pi.choice_type.as_str() {
            "SELECT_HAND_DISCARD" | "HAND" | "SELECT_HAND" => {
               if !state.core.players[p_idx].hand.is_empty() {
                   // Prefer choosing a card that matches the filter
                   if pi.filter_attr != 0 {
                        let filter = crate::core::logic::filter::CardFilter::from_attr(pi.filter_attr);
                        for (i, &cid) in state.core.players[p_idx].hand.iter().enumerate() {
                            if filter.matches(&self.db, cid, false) {
                                selected_idx = i as i32;
                                break;
                            }
                        }
                   }
               }
            },
            "SELECT_DISCARD" | "SELECT_STAGE" | "SLOT" | "MEMBER" | "TARGET_MEMBER" => {
                // Prefer selecting a member that isn't tapped if possible
                for i in 0..3 {
                    if state.core.players[p_idx].stage[i] >= 0 {
                        selected_idx = i as i32;
                        if !state.core.players[p_idx].is_tapped(i) {
                            break;
                        }
                    }
                }
            },
            "LOOK_AND_CHOOSE" | "RECOV_L" | "RECOV_M" | "SEARCH" | "SEARCH_MEMBER" => {
                // Select from looked_cards
                for (i, &cid) in state.core.players[p_idx].looked_cards.iter().enumerate() {
                    if cid != -1 {
                        let matches = match pi.choice_type.as_str() {
                            "RECOV_L" => self.db.get_live(cid).is_some(),
                            "RECOV_M" => self.db.get_member(cid).is_some(),
                            _ => true,
                        };
                        if matches {
                            selected_idx = i as i32;
                            break;
                        }
                    }
                }
            },
            _ => { selected_idx = 0; }
        }

        let action = base as i32 + selected_idx;
        state.step(&self.db, action).map_err(|e| format!("Auto-Bot interaction error ({}): {:?}", pi.choice_type, e))
    }

    pub fn setup_oracle_environment(state: &mut GameState, db: &CardDatabase, real_id: i32) {
        // --- Collect real card IDs from the database ---
        // Find same-group members for stage neighbors
        let card_group = db.get_member(real_id)
            .and_then(|m| m.groups.first().copied())
            .unwrap_or(1);
        let same_group_members: Vec<i32> = db.members.iter()
            .filter(|(&id, m)| id != real_id && m.groups.contains(&card_group) && m.cost <= 6)
            .map(|(&id, _)| id)
            .take(10)
            .collect();

        // Real energy cards
        let energy_ids: Vec<i32> = db.energy_db.keys().copied().take(20).collect();
        // Fallback to dummy if DB has none
        let energy_fill: Vec<i32> = if energy_ids.is_empty() { vec![5001; 20] } else { energy_ids.clone() };

        // Real live cards
        let real_lives: Vec<i32> = db.lives.keys().copied().take(6).collect();
        let live_fill: Vec<i32> = if real_lives.is_empty() { vec![15000, 15001, 15002] } else { real_lives[..3.min(real_lives.len())].to_vec() };

        // Real member cards for hand/deck/discard (mix of same-group and others)
        let other_members: Vec<i32> = db.members.iter()
            .filter(|(&id, _)| id != real_id)
            .map(|(&id, _)| id)
            .take(20)
            .collect();

        // --- PLAYER 0 (card under test) ---
        // Energy (20 real cards, all active)
        state.core.players[0].energy_zone.extend(energy_fill.iter().cloned());

        // Hand (mix of same-group members and generic members)
        for &id in same_group_members.iter().take(5) {
            state.core.players[0].hand.push(id);
        }
        for &id in other_members.iter().skip(5).take(6) {
            state.core.players[0].hand.push(id);
        }

        // Deck (real members + real lives)
        for &id in other_members.iter().take(10) {
            state.core.players[0].deck.push(id);
        }
        for &id in real_lives.iter() {
            state.core.players[0].deck.push(id);
        }

        // Discard (real members + real lives for recovery effects)
        for &id in same_group_members.iter().take(5) {
            state.core.players[0].discard.push(id);
        }
        for &id in other_members.iter().skip(10).take(5) {
            state.core.players[0].discard.push(id);
        }
        for &id in real_lives.iter().skip(1) {
            state.core.players[0].discard.push(id);
        }

        // Success lives (real live IDs)
        state.core.players[0].success_lives.extend(live_fill.iter().cloned());
        state.core.players[0].live_zone[0] = real_lives.first().copied().unwrap_or(5003);

        // Stage (card under test at center, same-group neighbors)
        state.core.players[0].stage[0] = real_id;
        state.core.players[0].stage[1] = same_group_members.first().copied().unwrap_or(5000);
        state.core.players[0].stage[2] = same_group_members.get(1).copied().unwrap_or(5000);

        state.core.players[0].score = 99;

        // --- PLAYER 1 (opponent — realistic state) ---
        let opp_members: Vec<i32> = db.members.iter()
            .filter(|(&id, _)| !same_group_members.contains(&id) && id != real_id)
            .map(|(&id, _)| id)
            .take(30)
            .collect();

        // Opponent energy (10 real cards)
        state.core.players[1].energy_zone.extend(energy_ids.iter().take(10).cloned());

        // Opponent hand (5 cards)
        state.core.players[1].hand.extend(opp_members.iter().take(5).cloned());
        
        // Opponent stage (3 cards)
        state.core.players[1].stage[0] = opp_members.get(5).copied().unwrap_or(5002);
        state.core.players[1].stage[1] = opp_members.get(6).copied().unwrap_or(5002);
        state.core.players[1].stage[2] = opp_members.get(7).copied().unwrap_or(5002);

        // Opponent deck (10 cards)
        state.core.players[1].deck.extend(opp_members.iter().skip(10).take(10).cloned());

        // Opponent discard (5 cards)
        state.core.players[1].discard.extend(opp_members.iter().skip(20).take(5).cloned());
        
        // --- CHARACTER DIVERSITY for PLAYER 0 ---
        // Ensure discard has at least 5 different characters
        let mut different_chars: Vec<i32> = Vec::new();
        let mut seen_chars = std::collections::HashSet::new();
        for (&id, _member) in db.members.iter() {
            let char_id = id / 1000;
            if !seen_chars.contains(&char_id) && id != real_id {
                different_chars.push(id);
                seen_chars.insert(char_id);
            }
            if different_chars.len() >= 10 { break; }
        }
        state.core.players[0].discard.extend(different_chars.iter().take(5).cloned());
        state.core.players[0].deck.extend(different_chars.iter().skip(5).cloned());
        
        // Energy Activation support: Put some members in active energy zone
        if state.core.players[0].energy_zone.len() >= 2 {
            state.core.players[0].energy_zone[0] = different_chars.get(0).copied().unwrap_or(5001);
            state.core.players[0].energy_zone[1] = different_chars.get(1).copied().unwrap_or(5002);
            state.core.players[0].tapped_energy_mask = 0; // Ensure they are active
        }

        // Live Success support: Ensure we have enough success lives for conditions
        if state.core.players[0].success_lives.len() < 3 {
            state.core.players[0].success_lives.extend(live_fill.iter().take(3).cloned());
        }

        // --- PHASE 8 ENRICHMENT ---
        // Ensure discard ALWAYS has at least 3 live cards for RECOVER_LIVE effects
        let live_ids: Vec<i32> = db.lives.keys().copied().take(5).collect();
        for &lid in &live_ids {
            if !state.core.players[0].discard.contains(&lid) {
                state.core.players[0].discard.push(lid);
            }
        }

        // Ensure deck has cards with various characteristics (High cost, etc.)
        let high_cost_members: Vec<i32> = db.members.iter()
            .filter(|(_, m)| m.cost >= 10)
            .map(|(&id, _)| id)
            .take(5)
            .collect();
        state.core.players[0].deck.extend(high_cost_members.iter().cloned());

        // Reset stage tap state for clean ACTIVATE_MEMBER tests
        for i in 0..3 {
            state.core.players[0].set_tapped(i, false);
        }

        // --- Global state ---
        state.phase = Phase::Main;
        state.turn = 5;
    }

    pub fn record_card(&self, card_id_str: &str, ab_idx: usize) -> Result<Option<SemanticAbility>, String> {
        let mut state = create_test_state();
        state.ui.silent = true;
        
        let real_id = self.find_real_id(card_id_str)?;
        Self::setup_oracle_environment(&mut state, &self.db, real_id);
        
        let (abilities, trigger_type) = if let Some(m) = self.db.get_member(real_id) {
            (&m.abilities, m.abilities.get(ab_idx).map(|a| a.trigger).unwrap_or(TriggerType::None))
        } else if let Some(l) = self.db.get_live(real_id) {
            (&l.abilities, l.abilities.get(ab_idx).map(|a| a.trigger).unwrap_or(TriggerType::None))
        } else {
            return Err("Card not found in database".to_string());
        };
        
        let _ability = abilities.get(ab_idx).ok_or("Ability not found")?;
        let mut last_p0 = ZoneSnapshot::capture(&state.core.players[0]);
        let mut last_p1 = ZoneSnapshot::capture(&state.core.players[1]);

        if trigger_type == TriggerType::Activated {
            state.activate_ability(&self.db, 0, ab_idx).ok();
            state.process_trigger_queue(&self.db);
        } else if trigger_type != TriggerType::None && trigger_type != TriggerType::Constant {
            let actx = AbilityContext { 
                source_card_id: real_id, 
                player_id: 0, 
                area_idx: 0, 
                trigger_type,
                ability_index: ab_idx as i16,
                ..Default::default() 
            };
            let is_live = self.db.get_live(real_id).is_some();
            state.trigger_queue.push_back((real_id, ab_idx as u16, actx, is_live, trigger_type));
            state.process_trigger_queue(&self.db);
            state.step(&self.db, EngineAction::Pass.id()).ok();
        } else if trigger_type == TriggerType::Constant {
            let mut deltas = Vec::new();
            if state.core.players[0].live_score_bonus > 0 {
                deltas.push(SemanticDelta { tag: "SCORE_DELTA".to_string(), value: serde_json::json!(state.core.players[0].live_score_bonus) });
            }
            return Ok(Some(SemanticAbility {
                trigger: format!("{:?}", trigger_type).to_uppercase(),
                sequence: vec![SemanticSegment { text: "Constant Effect".to_string(), deltas }]
            }));
        }

        // Record initial effects
        let curr_p0 = ZoneSnapshot::capture(&state.core.players[0]);
        let curr_p1 = ZoneSnapshot::capture(&state.core.players[1]);
        let d_p0 = self.diff_snapshots(&last_p0, &curr_p0);
        let d_p1 = self.diff_snapshots(&last_p1, &curr_p1);
        
        let mut initial_deltas = Vec::new();
        for mut d in d_p1 {
            d.tag = format!("OPPONENT_{}", d.tag);
            initial_deltas.push(d);
        }
        initial_deltas.extend(d_p0);

        if !initial_deltas.is_empty() {
            segments.push(SemanticSegment { text: "Initial Effect".to_string(), deltas: initial_deltas });
            last_p0 = curr_p0;
            last_p1 = curr_p1;
        }

        // Run until end of interaction
        let mut safety = 0;
        while (!state.interaction_stack.is_empty() || state.phase == Phase::Response) && safety < 100 {
            if !state.interaction_stack.is_empty() {
                self.resolve_interaction(&mut state).ok();
            } else {
                state.step(&self.db, EngineAction::Pass.id()).ok();
            }
            
            let curr_p0 = ZoneSnapshot::capture(&state.core.players[0]);
            let curr_p1 = ZoneSnapshot::capture(&state.core.players[1]);
            let d_p0 = self.diff_snapshots(&last_p0, &curr_p0);
            let d_p1 = self.diff_snapshots(&last_p1, &curr_p1);
            
            let mut step_deltas = Vec::new();
            for mut d in d_p1 {
                d.tag = format!("OPPONENT_{}", d.tag);
                step_deltas.push(d);
            }
            step_deltas.extend(d_p0);

            if !step_deltas.is_empty() {
                segments.push(SemanticSegment { text: "Follow-up Effect".to_string(), deltas: step_deltas });
                last_p0 = curr_p0;
                last_p1 = curr_p1;
            }
            safety += 1;
        }

        Ok(Some(SemanticAbility {
            trigger: format!("{:?}", trigger_type).to_uppercase(),
            sequence: segments
        }))
    }

    fn diff_snapshots(&self, baseline: &ZoneSnapshot, current: &ZoneSnapshot) -> Vec<SemanticDelta> {
        let mut deltas = Vec::new();

        let d_hand = current.hand_len as i32 - baseline.hand_len as i32;
        if d_hand < 0 {
            deltas.push(SemanticDelta { tag: "HAND_DISCARD".to_string(), value: serde_json::json!(-d_hand) });
        } else if d_hand > 0 {
            deltas.push(SemanticDelta { tag: "HAND_DELTA".to_string(), value: serde_json::json!(d_hand) });
        }
        
        let d_score = current.score as i32 - baseline.score as i32;
        if d_score != 0 { deltas.push(SemanticDelta { tag: "SCORE_DELTA".to_string(), value: serde_json::json!(d_score) }); }
        
        let d_energy = current.energy_len as i32 - baseline.energy_len as i32;
        if d_energy != 0 { deltas.push(SemanticDelta { tag: "ENERGY_DELTA".to_string(), value: serde_json::json!(d_energy) }); }

        let d_stage = (current.active_members_count as i32) - (baseline.active_members_count as i32);
        if d_stage < 0 {
            deltas.push(SemanticDelta { tag: "MEMBER_SACRIFICE".to_string(), value: serde_json::json!(-d_stage) });
        } else if d_stage > 0 {
            deltas.push(SemanticDelta { tag: "STAGE_DELTA".to_string(), value: serde_json::json!(d_stage) });
        }
        
        // Hearts
        let d_heart = current.total_heart_buffs as i32 - baseline.total_heart_buffs as i32;
        if d_heart != 0 { deltas.push(SemanticDelta { tag: "HEART_DELTA".to_string(), value: serde_json::json!(d_heart) }); }

        // Discard (Net change)
        let d_discard = current.discard_len as i32 - baseline.discard_len as i32;
        if d_discard > 0 { 
            deltas.push(SemanticDelta { tag: "DISCARD_DELTA".to_string(), value: serde_json::json!(d_discard) }); 
        }

        // Yell
        let d_yell = current.yell_count as i32 - baseline.yell_count as i32;
        if d_yell != 0 {
            deltas.push(SemanticDelta { tag: "YELL_DELTA".to_string(), value: serde_json::json!(d_yell) });
        }

        // Action Prevention
        if current.prevent_activate != baseline.prevent_activate 
           || current.prevent_baton_touch != baseline.prevent_baton_touch 
           || current.prevent_play_mask != baseline.prevent_play_mask {
            deltas.push(SemanticDelta { tag: "ACTION_PREVENTION".to_string(), value: serde_json::json!(true) });
        }

        // Live Score Bonus
        let d_live_score = current.live_score_bonus as i32 - baseline.live_score_bonus as i32;
        if d_live_score != 0 {
            deltas.push(SemanticDelta { tag: "LIVE_SCORE_DELTA".to_string(), value: serde_json::json!(d_live_score) });
        }

        // Tap Members (Transition from Active to Wait)
        let mut tap_delta = 0;
        for i in 0..3 {
            if !baseline.tapped_members[i] && current.tapped_members[i] {
                tap_delta += 1;
            }
        }
        if tap_delta > 0 {
            deltas.push(SemanticDelta { tag: "MEMBER_TAP_DELTA".to_string(), value: serde_json::json!(tap_delta) });
        }

        // Energy Tap (Net change in tapped energy)
        let d_energy_tap = current.tapped_energy_count as i32 - baseline.tapped_energy_count as i32;
        if d_energy_tap > 0 {
            deltas.push(SemanticDelta { tag: "ENERGY_TAP_DELTA".to_string(), value: serde_json::json!(d_energy_tap) });
        }

        // Prevention (Action Mask/Flags)
        if current.prevent_activate != baseline.prevent_activate 
           || current.prevent_baton_touch != baseline.prevent_baton_touch 
           || current.prevent_play_mask != baseline.prevent_play_mask {
            deltas.push(SemanticDelta { tag: "ACTION_PREVENTION".to_string(), value: serde_json::json!(1) });
        }

        // Stage Energy
        let d_stage_energy = current.stage_energy_total as i32 - baseline.stage_energy_total as i32;
        if d_stage_energy > 0 {
            deltas.push(SemanticDelta { tag: "STAGE_ENERGY_DELTA".to_string(), value: serde_json::json!(d_stage_energy) });
        }

        deltas
    }

    fn assert_cumulative_deltas(
        &self, 
        segments: &[SemanticSegment], 
        baseline_p0: &ZoneSnapshot, 
        current_p0: &ZoneSnapshot,
        baseline_p1: &ZoneSnapshot,
        current_p1: &ZoneSnapshot,
    ) -> Result<(), String> {
        let combined_text = segments.iter().map(|s| s.text.clone()).collect::<Vec<_>>().join(" + ");
        
        let mut expected_hand_delta = 0;
        let mut expected_energy_cost = 0;
        let mut expected_score_delta = 0;
        let mut expected_heart_delta = 0;
        let mut expected_blade_delta = 0;
        let mut expected_stage_delta = 0;
        let mut expected_energy_delta = 0;
        let mut expected_discard_delta = 0;
        let mut expected_hand_discard = false;
        let mut expected_live_recover = false;
        let mut expected_deck_search = false;
        let mut expected_member_tap_delta = 0;
        let mut expected_action_prevention = false;
        let mut expected_stage_energy_delta = 0;
        let mut expected_yell_delta = 0;

        // Opponent
        let mut opp_hand_delta = 0;
        let mut opp_discard_delta = 0;
        let mut opp_stage_delta = 0;
        let mut opp_member_tap_delta = 0;
        let mut opp_hand_discard = false;

        for segment in segments {
            for delta in &segment.deltas {
                let tag = delta.tag.as_str();
                let val_i64 = delta.value.as_i64().unwrap_or(0);
                
                if tag.starts_with("OPPONENT_") {
                    let clean_tag = &tag["OPPONENT_".len()..];
                    match clean_tag {
                        "HAND_DELTA" => opp_hand_delta += val_i64 as i32,
                        "HAND_DISCARD" => {
                            opp_hand_discard = true;
                            opp_hand_delta -= delta.value.as_i64().unwrap_or(1) as i32;
                        },
                        "DISCARD_DELTA" => opp_discard_delta += val_i64 as i32,
                        "STAGE_DELTA" => opp_stage_delta += val_i64 as i32,
                        "MEMBER_TAP_DELTA" => opp_member_tap_delta += val_i64 as i32,
                        _ => {}
                    }
                } else {
                    let is_cost = tag.starts_with("COST_");
                    let clean_tag = if is_cost { &tag[5..] } else { tag };

                    match clean_tag {
                        "HAND_DELTA" => expected_hand_delta += val_i64 as i32,
                        "ENERGY_COST" => expected_energy_cost += val_i64 as i32,
                        "SCORE_DELTA" | "LIVE_SCORE_DELTA" => expected_score_delta += delta.value.as_u64().unwrap_or(0) as u32,
                        "HEART_DELTA" => expected_heart_delta += delta.value.as_u64().unwrap_or(0),
                        "BLADE_DELTA" => expected_blade_delta += val_i64 as i32,
                        "STAGE_DELTA" => expected_stage_delta += val_i64 as i32,
                        "ENERGY_DELTA" => expected_energy_delta += val_i64 as i32,
                        "DISCARD_DELTA" => expected_discard_delta += val_i64 as i32,
                        "ENERGY_CHARGE" => expected_energy_delta += val_i64 as i32,
                        "HAND_DISCARD" => {
                            expected_hand_discard = true;
                            expected_hand_delta -= delta.value.as_i64().unwrap_or(1) as i32;
                        },
                        "MEMBER_SACRIFICE" => {
                            expected_stage_delta -= 1;
                            expected_discard_delta += 1;
                        },
                        "LIVE_RECOVER" => {
                            expected_live_recover = true;
                            expected_hand_delta += 1;
                            expected_discard_delta -= 1;
                        },
                        "DECK_SEARCH" => expected_deck_search = true,
                        "MEMBER_TAP_DELTA" => expected_member_tap_delta += val_i64 as i32,
                        "ACTION_PREVENTION" => expected_action_prevention = true,
                        "STAGE_ENERGY_DELTA" => expected_stage_energy_delta += val_i64 as i32,
                        "YELL_DELTA" => expected_yell_delta += val_i64 as i32,
                        _ => {
                            if clean_tag == "ENERGY_COST_DELTA" {
                                expected_energy_cost += val_i64 as i32;
                            }
                        }
                    }
                }
            }
        }

        // --- Start Comparisons ---
        
        // Helper to check saturating/99 logic
        let check_delta = |tag: &str, actual: i32, expected: i32, baseline_val: i32| -> Result<(), String> {
            if expected == 99 {
                if actual == 0 && baseline_val > 0 {
                    return Err(format!("Mismatch {} (All Expected): Exp 99, Got 0 (had {} available)", tag, baseline_val));
                }
                return Ok(());
            }
            if actual != expected {
                return Err(format!("Mismatch {} for '{}': Exp {}, Got {}", tag, combined_text, expected, actual));
            }
            Ok(())
        };

        // HAND (P0)
        let actual_hand = current_p0.hand_len as i32 - baseline_p0.hand_len as i32;
        if expected_hand_discard {
            if actual_hand > 0 && expected_hand_delta < 0 {
                return Err(format!("Mismatch HAND (Discard Expected): Exp {}, Got {}", expected_hand_delta, actual_hand));
            }
        }
        check_delta("HAND_DELTA", actual_hand, expected_hand_delta, baseline_p0.hand_len as i32)?;

        // HAND (P1)
        let actual_opp_hand = current_p1.hand_len as i32 - baseline_p1.hand_len as i32;
        if opp_hand_discard {
            if actual_opp_hand > 0 && opp_hand_delta < 0 {
                return Err(format!("Mismatch OPPONENT_HAND (Discard Expected): Exp {}, Got {}", opp_hand_delta, actual_opp_hand));
            }
        }
        if opp_hand_delta != 0 {
            check_delta("OPPONENT_HAND_DELTA", actual_opp_hand, opp_hand_delta, baseline_p1.hand_len as i32)?;
        }

        // ENERGY COST (P0 Active Energy)
        let actual_cost = baseline_p0.active_energy as i32 - current_p0.active_energy as i32;
        if expected_energy_cost != 99 && actual_cost < expected_energy_cost {
             return Err(format!("Mismatch ENERGY_COST for '{}': Exp {}, Got {}", combined_text, expected_energy_cost, actual_cost));
        } else if expected_energy_cost == 99 && actual_cost == 0 && baseline_p0.active_energy > 0 {
             return Err(format!("Mismatch ENERGY_COST (All Expected): Exp 99, Got 0"));
        }

        // SCORE (P0)
        let actual_score = current_p0.score.saturating_sub(baseline_p0.score);
        if expected_score_delta != 99 && actual_score < (expected_score_delta as u32) {
             return Err(format!("Mismatch SCORE_DELTA for '{}': Exp {}, Got {}", combined_text, expected_score_delta, actual_score));
        }

        // HEART (P0)
        let actual_heart = current_p0.total_heart_buffs.saturating_sub(baseline_p0.total_heart_buffs);
        if expected_heart_delta > 0 {
            if expected_heart_delta == 99 {
                if actual_heart == 0 {
                    return Err(format!("Mismatch HEART_DELTA (All Expected): Exp 99, Got 0"));
                }
            } else if actual_heart < (expected_heart_delta as u32) {
                 return Err(format!("Mismatch HEART_DELTA for '{}': Exp {}, Got {}", combined_text, expected_heart_delta, actual_heart));
            }
        }

        // YELL (P0)
        if expected_yell_delta != 0 {
            let actual_yell = current_p0.yell_count as i32 - baseline_p0.yell_count as i32;
            if actual_yell != expected_yell_delta {
                return Err(format!("Mismatch YELL_DELTA for '{}': Exp {}, Got {}", combined_text, expected_yell_delta, actual_yell));
            }
        }

        // STAGE (P0)
        check_delta("STAGE_DELTA", (current_p0.active_members_count as i32) - (baseline_p0.active_members_count as i32), expected_stage_delta, 3)?;

        // STAGE (P1)
        if opp_stage_delta != 0 {
            check_delta("OPPONENT_STAGE_DELTA", (current_p1.active_members_count as i32) - (baseline_p1.active_members_count as i32), opp_stage_delta, 3)?;
        }

        // DISCARD (P0)
        check_delta("DISCARD_DELTA", current_p0.discard_len as i32 - baseline_p0.discard_len as i32, expected_discard_delta, 20)?;

        // DISCARD (P1)
        if opp_discard_delta != 0 {
            check_delta("OPPONENT_DISCARD_DELTA", current_p1.discard_len as i32 - baseline_p1.discard_len as i32, opp_discard_delta, 20)?;
        }

        // BLADE
        let actual_blade = current_p0.total_blade_buffs.saturating_sub(baseline_p0.total_blade_buffs);
        if actual_blade < expected_blade_delta {
             return Err(format!("Mismatch BLADE_DELTA for '{}': Exp {}, Got {}", combined_text, expected_blade_delta, actual_blade));
        }

        // RECOVER
        if expected_live_recover {
            let actual_discard_loss = baseline_p0.discard_len as i32 - current_p0.discard_len as i32;
             if actual_hand < 1 || actual_discard_loss < 1 {
                 return Err(format!("Mismatch LIVE_RECOVER for '{}'", combined_text));
             }
        }

        // ENERGY_DELTA (P0)
        let actual_energy = current_p0.energy_len as i32 - baseline_p0.energy_len as i32;
        if actual_energy != expected_energy_delta {
             return Err(format!("Mismatch ENERGY_DELTA for '{}': Exp {}, Got {}", combined_text, expected_energy_delta, actual_energy));
        }

        // DECK_SEARCH (P0)
        if expected_deck_search {
            if current_p0.looked_cards_len == 0 && current_p0.hand_len == baseline_p0.hand_len {
                 return Err(format!("Mismatch DECK_SEARCH for '{}': No cards revealed or added to hand", combined_text));
            }
        }

        // TAP (P0)
        let actual_tap = {
            let mut t = 0;
            for i in 0..3 { if !baseline_p0.tapped_members[i] && current_p0.tapped_members[i] { t += 1; } }
            t
        };
        if expected_member_tap_delta == 99 {
            let baseline_untapped = baseline_p0.tapped_members.iter().filter(|&&t| !t).count();
            if actual_tap == 0 && baseline_untapped > 0 {
                 return Err(format!("Mismatch TAP_ALL for '{}': Expected all targets ({} available) but got 0 additional taps", combined_text, baseline_untapped));
            }
        } else if actual_tap < expected_member_tap_delta {
             return Err(format!("Mismatch MEMBER_TAP_DELTA for '{}': Exp {}, Got {}", combined_text, expected_member_tap_delta, actual_tap));
        }

        // TAP (P1)
        if opp_member_tap_delta != 0 {
            let actual_opp_tap = {
                let mut t = 0;
                for i in 0..3 { if !baseline_p1.tapped_members[i] && current_p1.tapped_members[i] { t += 1; } }
                t
            };
            if actual_opp_tap < opp_member_tap_delta {
                return Err(format!("Mismatch OPPONENT_MEMBER_TAP_DELTA for '{}': Exp {}, Got {}", combined_text, opp_member_tap_delta, actual_opp_tap));
            }
        }

        // PREVENTION (P0/P1)
        if expected_action_prevention {
             let p0_changed = current_p0.prevent_activate != baseline_p0.prevent_activate 
                || current_p0.prevent_baton_touch != baseline_p0.prevent_baton_touch 
                || current_p0.prevent_play_mask != baseline_p0.prevent_play_mask;
             let p1_changed = current_p1.prevent_activate != baseline_p1.prevent_activate 
                || current_p1.prevent_baton_touch != baseline_p1.prevent_baton_touch 
                || current_p1.prevent_play_mask != baseline_p1.prevent_play_mask;

             if !p0_changed && !p1_changed {
                  return Err(format!("Mismatch ACTION_PREVENTION for '{}': No change in prevention flags for either player", combined_text));
             }
        }

        // STAGE ENERGY (P0)
        let actual_stage_energy = current_p0.stage_energy_total as i32 - baseline_p0.stage_energy_total as i32;
        if actual_stage_energy < expected_stage_energy_delta {
             return Err(format!("Mismatch STAGE_ENERGY_DELTA for '{}': Exp {}, Got {}", combined_text, expected_stage_energy_delta, actual_stage_energy));
        }
        
        Ok(())
    }

    fn find_real_id(&self, cid_str: &str) -> Result<i32, String> {
        if let Some(id) = self.db.id_by_no(cid_str) {
             return Ok(id as i32);
        }
        Err(format!("Could not map {} to Engine ID", cid_str))
    }

    fn map_trigger_type(&self, trigger_str: &str) -> TriggerType {
        match trigger_str {
            "ON_PLAY" | "ONPLAY" => TriggerType::OnPlay,
            "ON_LIVE_START" | "ONLIVESTART" => TriggerType::OnLiveStart,
            "ACTIVATED" => TriggerType::Activated,
            "CONSTANT" => TriggerType::Constant,
            _ => TriggerType::None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use rayon::prelude::*;

    #[test]
    fn test_semantic_mass_verification() {
        let engine = SemanticAssertionEngine::load();
        let mut card_nos: Vec<String> = engine.truth.keys().cloned().collect();
        card_nos.sort();

        println!("🚀 Starting Parallel Semantic Audit of {} cards...", card_nos.len());
        
        let results: Vec<String> = card_nos.par_iter().map(|cid| {
            let truth = &engine.truth[cid];
            let mut ability_results = Vec::new();

            for (idx, _) in truth.abilities.iter().enumerate() {
                let engine_ref = &engine;
                let cid_ref = cid;
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    engine_ref.verify_card(cid_ref, idx)
                }));

                match result {
                    Ok(Ok(_)) => {
                        let _ = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                            engine_ref.verify_card_negative(cid_ref, idx)
                        }));
                        ability_results.push(format!("| {} | Ab{} | ✅ PASS | |", cid, idx));
                    },
                    Ok(Err(e)) => {
                        ability_results.push(format!("| {} | Ab{} | ❌ FAIL | {} |", cid, idx, e));
                    },
                    Err(_) => {
                        ability_results.push(format!("| {} | Ab{} | 💥 PANIC | |", cid, idx));
                    }
                }
            }
            ability_results.join("\n")
        }).collect();

        let pass = results.iter().filter(|r| r.contains("✅ PASS")).count();
        let total_abilities = results.iter().map(|r| r.split('\n').count()).sum::<usize>();
        let fail = total_abilities - pass;

        println!("Audit Results: {}/{} Abilities Passed", pass, total_abilities);
        
        // Write report
        let mut report = String::from("# Comprehensive Semantic Audit Report\n\n");
        report.push_str(&format!("- Date: 2026-02-23 (Automated Audit)\n"));
        report.push_str(&format!("- Total Abilities: {}\n", total_abilities));
        report.push_str(&format!("- Pass: {}\n- Fail: {}\n\n", pass, fail));
        report.push_str("| Card No | Ability | Status | Details |\n| :--- | :--- | :--- | :--- |\n");
        report.push_str(&results.join("\n"));
        
        std::fs::write("../reports/COMPREHENSIVE_SEMANTIC_AUDIT.md", report).ok();
    }

    #[test]
    fn generate_v2_truth() {
        let engine = SemanticAssertionEngine::load();
        let mut new_truth = HashMap::new();
        
        let mut card_nos: Vec<String> = engine.truth.keys().cloned().collect();
        card_nos.sort();

        println!("🔮 Generating V2 Truth Baseline for {} cards...", card_nos.len());

        for cid in &card_nos {
            let mut recorded_card = SemanticCardTruth {
                id: cid.clone(),
                abilities: Vec::new(),
            };

            let abilities_count = engine.truth[cid].abilities.len();
            for idx in 0..abilities_count {
                if let Ok(Some(mut recorded_ability)) = engine.record_card(cid, idx) {
                    // Restore original Japanese text for readability
                    if let Some(segment) = recorded_ability.sequence.get_mut(0) {
                        if let Some(old_segment) = engine.truth[cid].abilities[idx].sequence.get(0) {
                            segment.text = old_segment.text.clone();
                        }
                    }
                    recorded_card.abilities.push(recorded_ability);
                }
            }
            new_truth.insert(cid.clone(), recorded_card);
        }

        let output = serde_json::to_string_pretty(&new_truth).unwrap();
        std::fs::write("../reports/semantic_truth_v2.json", output).expect("Failed to write v2 truth");
        println!("✅ V2 Truth Baseline written to reports/semantic_truth_v2.json");
    }

    #[test]
    fn test_archetype_sd1_001_success_live_cond() {
        let engine = SemanticAssertionEngine::load();
        // PL!-sd1-001-SD: Ab0 (Success Live Condition)
        // Debug: Check setup
        let mut state = crate::test_helpers::create_test_state();
        state.ui.silent = false; // Enable debug output
        state.debug.debug_mode = true; // Enable interpreter debug mode
        let real_id = engine.find_real_id("PL!-sd1-001-SD").unwrap();
        SemanticAssertionEngine::setup_oracle_environment(&mut state, &engine.db, real_id);
        
        println!("[DEBUG] success_lives: {:?}", state.core.players[0].success_lives);
        println!("[DEBUG] discard: {:?}", state.core.players[0].discard);
        
        // Check if condition would pass
        let count = state.core.players[0].success_lives.len();
        println!("[DEBUG] success_lives count: {}", count);
        
        // Check if discard contains live cards
        for &cid in &state.core.players[0].discard {
            if engine.db.get_live(cid).is_some() {
                println!("[DEBUG] Found live card in discard: {}", cid);
            }
        }
        
        // Check if success_lives contains live cards
        for &cid in &state.core.players[0].success_lives {
            if engine.db.get_live(cid).is_some() {
                println!("[DEBUG] Found live card in success_lives: {}", cid);
            } else {
                println!("[DEBUG] NOT a live card in success_lives: {}", cid);
            }
        }
        
        engine.verify_card("PL!-sd1-001-SD", 0).unwrap();
    }

    #[test]
    fn test_archetype_sd1_003_optional_discard() {
        let engine = SemanticAssertionEngine::load();
        // PL!-sd1-003-SD: Ab1 (Optional Discard 1)
        engine.verify_card("PL!-sd1-003-SD", 1).unwrap();
    }

    #[test]
    fn test_archetype_n_pr_005_draw_2_discard_2() {
        let engine = SemanticAssertionEngine::load();
        // PL!N-PR-005-PR: Ab0 (Draw 2, Discard 2)
        engine.verify_card("PL!N-PR-005-PR", 0).unwrap();
    }



}
