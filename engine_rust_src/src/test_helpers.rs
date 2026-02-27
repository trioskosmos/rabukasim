use crate::core::logic::*;
use crate::core::logic::player::PlayerState;
use crate::core::logic::card_db::CardDatabase;

#[cfg(feature = "gpu")]
use crate::core::gpu_state::{GpuGameState, GpuCardStats, GpuTriggerRequest};
#[cfg(feature = "gpu")]
use crate::core::gpu_conversions::GpuConverter;

#[derive(Debug, Clone)]
pub struct ZoneSnapshot {
    pub hand_len: usize,
    pub deck_len: usize,
    pub discard_len: usize,
    pub energy_len: usize,
    pub tapped_energy_count: usize,
    pub active_energy: usize,
    pub stage: [i32; 3],
    pub live_zone: [i32; 3],
    pub looked_cards_len: usize,
    pub score: u32,
    pub active_members_count: usize,
    pub total_heart_buffs: u32,
    pub total_blade_buffs: i32,
    pub tapped_members: [bool; 3],
    pub prevent_activate: u8,
    pub prevent_baton_touch: u8,
    pub prevent_success_pile_set: u8,
    pub prevent_play_mask: u8,
    pub cost_reduction: i16,
    pub stage_energy_total: u32,
    pub live_score_bonus: i32,
    pub looked_cards: Vec<i32>,
    pub yell_count: usize,
    pub opponent_tapped_members: [bool; 3],
    pub opponent_tapped_count: usize,
}

impl ZoneSnapshot {
    pub fn capture(p: &PlayerState, state: &GameState) -> Self {
        let mut total_hearts = 0;
        let mut total_blades = 0;
        let mut active_members = 0;
        let mut stage_energy_total = 0;
        for i in 0..3 {
            total_hearts += p.heart_buffs[i].get_total_count();
            total_blades += p.blade_buffs[i] as i32;
            if p.stage[i] != -1 { 
                active_members += 1; 
                stage_energy_total += p.stage_energy[i].len() as u32;
            }
        }

        // Count actual cards (not -1 placeholders) for hand and deck
        let actual_hand_len = p.hand.iter().filter(|&&c| c >= 0).count();
        let actual_deck_len = p.deck.iter().filter(|&&c| c >= 0).count();

        Self {
            hand_len: actual_hand_len,
            deck_len: actual_deck_len,
            discard_len: p.discard.len(),
            energy_len: p.energy_zone.len(),
            tapped_energy_count: p.tapped_energy_mask.count_ones() as usize,
            active_energy: p.energy_zone.len().saturating_sub(p.tapped_energy_mask.count_ones() as usize),
            stage: p.stage,
            live_zone: p.live_zone,
            looked_cards_len: p.looked_cards.len(),
            score: p.score,
            active_members_count: active_members,
            total_heart_buffs: total_hearts,
            total_blade_buffs: total_blades,
            tapped_members: [p.is_tapped(0), p.is_tapped(1), p.is_tapped(2)],
            prevent_activate: p.prevent_activate,
            prevent_baton_touch: p.prevent_baton_touch,
            prevent_success_pile_set: p.prevent_success_pile_set,
            prevent_play_mask: p.prevent_play_to_slot_mask,
            cost_reduction: p.cost_reduction,
            stage_energy_total,
            live_score_bonus: p.live_score_bonus,
            looked_cards: p.looked_cards.iter().cloned().collect(),
            yell_count: p.yell_cards.len(),
            opponent_tapped_members: [
                state.core.players[1].is_tapped(0),
                state.core.players[1].is_tapped(1),
                state.core.players[1].is_tapped(2),
            ],
            opponent_tapped_count: [
                state.core.players[1].is_tapped(0),
                state.core.players[1].is_tapped(1),
                state.core.players[1].is_tapped(2),
            ].iter().filter(|&&t| t).count(),
        }
    }
}

