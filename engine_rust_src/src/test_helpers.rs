use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::player::PlayerState;
use crate::core::logic::*;
use crate::core::enums::Zone;
use crate::core::generated_layout::*;
use crate::core::logic::constants::FILTER_IS_OPTIONAL;

#[derive(Debug, Clone, Default)]
pub struct AbilityBuilder {
    pub bytecode: Vec<i32>,
}

impl AbilityBuilder {
    pub fn new() -> Self {
        Self { bytecode: Vec::new() }
    }

    pub fn push(mut self, op: i32, arg1: i32, arg2: i32, arg3: i32) -> Self {
        self.bytecode.extend_from_slice(&[op, arg1, arg2, arg3]);
        self
    }

    pub fn recover_live(self, amount: i32) -> Self {
        self.push(crate::core::logic::O_RECOVER_LIVE, amount, 0, 0)
    }

    pub fn pay_energy(self, amount: i32) -> Self {
        self.push(crate::core::logic::O_PAY_ENERGY, amount, 0, 0)
    }

    pub fn return_op(self) -> Self {
        self.push(crate::core::logic::O_RETURN, 0, 0, 0)
    }

    pub fn build(self) -> Vec<i32> {
        self.bytecode
    }
}

pub struct BytecodeBuilder {
    pub bytecode: Vec<i32>,
}

impl BytecodeBuilder {
    pub fn new(op: i32) -> Self {
        let mut bc = Vec::with_capacity(5);
        bc.extend_from_slice(&[op, 0, 0, 0, 0]);
        Self { bytecode: bc }
    }

    pub fn op(mut self, op: i32) -> Self {
        self.bytecode.extend_from_slice(&[op, 0, 0, 0, 0]);
        self
    }

    fn last_idx(&self) -> usize {
        self.bytecode.len() - 5
    }

    pub fn v(mut self, v: i32) -> Self {
        let idx = self.last_idx();
        self.bytecode[idx + 1] = v;
        self
    }

    pub fn attr(mut self, a: i64) -> Self {
        let idx = self.last_idx();
        self.bytecode[idx + 2] = a as i32;
        self.bytecode[idx + 3] = (a >> 32) as i32;
        self
    }

    pub fn a(self, a: i64) -> Self {
        self.attr(a)
    }

    pub fn optional(mut self, val: bool) -> Self {
        let idx = self.last_idx();
        let mut a = ((self.bytecode[idx+3] as i64) << 32) | (self.bytecode[idx+2] as u32 as i64);
        if val {
            a |= FILTER_IS_OPTIONAL as i64;
        } else {
            a &= !(FILTER_IS_OPTIONAL as i64);
        }
        self.bytecode[idx+2] = a as i32;
        self.bytecode[idx+3] = (a >> 32) as i32;
        self
    }

    pub fn slot(mut self, s: i32) -> Self {
        let idx = self.last_idx();
        self.bytecode[idx + 4] = s;
        self
    }

    pub fn source(mut self, zone: Zone) -> Self {
        let zone_val = self.encode_zone(zone);
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        s &= !((S_STANDARD_SOURCE_ZONE_MASK as u32) << S_STANDARD_SOURCE_ZONE_SHIFT);
        s |= (zone_val as u32 & S_STANDARD_SOURCE_ZONE_MASK as u32) << S_STANDARD_SOURCE_ZONE_SHIFT;
        self.bytecode[idx + 4] = s as i32;
        self
    }

    pub fn dest(mut self, zone: Zone) -> Self {
        let zone_val = self.encode_zone(zone);
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        s &= !((S_STANDARD_DEST_ZONE_MASK as u32) << S_STANDARD_DEST_ZONE_SHIFT);
        s |= (zone_val as u32 & S_STANDARD_DEST_ZONE_MASK as u32) << S_STANDARD_DEST_ZONE_SHIFT;
        self.bytecode[idx + 4] = s as i32;
        self
    }

