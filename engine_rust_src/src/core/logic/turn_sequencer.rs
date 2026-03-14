// ─────────────────────────────────────────────────────────────────────────────
// turn_sequencer – LOVECA vanilla heuristic and exact/beam DFS search
// ─────────────────────────────────────────────────────────────────────────────
//
// OVERVIEW
// ┌──────────────────────────────────────────────────────────────────────┐
// │ plan_full_turn()  →  exact_root_turn_search() or beam_search_turn() │
// │      ↓ leaf evaluation                                               │
// │ evaluate_turn_goal_breakdown()   ← main heuristic (see below)       │
// │      ↓ used during LiveSet selection                                 │
// │ find_best_liveset_selection_internal()                               │
// └──────────────────────────────────────────────────────────────────────┘
//
// HEURISTIC PRIORITY (evaluate_turn_goal_breakdown)
//  1. WIN  – terminal win or guaranteed zone slam (success_count + guaranteed ≥ 3)
//            → TURN_GOAL_WIN_WEIGHT + speed bonus (earlier wins worth more)
//  2. SUCCESS COUNT – confirmed past successes × TURN_GOAL_SUCCESS_WEIGHT
//  3. ZONE – lives currently in live zone
//     a. Guaranteed (prob ≥ 1.2): GUARANTEED_CLEAR_BASE
//     b. Uncertain: net_ev = p × PASS_WEIGHT − (1−p) × DISCARD_COST
//        Negative for low-probability lives → AI will NOT commit them until the
//        stage is strong enough to pass.
//  4. CLOSEOUT PRESSURE – as the turn cap approaches, current zone pressure matters
//     more than theoretical future value from deck/hand lives.
//  5. PENALTIES – deadline, empty live zone when must commit, uncertain overcommit
//
// KEY CONSTANTS – tune here to change play-style:
//   GUARANTEED_CLEAR_BASE       base value for a certain zone clear
//   LIVE_DISCARD_COST_SCALE     opportunity cost of wasting a failed live card
//   SPEED_PER_TURN_BONUS        per-remaining-turn reward when winning is guaranteed
//   TURN_GOAL_WIN_WEIGHT        terminal or committed-win absolute value
//   TURN_GOAL_SUCCESS_WEIGHT    each confirmed success live (past rounds)
//   HARD_TURN_LIMIT             maximum rounds the game is allowed to run
//
// DECK ORDER NOTE
//   The heuristic NEVER uses the order of cards in player.deck.
//   Future deck live EV is computed via HashMap<card_id, count> (composition-only).
// ─────────────────────────────────────────────────────────────────────────────
use std::collections::HashMap;
use std::fs;
use std::hash::{Hash, Hasher};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, RwLock};
use std::thread;
use std::time::{Duration, Instant};
use std::sync::OnceLock;
use rand::seq::IndexedRandom;
use rand::rngs::SmallRng;
use rand::SeedableRng;
#[cfg(feature = "parallel")]
use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

use crate::core::enums::Phase;
use crate::core::logic::constants::*;
use crate::core::logic::{CardDatabase, GameState};
use crate::core::{ACTION_BASE_HAND, ACTION_BASE_LIVESET, ACTION_BASE_PASS};
use std::ops::BitXor;

// ═════════════════════════════════════════════════════════════════════════════
// MODULE: CONSTANTS & CONFIGURATION
// ═════════════════════════════════════════════════════════════════════════════

// MCTS Constants
#[allow(dead_code)]
const MCTS_EXPLORATION_CONST: f32 = 1.414; // sqrt(2) for UCB1
const HARD_TURN_LIMIT: u16 = 10;

// ─────────────────────────────────────────────────────────────────────────────
// Heuristic weight constants
// ─────────────────────────────────────────────────────────────────────────────
// Win/Loss detection (terminal or committed-to-win this pass)
const TURN_GOAL_WIN_WEIGHT: f32 = 100_000.0;
// Reward winning earlier: each turn of headroom at a guaranteed-win moment
const SPEED_PER_TURN_BONUS: f32 = 800.0;
// Each confirmed success (live already passed)
const TURN_GOAL_SUCCESS_WEIGHT: f32 = 10_000.0;
// Guaranteed zone clear (prob >= 1.2): base value
// MUST be far above the max non-guaranteed zone value so a certain clear always beats uncertain
const GUARANTEED_CLEAR_BASE: f32 = 30_000.0;
// Non-guaranteed zone clear: expected-value weight
const TURN_GOAL_LIVE_PASS_WEIGHT: f32 = 4_000.0;  // max ~4000 for prob=1.0
// Opportunity cost of discarding a live card when it fails.
// net_ev = p × PASS_WEIGHT - (1-p) × DISCARD_COST
// At scale=1400, breakeven is ~26% regardless of a live's printed judgement value.
// This keeps the planner focused on reaching 3 successes quickly instead of hoarding lives.
const LIVE_DISCARD_COST_SCALE: f32 = 1_400.0;
// Future potential (hand/deck lives not yet placed)
const FUTURE_LIVE_WEIGHT_HAND: f32 = 24.0;   // immediate access, probability-weighted only
const FUTURE_LIVE_WEIGHT_DECK: f32 = 9.0;    // lower than hand because it still must be drawn
// Momentum / completion acceleration
const TURN_GOAL_COMPLETION_WEIGHT: f32 = 3_000.0;
const TURN_GOAL_ZONE_PRESSURE_WEIGHT: f32 = 4_500.0;
// Penalties
const TURN_GOAL_DEADLINE_PENALTY: f32 = 5_000.0;    // cannot reach 3 in time
const TURN_GOAL_OVERCOMMIT_PENALTY: f32 = 1_800.0;  // risky excess uncertain lives in zone
const TURN_GOAL_EMPTY_LIVE_PENALTY: f32 = 4_000.0;  // must commit but zone is empty
const TURN_GOAL_LATE_EMPTY_LIVE_PENALTY: f32 = 6_500.0;
// Weak-member cycling (useless hand card can be replaced)
#[allow(dead_code)]
const WEAK_MEMBER_CYCLE_BONUS: f32 = 100.0;

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct WeightsConfig {
    pub board_presence: f32,
    pub blades: f32,
    pub hearts: f32,
    pub saturation_bonus: f32,
    pub energy_penalty: f32,
    pub live_ev_multiplier: f32,
    pub uncertainty_penalty_pow: f32,
    pub liveset_placement_bonus: f32,
    pub cycling_bonus: f32,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SearchConfig {
    pub max_dfs_depth: usize,
    pub mc_trials: usize,
    pub beam_width: usize,
    pub use_memoization: bool,
    pub beam_search: bool,
    pub use_alpha_beta: bool,
}

#[derive(Debug, Clone)]
pub struct EvaluationContext {
    pub deck_stats: [crate::core::logic::DeckStats; 2],
    pub deck_live_counts: [HashMap<i32, u32>; 2],
    pub yell_bonus_table: [[[f32; 7]; 61]; 2],
    pub notes_bonus_table: [[f32; 61]; 2],
}

impl EvaluationContext {
    pub fn new(state: &crate::core::logic::GameState, db: &crate::core::logic::CardDatabase) -> Self {
        use crate::core::heuristics::calculate_deck_expectations;
        let mut deck_stats = [crate::core::logic::DeckStats::default(), crate::core::logic::DeckStats::default()];
        let mut deck_live_counts = [HashMap::new(), HashMap::new()];
        let mut yell_bonus_table = [[[0.0; 7]; 61]; 2];
        let mut notes_bonus_table = [[0.0; 61]; 2];

        for p_idx in 0..2 {
            let player = &state.players[p_idx];
            let stats = calculate_deck_expectations(&player.deck, db);
            deck_stats[p_idx] = stats;
            
            // Pre-calculate yell bonus table for all possible counts (0-60)
            for count in 0..61 {
                for color in 0..7 {
                    yell_bonus_table[p_idx][count][color] = stats.avg_hearts[color] * count as f32;
                }
                notes_bonus_table[p_idx][count] = stats.avg_notes * count as f32;
            }

            let mut live_counts = HashMap::new();
            for &cid in &player.deck {
                if db.get_live(cid).is_some() {
                    *live_counts.entry(cid).or_insert(0) += 1;
                }
            }
            deck_live_counts[p_idx] = live_counts;
        }

        Self {
            deck_stats,
            deck_live_counts,
            yell_bonus_table,
            notes_bonus_table,
        }
    }
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct SequencerConfig {
    pub weights: WeightsConfig,
    pub search: SearchConfig,
}

pub static CONFIG: OnceLock<RwLock<SequencerConfig>> = OnceLock::new();

pub fn get_config() -> &'static RwLock<SequencerConfig> {
    CONFIG.get_or_init(|| {
        let path = "sequencer_config.json";
        let base = if let Ok(content) = fs::read_to_string(path) {
            serde_json::from_str(&content).unwrap_or_default()
        } else {
            SequencerConfig::default()
        };
        RwLock::new(base)
    })
}

pub struct SearchTelemetry {
    enabled: bool,
    done: AtomicBool,
    aborted: AtomicBool,
    node_count: AtomicUsize,
    root_done: AtomicUsize,
    root_total: AtomicUsize,
    best_seq_len: AtomicUsize,
    best_val_bits: AtomicU32Compat,
}

struct AtomicU32Compat(std::sync::atomic::AtomicU32);

#[allow(dead_code)]
impl AtomicU32Compat {
    fn new(value: u32) -> Self {
        Self(std::sync::atomic::AtomicU32::new(value))
    }

    fn load(&self, ordering: Ordering) -> u32 {
        self.0.load(ordering)
    }

    fn store(&self, value: u32, ordering: Ordering) {
        self.0.store(value, ordering)
    }
}

#[allow(dead_code)]
impl SearchTelemetry {
    fn disabled() -> Self {
        Self {
            enabled: false,
            done: AtomicBool::new(false),
            aborted: AtomicBool::new(false),
            node_count: AtomicUsize::new(0),
            root_done: AtomicUsize::new(0),
            root_total: AtomicUsize::new(0),
            best_seq_len: AtomicUsize::new(0),
            best_val_bits: AtomicU32Compat::new(f32::NEG_INFINITY.to_bits()),
        }
    }
}

static SEARCH_TELEMETRY: OnceLock<RwLock<Option<Arc<SearchTelemetry>>>> = OnceLock::new();

pub fn get_search_telemetry() -> &'static RwLock<Option<Arc<SearchTelemetry>>> {
    SEARCH_TELEMETRY.get_or_init(|| RwLock::new(None))
}

impl Default for SequencerConfig {
    fn default() -> Self {
        Self {
            weights: WeightsConfig::default(),
            search: SearchConfig::default(),
        }
    }
}

impl Default for WeightsConfig {
    fn default() -> Self {
        Self {
            board_presence: 2.5,
            blades: 3.5,               // INCREASED: Blades are game-enders
            hearts: 1.5,               // INCREASED: Hearts are the fuel
            saturation_bonus: 8.0,     // INCREASED: Board filling is vital
            energy_penalty: 0.1,
            live_ev_multiplier: 55.0,  // SIGNIFICANTLY INCREASED: Focus on winning
            uncertainty_penalty_pow: 1.1,
            liveset_placement_bonus: 12.0, // INCREASED: Encourage putting cards in zone
            cycling_bonus: 4.5,        // NEW: Bonus for placing cards in zone (draw potential)
        }
    }
}

#[derive(Debug, Clone, Default)]
pub struct HeuristicBreakdown {
    pub board_score: f32,
    pub live_ev: f32,
    pub success_val: f32,
    pub win_bonus: f32,
    pub hand_momentum: f32,
    pub cycling_bonus: f32,
    pub total: f32,
}

// ═════════════════════════════════════════════════════════════════════════════
// MODULE: STATE CACHING & HASHING
// ═════════════════════════════════════════════════════════════════════════════