pub enum Action {
    Pass,
    SelectMode { mode_idx: usize },
    LiveSet { live_idx: usize },
    Mulligan { hand_indices: Vec<usize> },
    ColorSelect { color_idx: usize },
    PlayMember { hand_idx: usize, slot_idx: usize },
    SelectHand { hand_idx: usize },
    SelectChoice { choice_idx: usize },
    ActivateAbility { slot_idx: usize, ab_idx: usize },
    Rps { player_idx: usize, choice: usize },
    ChooseTurnOrder { first: bool },
}

impl Action {
    pub fn id(&self) -> i32 {
        let res = match self {
            Action::Pass => ACTION_BASE_PASS as usize,
            Action::SelectMode { mode_idx } => (ACTION_BASE_MODE as usize) + mode_idx,
            Action::LiveSet { live_idx } => (ACTION_BASE_LIVESET as usize) + live_idx,
            Action::Mulligan { .. } => ACTION_BASE_MULLIGAN as usize,
            Action::ColorSelect { color_idx } => (ACTION_BASE_COLOR as usize) + color_idx,
            Action::PlayMember { hand_idx, slot_idx } => (ACTION_BASE_HAND as usize) + (hand_idx * 3) + slot_idx,
            Action::SelectHand { hand_idx } => (ACTION_BASE_HAND_SELECT as usize) + hand_idx,
            Action::SelectChoice { choice_idx } => (ACTION_BASE_CHOICE as usize) + choice_idx,
            Action::ActivateAbility { slot_idx, ab_idx } => (ACTION_BASE_STAGE as usize) + (slot_idx * 100) + ab_idx,
            Action::Rps { player_idx, choice } => 10000 + (player_idx * 1000) + choice,
            Action::ChooseTurnOrder { first } => if *first { 5000 } else { 5001 },
        };
        res as i32
    }
}

pub trait TestUtils {
    fn set_hand(&mut self, p_idx: usize, cards: &[i32]);
    fn set_deck(&mut self, p_idx: usize, cards: &[i32]);
    fn set_discard(&mut self, p_idx: usize, cards: &[i32]);
    fn set_energy(&mut self, p_idx: usize, cards: &[i32]);
    fn set_stage(&mut self, p_idx: usize, slot: usize, card_id: i32);
    fn set_live(&mut self, p_idx: usize, slot: usize, card_id: i32);
    fn dump(&self);
}

impl TestUtils for GameState {
    fn set_hand(&mut self, p_idx: usize, cards: &[i32]) {
        self.core.players[p_idx].hand = cards.iter().cloned().collect();
    }
    fn set_deck(&mut self, p_idx: usize, cards: &[i32]) {
        self.core.players[p_idx].deck = cards.iter().cloned().collect();
    }
    fn set_discard(&mut self, p_idx: usize, cards: &[i32]) {
        self.core.players[p_idx].discard = cards.iter().cloned().collect();
    }
    fn set_energy(&mut self, p_idx: usize, cards: &[i32]) {
        self.core.players[p_idx].energy_zone = cards.iter().cloned().collect();
        self.core.players[p_idx].tapped_energy_mask = 0;
    }
    fn set_stage(&mut self, p_idx: usize, slot: usize, card_id: i32) {
        if slot < 3 { self.core.players[p_idx].stage[slot] = card_id; }
    }
    fn set_live(&mut self, p_idx: usize, slot: usize, card_id: i32) {
        if slot < 3 { self.core.players[p_idx].live_zone[slot] = card_id; }
    }
    fn dump(&self) {
        if !self.ui.silent {
            println!("DEBUG STATE: Phase={:?}, InteractionStack={:?}", self.phase, self.interaction_stack.last().map(|i| i.choice_type.as_str()).unwrap_or("EMPTY"));
            for (idx, p) in self.core.players.iter().enumerate() {
                println!("P{}: Score={}, HandLen={}, DeckLen={}, DiscardLen={}, EnergyLen={}, Stage={:?}", idx, p.score, p.hand.len(), p.deck.len(), p.discard.len(), p.energy_zone.len(), p.stage);
            }
        }
    }
}

pub fn p_state(state: &GameState, p_idx: usize) -> &PlayerState {
    &state.core.players[p_idx]
}