    pub fn target(mut self, slot: u8) -> Self {
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        // Optimization: Use 0x0F mask to avoid overlapping with legacy comparison_mode (bits 4-7)
        s &= !0x0F;
        s |= slot as u32 & 0x0F;
        self.bytecode[idx + 4] = s as i32;
        self
    }

    pub fn reveal_until_live(mut self, is_live: bool) -> Self {
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        if is_live {
            s |= 1u32 << S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT;
        } else {
            s &= !(1u32 << S_STANDARD_IS_REVEAL_UNTIL_LIVE_SHIFT);
        }
        self.bytecode[idx + 4] = s as i32;
        self
    }

    pub fn comparison_mode(mut self, mode: u8) -> Self {
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        // Legacy/Condition mode: bits 4-7
        s &= !(0x0F << 4);
        s |= (mode as u32 & 0x0F) << 4;
        self.bytecode[idx + 4] = s as i32;
        self
    }

    pub fn is_opponent(mut self, val: bool) -> Self {
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        if val {
            s |= 1u32 << S_STANDARD_IS_OPPONENT_SHIFT;
        } else {
            s &= !(1u32 << S_STANDARD_IS_OPPONENT_SHIFT);
        }
        self.bytecode[idx + 4] = s as i32;
        self
    }

    pub fn area_idx(mut self, idx_val: u8) -> Self {
        let idx = self.last_idx();
        let mut s = self.bytecode[idx + 4] as u32;
        s &= !((S_STANDARD_AREA_IDX_MASK as u32) << S_STANDARD_AREA_IDX_SHIFT);
        s |= (idx_val as u32 & S_STANDARD_AREA_IDX_MASK as u32) << S_STANDARD_AREA_IDX_SHIFT;
        self.bytecode[idx + 4] = s as i32;
        self
    }

    fn encode_zone(&self, zone: Zone) -> u8 {
        match zone {
            Zone::DeckTop => 1,
            Zone::DeckBottom => 2,
            Zone::Energy => 3,
            Zone::Stage => 4,
            Zone::Hand => 6,
            Zone::Discard => 7,
            Zone::Deck => 8,
            Zone::LiveSet => 13,
            Zone::SuccessPile => 14,
            Zone::Yell => 15,
            _ => 0,
        }
    }

