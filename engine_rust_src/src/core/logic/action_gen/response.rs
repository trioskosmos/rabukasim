use crate::core::logic::{ActionReceiver, CardDatabase, GameState, Ability, PendingInteraction};
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::enums::*;

pub struct ResponseGenerator;

impl ActionGenerator for ResponseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R) {
        let pi = if let Some(p) = state.core.interaction_stack.last() { p } else { return; };
        let ctx = &pi.ctx;
        let opcode = pi.effect_opcode;
        let choice_type = &pi.choice_type;
        let source_card_id = pi.ctx.source_card_id;

        if ctx.player_id as usize != p_idx {
            return;
        }

        let player = &state.core.players[p_idx];
        
        // 1. Determine action 0 (fallback)
        let mut allow_action_0 = true;
        if choice_type == "REVEAL_HAND" || choice_type == "SELECT_SWAP_SOURCE" || choice_type == "SELECT_SWAP_TARGET" || choice_type == "PAY_ENERGY" {
            allow_action_0 = false;
        }
        if allow_action_0 {
            receiver.add_action(0);
        }
        
        let member = db.get_member(source_card_id as i32);
        let live = db.get_live(source_card_id as i32);
        let abilities = if let Some(m) = member { Some(&m.abilities) } else { live.map(|l| &l.abilities) };