#[cfg(not(target_arch = "wasm32"))]
pub fn load_real_db() -> CardDatabase {
    let manifest_dir = env!("CARGO_MANIFEST_DIR");
    let path = std::path::Path::new(manifest_dir).join("../data/cards_compiled.json");
    let json_content = std::fs::read_to_string(path).expect("Failed to read cards_compiled.json");
    CardDatabase::from_json(&json_content).expect("Failed to load production CardDatabase in test_helpers")
}

#[cfg(target_arch = "wasm32")]
pub fn load_real_db() -> CardDatabase {
    panic!("load_real_db not supported on WASM targets as it requires file I/O");
}

pub fn create_test_db() -> CardDatabase {
    let mut db = CardDatabase::default();
    
    // Generic cards
    for i in 3000..3501 {
        let mut hearts = [0u8; 7]; hearts[0] = 1;
        let m = MemberCard {
            card_id: i, card_no: format!("GEN-M-{}", i), name: format!("Mem {}", i),
            cost: 1, hearts, groups: vec![1], ..Default::default()
        };
        db.members.insert(i, m.clone());
        let lid = (i & LOGIC_ID_MASK) as usize;
        if lid < db.members_vec.len() { db.members_vec[lid] = Some(m); }
    }

    // Energy Card
    let mut energy = MemberCard::default();
    energy.card_id = 2000;
    energy.name = "Test Energy".to_string();
    energy.hearts[0] = 1; // 1 Pink heart
    db.members.insert(2000, energy.clone());
    let eid = (2000 & LOGIC_ID_MASK) as usize;
    if eid < db.members_vec.len() { db.members_vec[eid] = Some(energy); }

    // Generic Live
    let l55001 = LiveCard {
        card_id: 55001, card_no: "GEN-L-55001".to_string(), name: "Live 55001".to_string(),
        score: 1, required_hearts: [1, 0, 0, 0, 0, 0, 0], ..Default::default()
    };
    db.lives.insert(55001, l55001.clone());
    let llid = (55001 & LOGIC_ID_MASK) as usize;
    if llid < db.lives_vec.len() { db.lives_vec[llid] = Some(l55001); }

    // Archetype Cards
    add_card(&mut db, 3121, "ARCH-02", vec![1], vec![(TriggerType::Activated, vec![58, 1, 0, 0, 4, 17, 1, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);
    add_card(&mut db, 3124, "ARCH-01", vec![1], vec![(TriggerType::Activated, vec![58, 1, 0, 0, 4, 15, 1, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);
    // CID 130: PL!-sd1-011-SD (OnPlay: MoveToDiscard(1) -> LookAndChoose(3,1))
    // Bytecode: [58, 1, 2, 6, 41, 3, 1, 6, 1, 0, 0, 0]
    add_card(&mut db, 130, "PL!-sd1-011", vec![1], vec![(TriggerType::OnPlay, vec![58, 1, 2, 0, 6, 41, 3, 1, 0, 6, 1, 0, 0, 0, 0], vec![])]);
    // Old incorrect mock
    add_card(&mut db, 3130, "ARCH-03", vec![1], vec![(TriggerType::OnPlay, vec![64, 0, 130, 0, 0, 41, 1, 24577, 0, 0, 14, 3, 0, 0, 0, 41, 1, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);
    add_card(&mut db, 3159, "ARCH-04", vec![1], vec![(TriggerType::OnLiveStart, vec![64, 0, 130, 0, 0, 58, 1, 24576, 0, 0, 64, 1, 0, 0, 0, 16, 5, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);
    add_card(&mut db, 304347, "ARCH-06", vec![1], vec![(TriggerType::OnPlay, vec![10, 1, 0, 0, 0, 58, 1, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);
    add_card(&mut db, 300223, "ARCH-09", vec![1], vec![(TriggerType::OnPlay, vec![10, 2, 0, 0, 0, 58, 2, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);
    // CID 3001: Test card for O_OPPONENT_CHOOSE -> O_DRAW
    // O_OPPONENT_CHOOSE(75) v=1 -> O_DRAW(10) v=1 -> O_RETURN(1)
    add_card(&mut db, 3001, "OPP_CHOOSE_TEST", vec![1], vec![(TriggerType::OnPlay, vec![75, 1, 0, 0, 0, 10, 1, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);

    // CID 4332: RANK-13 (OnLiveStart: PayEnergy(1) -> ColorSelect -> AddHearts(1))
    // Real Bytecode: [64, 1, 2, 0, 45, 1, 0, 1, 12, 1, 0, 1, 1, 0, 0, 0]
    add_card(&mut db, 4332, "RANK-13", vec![2], vec![(TriggerType::OnLiveStart, vec![64, 1, 2, 0, 0, 45, 1, 0, 0, 1, 12, 1, 0, 0, 1, 1, 0, 0, 0, 0], vec![])]);
    add_card(&mut db, 4335, "RANK-14", vec![2], vec![(TriggerType::Activated, vec![58, 1, 1, 0, 6, 3, 2, 0, 0, 0, 81, 2, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]); // Archetype 13: OnPlay -> Select Mode (2 options) -> [Op 8] or [Op 16] (Dummy) -> Tap Opponent / Draw
    add_card(&mut db, 3017, "ARCH-13", vec![1], vec![(TriggerType::OnPlay, vec![30, 2, 8, 0, 16, 1, 0, 0, 0, 0, 32, 1, 0, 0, 0, 1, 0, 0, 0, 0, 10, 1, 0, 0, 0, 1, 0, 0, 0, 0], vec![])]);

    db
}

pub fn create_test_state() -> GameState {
    let mut state = GameState::default();
    state.core.players[0].player_id = 0; state.core.players[1].player_id = 1;
    state.phase = Phase::Main;
    for i in 0..2 {
        state.core.players[i].deck = vec![51001, 51002, 51003, 51004, 51005].into();
        state.core.players[i].energy_zone = vec![3101, 3102, 3103].into();
    }
    state
}

pub fn add_card(db: &mut CardDatabase, cid: i32, no: &str, groups: Vec<u8>, abilities: Vec<(TriggerType, Vec<i32>, Vec<Condition>)>) {
    let mut abs = Vec::new();
    for (t, b, c) in abilities {
        abs.push(Ability { trigger: t, bytecode: b, conditions: c, ..Default::default() });
    }
    let m = MemberCard {
        card_id: cid, card_no: no.to_string(), name: no.to_string(),
        groups, abilities: abs, ..Default::default()
    };
    db.members.insert(cid, m.clone());
    let lid = (cid & LOGIC_ID_MASK) as usize;
    if lid < db.members_vec.len() { db.members_vec[lid] = Some(m); }
}

// --- GPU PARITY HARNESS ---
#[cfg(feature = "gpu")]
pub struct GpuParityHarness {
    pub manager: crate::core::gpu_manager::GpuManager,
}

#[cfg(feature = "gpu")]
impl GpuParityHarness {
    pub fn new(db: &CardDatabase) -> Self {
        let (stats, bytecode) = db.convert_to_gpu();
        let manager = crate::core::gpu_manager::GpuManager::new(&stats, &bytecode, wgpu::Backends::all())
            .expect("Failed to initialize GPU manager for harness");
        Self { manager }
    }

    pub fn assert_bytecode_parity(
        &self,
        db: &CardDatabase,
        state: &GameState,
        bytecode: &[i32],
        ctx: &AbilityContext,
        name: &str,
    ) {
        // 1. Run CPU
        let mut cpu_final = state.clone();
        crate::core::logic::interpreter::resolve_bytecode(&mut cpu_final, db, bytecode, &mut ctx.clone());

        // 2. Run GPU
        let mut gpu_input = state.to_gpu(db);
        // We use a special forced_action or manual trigger push?
        // For bytecode parity, we can't use forced_action (which is for Main phase actions).
        // Instead, we manually push a trigger to the queue and run one step.
        gpu_input.trigger_queue[0] = GpuTriggerRequest {
            card_id: ctx.source_card_id as u32,
            slot_idx: ctx.area_idx as u32,
            trigger_filter: ctx.trigger_type as i32,
            ab_filter: -1, // Use provided bytecode directly
            choice: ctx.choice_index as i32,
            _pad: [0; 3],
        };
        gpu_input.queue_tail = 1;
        gpu_input.phase = 6; // PHASE_MAIN (to allow process_trigger_queue)
        gpu_input.forced_action = -1;
        gpu_input.is_debug = 1;

        let mut results = vec![crate::core::gpu_state::GpuGameState::default(); 1];
        self.manager.run_single_step(&[gpu_input], &mut results);
        let gpu_final = &results[0];

        // 3. Compare
        self.compare_and_panic(&cpu_final, gpu_final, name);
    }

    pub fn assert_step_parity(&self, db: &CardDatabase, state: &GameState, action_id: i32, name: &str) {
        // 1. Run CPU
        let mut cpu_final = state.clone();
        cpu_final.step(db, action_id).expect("CPU step failed in harness");
        
        // Match GPU's eager resumption for interactions
        let mut loop_limit = 0;
        while !cpu_final.interaction_stack.is_empty() && loop_limit < 10 {
            cpu_final.step(db, (ACTION_BASE_CHOICE + 0) as i32).expect("CPU auto-choice failed");
            loop_limit += 1;
        }

        // 2. Run GPU
        let mut gpu_input = state.to_gpu(db);
        gpu_input.forced_action = action_id;
        gpu_input.is_debug = 1;

        let mut results = vec![crate::core::gpu_state::GpuGameState::default(); 1];
        self.manager.run_single_step(&[gpu_input], &mut results);
        let gpu_final = &results[0];

        // 3. Compare
        self.compare_and_panic(&cpu_final, gpu_final, name);
    }

    fn compare_and_panic(&self, cpu: &GameState, gpu: &crate::core::gpu_state::GpuGameState, name: &str) {
        let mut errors = Vec::new();
        let p0 = &cpu.core.players[0];
        let gp0 = &gpu.player0;

        if p0.hand.len() as u32 != gp0.hand_len {
            errors.push(format!("Hand len: CPU {}, GPU {}", p0.hand.len(), gp0.hand_len));
        }
        if p0.deck.len() as u32 != gp0.deck_len {
            errors.push(format!("Deck len: CPU {}, GPU {}", p0.deck.len(), gp0.deck_len));
        }
        if p0.score != gp0.score {
            errors.push(format!("Score: CPU {}, GPU {}", p0.score, gp0.score));
        }
        if p0.live_score_bonus != gp0.live_score_bonus {
            errors.push(format!("Live Score Bonus: CPU {}, GPU {}", p0.live_score_bonus, gp0.live_score_bonus));
        }
        if p0.tapped_energy_mask.count_ones() as u32 != gp0.tapped_energy_count {
            errors.push(format!("Tapped Energy: CPU {}, GPU {}", p0.tapped_energy_mask.count_ones(), gp0.tapped_energy_count));
        }
        for i in 0..3 {
            if p0.blade_buffs[i] as i32 != gp0.blade_buffs[i] as i32 {
                errors.push(format!("Blade Buff [{}]: CPU {}, GPU {}", i, p0.blade_buffs[i], gp0.blade_buffs[i]));
            }
        }
        if p0.flags != gp0.flags {
            errors.push(format!("Flags: CPU {:08x}, GPU {:08x}", p0.flags, gp0.flags));
        }

        if !errors.is_empty() {
            panic!("\n--- GPU PARITY FAILURE: {} ---\n{}\n", name, errors.join("\n"));
        }
    }
}

#[derive(Default)]
pub struct TestActionReceiver {
    pub actions: Vec<i32>,
}

impl ActionReceiver for TestActionReceiver {
    fn add_action(&mut self, action_id: usize) {
        self.actions.push(action_id as i32);
    }
    fn reset(&mut self) {
        self.actions.clear();
    }
    fn is_empty(&self) -> bool {
        self.actions.is_empty()
    }
}