    pub fn build(self) -> Vec<i32> {
        self.bytecode
    }
}

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
            active_energy: p
                .energy_zone
                .len()
                .saturating_sub(p.tapped_energy_mask.count_ones() as usize),
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
                state.players[1].is_tapped(0),
                state.players[1].is_tapped(1),
                state.players[1].is_tapped(2),
            ],
            opponent_tapped_count: [
                state.players[1].is_tapped(0),
                state.players[1].is_tapped(1),
                state.players[1].is_tapped(2),
            ]
            .iter()
            .filter(|&&t| t)
            .count(),
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
            Action::PlayMember { hand_idx, slot_idx } => {
                (ACTION_BASE_HAND as usize) + (hand_idx * 10) + slot_idx
            }
            Action::SelectHand { hand_idx } => (ACTION_BASE_HAND_SELECT as usize) + hand_idx,
            Action::SelectChoice { choice_idx } => (ACTION_BASE_CHOICE as usize) + choice_idx,
            Action::ActivateAbility { slot_idx, ab_idx } => {
                (ACTION_BASE_STAGE as usize) + (slot_idx * 100) + (ab_idx * 10)
            }
            Action::Rps { player_idx, choice } => {
                if *player_idx == 0 {
                    (ACTION_BASE_RPS as usize) + choice
                } else {
                    (ACTION_BASE_RPS_P2 as usize) + choice
                }
            }
            Action::ChooseTurnOrder { first } => {
                if *first {
                    5000
                } else {
                    5001
                }
            }
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
    fn dump_verbose(&self);
    fn dump_trace(&self);
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
        if slot < 3 {
            self.core.players[p_idx].stage[slot] = card_id;
        }
    }
    fn set_live(&mut self, p_idx: usize, slot: usize, card_id: i32) {
        if slot < 3 {
            self.core.players[p_idx].live_zone[slot] = card_id;
        }
    }
    fn dump(&self) {
        if !self.ui.silent {
            println!(
                "DEBUG STATE: Phase={:?}, InteractionStack={:?}",
                self.phase,
                self.interaction_stack
                    .last()
                    .map(|i| i.choice_type.as_str())
                    .unwrap_or("EMPTY")
            );
            for (idx, p) in self.core.players.iter().enumerate() {
                println!("P{}: Score={}, HandLen={}, DeckLen={}, DiscardLen={}, EnergyLen={}, Stage={:?}", idx, p.score, p.hand.len(), p.deck.len(), p.discard.len(), p.energy_zone.len(), p.stage);
            }
        }
    }
    fn dump_verbose(&self) {
        println!("=== VERBOSE STATE DUMP ===");
        println!("Phase: {:?}", self.phase);
        println!("Current Player: {}", self.current_player);
        println!("Interaction Stack: {:?}", self.interaction_stack);
        for (i, p) in self.core.players.iter().enumerate() {
            println!("Player {}:", i);
            println!("  Score: {}", p.score);
            println!("  Hand: {:?}", p.hand);
            println!("  Deck: (len={})", p.deck.len());
            println!("  Discard: {:?}", p.discard);
            println!(
                "  Energy: {:?} (Tapped Mask: {:b})",
                p.energy_zone, p.tapped_energy_mask
            );
            println!("  Stage: {:?}", p.stage);
            println!("  Hearts: {:?}", p.heart_buffs);
            println!("  Blades: {:?}", p.blade_buffs);
        }
        println!("===========================");
    }

    fn dump_trace(&self) {
        println!("=== TRACE LOG ===");
        if self.debug.trace_log.is_empty() {
            println!("(Trace log is empty)");
        } else {
            for t in &self.debug.trace_log {
                println!("{}", t);
            }
        }
        println!("=================");
    }
}

pub fn generate_card_report(card_id: i32) {
    println!("[TEST_DEBUG] Requesting report for Card ID: {}", card_id);
    let output = std::process::Command::new("uv")
        .args(&[
            "run",
            "python",
            "tools/card_finder.py",
            &card_id.to_string(),
            "--output",
            &format!("reports/card_{}.md", card_id),
        ])
        .current_dir("..")
        .output();

    match output {
        Ok(out) => {
            if !out.status.success() {
                println!(
                    "[TEST_DEBUG] Report generation failed for Card {}: {}",
                    card_id,
                    String::from_utf8_lossy(&out.stderr)
                );
            } else {
                println!("[TEST_DEBUG] Report generated: reports/card_{}.md", card_id);
            }
        }
        Err(e) => println!(
            "[TEST_DEBUG] Failed to execute card_finder for Card {}: {}",
            card_id, e
        ),
    }
}

pub fn p_state(state: &GameState, p_idx: usize) -> &PlayerState {
    &state.players[p_idx]
}

// const DB_JSON: &str = include_str!("../../data/cards_compiled.json");

pub fn load_real_db() -> CardDatabase {
    let mut path = std::env::var("CARDS_JSON_PATH")
        .unwrap_or_else(|_| "../../data/cards_compiled.json".to_string());
    if !std::path::Path::new(&path).exists() {
        path = "../data/cards_compiled.json".to_string();
    }
    if !std::path::Path::new(&path).exists() {
        path = "data/cards_compiled.json".to_string();
    }
    let abs_path = std::fs::canonicalize(&path).unwrap_or_else(|_| std::path::PathBuf::from(&path));
    println!("[DB_LOAD] Loading CardDatabase from: {:?}", abs_path);
    let json = std::fs::read_to_string(&path)
        .expect(&format!("Failed to read CardDatabase from {}", path));
    CardDatabase::from_json(&json).expect("Failed to parse production CardDatabase in test_helpers")
}