const TT_SIZE: usize = 262144; // 2^18
const TT_MASK: u64 = (TT_SIZE - 1) as u64;

#[derive(Clone)]
struct TTEntry {
    key: u64,
    depth: usize,
    value: (SmallVec<[i32; 16]>, f32, (f32, f32)),
}

struct TranspositionTable {
    entries: Vec<Option<TTEntry>>,
}

#[allow(dead_code)]
impl TranspositionTable {
    fn new() -> Self {
        Self {
            entries: vec![None; TT_SIZE],
        }
    }

    fn get(&self, _state: &GameState, depth: usize) -> Option<(Vec<i32>, f32, (f32, f32))> {
        // Simple manual hash of key state fields for TT indexing
        let mut key = _state.turn as u64;
        key ^= (_state.current_player as u64) << 16;
        key ^= (_state.phase as u64) << 24;
        key ^= _state.players[0].cached_total_hearts.0.rotate_left(17);
        key ^= _state.players[1].cached_total_hearts.0.rotate_left(41);
        
        let idx = (key & TT_MASK) as usize;
        
        if let Some(entry) = &self.entries[idx] {
            if entry.key == key && entry.depth >= depth {
                return Some((entry.value.0.to_vec(), entry.value.1, entry.value.2));
            }
        }
        None
    }

    fn insert(&mut self, _state: &GameState, depth: usize, value: (Vec<i32>, f32, (f32, f32))) {
        // Simple manual hash of key state fields for TT indexing
        let mut key = _state.turn as u64;
        key ^= (_state.current_player as u64) << 16;
        key ^= (_state.phase as u64) << 24;
        key ^= _state.players[0].cached_total_hearts.0.rotate_left(17);
        key ^= _state.players[1].cached_total_hearts.0.rotate_left(41);
        let idx = (key & TT_MASK) as usize;

        // Depth-preferred replacement
        let replace = match &self.entries[idx] {
            Some(existing) => depth >= existing.depth,
            None => true,
        };

        if replace {
            self.entries[idx] = Some(TTEntry { 
                key, 
                depth, 
                value: (SmallVec::from(value.0), value.1, value.2) 
            });
        }
    }
}

impl Default for SearchConfig {
    fn default() -> Self {
        Self {
            max_dfs_depth: HARD_TURN_LIMIT as usize,
            mc_trials: 100,
            beam_width: 8,
            use_memoization: false,
            beam_search: false,
            use_alpha_beta: false,
        }
    }
}

#[allow(dead_code)]
fn hash_pending_interaction<H: Hasher>(pending: &crate::core::logic::PendingInteraction, state: &mut H) {
    pending.ctx.hash(state);
    pending.card_id.hash(state);
    pending.ability_index.hash(state);
    pending.effect_opcode.hash(state);
    pending.target_slot.hash(state);
    pending.choice_type.hash(state);
    pending.filter_attr.hash(state);
    pending.choice_text.hash(state);
    pending.v_remaining.hash(state);
    pending.original_phase.hash(state);
    pending.original_current_player.hash(state);
    pending.actions.hash(state);
    pending.execution_id.hash(state);
}

/// A fast, non-cryptographic hasher based on rustc-hash (FxHash)
/// specifically for use in the Transposition Table where speed is critical.
pub struct FxHasher {
    hash: u64,
}

impl Default for FxHasher {
    #[inline]
    fn default() -> Self {
        Self { hash: 0 }
    }
}

impl std::hash::Hasher for FxHasher {
    #[inline]
    fn finish(&self) -> u64 {
        self.hash
    }

    #[inline]
    fn write(&mut self, bytes: &[u8]) {
        let mut hash = self.hash;
        for &byte in bytes {
            // FxHash constant: 0x517cc1b727220a95
            hash = hash.rotate_left(5).bitxor(byte as u64).wrapping_mul(0x517cc1b727220a95);
        }
        self.hash = hash;
    }

    #[inline]
    fn write_u64(&mut self, i: u64) {
        self.hash = self.hash.rotate_left(5).bitxor(i).wrapping_mul(0x517cc1b727220a95);
    }

    #[inline]
    fn write_u32(&mut self, i: u32) {
        self.hash = self.hash.rotate_left(5).bitxor(i as u64).wrapping_mul(0x517cc1b727220a95);
    }

    #[inline]
    fn write_usize(&mut self, i: usize) {
        self.hash = self.hash.rotate_left(5).bitxor(i as u64).wrapping_mul(0x517cc1b727220a95);
    }
}

#[allow(dead_code)]
fn state_cache_key(state: &GameState) -> u64 {
    use std::hash::Hasher;
    let mut hasher = FxHasher::default();
    
    // Hash players manually to avoid full struct overhead
    for p in &state.players {
        p.player_id.hash(&mut hasher);
        p.hand.hash(&mut hasher);
        p.deck.hash(&mut hasher);
        p.discard.hash(&mut hasher);
        p.energy_zone.hash(&mut hasher);
        p.stage.hash(&mut hasher);
        p.score.hash(&mut hasher);
        p.flags.hash(&mut hasher);
        p.tapped_energy_mask.hash(&mut hasher);
        p.success_lives.hash(&mut hasher);
        p.live_zone.hash(&mut hasher);
        p.baton_touch_count.hash(&mut hasher);
        p.blade_buffs.hash(&mut hasher);
        p.blade_overrides.hash(&mut hasher);
        p.heart_buffs.hash(&mut hasher);
        p.slot_cost_modifiers.hash(&mut hasher);
        p.hand_increased_this_turn.hash(&mut hasher);
        p.play_count_this_turn.hash(&mut hasher);
        p.board_aura.hash(&mut hasher);
    }

    state.current_player.hash(&mut hasher);
    state.first_player.hash(&mut hasher);
    state.phase.hash(&mut hasher);
    state.turn.hash(&mut hasher);
    state.trigger_depth.hash(&mut hasher);

    for pending in &state.interaction_stack {
        hash_pending_interaction(pending, &mut hasher);
    }
    for (card_id, opcode, ctx, mandatory, trigger) in &state.trigger_queue {
        card_id.hash(&mut hasher);
        opcode.hash(&mut hasher);
        ctx.hash(&mut hasher);
        mandatory.hash(&mut hasher);
        trigger.hash(&mut hasher);
    }

    hasher.finish()
}

pub struct TurnSequencer;

// ═════════════════════════════════════════════════════════════════════════════
// MODULE: MCTS IMPLEMENTATION
// ═════════════════════════════════════════════════════════════════════════════

/// MCTS Node for Monte Carlo Tree Search
#[allow(dead_code)]
#[derive(Clone)]
struct MctsNode {
    state: GameState,
    action: Option<i32>,
    parent: Option<usize>,
    children: Vec<usize>,
    visits: u32,
    total_score: f32,
    untried_actions: Vec<i32>,
    depth: usize,
}

#[allow(dead_code)]
impl MctsNode {
    fn new(state: GameState, action: Option<i32>, parent: Option<usize>, db: &CardDatabase) -> Self {
        // Get legal actions for this state
        let legal_ids = state.get_legal_action_ids(db);

        Self {
            state,
            action,
            parent,
            children: Vec::new(),
            visits: 0,
            total_score: 0.0,
            untried_actions: legal_ids,
            depth: 0, // Not used for limiting anymore
        }
    }

    fn ucb1(&self, parent_visits: u32) -> f32 {
        if self.visits == 0 {
            f32::INFINITY
        } else {
            let exploitation = self.total_score / self.visits as f32;
            let exploration = MCTS_EXPLORATION_CONST * (parent_visits as f32 / self.visits as f32).sqrt();
            exploitation + exploration
        }
    }

    fn is_fully_expanded(&self) -> bool {
        self.untried_actions.is_empty()
    }

    fn average_score(&self) -> f32 {
        if self.visits == 0 {
            0.0
        } else {
            self.total_score / self.visits as f32
        }
    }
}

/// MCTS Tree structure
#[allow(dead_code)]
struct MctsTree {
    nodes: Vec<MctsNode>,
    db: CardDatabase,
}

#[allow(dead_code)]
impl MctsTree {
    fn new(root_state: GameState, db: CardDatabase) -> Self {
        let mut nodes = Vec::new();

        // Get legal actions for root with actual db
        let legal_ids = root_state.get_legal_action_ids(&db);

        let root = MctsNode {
            state: root_state,
            action: None,
            parent: None,
            children: Vec::new(),
            visits: 0,
            total_score: 0.0,
            untried_actions: legal_ids,
            depth: 0,
        };

        nodes.push(root);

        Self { nodes, db }
    }

    fn root_index(&self) -> usize {
        0
    }

    fn select_child(&self, node_idx: usize) -> Option<usize> {
        let node = &self.nodes[node_idx];
        if node.children.is_empty() {
            return None;
        }

        let parent_visits = node.visits;
        let mut best_idx = None;
        let mut best_ucb = f32::NEG_INFINITY;

        for &child_idx in &node.children {
            let ucb = self.nodes[child_idx].ucb1(parent_visits);
            if ucb > best_ucb {
                best_ucb = ucb;
                best_idx = Some(child_idx);
            }
        }

        best_idx
    }

    fn expand(&mut self, parent_idx: usize) -> Option<usize> {
        let parent = &mut self.nodes[parent_idx];

        if parent.untried_actions.is_empty() {
            return None;
        }

        // Pick a random untried action
        let action_idx = parent.untried_actions.len() - 1;
        let action = parent.untried_actions.remove(action_idx);

        // Apply action to create new state
        let mut new_state = parent.state.clone();
        new_state.ui.silent = true;

        let success = new_state.step(&self.db, action).is_ok();

        if !success {
            // Action failed, create a terminal node with low score
            let new_node = MctsNode {
                state: new_state,
                action: Some(action),
                parent: Some(parent_idx),
                children: Vec::new(),
                visits: 1,
                total_score: -100.0, // Failed action gets negative score
                untried_actions: Vec::new(),
                depth: parent.depth + 1,
            };

            let new_idx = self.nodes.len();
            self.nodes.push(new_node);
            self.nodes[parent_idx].children.push(new_idx);
            return Some(new_idx);
        }

        // Get legal actions for the new state (no depth limit for MCTS)
        let new_legal_ids = new_state.get_legal_action_ids(&self.db);

        let new_node = MctsNode {
            state: new_state,
            action: Some(action),
            parent: Some(parent_idx),
            children: Vec::new(),
            visits: 0,
            total_score: 0.0,
            untried_actions: new_legal_ids,
            depth: parent.depth + 1,
        };

        let new_idx = self.nodes.len();
        self.nodes.push(new_node);
        self.nodes[parent_idx].children.push(new_idx);

        Some(new_idx)
    }

    fn simulate(&self, node_idx: usize) -> f32 {
        let node = &self.nodes[node_idx];

        // Simulate to the end of the turn (Main + LiveSet phases)
        let mut sim_state = node.state.clone();
        sim_state.ui.silent = true;

        // Use random playout for the rest of the turn
        thread_local! {
            static LOCAL_RNG: std::cell::RefCell<SmallRng> = std::cell::RefCell::new(SmallRng::from_os_rng());
        }
        
        LOCAL_RNG.with(|rng_cell| {
            let mut rng = rng_cell.borrow_mut();
            let mut steps = 0;
            let max_steps = 100; // Safety limit for simulation

            while sim_state.phase == Phase::Main && steps < max_steps {
                let legal = sim_state.get_legal_action_ids(&self.db);
                if legal.is_empty() {
                    break;
                }
                if let Some(&action) = legal.choose(&mut *rng) {
                    let _ = sim_state.step(&self.db, action);
                }
                steps += 1;
            }
        });

        // Handle LiveSet phase
        if sim_state.phase == Phase::LiveSet {
            // Use the best liveset selection for simulation
            let weights = TurnSequencer::config_snapshot().weights;
            let eval_ctx = EvaluationContext::new(&sim_state, &self.db);
            let (ls_actions, _, _) = TurnSequencer::find_best_liveset_selection_internal(&sim_state, &self.db, &weights, &eval_ctx);
            for &act in &ls_actions {
                let _ = sim_state.step(&self.db, act);
            }
        }

        // Evaluate final state
        let (board_score, live_ev) = TurnSequencer::evaluate_state_internal(&sim_state, &self.db);
        board_score + live_ev
    }