        match choice_type.as_str() {
            "OPTIONAL" => {
                receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + 0) as usize);
                return;
            }
            "PAY_ENERGY" => {
                for i in 0..player.energy_zone.len().min(16) {
                    if !player.is_energy_tapped(i) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_ENERGY + i as i32) as usize);
                    }
                }
                return;
            }
            "REVEAL_HAND" => {
                for i in 0..player.hand.len() {
                    receiver.add_action((crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                return;
            }
            "SELECT_DISCARD" => {
                for i in 0..player.discard.len() {
                    receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                }
                return;
            }
            "SELECT_SWAP_SOURCE" => {
                for i in 0..player.success_lives.len() {
                    receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
                return;
            }
            "SELECT_SWAP_TARGET" => {
                for i in 0..player.hand.len() {
                    receiver.add_action((crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                return;
            }
            _ => {}
        }

        match opcode {
            O_TAP_MEMBER | O_TAP_OPPONENT => {
                for c in 0..3 {
                    receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + c as i32) as usize);
                }
                return;
            }
            O_ORDER_DECK => {
                let count = player.looked_cards.len();
                for c in 0..count {
                    if player.looked_cards[c] != -1 {
                        receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + c as i32) as usize);
                    }
                }
                return;
            }
            O_COLOR_SELECT => {
                for c in 0..6 {
                    receiver.add_action((crate::core::logic::ACTION_BASE_COLOR + c as i32) as usize);
                }
                return;
            }
            O_LOOK_AND_CHOOSE => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                return;
            }
            O_MOVE_TO_DISCARD => {
                let masked_filter = (pi.filter_attr as u32 as u64) & 0xFFFFFFFFFFFF0FFF;
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, masked_filter) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & 0x02) != 0 || receiver.is_empty() {
                    receiver.add_action(0);
                }
                return;
            }
            O_RECOVER_MEMBER | O_RECOVER_LIVE => {
                let count = player.looked_cards.len();
                for i in 0..count {
                    let cid = player.looked_cards[i];
                    if cid != -1 && state.card_matches_filter(db, cid, (pi.filter_attr as u32) as u64) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                receiver.add_action(0);
                return;
            }
            O_PLAY_MEMBER_FROM_HAND => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, pi.filter_attr) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_HAND + i as i32) as usize);
                    }
                }
                receiver.add_action(0);
                return;
            }
            O_SELECT_MEMBER => {
                self.generate_select_member_actions(db, p_idx, state, receiver, pi, pi.filter_attr);
                return;
            }
            O_SELECT_LIVE => {
                for i in 0..player.live_zone.len().min(10) {
                    if player.live_zone[i] >= 0 {
                        receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
                receiver.add_action(0);
                return;
            }
            O_SELECT_PLAYER => {
                receiver.add_action(0);
                receiver.add_action(1);
                return;
            }
            O_SELECT_MODE => {
                self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
                return;
            }
            O_SELECT_CARDS => {
                for i in 0..player.hand.len() {
                    receiver.add_action((crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                if (pi.filter_attr & 0x02) != 0 || receiver.is_empty() {
                    receiver.add_action(0);
                }
                return;
            }
            _ => {
                if choice_type == "SELECT_MEMBER" {
                    self.generate_select_member_actions(db, p_idx, state, receiver, pi, pi.filter_attr);
                    return;
                }
                if choice_type == "SELECT_STAGE" {
                    for i in 0..3 { receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize); }
                    return;
                }
                if choice_type == "SELECT_LIVE_SLOT" {
                    for i in 0..player.live_zone.len().min(10) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                    return;
                }
            }
        }

        if receiver.is_empty() {
            receiver.add_action(0);
        }
    }
}

impl ResponseGenerator {
    fn generate_look_and_choose_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R, pi: &PendingInteraction, abilities: Option<&Vec<Ability>>) {
        let player = &state.core.players[p_idx];
        let mut final_filter_attr = pi.filter_attr;
        if final_filter_attr == 0 {
            if let Some(abs) = abilities {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter().position(|ab| (ab.choice_flags & (CHOICE_FLAG_LOOK | CHOICE_FLAG_MODE | CHOICE_FLAG_COLOR | CHOICE_FLAG_ORDER)) != 0).unwrap_or(0)
                } else { pi.ability_index as usize };

                if let Some(ab) = abs.get(ab_idx_real) {
                    if let Some(chunk) = ab.bytecode.chunks(4).find(|ch| ch[0] == O_LOOK_AND_CHOOSE) {
                        final_filter_attr = (chunk[2] as u32) as u64;
                    }
                }
            }
        }

        match pi.choice_type.as_str() {
            "SELECT_HAND_DISCARD" => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, final_filter_attr) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
            }
            "SELECT_DISCARD_PLAY" => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if state.card_matches_filter(db, cid, final_filter_attr) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            }
            "SELECT_STAGE" => {
                for i in 0..3 { receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize); }
            }
            "SELECT_LIVE_SLOT" => {
                for i in 0..player.live_zone.len().min(10) {
                    if player.live_zone[i] >= 0 { receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize); }
                }
            }
            "PAY_ENERGY" => {
                for i in 0..player.energy_zone.len().min(10) {
                    if !player.is_energy_tapped(i) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_ENERGY + i as i32) as usize);
                    }
                }
            }
            _ => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    let filter_only = final_filter_attr & 0xFFFFFFFFFFFF0FFF;
                    if state.card_matches_filter(db, cid, filter_only) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            }
        }
    }

    fn generate_select_member_actions<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R, pi: &PendingInteraction, filter_attr: u64) {
        let player = &state.core.players[p_idx];
        let packed_zone = (filter_attr >> 12) & 0x0F;
        let target_slot = if packed_zone > 0 { packed_zone as usize } else { 
            if pi.effect_opcode == O_SELECT_MEMBER || (pi.choice_type == "SELECT_MEMBER" && pi.effect_opcode == 0) {
                pi.target_slot as usize
            } else {
                crate::core::logic::interpreter::resolve_target_slot(pi.effect_opcode, &pi.ctx) 
            }
        };

        match target_slot {
            6 => { // Hand
                for i in 0..player.hand.len() {
                    let cid = player.hand[i];
                    if state.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
            },
            7 => { // Discard
                for i in 0..player.discard.len() {
                    let cid = player.discard[i];
                    if state.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            },
            _ => { // Stage (0-2) or Default
                for i in 0..3 {
                    let cid = player.stage[i];
                    if cid >= 0 && state.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action((crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
            }
        }
        receiver.add_action(0);
    }

    fn generate_select_mode_actions<R: ActionReceiver + ?Sized>(&self, _db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R, pi: &PendingInteraction, abilities: Option<&Vec<Ability>>) {
        let count = if pi.v_remaining > 0 { pi.v_remaining as i32 } else { 4 };
        for i in 0..count {
            let mut option_valid = true;
            if let Some(abs) = abilities {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter().position(|ab| (ab.choice_flags & CHOICE_FLAG_MODE) != 0).unwrap_or(0)
                } else { pi.ability_index as usize };

                if ab_idx_real < abs.len() {
                    let ab = &abs[ab_idx_real];
                    let bc = &ab.bytecode;
                    
                    let mut ip = 0;
                    if let Some(pos) = bc.chunks(4).position(|chunk| chunk[0] == O_SELECT_MODE) {
                        ip = pos * 4;
                    }
                    
                    let target_ip = if i < 2 {
                        let offset = ip + 2 + i as usize;
                        if offset < bc.len() { bc[offset] as usize } else { 0 }
                    } else {
                        let offset = ip + 4 + (i as usize - 2);
                        if offset < bc.len() { bc[offset] as usize } else { 0 }
                    };
                    
                    if target_ip > 0 && target_ip < bc.len() {
                        let target_op = bc[target_ip];
                        if target_op == O_PAY_ENERGY || target_op == O_MOVE_TO_DISCARD || target_op == O_MOVE_TO_DECK {
                            let v = if target_ip + 1 < bc.len() { bc[target_ip + 1] } else { 0 };
                            let s = if target_ip + 3 < bc.len() { bc[target_ip + 3] } else { 0 };
                            
                            if target_op == O_PAY_ENERGY {
                                let available = (0..state.core.players[p_idx].energy_zone.len()).filter(|&idx| !state.core.players[p_idx].is_energy_tapped(idx)).count() as i32;
                                if available < v { option_valid = false; }
                            } else if target_op == O_MOVE_TO_DISCARD {
                                if s == 6 || s == 0 { // TargetType.CARD_HAND or Generic
                                    if (state.core.players[p_idx].hand.len() as i32) < v { option_valid = false; }
                                }
                            }
                        }
                    }
                }
            }
            
            if option_valid {
                receiver.add_action((crate::core::logic::ACTION_BASE_MODE + i as i32) as usize);
            }
        }
    }
}