pub fn create_test_db() -> CardDatabase {
    let mut db = CardDatabase::default();

    // Generic cards
    for i in 3000..3501 {
        let mut hearts = [0u8; 7];
        hearts[0] = 1;
        let m = MemberCard {
            card_id: i,
            card_no: format!("GEN-M-{}", i),
            name: format!("Mem {}", i),
            cost: 1,
            hearts,
            groups: vec![1],
            ..Default::default()
        };
        db.members.insert(i, m.clone());
        let lid = (i & LOGIC_ID_MASK) as usize;
        if lid < db.members_vec.len() {
            db.members_vec[lid] = Some(m);
        }
    }

    // Energy Card
    let mut energy = MemberCard::default();
    energy.card_id = 2000;
    energy.name = "Test Energy".to_string();
    energy.hearts[0] = 1; // 1 Pink heart
    db.members.insert(2000, energy.clone());
    let eid = (2000 & LOGIC_ID_MASK) as usize;
    if eid < db.members_vec.len() {
        db.members_vec[eid] = Some(energy);
    }

    // Generic Live
    let l55001 = LiveCard {
        card_id: 55001,
        card_no: "GEN-L-55001".to_string(),
        name: "Live 55001".to_string(),
        score: 1,
        required_hearts: [1, 0, 0, 0, 0, 0, 0],
        ..Default::default()
    };
    db.lives.insert(55001, l55001.clone());
    let llid = (55001 & LOGIC_ID_MASK) as usize;
    if llid < db.lives_vec.len() {
        db.lives_vec[llid] = Some(l55001);
    }

    // Archetype Cards
    add_card(
        &mut db,
        3121,
        "ARCH-02",
        vec![1],
        vec![(
            TriggerType::Activated,
            vec![58, 1, 0, 0, 4, 17, 1, 0, 0, 0, 1, 0, 0, 0, 0],
            vec![],
        )],
    );
    add_card(
        &mut db,
        3124,
        "ARCH-01",
        vec![1],
        vec![(
            TriggerType::Activated,
            vec![58, 1, 0, 0, 4, 15, 1, 0, 0, 0, 1, 0, 0, 0, 0],
            vec![],
        )],
    );
    // CID 130: PL!-sd1-011-SD (OnPlay: MoveToDiscard(1) -> LookAndChoose(3,1))
    // Bytecode: [58, 1, 2, 6, 41, 3, 1, 6, 1, 0, 0, 0]
    add_card(
        &mut db,
        130,
        "PL!-sd1-011",
        vec![1],
        vec![(
            TriggerType::OnPlay,
            vec![58, 1, 2, 0, 6, 41, 3, 1, 0, 6, 1, 0, 0, 0, 0],
            vec![],
        )],
    );
    // Old incorrect mock
    add_card(
        &mut db,
        3130,
        "ARCH-03",
        vec![1],
        vec![(
            TriggerType::OnPlay,
            vec![
                64, 0, 130, 0, 0, 41, 1, 24577, 0, 0, 14, 3, 0, 0, 0, 41, 1, 0, 0, 0, 1, 0, 0, 0, 0,
            ],
            vec![],
        )],
    );
    add_card(
        &mut db,
        3159,
        "ARCH-04",
        vec![1],
        vec![(
            TriggerType::OnLiveStart,
            vec![
                64, 0, 130, 0, 0, 58, 1, 24576, 0, 0, 64, 1, 0, 0, 0, 16, 5, 0, 0, 0, 1, 0, 0, 0, 0,
            ],
            vec![],
        )],
    );
    add_card(
        &mut db,
        304347,
        "ARCH-06",
        vec![1],
        vec![(
            TriggerType::OnPlay,
            vec![10, 1, 0, 0, 0, 58, 1, 0, 0, 0, 1, 0, 0, 0, 0],
            vec![],
        )],
    );
    add_card(
        &mut db,
        300223,
        "ARCH-09",
        vec![1],
        vec![(
            TriggerType::OnPlay,
            vec![10, 2, 0, 0, 0, 58, 2, 0, 0, 0, 1, 0, 0, 0, 0],
            vec![],
        )],
    );
    // CID 3001: Test card for O_OPPONENT_CHOOSE -> O_DRAW
    // O_OPPONENT_CHOOSE(75) v=1 -> O_DRAW(10) v=1 -> O_RETURN(1)
    add_card(
        &mut db,
        3001,
        "OPP_CHOOSE_TEST",
        vec![1],
        vec![(
            TriggerType::OnPlay,
            vec![75, 1, 0, 0, 0, 10, 1, 0, 0, 0, 1, 0, 0, 0, 0],
            vec![],
        )],
    );

    // CID 4332: RANK-13 (OnLiveStart: PayEnergy(1) -> ColorSelect -> AddHearts(1))
    // Real Bytecode: [64, 1, 2, 0, 45, 1, 0, 1, 12, 1, 0, 1, 1, 0, 0, 0]
    add_card(
        &mut db,
        4332,
        "RANK-13",
        vec![2],
        vec![(
            TriggerType::OnLiveStart,
            vec![
                64, 1, 2, 0, 0, 45, 1, 0, 0, 1, 12, 1, 0, 0, 1, 1, 0, 0, 0, 0,
            ],
            vec![],
        )],
    );
    add_card(
        &mut db,
        4335,
        "RANK-14",
        vec![2],
        vec![(
            TriggerType::Activated,
            vec![58, 1, 1, 0, 6, 3, 2, 0, 0, 0, 81, 2, 0, 0, 0, 1, 0, 0, 0, 0],
            vec![],
        )],
    ); // Archetype 13: OnPlay -> Select Mode (2 options) -> [Op 8] or [Op 16] (Dummy) -> Tap Opponent / Draw
    add_card(
        &mut db,
        3017,
        "ARCH-13",
        vec![1],
        vec![(
            TriggerType::OnPlay,
            vec![
                30, 2, 8, 0, 16, 1, 0, 0, 0, 0, 32, 1, 0, 0, 0, 1, 0, 0, 0, 0, 10, 1, 0, 0, 0, 1,
                0, 0, 0, 0,
            ],
            vec![],
        )],
    );

    db
}