    fn backpropagate(&mut self, node_idx: usize, score: f32) {
        let mut idx = Some(node_idx);
        while let Some(i) = idx {
            self.nodes[i].visits += 1;
            self.nodes[i].total_score += score;
            idx = self.nodes[i].parent;
        }
    }

    fn get_best_sequence(&self) -> Vec<i32> {
        let root = &self.nodes[self.root_index()];
        if root.children.is_empty() {
            return Vec::new();
        }

        // Find the child with highest average score
        let mut best_child = root.children[0];
        let mut best_avg = f32::NEG_INFINITY;

        for &child_idx in &root.children {
            let avg = self.nodes[child_idx].average_score();
            if avg > best_avg {
                best_avg = avg;
                best_child = child_idx;
            }
        }

        // Build sequence by following best children
        let mut sequence = Vec::new();
        let mut current_idx = best_child;

        while !self.nodes[current_idx].children.is_empty() {
            if let Some(action) = self.nodes[current_idx].action {
                sequence.push(action);
            }

            // Continue with best child
            let mut best_next = self.nodes[current_idx].children[0];
            let mut best_next_avg = f32::NEG_INFINITY;

            for &child_idx in &self.nodes[current_idx].children {
                let avg = self.nodes[child_idx].average_score();
                if avg > best_next_avg {
                    best_next_avg = avg;
                    best_next = child_idx;
                }
            }

            current_idx = best_next;
        }

        // Add final action
        if let Some(action) = self.nodes[current_idx].action {
            sequence.push(action);
        }

        sequence
    }
}

#[derive(Clone)]
pub struct SequenceResult {
    pub actions: Vec<i32>,
    pub expected_value: f32,
    pub success_prob: f32,
}

// ═════════════════════════════════════════════════════════════════════════════
// MODULE: MAIN SEARCH & EVALUATION ENGINE
// ═════════════════════════════════════════════════════════════════════════════
// Contains: Telemetry helpers, Search algorithms (exact/beam), Evaluation heuristics,
//            LiveSet selection, and the main turn planning API.
// ═════════════════════════════════════════════════════════════════════════════

impl TurnSequencer {
    fn config_snapshot() -> SequencerConfig {
        get_config().read().unwrap().clone()
    }

    #[allow(dead_code)]
    fn progress_enabled() -> bool {
        matches!(std::env::var("TURNSEQ_PROGRESS").ok().as_deref(), Some("1") | Some("true") | Some("TRUE"))
    }

    #[allow(dead_code)]
    fn stall_seconds() -> u64 {
        std::env::var("TURNSEQ_STALL_SECS")
            .ok()
            .and_then(|value| value.parse().ok())
            .unwrap_or(10)
    }

    #[allow(dead_code)]
    fn install_telemetry(root_total: usize) -> (Arc<SearchTelemetry>, Option<thread::JoinHandle<()>>) {
        let telemetry = Arc::new(if Self::progress_enabled() {
            SearchTelemetry {
                enabled: true,
                done: AtomicBool::new(false),
                aborted: AtomicBool::new(false),
                node_count: AtomicUsize::new(0),
                root_done: AtomicUsize::new(0),
                root_total: AtomicUsize::new(root_total),
                best_seq_len: AtomicUsize::new(0),
                best_val_bits: AtomicU32Compat::new(f32::NEG_INFINITY.to_bits()),
            }
        } else {
            SearchTelemetry::disabled()
        });

        *get_search_telemetry().write().unwrap() = Some(Arc::clone(&telemetry));

        if !telemetry.enabled {
            return (telemetry, None);
        }

        let telemetry_for_thread = Arc::clone(&telemetry);
        let handle = thread::spawn(move || {
            let stall_secs = Self::stall_seconds();
            let start = Instant::now();
            let mut last_nodes = 0usize;
            let mut stagnant_seconds = 0u64;

            loop {
                thread::sleep(Duration::from_secs(1));

                let nodes = telemetry_for_thread.node_count.load(Ordering::Relaxed);
                let elapsed = start.elapsed().as_secs_f32().max(1.0);
                let rate = nodes as f32 / elapsed;
                let roots_done = telemetry_for_thread.root_done.load(Ordering::Relaxed);
                let roots_total = telemetry_for_thread.root_total.load(Ordering::Relaxed);
                let best_len = telemetry_for_thread.best_seq_len.load(Ordering::Relaxed);
                let best_val = f32::from_bits(telemetry_for_thread.best_val_bits.load(Ordering::Relaxed));

                eprintln!(
                    "[search] t={:.0}s nodes={} rate={:.1}/s roots={}/{} best_val={:.3} best_len={}",
                    elapsed,
                    nodes,
                    rate,
                    roots_done,
                    roots_total,
                    best_val,
                    best_len,
                );

                if telemetry_for_thread.done.load(Ordering::Relaxed) {
                    break;
                }

                if nodes == last_nodes {
                    stagnant_seconds += 1;
                    if stagnant_seconds >= stall_secs {
                        telemetry_for_thread.aborted.store(true, Ordering::Relaxed);
                        eprintln!("[search] stalled for {}s without node progress; aborting current search", stall_secs);
                        break;
                    }
                } else {
                    last_nodes = nodes;
                    stagnant_seconds = 0;
                }
            }
        });

        (telemetry, Some(handle))
    }

    #[allow(dead_code)]
    fn clear_telemetry(telemetry: &Arc<SearchTelemetry>, handle: Option<thread::JoinHandle<()>>) {
        telemetry.done.store(true, Ordering::Relaxed);
        if let Some(join_handle) = handle {
            let _ = join_handle.join();
        }
        *get_search_telemetry().write().unwrap() = None;
    }

    #[allow(dead_code)]
    fn telemetry_snapshot() -> Option<Arc<SearchTelemetry>> {
        get_search_telemetry().read().unwrap().clone()
    }

    #[allow(dead_code)]
    fn exact_turn_threshold() -> usize {
        std::env::var("TURNSEQ_EXACT_THRESHOLD")
            .ok()
            .and_then(|value| value.parse().ok())
            .unwrap_or(1500)
    }

    #[allow(dead_code)]
    fn vanilla_exact_turn_threshold() -> usize {
        std::env::var("TURNSEQ_VANILLA_EXACT_THRESHOLD")
            .ok()
            .and_then(|value| value.parse().ok())
            .unwrap_or(512)
    }

    fn exact_parallel_min_actions() -> usize {
        std::env::var("TURNSEQ_EXACT_PARALLEL_MIN_ACTIONS")
            .ok()
            .and_then(|value| value.parse().ok())
            .unwrap_or(4)
    }

    fn exact_parallel_enabled() -> bool {
        !matches!(
            std::env::var("TURNSEQ_DISABLE_EXACT_PARALLEL").ok().as_deref(),
            Some("1") | Some("true") | Some("TRUE")
        )
    }

    #[allow(dead_code)]
    fn exact_turn_threshold_for_state(state: &GameState, db: &CardDatabase) -> usize {
        let base_threshold = if db.is_vanilla {
            Self::vanilla_exact_turn_threshold()
        } else {
            Self::exact_turn_threshold()
        };
        let mut threshold = base_threshold;

        let p_idx = state.current_player as usize;
        let success_count = state.players[p_idx].success_lives.len();
        let turns_remaining = Self::turns_remaining_after_current(state);
        let (live_pass_prob, _, live_count) = Self::live_zone_joint_success_metrics(state, db, p_idx);
        let projected_success = success_count as f32 + live_pass_prob;

        if success_count >= 2 {
            threshold = threshold.saturating_mul(4);
        } else if live_count > 0 && projected_success >= 2.6 {
            threshold = threshold.saturating_mul(3);
        }

        if turns_remaining == 0 {
            threshold = threshold.max(base_threshold.saturating_mul(4));
        }

        if turns_remaining <= 1 && success_count == 0 {
            threshold = threshold.saturating_div(2).max(64);
        } else if turns_remaining <= 1 && success_count == 1 && live_count == 0 {
            threshold = threshold.saturating_mul(3).saturating_div(4).max(64);
        }

        threshold.max(64)
    }

    fn exact_result_is_better(
        candidate_val: f32,
        candidate_seq: &[i32],
        candidate_brk: (f32, f32),
        best_val: f32,
        best_seq: &[i32],
        best_brk: (f32, f32),
    ) -> bool {
        const EPS: f32 = 0.001;

        if candidate_val > best_val + EPS {
            return true;
        }
        if candidate_val + EPS < best_val {
            return false;
        }
        if candidate_brk.1 > best_brk.1 + EPS {
            return true;
        }
        if candidate_brk.1 + EPS < best_brk.1 {
            return false;
        }

        candidate_seq.len() < best_seq.len()
    }

    // ─────────────────────────────────────────────────────────────────────────
    // SEARCH ALGORITHMS
    // ─────────────────────────────────────────────────────────────────────────

    fn exact_root_turn_search(
        state: &GameState,
        db: &CardDatabase,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, f32, (f32, f32), usize) {
        let root_player = state.current_player as usize;
        let mut total_nodes = 0;
        let p_idx = root_player;
        let _hand_len = state.players[p_idx].hand.len();
        let weights = Self::config_snapshot().weights;
        let depth = Self::config_snapshot().search.max_dfs_depth.min(HARD_TURN_LIMIT as usize);

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        let mut pass_state = state.clone();
        let _ = pass_state.step(db, ACTION_BASE_PASS);
        let (mut best_val, mut best_brk, nodes) = Self::evaluate_stop_state_with_nodes(&pass_state, db, root_player, &weights, eval_ctx);
        total_nodes += nodes;
        let mut best_seq = vec![ACTION_BASE_PASS];

        let mut ordered_actions = Vec::new();
        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            let mut next_state = state.clone();
            if next_state.step(db, action).is_err() {
                continue;
            }

            let order_score = Self::quick_move_order_score(&next_state, root_player);
            ordered_actions.push((action, order_score, next_state));
        }