pub fn create_test_state() -> GameState {
    let mut state = GameState::default();
    state.players[0].player_id = 0;
    state.players[1].player_id = 1;
    state.phase = Phase::Main;
    state.debug.debug_mode = true; // NEW: Enable debug mode for tests
    state.ui.silent = false; // NEW: Disable silent mode for tests
    for i in 0..2 {
        state.players[i].deck = vec![51001, 51002, 51003, 51004, 51005].into();
        state.players[i].energy_zone = vec![3101, 3102, 3103].into();
    }
    state
}

pub fn add_card(
    db: &mut CardDatabase,
    cid: i32,
    no: &str,
    groups: Vec<u8>,
    abilities: Vec<(TriggerType, Vec<i32>, Vec<Condition>)>,
) {
    let mut abs = Vec::new();
    for (t, b, c) in abilities {
        abs.push(Ability {
            trigger: t,
            bytecode: b,
            conditions: c,
            ..Default::default()
        });
    }
    let m = MemberCard {
        card_id: cid,
        card_no: no.to_string(),
        name: no.to_string(),
        groups,
        abilities: abs,
        ..Default::default()
    };
    db.members.insert(cid, m.clone());
    let lid = (cid & LOGIC_ID_MASK) as usize;
    if lid < db.members_vec.len() {
        db.members_vec[lid] = Some(m);
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