        ordered_actions.sort_by(|a, b| {
            b.1.partial_cmp(&a.1)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| a.0.cmp(&b.0))
        });

        if Self::exact_parallel_enabled() && ordered_actions.len() >= Self::exact_parallel_min_actions() {
            #[cfg(feature = "parallel")]
            let results: Vec<(Vec<i32>, f32, (f32, f32), usize)> = ordered_actions
                .into_par_iter()
                .map(|(action, _, mut next_state)| {
                    let (mut suffix, val, brk, nodes) = Self::exact_small_turn_search(
                        &mut next_state,
                        db,
                        depth.saturating_sub(1),
                        root_player,
                        &weights,
                        eval_ctx,
                    );
                    let mut full = vec![action];
                    full.append(&mut suffix);
                    (full, val, brk, nodes)
                })
                .collect();

            #[cfg(not(feature = "parallel"))]
            let results: Vec<(Vec<i32>, f32, (f32, f32), usize)> = ordered_actions
                .into_iter()
                .map(|(action, _, mut next_state)| {
                    let (mut suffix, val, brk, nodes) = Self::exact_small_turn_search(
                        &mut next_state,
                        db,
                        depth.saturating_sub(1),
                        root_player,
                        &weights,
                        eval_ctx,
                    );
                    let mut full = vec![action];
                    full.append(&mut suffix);
                    (full, val, brk, nodes)
                })
                .collect();

            for (seq, val, brk, nodes) in results {
                total_nodes += nodes;
                if Self::exact_result_is_better(val, &seq, brk, best_val, &best_seq, best_brk) {
                    best_seq = seq;
                    best_val = val;
                    best_brk = brk;
                }
            }

            return (best_seq, best_val, best_brk, total_nodes);
        }

        for (action, _, mut next_state) in ordered_actions {
            let (mut suffix, val, brk, nodes) = Self::exact_small_turn_search(
                &mut next_state,
                db,
                depth.saturating_sub(1),
                root_player,
                &weights,
                eval_ctx,
            );
            total_nodes += nodes;

            let mut full = vec![action];
            full.append(&mut suffix);
            if Self::exact_result_is_better(val, &full, brk, best_val, &best_seq, best_brk) {
                best_seq = full;
                best_val = val;
                best_brk = brk;
            }
        }

        (best_seq, best_val, best_brk, total_nodes)
    }

    fn beam_width_for_state(state: &GameState, search: &SearchConfig) -> usize {
        let p_idx = state.current_player as usize;
        let success_count = state.players[p_idx].success_lives.len();
        let turns_remaining = Self::turns_remaining_after_current(state);
        let mut beam_width = search.beam_width.max(4);

        if success_count == 0 {
            beam_width += 4;
        } else if success_count == 1 {
            beam_width += 2;
        } else if success_count >= 2 {
            beam_width += 2;
        }

        if turns_remaining <= 1 {
            beam_width += 1;
        }

        beam_width
    }

    #[allow(dead_code)]
    fn vanilla_exact_depth_limit(search: &SearchConfig) -> usize {
        search.max_dfs_depth.max(24)
    }

    #[allow(dead_code)]
    fn count_main_end_sequences(state: &GameState, db: &CardDatabase, depth: usize) -> usize {
        if state.phase != Phase::Main || depth == 0 {
            return 1;
        }

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        let mut total = 1usize;
        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            let mut next_state = state.clone();
            if next_state.step(db, action).is_ok() {
                total += Self::count_main_end_sequences(&next_state, db, depth.saturating_sub(1));
            }
        }

        total
    }

    #[allow(dead_code)]
    fn count_main_end_sequences_capped(
        state: &GameState,
        db: &CardDatabase,
        depth: usize,
        cap: usize,
    ) -> usize {
        if state.phase != Phase::Main || depth == 0 {
            return 1;
        }

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        let mut total = 1usize;
        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            if total > cap {
                return cap + 1;
            }

            let mut next_state = state.clone();
            if next_state.step(db, action).is_err() {
                continue;
            }

            let remaining_cap = cap.saturating_sub(total);
            total = total.saturating_add(Self::count_main_end_sequences_capped(
                &next_state,
                db,
                depth.saturating_sub(1),
                remaining_cap,
            ));
        }

        total
    }

    #[allow(dead_code)]
    fn evaluate_stop_state(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        weights: &WeightsConfig,
    ) -> (f32, (f32, f32)) {
        let eval_ctx = EvaluationContext::new(state, db);
        let res = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, &eval_ctx);
        (res.0, res.1)
    }

    fn evaluate_stop_state_with_nodes(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> (f32, (f32, f32), usize) {
        let mut final_state = state.clone();
        let mut nodes = 1;
        if final_state.phase == Phase::LiveSet {
            let (ls_actions, _, ls_nodes) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights, eval_ctx);
            nodes += ls_nodes as usize;
            for &ls_act in &ls_actions {
                let _ = final_state.step(db, ls_act);
            }
        }
        let brk = Self::evaluate_state_for_player_with_weights_ctx(&final_state, db, root_player, weights, eval_ctx);
        (brk.0 + brk.1, brk, nodes)
    }

    /// Fast board state hash: stage composition + hand count + energy state
    #[allow(dead_code)]
    #[inline]
    fn board_state_hash(state: &GameState, p_idx: usize) -> u64 {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::Hasher;
        let mut hasher = DefaultHasher::new();
        
        // Hash stage (which cards are placed)
        for &cid in &state.players[p_idx].stage {
            hasher.write_i32(cid);
        }
        
        // Hash hand count (not individual cards, just total)
        hasher.write_usize(state.players[p_idx].hand.len());
        
        // Hash energy state (tapped vs untapped matters)
        hasher.write_usize(state.players[p_idx].energy_zone.len());
        hasher.write_usize(state.players[p_idx].tapped_energy_count() as usize);
        
        hasher.finish()
    }

    fn exact_small_turn_search(
        state: &mut GameState,
        db: &CardDatabase,
        depth: usize,
        root_player: usize,
        weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, f32, (f32, f32), usize) {
        let mut node_count = 1;

        if depth >= Self::config_snapshot().search.max_dfs_depth {
            let (board, live) = Self::evaluate_state_for_player_with_weights_ctx(state, db, root_player, weights, eval_ctx);
            return (Vec::new(), board + live, (board, live), 1);
        }

        if state.phase != Phase::Main {
            let (val, brk, nodes) = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, eval_ctx);
            return (vec![], val, brk, nodes);
        }

        if depth == 0 {
            let mut pass_state = state.clone();
            if pass_state.step(db, ACTION_BASE_PASS).is_ok() {
                let (val, brk, nodes) = Self::evaluate_stop_state_with_nodes(&pass_state, db, root_player, weights, eval_ctx);
                return (vec![ACTION_BASE_PASS], val, brk, nodes);
            }

            let (val, brk, nodes) = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, eval_ctx);
            return (vec![], val, brk, nodes);
        }

        let mut best_seq = vec![ACTION_BASE_PASS];
        let mut pass_state = state.clone();
        let _ = pass_state.step(db, ACTION_BASE_PASS);
        let (mut best_val, mut best_brk, nodes) = Self::evaluate_stop_state_with_nodes(&pass_state, db, root_player, weights, eval_ctx);
        node_count += nodes;

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        for action in actions.into_iter().filter(|&action| action != ACTION_BASE_PASS) {
            let mut next_state = state.clone();
            if next_state.step(db, action).is_err() {
                continue;
            }

            let (mut suffix, val, brk, nodes) = Self::exact_small_turn_search(
                &mut next_state,
                db,
                depth.saturating_sub(1),
                root_player,
                weights,
                eval_ctx,
            );
            node_count += nodes;

            if val > best_val {
                let mut full = vec![action];
                full.append(&mut suffix);
                best_seq = full;
                best_val = val;
                best_brk = brk;
            }
        }

        (best_seq, best_val, best_brk, node_count)
    }

    /// Returns a list of (ActionID, Total, Board, Live) for all legal actions,
    /// the best overall sequence, the total nodes, and the best score breakdown.
    pub fn plan_full_turn(state: &GameState, db: &CardDatabase) -> (Vec<i32>, f32, (f32, f32), usize) {
        let config = Self::config_snapshot();
        let weights = config.weights.clone();
        let p_idx = state.current_player as usize;
        let capped_depth = config.search.max_dfs_depth.min(HARD_TURN_LIMIT as usize);

        if state.phase != Phase::Main {
            let eval_ctx = EvaluationContext::new(state, db);
            let (seq, val, brk, nodes) = Self::exact_small_turn_search(
                &mut state.clone(), // exact_small_turn_search expects &mut GameState
                db,
                capped_depth,
                p_idx,
                &weights,
                &eval_ctx,
            );
            return (seq, val, brk, nodes);
        }

        let exact_threshold = Self::exact_turn_threshold_for_state(state, db);
        let sequence_estimate = if config.search.beam_search {
            exact_threshold.saturating_add(1)
        } else {
            Self::count_main_end_sequences_capped(state, db, capped_depth, exact_threshold)
        };

        let eval_ctx = EvaluationContext::new(state, db);

        if config.search.beam_search || sequence_estimate > exact_threshold {
            let mut beam_width = Self::beam_width_for_state(state, &config.search);
            if sequence_estimate <= exact_threshold.saturating_mul(2) {
                beam_width += 2;
            }
            let (seq, val, brk) = Self::beam_search_turn(
                state,
                db,
                p_idx,
                capped_depth,
                beam_width,
                &weights,
                &eval_ctx,
            );
            return (seq, val, brk, sequence_estimate.min(exact_threshold.saturating_add(1)));
        }

        let (seq, val, brk, total_evals) = Self::exact_root_turn_search(
            state,
            db,
            &eval_ctx,
        );
        (seq, val, brk, total_evals)
    }

    /// Compatibility wrapper for the rest of the engine (e.g. MCTS and Heuristics)
    pub fn find_best_main_sequence(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let (seq, _, _, evals) = Self::plan_full_turn(state, db);
        (seq, 0, evals as u128)
    }

    pub fn plan_full_turn_exact(state: &GameState, db: &CardDatabase) -> (Vec<i32>, f32, (f32, f32), usize) {
        let config = Self::config_snapshot();
        let weights = config.weights;
        let p_idx = state.current_player as usize;
        let depth = config.search.max_dfs_depth.min(HARD_TURN_LIMIT as usize);
        let eval_ctx = EvaluationContext::new(state, db);
        let (seq, val, brk, total_evals) = if state.phase == Phase::Main {
            Self::exact_root_turn_search(
                state,
                db,
                &eval_ctx,
            )
        } else {
            Self::exact_small_turn_search(
                &mut state.clone(),
                db,
                depth,
                p_idx,
                &weights,
                &eval_ctx,
            )
        };
        (seq, val, brk, total_evals)
    }

    /// Run exhaustive search to find the best sequence of moves for the current turn
    /// This explores ALL legal combinations to the end of the turn (Main + LiveSet phases)
    /// Note: This uses DFS with no depth limit, exploring all possible action sequences
    pub fn plan_full_turn_mcts(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let mut best_seq = Vec::new();
        let mut best_val = f32::NEG_INFINITY;
        let mut nodes_visited = 0;

        let eval_ctx = EvaluationContext::new(state, db);

        // Get all legal actions for the current state
        let legal_actions = state.get_legal_action_ids(db);
        let total_legal = legal_actions.len();

        for &action in &legal_actions {
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            // Apply the action
            if sim_state.step(db, action).is_ok() {
                let mut current_seq = vec![action];

                // Recursively explore remaining moves in Main phase
                Self::exhaustive_search_main(&mut sim_state, db, &mut current_seq, &mut best_seq, &mut best_val, &mut nodes_visited, &eval_ctx);
            }
        }

        (best_seq, total_legal, nodes_visited as u128)
    }

    /// Recursively search all combinations in Main phase
    /// Stops when no more legal actions in Main phase
    fn exhaustive_search_main(
        state: &mut GameState,
        db: &CardDatabase,
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        nodes_visited: &mut usize,
        eval_ctx: &EvaluationContext,
    ) {
        *nodes_visited += 1;

        // Safety: limit recursion depth to prevent stack overflow
        if *nodes_visited > 100000 {
            return;
        }

        // Check if we're still in Main phase
        if state.phase != Phase::Main {
            // We've exited Main, now handle LiveSet
            Self::exhaustive_search_liveset(state, db, current_seq, best_seq, best_val, nodes_visited, eval_ctx);
            return;
        }

        // Get legal actions from current state
        let legal_actions = state.get_legal_action_ids(db);

        // If no more actions in Main, try LiveSet
        if legal_actions.is_empty() {
            Self::exhaustive_search_liveset(state, db, current_seq, best_seq, best_val, nodes_visited, eval_ctx);
            return;
        }

        // Try each legal action - but limit to prevent explosion
        // Only explore a reasonable number of paths
        let max_paths = 1000;
        let paths_to_try = legal_actions.len().min(max_paths);

        for i in 0..paths_to_try {
            let action = legal_actions[i];
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            if sim_state.step(db, action).is_ok() {
                current_seq.push(action);
                Self::exhaustive_search_main(&mut sim_state, db, current_seq, best_seq, best_val, nodes_visited, eval_ctx);
                current_seq.pop();
            }
        }
    }

    /// Exhaustively search LiveSet combinations and evaluate
    fn exhaustive_search_liveset(
        state: &mut GameState,
        db: &CardDatabase,
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        nodes_visited: &mut usize,
        eval_ctx: &EvaluationContext,
    ) {
        *nodes_visited += 1;

        // If we're not in LiveSet phase, just evaluate
        if state.phase != Phase::LiveSet {
            let weights = Self::config_snapshot().weights;
            let (board_score, live_ev) = Self::evaluate_state_for_player_with_weights_ctx(state, db, state.current_player as usize, &weights, eval_ctx);
            let total_val = board_score + live_ev;

            if total_val > *best_val {
                *best_val = total_val;
                *best_seq = current_seq.clone();
            }
            return;
        }

        // Get legal LiveSet actions
        let legal_actions = state.get_legal_action_ids(db);

        // If no more LiveSet actions, evaluate
        if legal_actions.is_empty() {
            let weights = Self::config_snapshot().weights;
            let (board_score, live_ev) = Self::evaluate_state_for_player_with_weights_ctx(state, db, state.current_player as usize, &weights, eval_ctx);
            let total_val = board_score + live_ev;

            if total_val > *best_val {
                *best_val = total_val;
                *best_seq = current_seq.clone();
            }
            return;
        }

        // Try each LiveSet action
        for &action in &legal_actions {
            let mut sim_state = state.clone();
            sim_state.ui.silent = true;

            if sim_state.step(db, action).is_ok() {
                current_seq.push(action);
                Self::exhaustive_search_liveset(&mut sim_state, db, current_seq, best_seq, best_val, nodes_visited, eval_ctx);
                current_seq.pop();
            }
        }
    }

    pub fn plan_full_turn_with_stats(state: &GameState, db: &CardDatabase) -> (Vec<(i32, f32, f32, f32)>, Vec<i32>, usize, f32, (f32, f32)) {
        let start = Instant::now();
        let (seq, _, breakdown, evals) = Self::plan_full_turn(state, db);
        let duration = start.elapsed().as_secs_f32();
        (vec![], seq, evals, duration, breakdown)
    }
    pub fn find_best_liveset_selection(state: &GameState, db: &CardDatabase) -> (Vec<i32>, usize, u128) {
        let weights = Self::config_snapshot().weights;
        let eval_ctx = EvaluationContext::new(state, db);
        Self::find_best_liveset_selection_internal(state, db, &weights, &eval_ctx)
    }

    pub fn beam_search_turn(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        beam_width: usize,
        weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        let mut beam: Vec<(GameState, Vec<i32>, f32, (f32, f32))> = vec![(state.clone(), Vec::new(), 0.0, (0.0, 0.0))];
        let mut best_overall_seq = Vec::new();
        let mut best_overall_val = f32::NEG_INFINITY;
        let mut best_overall_breakdown = (0.0, 0.0);

        for _ in 0..depth {
            let mut next_beam = Vec::new();
            let mut any_main = false;

            for (curr_state, seq, _, _) in beam {
                if curr_state.phase != Phase::Main {
                    continue;
                }
                any_main = true;

                let mut legal_actions = SmallVec::<[i32; 64]>::new();
                curr_state.generate_legal_actions(db, curr_state.current_player as usize, &mut legal_actions);
                let mut candidates = Vec::new();

                for action in legal_actions {
                    let mut next_state = curr_state.clone();
                    if next_state.step(db, action).is_ok() {
                        if next_state.phase != Phase::Main {
                            // Evaluate transition to LiveSet
                            let mut final_state = next_state.clone();
                            if final_state.phase == Phase::LiveSet {
                                let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(&final_state, db, weights, eval_ctx);
                                for &ls_act in &ls_actions {
                                    let _ = final_state.step(db, ls_act);
                                }
                            }
                            let (b, l) = Self::evaluate_state_for_player_with_weights_ctx(&final_state, db, root_player, weights, eval_ctx);
                            candidates.push((next_state, action, b + l, (b, l)));
                        } else {
                            // Immediate heuristic for move ordering
                            let (b, l) = Self::evaluate_state_for_player_with_weights_ctx(&next_state, db, root_player, weights, eval_ctx);
                            candidates.push((next_state, action, b + l, (b, l)));
                        }
                    }
                }

                // Sort and take top beam_width
                candidates.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
                for (ns, act, val, brk) in candidates.into_iter().take(beam_width) {
                    let mut next_seq = seq.clone();
                    next_seq.push(act);
                    next_beam.push((ns, next_seq, val, brk));
                }
            }

            if !any_main { break; }

            next_beam.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
            beam = next_beam.into_iter().take(beam_width).collect();

            if let Some((_, seq, val, brk)) = beam.first() {
                if *val > best_overall_val {
                    best_overall_val = *val;
                    best_overall_seq = seq.clone();
                    best_overall_breakdown = *brk;
                }
            }
        }

        (best_overall_seq, best_overall_val, best_overall_breakdown)
    }

    #[allow(dead_code)]
    fn dfs_turn_memoized(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        search: &SearchConfig,
        weights: &WeightsConfig,
        tt: &mut TranspositionTable,
        total_count: &AtomicUsize,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        let eval_ctx = EvaluationContext::new(state, db);
        if search.use_alpha_beta {
            Self::dfs_alpha_beta(
                state, db, root_player, depth, search, weights, tt, total_count,
                f32::NEG_INFINITY, f32::INFINITY, &eval_ctx
            )
        } else {
            Self::dfs_negamax(state, db, root_player, depth, search, weights, tt, total_count, &eval_ctx)
        }
    }

    /// Alpha-beta pruned DFS: dramatically reduces node count while preserving optimal result
    #[allow(dead_code)]
    fn dfs_alpha_beta(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        search: &SearchConfig,
        weights: &WeightsConfig,
        tt: &mut TranspositionTable,
        total_count: &AtomicUsize,
        mut alpha: f32,
        beta: f32,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        total_count.fetch_add(1, Ordering::Relaxed);

        if let Some(telemetry) = Self::telemetry_snapshot() {
            telemetry.node_count.fetch_add(1, Ordering::Relaxed);
            if telemetry.aborted.load(Ordering::Relaxed) {
                return (vec![ACTION_BASE_PASS], f32::NEG_INFINITY, (f32::NEG_INFINITY, 0.0));
            }
        }

        if depth == 0 || state.phase != Phase::Main {
            let res = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, eval_ctx);
            return (vec![], res.0, res.1);
        }

        if search.use_memoization {
            if let Some(entry) = tt.get(state, depth) {
                return entry;
            }
        }

        let mut best_val = f32::NEG_INFINITY;
        let mut best_seq = Vec::new();
        let mut best_brk = (0.0, 0.0);

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        // Quick heuristic scoring and sorting (ESSENTIAL for AB pruning) - but cheap!
        let do_order = depth > 8; 
        let mut sorted_actions = Vec::with_capacity(actions.len());
        
        if do_order {
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    let board_score = Self::move_order_score(&next_state, db, root_player, weights);
                    sorted_actions.push((action, board_score, next_state));
                }
            }
            sorted_actions.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        } else {
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    sorted_actions.push((action, 0.0, next_state));
                }
            }
        }

        for (action, _, next_state) in sorted_actions {
            let (mut suffix, val, brk) = Self::dfs_alpha_beta(
                &next_state,
                db,
                root_player,
                depth.saturating_sub(1),
                search,
                weights,
                tt,
                total_count,
                alpha,
                beta,
                eval_ctx,
            );
            
            if val > best_val {
                best_val = val;
                best_brk = brk;
                let mut full = vec![action];
                full.append(&mut suffix);
                best_seq = full;
                alpha = alpha.max(val);
            }
            
            if alpha >= beta {
                break;
            }
        }

        if best_val == f32::NEG_INFINITY {
            let res = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, eval_ctx);
            best_val = res.0;
            best_brk = res.1;
        }

        let result = (best_seq, best_val, best_brk);
        if search.use_memoization {
            tt.insert(state, depth, result.clone());
        }
        result
    }

    /// Original DFS without pruning (for comparison/debugging)
    #[allow(dead_code)]
    fn dfs_negamax(
        state: &GameState,
        db: &CardDatabase,
        root_player: usize,
        depth: usize,
        search: &SearchConfig,
        weights: &WeightsConfig,
        tt: &mut TranspositionTable,
        total_count: &AtomicUsize,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, f32, (f32, f32)) {
        total_count.fetch_add(1, Ordering::Relaxed);

        if let Some(telemetry) = Self::telemetry_snapshot() {
            telemetry.node_count.fetch_add(1, Ordering::Relaxed);
            if telemetry.aborted.load(Ordering::Relaxed) {
                return (vec![ACTION_BASE_PASS], f32::NEG_INFINITY, (f32::NEG_INFINITY, 0.0));
            }
        }

        if depth == 0 || state.phase != Phase::Main {
            let res = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, eval_ctx);
            return (vec![], res.0, res.1);
        }

        if search.use_memoization {
            if let Some(entry) = tt.get(state, depth) {
                return entry;
            }
        }

        let mut best_val = f32::NEG_INFINITY;
        let mut best_seq = Vec::new();
        let mut best_brk = (0.0, 0.0);

        let mut actions = SmallVec::<[i32; 64]>::new();
        state.generate_legal_actions(db, state.current_player as usize, &mut actions);

        // Light move ordering only at shallow depths (depth counts DOWN from 15, so depth > 8 is shallow)
        let do_order = depth > 8;  // Order in first ~7 moves for better search quality
        
        if do_order {
            // Light move ordering for shallow searches (ultra-light: count pieces only)
            let mut sorted_actions = Vec::with_capacity(actions.len());
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                    // Board-state heuristic for move ordering (good pruning signal)
                    let board_score = Self::move_order_score(&next_state, db, root_player, weights);
                    sorted_actions.push((action, board_score, next_state));
                }
            }
            sorted_actions.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));

            for (action, _, next_state) in sorted_actions {
                let (mut suffix, val, brk) = Self::dfs_negamax(
                    &next_state,
                    db,
                    root_player,
                    depth.saturating_sub(1),
                    search,
                    weights,
                    tt,
                    total_count,
                    eval_ctx,
                );
                if val > best_val {
                    best_val = val;
                    best_brk = brk;
                    let mut full = vec![action];
                    full.append(&mut suffix);
                    best_seq = full;
                }
            }
        } else {
            // No move ordering at deep levels - just explore
            for action in actions {
                let mut next_state = state.clone();
                if next_state.step(db, action).is_ok() {
                let (mut suffix, val, brk) = Self::dfs_negamax(
                    &next_state,
                    db,
                    root_player,
                    depth.saturating_sub(1),
                    search,
                    weights,
                    tt,
                    total_count,
                    eval_ctx,
                );
                    if val > best_val {
                        best_val = val;
                        best_brk = brk;
                        let mut full = vec![action];
                        full.append(&mut suffix);
                        best_seq = full;
                    }
                }
            }
        }

        if best_val == f32::NEG_INFINITY {
            let res = Self::evaluate_stop_state_with_nodes(state, db, root_player, weights, eval_ctx);
            best_val = res.0;
            best_brk = res.1;
        }

        let result = (best_seq, best_val, best_brk);
        if search.use_memoization {
            tt.insert(state, depth, result.clone());
        }
        result
    }

    fn find_best_liveset_selection_with_weights(
        state: &GameState,
        db: &CardDatabase,
        weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, usize, u128) {
        Self::find_best_liveset_selection_internal(state, db, weights, eval_ctx)
    }

    /// Strategic turn phase detector (early/mid/late game)
    #[inline]
    #[allow(dead_code)]
    fn get_game_phase(state: &GameState) -> &'static str {
        if state.turn <= 3 { "early" }
        else if state.turn <= HARD_TURN_LIMIT { "mid" }
        else { "late" }
    }

    /// Phased energy penalty - more aggressive early, more conservative late
    #[inline]
    #[allow(dead_code)]
    fn phased_energy_penalty(state: &GameState, weights: &WeightsConfig) -> f32 {
        match Self::get_game_phase(state) {
            "early" => weights.energy_penalty * 0.5,  // Aggressive spending early
            "mid" => weights.energy_penalty,
            "late" => weights.energy_penalty * 2.0,   // Conservative late game
            _ => weights.energy_penalty,
        }
    }

    /// Phased saturation bonus - higher values late game, but penalize 1-card boards
    #[inline]
    #[allow(dead_code)]
    fn phased_saturation_bonus(state: &GameState, filled_slots: usize, weights: &WeightsConfig) -> f32 {
        if filled_slots == 0 { return 0.0; }
        
        let phase = Self::get_game_phase(state);
        match filled_slots {
            1 => {
                // Heavily penalize slow 1-card boards in mid/late game
                match phase {
                    "early" => weights.saturation_bonus * 0.15,
                    "mid" => -2.0,
                    "late" => -4.0,
                    _ => weights.saturation_bonus * 0.1,
                }
            }
            2 => {
                // Good progress, scale by phase
                match phase {
                    "early" => weights.saturation_bonus * 0.35,
                    "mid" => weights.saturation_bonus * 0.6,
                    "late" => weights.saturation_bonus * 0.8,
                    _ => weights.saturation_bonus * 0.35,
                }
            }
            3 => {
                // Full board always good, stronger late
                match phase {
                    "late" => weights.saturation_bonus * 1.3,
                    _ => weights.saturation_bonus,
                }
            }
            _ => 0.0,
        }
    }

    /// Count feasible live cards in hand (can be reached with current board + yells)
    #[inline]
    #[allow(dead_code)]
    fn count_feasible_lives(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
    ) -> usize {
        let p = &state.players[p_idx];
        p.hand
            .iter()
            .filter_map(|&cid| db.get_live(cid))
            .filter(|live| {
                // A live is feasible if at least one color can be reached
                (0..7).any(|c| {
                    board_hearts[c] as f32 + expected_yell_hearts[c] 
                        >= live.required_hearts[c] as f32
                })
            })
            .count()
    }

    /// Dynamic live_ev_multiplier based on reachable lives
    #[inline]
    #[allow(dead_code)]
    fn dynamic_live_ev_multiplier(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
        base_multiplier: f32,
    ) -> f32 {
        let feasible_count = Self::count_feasible_lives(state, db, p_idx, board_hearts, expected_yell_hearts);
        
        match feasible_count {
            0 => base_multiplier * 0.3,    // Defensive (no viable lives, focus on board)
            1 => base_multiplier * 0.7,    // Single target (moderate push)
            2 => base_multiplier,          // Two targets (balanced)
            3 => base_multiplier * 1.3,    // Three+ targets (aggressive race)
            _ => base_multiplier * 1.5,
        }
    }

    /// Assess hand quality (how many playable cards, diversity of costs)
    #[inline]
    #[allow(dead_code)]
    fn assess_hand_quality(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
        let p = &state.players[p_idx];
        let untapped_energy = p.energy_zone.len() - p.tapped_energy_count() as usize;
        
        let mut playable_count = 0;
        let mut cost_sum = 0usize;
        let mut cost_variance = 0.0f32;
        let avg_cost = if p.hand.is_empty() { 0.0 } else {
            let total: usize = p.hand.iter()
                .filter_map(|&cid| {
                    db.get_member(cid).map(|m| {
                        if m.cost as usize <= untapped_energy {
                            playable_count += 1;
                        }
                        cost_sum += m.cost as usize;
                        m.cost as usize
                    })
                })
                .sum();
            total as f32 / p.hand.len() as f32
        };
        
        // Calculate cost diversity (higher is better - means more flexibility)
        for &cid in &p.hand {
            if let Some(m) = db.get_member(cid) {
                let diff = (m.cost as f32 - avg_cost).abs();
                cost_variance += diff * diff;
            }
        }
        
        let playable_ratio = if p.hand.is_empty() { 0.0 } else {
            playable_count as f32 / p.hand.len() as f32
        };
        
        // Hand quality score: playability * diversity
        let diversity_bonus = if cost_variance > 0.0 { 1.0 + (cost_variance / 10.0).min(1.0) } else { 0.5 };
        playable_ratio * diversity_bonus * p.hand.len() as f32 * 1.2
    }

    #[allow(dead_code)]
    fn evaluate_members_only_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> (f32, f32) { // (base_score, hand_momentum)
        let mut score = 0.0;
        let mut filled_slots = 0;
        let p = &state.players[p_idx];

        // Pre-calculate board hearts (color 6 is Any/Wild)
        let board_hearts = state.get_total_hearts(p_idx, db, 0).to_array();
        
        // Calculate deficits from active lives
        let mut deficits = [0i32; 7];
        let mut active_lives_found = false;
        
        for &cid in &p.live_zone {
            if cid >= 0 {
                if let Some(live) = db.get_live(cid) {
                    active_lives_found = true;
                    for c in 0..7 {
                        let red = p.heart_req_reductions.get_color_count(c) as i32;
                        let req = (live.required_hearts[c] as i32 - red).max(0);
                        deficits[c] += (req - board_hearts[c] as i32).max(0);
                    }
                }
            }
        }

        // If no active lives, look at hand for the most promising candidate
        if !active_lives_found {
            let mut best_candidate = None;
            let mut max_promise = -1.0;
            for &cid in &p.hand {
                if let Some(live) = db.get_live(cid) {
                    let difficulty: u32 = live.required_hearts.iter().map(|&h| h as u32).sum();
                    let promise = live.score as f32 / (difficulty as f32).max(1.0);
                    if promise > max_promise {
                        max_promise = promise;
                        best_candidate = Some(live);
                    }
                }
            }
            if let Some(live) = best_candidate {
                for c in 0..7 {
                    let red = p.heart_req_reductions.get_color_count(c) as i32;
                    let req = (live.required_hearts[c] as i32 - red).max(0);
                    deficits[c] += (req - board_hearts[c] as i32).max(0);
                }
            }
        }

        // Score members on stage
        for i in 0..3 {
            let cid = p.stage[i];
            if cid >= 0 {
                filled_slots += 1;
                score += weights.board_presence;

                if let Some(m) = db.get_member(cid) {
                    score += m.blades as f32 * weights.blades;
                    
                    // Needs-aware heart scoring: prioritize deficit hearts
                    for c in 0..7 {
                        let count = m.hearts[c] as f32;
                        if count > 0.0 {
                            if deficits[c] > 0 {
                                // STRATEGIC: Heavily prioritize filling deficits
                                score += count * weights.hearts * 3.0;
                            } else if deficits[c] == 0 && active_lives_found {
                                // Mid value if requirements met (encourages building reserve)
                                score += count * weights.hearts * 0.7;
                            } else {
                                // Low value if no live requirement exists yet
                                score += count * weights.hearts * 0.4;
                            }
                        }
                    }
                }
            }
        }

        // STRATEGIC: Phased saturation bonus (turn-aware, discourages slow 1-card boards)
        score += Self::phased_saturation_bonus(state, filled_slots, weights);

        let untapped = p.energy_zone.len() - p.tapped_energy_count() as usize;
        
        // STRATEGIC: Hand quality assessment (not just quantity)
        let hand_quality = Self::assess_hand_quality(state, db, p_idx);
        
        // Evaluate potential future plays from hand (costed appropriately)
        let mut reserve_member_values = SmallVec::<[f32; 16]>::new();
        for &cid in &p.hand {
            if let Some(m) = db.get_member(cid) {
                // Heuristic for playing from hand: slightly reduced immediate value
                let immediate_value = (weights.board_presence * 0.35)
                    + (m.blades as f32 * weights.blades * 0.35)
                    + (m.hearts.iter().sum::<u8>() as f32 * weights.hearts * 0.25);
                
                // STRATEGIC: Phase-aware energy cost penalty
                let phase_penalty = Self::phased_energy_penalty(state, weights);
                let cost_drag = (m.cost as usize).saturating_sub(untapped) as f32 * phase_penalty;
                reserve_member_values.push((immediate_value - cost_drag).max(0.0));
            }
        }
        reserve_member_values.sort_by(|a, b| b.partial_cmp(a).unwrap_or(std::cmp::Ordering::Equal));
        score += reserve_member_values.into_iter().take(3).sum::<f32>() * 0.5;

        // STRATEGIC: Hand Momentum weighted by quality, not just quantity
        let hand_momentum = hand_quality;

        // STRATEGIC: Phase-aware energy penalty
        let phase_penalty = Self::phased_energy_penalty(state, weights);
        score -= untapped as f32 * phase_penalty;
        
        (score, hand_momentum)
    }

    /// Ultra-light scoring JUST for move ordering - avoids DB lookups
    #[inline]
    #[allow(dead_code)]
    fn quick_move_order_score(
        state: &GameState,
        p_idx: usize,
    ) -> f32 {
        let mut score = 0.0;
        let mut filled_slots = 0;

        // Just count pieces, no DB lookups
        for i in 0..3 {
            if state.players[p_idx].stage[i] >= 0 {
                filled_slots += 1;
                score += 1.0;  // Base unit for piece presence
            }
        }

        if filled_slots == 3 {
            score += 1.0;  // Bonus for full board
        }

        let untapped = state.players[p_idx].energy_zone.len() - state.players[p_idx].tapped_energy_count() as usize;
        score -= untapped as f32 * 0.1;  // Light energy penalty
        score
    }

    // Use board-state eval for move ordering (weights included = good pruning signal)
    #[inline]
    #[allow(dead_code)]
    fn move_order_score(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> f32 {
        let (base_score, _hand_momentum) = Self::evaluate_members_only_with_weights(state, db, p_idx, weights);
        base_score
    }

    fn turns_remaining_after_current(state: &GameState) -> usize {
        HARD_TURN_LIMIT.saturating_sub(state.turn) as usize
    }

    #[allow(dead_code)]
    fn zone_card_cycle_priority(cid: i32, db: &CardDatabase) -> f32 {
        if let Some(member) = db.get_member(cid) {
            let heart_total = member.hearts.iter().map(|&value| value as f32).sum::<f32>();
            let blade_heart_total = member
                .blade_hearts
                .iter()
                .map(|&value| value as f32)
                .sum::<f32>();
            let pressure = member.blades as f32 * 1.5 + heart_total + blade_heart_total * 0.5;
            (8.0 - pressure).max(0.0) + member.cost as f32 * 0.4
        } else if let Some(live) = db.get_live(cid) {
            let difficulty = live
                .required_hearts
                .iter()
                .map(|&value| value as f32)
                .sum::<f32>();
            (difficulty - live.score as f32 * 0.15).max(0.0)
        } else {
            0.0
        }
    }

    fn live_zone_joint_success_metrics(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
    ) -> (f32, f32, usize) {
        use crate::core::heuristics::calculate_live_success_prob;

        let eval_ctx = EvaluationContext::new(state, db);
        let Some((board_hearts, expected_yell_hearts, heart_reductions)) =
            Self::build_live_eval_context_ctx(state, db, p_idx, &eval_ctx)
        else {
            return (0.0, 0.0, 0);
        };

        let mut combined = crate::core::logic::card_db::LiveCard::default();
        let mut best_live_score: f32 = 0.0;
        let mut live_count = 0usize;

        for &cid in &state.players[p_idx].live_zone {
            if let Some(live) = db.get_live(cid) {
                for color in 0..7 {
                    combined.required_hearts[color] = combined.required_hearts[color]
                        .saturating_add(live.required_hearts[color]);
                }
                best_live_score = best_live_score.max(live.score as f32);
                live_count += 1;
            }
        }

        if live_count == 0 {
            return (0.0, 0.0, 0);
        }

        let prob = calculate_live_success_prob(
            &combined,
            &board_hearts,
            &expected_yell_hearts,
            heart_reductions,
        )
        .min(1.0);

        (prob, best_live_score, live_count)
    }

    // ─────────────────────────────────────────────────────────────────────────
    // EVALUATION & HEURISTIC SCORING
    // ─────────────────────────────────────────────────────────────────────────

    fn evaluate_turn_goal_breakdown(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        _weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> HeuristicBreakdown {
        use crate::core::heuristics::calculate_live_success_prob;

        let player = &state.players[p_idx];
        let success_count = player.success_lives.len();

        // Track actual score earned from past successes.
        let turns_remaining = Self::turns_remaining_after_current(state);
        let needed_successes = 3usize.saturating_sub(success_count);

        // ── Build context for live probability calculations ────────────────────
        let (board_hearts, expected_yell_hearts, heart_reductions) =
            match Self::build_live_eval_context_ctx(state, db, p_idx, eval_ctx) {
                Some(ctx) => ctx,
                None => {
                    let success_val = success_count as f32 * TURN_GOAL_SUCCESS_WEIGHT;
                    let win_bonus = if success_count >= 3
                        || (state.is_terminal() && state.get_winner() == p_idx as i32)
                    {
                        TURN_GOAL_WIN_WEIGHT
                    } else if state.is_terminal() && state.get_winner() != p_idx as i32 && state.get_winner() != 2 {
                        -TURN_GOAL_WIN_WEIGHT * 0.5
                    } else {
                        0.0
                    };
                    return HeuristicBreakdown {
                        board_score: 0.0,
                        live_ev: 0.0,
                        success_val,
                        win_bonus,
                        hand_momentum: 0.0,
                        cycling_bonus: 0.0,
                        total: win_bonus + success_val,
                    };
                }
            };

        // ── Priority 1: Lives currently in live zone ───────────────────────────
        // Guaranteed (prob >= 1.2): every heart requirement satisfied → certain pass.
        //   Zone value = GUARANTEED_CLEAR_BASE
        // Non-guaranteed: expected value = prob × TURN_GOAL_LIVE_PASS_WEIGHT.
        let mut zone_ev_total = 0.0f32;
        let mut zone_prob_sum = 0.0f32;
        let mut live_count = 0usize;
        let mut guaranteed_count = 0usize;  // lives with certainty (prob >= 1.2)
        for &cid in &player.live_zone {
            if cid < 0 {
                continue;
            }
            if let Some(live) = db.get_live(cid) {
                let prob = calculate_live_success_prob(
                    live,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                );
                if prob >= 1.2 {
                    zone_ev_total += GUARANTEED_CLEAR_BASE;
                    zone_prob_sum += 1.0;
                    guaranteed_count += 1;
                } else {
                    let p = prob.min(1.0);
                    let gross_ev = p * TURN_GOAL_LIVE_PASS_WEIGHT;
                    let discard_cost = (1.0 - p) * LIVE_DISCARD_COST_SCALE;
                    let net_ev = gross_ev - discard_cost;
                    zone_ev_total += net_ev;  // May be negative → AI prefers not placing this live
                    zone_prob_sum += p;
                }
                live_count += 1;
            }
        }

        // ── Win detection: already won, terminal, or guaranteed this pass ──────
        // "Will win this pass" = the guaranteed zone clears will push success_count to 3+.
        // This is the most valuable state: assign near-WIN bonus plus a speed reward
        // so earlier wins score higher (forces decisive play, shorter games).
        let will_win_this_pass = (success_count + guaranteed_count) >= 3;
        let already_won = success_count >= 3
            || (state.is_terminal() && state.get_winner() == p_idx as i32);

        let win_bonus = if already_won {
            TURN_GOAL_WIN_WEIGHT
        } else if will_win_this_pass {
            // Committed win this turn: near-full win value + speed bonus
            let turns_left = HARD_TURN_LIMIT.saturating_sub(state.turn) as f32;
            TURN_GOAL_WIN_WEIGHT * 0.95 + turns_left * SPEED_PER_TURN_BONUS
        } else if state.is_terminal()
            && state.get_winner() != p_idx as i32
            && state.get_winner() != 2  // 2 = draw
        {
            -TURN_GOAL_WIN_WEIGHT * 0.5
        } else {
            0.0
        };

        let success_val = success_count as f32 * TURN_GOAL_SUCCESS_WEIGHT;

        // ── Priority 2a: Future clearing potential – lives in hand ────────────
        // Lives in hand can be placed next LiveSet phase (immediate access).
        // Uses composition-only knowledge: does not peek at deck order.
        let mut hand_live_ev = 0.0f32;
        let mut hand_live_count = 0usize;
        for &cid in &player.hand {
            if let Some(live) = db.get_live(cid) {
                let prob = calculate_live_success_prob(
                    live,
                    &board_hearts,
                    &expected_yell_hearts,
                    heart_reductions,
                )
                .min(1.0);
                hand_live_ev += prob * FUTURE_LIVE_WEIGHT_HAND;
                hand_live_count += 1;
            }
        }

        // ── Priority 2b: Future clearing potential – lives in deck ────────────
        // Composition-based only: count how many copies of each live card ID are in the
        // deck, then estimate P(draw ≥1 copy) over remaining turns.  This never uses
        // deck order, only composition (which a human player could also estimate).
        let turns_left_now = HARD_TURN_LIMIT.saturating_sub(state.turn) as f32;
        let deck_access = ((turns_left_now / HARD_TURN_LIMIT as f32) * 4.0).clamp(0.1, 4.0);
        let deck_size = player.deck.len() as f32;

        let mut deck_live_ev = 0f32;
        if deck_size > 0.0 {
            let live_counts = &eval_ctx.deck_live_counts[p_idx];
            for (&cid, &count) in live_counts {
                if let Some(live) = db.get_live(cid) {
                    let prob = calculate_live_success_prob(
                        live,
                        &board_hearts,
                        &expected_yell_hearts,
                        heart_reductions,
                    )
                    .min(1.0);
                    // P(drawing ≥1 copy) approximation
                    let draw_prob = 1.0
                        - ((deck_size - count as f32) / deck_size).powf(deck_access);
                    deck_live_ev += draw_prob * prob * FUTURE_LIVE_WEIGHT_DECK;
                }
            }
        }

        // ── Weak member cycling bonus ─────────────────────────────────────────
        // A member with no hearts and no blades is dead weight – cycling it out
        // gives a small bonus to encourage setting it in LiveSet.
        let mut weak_member_bonus = 0.0f32;
        for &cid in &player.hand {
            if let Some(m) = db.get_member(cid) {
                let heart_total: u32 = m.hearts.iter().map(|&h| h as u32).sum();
                if heart_total == 0 && m.blades == 0 {
                    weak_member_bonus += WEAK_MEMBER_CYCLE_BONUS;
                }
            }
        }

        // ── Completion pressure and deadline penalties ─────────────────────────
        let avg_zone_prob = if live_count > 0 {
            zone_prob_sum / live_count as f32
        } else {
            0.0
        };
        let projected_success = success_count as f32 + avg_zone_prob;
        let late_game_urgency = 1.0 + state.turn as f32 / HARD_TURN_LIMIT as f32;
        let zone_pressure_bonus = zone_prob_sum
            * TURN_GOAL_ZONE_PRESSURE_WEIGHT
            * late_game_urgency
            / needed_successes.max(1) as f32;
        let completion_bonus = projected_success * projected_success * TURN_GOAL_COMPLETION_WEIGHT
            + zone_pressure_bonus;

        // Deadline: if we can no longer reach 3 successes even with perfect draws
        let deadline_cap = success_count + 1 + turns_remaining;
        let deadline_penalty = if deadline_cap < 3 {
            TURN_GOAL_DEADLINE_PENALTY
        } else {
            0.0
        };

        // Must-commit: as the cap approaches, empty live zone is expensive.
        let must_commit_live = needed_successes > 0 && turns_remaining <= needed_successes + 1;
        let empty_live_penalty = if must_commit_live && live_count == 0 {
            TURN_GOAL_LATE_EMPTY_LIVE_PENALTY
        } else if needed_successes > 0
            && turns_remaining <= needed_successes + 2
            && live_count == 0
            && hand_live_count > 0
        {
            TURN_GOAL_EMPTY_LIVE_PENALTY
        } else {
            0.0
        };

        // Overcommit: penalise only UNCERTAIN (non-guaranteed) excess lives.
        // If all zone lives are guaranteed there is no overcommit risk – every one succeeds.
        let uncertain_live_count = live_count.saturating_sub(guaranteed_count);
        let overcommit_penalty = if success_count >= 1 && uncertain_live_count > 1 {
            uncertain_live_count.saturating_sub(1) as f32
                * TURN_GOAL_OVERCOMMIT_PENALTY
                * (1.1 - avg_zone_prob * 0.6).max(0.3)
        } else {
            0.0
        };

        // ── Assemble final score ───────────────────────────────────────────────
        let hand_future_decay = ((turns_remaining as f32 + 1.0) / 4.0).clamp(0.35, 1.0);
        let deck_future_decay = ((turns_remaining as f32 + 1.0) / HARD_TURN_LIMIT as f32)
            .powi(2)
            .clamp(0.05, 1.0);
        let future_live_score = hand_live_ev * hand_future_decay
            + deck_live_ev * deck_future_decay
            + weak_member_bonus * hand_future_decay;

        let total = win_bonus
            + success_val
            + zone_ev_total
            + future_live_score
            + completion_bonus
            - deadline_penalty
            - empty_live_penalty
            - overcommit_penalty;

        HeuristicBreakdown {
            board_score: future_live_score,
            live_ev: avg_zone_prob * 100.0,
            success_val,
            win_bonus,
            hand_momentum: hand_live_ev,
            cycling_bonus: deck_live_ev + weak_member_bonus,
            total,
        }
    }

    pub fn get_score_breakdown(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
    ) -> HeuristicBreakdown {
        let weights = Self::config_snapshot().weights;
        let eval_ctx = EvaluationContext::new(state, db);
        Self::evaluate_turn_goal_breakdown(state, db, p_idx, &weights, &eval_ctx)
    }

    fn evaluate_state_for_player_with_weights_ctx(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> (f32, f32) {
        let breakdown = Self::evaluate_turn_goal_breakdown(state, db, p_idx, weights, eval_ctx);
        (breakdown.total - breakdown.live_ev, breakdown.live_ev)
    }

    fn evaluate_state_for_player_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        weights: &WeightsConfig,
    ) -> (f32, f32) {
        let eval_ctx = EvaluationContext::new(state, db);
        Self::evaluate_state_for_player_with_weights_ctx(state, db, p_idx, weights, &eval_ctx)
    }

    #[allow(dead_code)]
    fn evaluate_live_zone_score_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        _weights: &WeightsConfig,
    ) -> f32 {
        let (prob, best_score, _) = Self::live_zone_joint_success_metrics(state, db, p_idx);
        prob * best_score
    }

    fn predict_best_liveset_score_with_weights(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        _weights: &WeightsConfig,
    ) -> f32 {
        let (prob, best_score, _) = Self::live_zone_joint_success_metrics(state, db, p_idx);
        prob * best_score
    }

    /// Fast approximation of live card value - O(1) instead of O(heart_check)
    #[inline]
    #[allow(dead_code)]
    fn live_card_heuristic_approximation(
        live: &crate::core::logic::card_db::LiveCard,
        _db: &CardDatabase,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
        _heart_reductions: [u8; 7],
    ) -> f32 {
        // Fast path: only check if this live CAN succeed (avoid probability calculation)
        // Live succeeds if for at least one heart color: board + yell >= required
        let mut can_succeed = false;
        for i in 0..7 {
            if board_hearts[i] as f32 + expected_yell_hearts[i] >= live.required_hearts[i] as f32 {
                can_succeed = true;
                break;
            }
        }

        if !can_succeed {
            return 0.0;  // Guaranteed failure, no value
        }

        // Fast path: if specifically board_hearts satisfies it, it's 100% (or very close)
        let mut board_guaranteed = true;
        for i in 0..7 {
            if (board_hearts[i] as f32) < live.required_hearts[i] as f32 {
                board_guaranteed = false;
                break;
            }
        }

        if board_guaranteed {
            return 1_000_000.0 + live.score as f32;
        }

        // For candidates that might succeed, use fast score scaling
        // Instead of exact probability, just scale by live card base score
        live.score as f32 * 0.7  // Conservative estimate (70% chance they help)
    }

    fn live_card_expected_value_with_weights(
        live: &crate::core::logic::card_db::LiveCard,
        db: &CardDatabase,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
        heart_reductions: [u8; 7],
        weights: &WeightsConfig,
    ) -> f32 {
        use crate::core::heuristics::calculate_live_success_prob;

        let prob = if db.is_vanilla {
            calculate_live_success_prob(live, board_hearts, expected_yell_hearts, heart_reductions)
        } else {
            0.5
        };

        if prob >= 1.2 {
            // Priority One: Guaranteed clear
            1_000_000.0 + live.score as f32
        } else {
            prob.powf(weights.uncertainty_penalty_pow) * live.score as f32
        }
    }

    /// Unified DFS that traverses Main and then looks into LiveSet
    #[allow(dead_code)]
    fn dfs_turn(
        state: &mut GameState,
        db: &CardDatabase,
        root_player: usize,
        current_seq: &mut Vec<i32>,
        best_seq: &mut Vec<i32>,
        best_val: &mut f32,
        best_breakdown: &mut (f32, f32),
        total_count: &mut usize,
        eval_ctx: &EvaluationContext,
    ) {
        *total_count += 1;

        if state.phase == Phase::Main {
            if current_seq.len() < Self::config_snapshot().search.max_dfs_depth {
                let p_idx = state.current_player as usize;
                let hand_len = state.players[p_idx].hand.len();

                for h_idx in 0..hand_len {
                    let s0_empty = state.players[p_idx].stage[0] == -1;
                    let s2_empty = state.players[p_idx].stage[2] == -1;
                    let skip_s2 = s0_empty && s2_empty;

                    for slot in 0..STAGE_SLOT_COUNT {
                        if slot == 2 && skip_s2 {
                            continue;
                        }
                        let action = ACTION_BASE_HAND + (h_idx as i32) * 10 + (slot as i32);

                        let cid = state.players[p_idx].hand[h_idx];
                        if state.players[p_idx].stage[slot] == -1 && !state.players[p_idx].is_moved(slot) {
                            let cost = state.get_member_cost(p_idx, cid, slot as i16, -1, db, 0);
                            let energy = state.players[p_idx].get_untapped_energy_indices(cost as usize).len();

                            if energy >= cost as usize {
                                let mut next_state = state.clone();
                                if next_state.step(db, action).is_ok() {
                                    current_seq.push(action);
                                    Self::dfs_turn(
                                        &mut next_state,
                                        db,
                                        root_player,
                                        current_seq,
                                        best_seq,
                                        best_val,
                                        best_breakdown,
                                        total_count,
                                        eval_ctx,
                                    );
                                    current_seq.pop();
                                }
                            }
                        }
                    }
                }
            }

            let mut stop_state = state.clone();
            stop_state.ui.silent = true;
            let _ = stop_state.step(db, ACTION_BASE_PASS);
            let weights = Self::config_snapshot().weights;
            let (board_score, live_ev) =
                Self::evaluate_state_for_player_with_weights_ctx(&stop_state, db, root_player, &weights, eval_ctx);
            let current_val = board_score + live_ev;

            if current_val > *best_val || (!current_seq.is_empty() && current_val >= *best_val) {
                *best_val = current_val;
                *best_seq = current_seq.clone();
                *best_breakdown = (board_score, live_ev);
            }
        } else if state.phase == Phase::LiveSet {
            let weights = Self::config_snapshot().weights;
            let (ls_actions, _, _) = Self::find_best_liveset_selection_with_weights(state, db, &weights, eval_ctx);
            let mut final_state = state.clone();
            for &act in &ls_actions {
                let _ = final_state.step(db, act);
            }
            let (board_score, live_ev) =
                Self::evaluate_state_for_player_with_weights_ctx(&final_state, db, root_player, &weights, eval_ctx);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                let mut full_seq = current_seq.clone();
                full_seq.extend(ls_actions);
                *best_seq = full_seq;
            }
        } else {
            let weights = Self::config_snapshot().weights;
            let (board_score, live_ev) =
                Self::evaluate_state_for_player_with_weights(state, db, root_player, &weights);
            let current_val = board_score + live_ev;

            if current_val > *best_val {
                *best_val = current_val;
                *best_breakdown = (board_score, live_ev);
                *best_seq = current_seq.clone();
            }
        }
    }

    fn find_best_liveset_selection_internal(
        state: &GameState,
        db: &CardDatabase,
        weights: &WeightsConfig,
        eval_ctx: &EvaluationContext,
    ) -> (Vec<i32>, usize, u128) {
        let p_idx = state.current_player as usize;
        let hand_len = state.players[p_idx].hand.len();
        if hand_len == 0 {
            return (Vec::new(), 0, 0);
        }

        let empty_slots = state.players[p_idx].live_zone.iter().filter(|&&cid| cid == -1).count();
        if empty_slots == 0 {
            return (Vec::new(), 0, 0);
        }

        fn enumerate_subsets(
            start_idx: usize,
            hand_len: usize,
            remaining_slots: usize,
            current: &mut Vec<usize>,
            all: &mut Vec<Vec<usize>>,
        ) {
            all.push(current.clone());
            if remaining_slots == 0 {
                return;
            }
            for idx in start_idx..hand_len {
                current.push(idx);
                enumerate_subsets(idx + 1, hand_len, remaining_slots - 1, current, all);
                current.pop();
            }
        }

        let mut subsets = Vec::new();
        let mut current = Vec::new();
        enumerate_subsets(0, hand_len, empty_slots, &mut current, &mut subsets);
        let total_subsets = subsets.len();

        let mut best_actions = Vec::new();
        let mut best_total = f32::NEG_INFINITY;
        let mut best_live_pct = 0.0;
 
        for subset in &subsets {
            let mut sim_state = state.clone();
            let mut ordered = subset.clone();
            ordered.sort_unstable_by(|a, b| b.cmp(a));

            let mut actions = Vec::with_capacity(ordered.len());
            let mut valid = true;
            for hand_idx in &ordered {
                let action = ACTION_BASE_LIVESET + *hand_idx as i32;
                if sim_state.step(db, action).is_err() {
                    valid = false;
                    break;
                }
                actions.push(action);
            }
            if !valid {
                continue;
            }

            let _ = sim_state.step(db, ACTION_BASE_PASS);
            let breakdown = Self::evaluate_turn_goal_breakdown(&sim_state, db, p_idx, weights, &eval_ctx);
            if breakdown.total > best_total {
                best_total = breakdown.total;
                best_live_pct = breakdown.live_ev;
                best_actions = actions;
            }
        }

        (best_actions, total_subsets, (best_live_pct.max(0.0) * 1000.0) as u128)
    }

    #[allow(dead_code)]
    fn evaluate_state(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        Self::evaluate_state_internal(state, db)
    }

    /// Internal evaluation function (public for MCTS use)
    fn evaluate_state_internal(state: &GameState, db: &CardDatabase) -> (f32, f32) {
        Self::evaluate_state_for_player(state, db, state.current_player as usize)
    }

    fn evaluate_state_for_player(state: &GameState, db: &CardDatabase, p_idx: usize) -> (f32, f32) {
        let weights = Self::config_snapshot().weights;
        Self::evaluate_state_for_player_with_weights(state, db, p_idx, &weights)
    }

    #[allow(dead_code)]
    fn evaluate_live_zone_score(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
        let weights = Self::config_snapshot().weights;
        Self::evaluate_live_zone_score_with_weights(state, db, p_idx, &weights)
    }

    #[allow(dead_code)]
    fn predict_best_liveset_score(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
        let weights = Self::config_snapshot().weights;
        Self::predict_best_liveset_score_with_weights(state, db, p_idx, &weights)
    }

    fn build_live_eval_context_ctx(
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        eval_ctx: &EvaluationContext,
    ) -> Option<([u32; 7], Vec<f32>, [u8; 7])> {
        let expected_yell_count = state.get_total_blades(p_idx, db, 0) as usize;
        let board_hearts = state.get_total_hearts(p_idx, db, 0).to_array().map(|v| v as u32);
        
        let expected_yell_hearts = if expected_yell_count < 61 {
            eval_ctx.yell_bonus_table[p_idx][expected_yell_count].to_vec()
        } else {
            let stats = &eval_ctx.deck_stats[p_idx];
            stats.avg_hearts.iter().map(|&h| h * expected_yell_count as f32).collect()
        };
        
        let heart_reductions = state.players[p_idx].heart_req_reductions.to_array();
        Some((board_hearts, expected_yell_hearts, heart_reductions))
    }

    #[allow(dead_code)]
    fn live_card_expected_value(
        live: &crate::core::logic::card_db::LiveCard,
        db: &CardDatabase,
        board_hearts: &[u32; 7],
        expected_yell_hearts: &[f32],
        heart_reductions: [u8; 7],
    ) -> f32 {
        let weights = Self::config_snapshot().weights;
        Self::live_card_expected_value_with_weights(
            live,
            db,
            board_hearts,
            expected_yell_hearts,
            heart_reductions,
            &weights,
        )
    }

    /*
    fn estimate_live_ev(state: &GameState, db: &CardDatabase) -> f32 {
        let p_idx = state.current_player as usize;
        let mut total_ev = 0.0;

        // For each card in the live zone, estimate success
        for i in 0..3 {
            let cid = state.players[p_idx].live_zone[i];
            if cid < 0 { continue; }
            if let Some(live) = db.get_live(cid) {
                let success_prob = Self::monte_carlo_success_prob(state, db, i);
                let score = live.score as f32; // Simplified score
                total_ev += success_prob * score;
            }
        }

        total_ev
    }
    */

    /*
    fn monte_carlo_success_prob(state: &GameState, db: &CardDatabase, slot_idx: usize) -> f32 {
        let p_idx = state.current_player as usize;
        let cid = state.players[p_idx].live_zone[slot_idx];
        let live = db.get_live(cid).unwrap();

        let board_hearts = state.get_total_hearts(p_idx, db, 0);
        let yell_count = state.get_total_blades(p_idx, db, 0);

        if yell_count == 0 {
            return if board_hearts.satisfies(live.hearts_board) { 1.0 } else { 0.0 };
        }

        // --- OPTIMIZATION: Vanilla Mode Statistical Expectation ---
        if db.is_vanilla {
            use crate::core::heuristics::{calculate_deck_expectations, calculate_live_success_prob};
            let stats = calculate_deck_expectations(&state.players[p_idx].deck, db);
            let expected_yell_hearts: Vec<f32> = stats.avg_hearts.iter().map(|&h| h * yell_count as f32).collect();

            // Use the soft probability estimation from heuristics
            return calculate_live_success_prob(
                live,
                &board_hearts.to_array().map(|v| v as u32),
                &expected_yell_hearts,
                state.players[p_idx].heart_req_reductions.to_array(),
            ).min(1.0);
        }

        let mut successes = 0;
        let trials = 100;
        let deck_cards = state.players[p_idx].deck.to_vec();

        let mut rng = rand::rngs::SmallRng::from_os_rng();

        for _ in 0..trials {
            let mut trial_deck = deck_cards.clone();
            trial_deck.shuffle(&mut rng);
            let mut trial_hearts = board_hearts.clone();
            let to_draw = yell_count.min(trial_deck.len() as u32) as usize;

            for j in 0..to_draw {
                let yid = trial_deck[j];
                if let Some(ym) = db.get_member(yid) {
                    trial_hearts.add(ym.blade_hearts_board);
                }
            }

            if trial_hearts.satisfies(live.hearts_board) {
                successes += 1;
            }
        }

        successes as f32 / trials as f32
    }
    */
}
