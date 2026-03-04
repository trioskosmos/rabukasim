use crate::core::enums::*;
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::{ChoiceType, Ability, ActionReceiver, CardDatabase, GameState, PendingInteraction};

pub struct ResponseGenerator;

impl ActionGenerator for ResponseGenerator {
    fn generate<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        self.generate_internal(db, p_idx, state, receiver);

        // FINAL FALLBACK: If no actions were generated for a mandatory interaction,
        // we MUST allow Pass (0) to avoid a complete softlock.
        if receiver.is_empty() {
            receiver.add_action(0);
        }
    }
}

impl ResponseGenerator {
    fn generate_internal<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let pi = if let Some(p) = state.interaction_stack.last() {
            p
        } else {
            return;
        };
        let ctx = &pi.ctx;
        let opcode = pi.effect_opcode;
        let choice_type = pi.choice_type;
        let source_card_id = pi.ctx.source_card_id;

        let mut expected_p_idx = ctx.player_id as usize;
        if choice_type == ChoiceType::TapO || choice_type == ChoiceType::OpponentChoose {
            expected_p_idx = 1 - expected_p_idx;
        }

        if expected_p_idx != p_idx {
            return;
        }

        let player = &state.players[p_idx];

        // 1. Determine action 0 (fallback/skip)
        // Only allow action 0 if the interaction is marked OPTIONAL in bytecode
        // or if the choice type is inherently skip-able.
        let mut allow_action_0 =
            (pi.filter_attr & crate::core::logic::constants::FILTER_IS_OPTIONAL) != 0;

        if choice_type == ChoiceType::Optional || choice_type == ChoiceType::SelectMode {
            allow_action_0 = true;
        }

        if !allow_action_0
            && (choice_type == ChoiceType::RevealHand
                || choice_type == ChoiceType::SelectSwapSource
                || choice_type == ChoiceType::SelectSwapTarget
                || choice_type == ChoiceType::PayEnergy
                || choice_type == ChoiceType::OpponentChoose)
        {
            allow_action_0 = false;
        }

        if allow_action_0 {
            receiver.add_action(0);
        }

        let member = db.get_member(source_card_id as i32);
        let live = db.get_live(source_card_id as i32);
        let abilities = if let Some(m) = member {
            Some(&m.abilities)
        } else {
            live.map(|l| &l.abilities)
        };

        match choice_type {
            ChoiceType::Optional => {
                receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + 0) as usize);
                return;
            }
            ChoiceType::PayEnergy => {
                for i in 0..player.energy_zone.len().min(16) {
                    if !player.is_energy_tapped(i) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_ENERGY + i as i32) as usize,
                        );
                    }
                }
                return;
            }
            ChoiceType::RevealHand => {
                for (i, &_cid) in player.hand.iter().enumerate() {
                    receiver.add_action(
                        (crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize,
                    );
                }
                return;
            }
            ChoiceType::SelectDiscard => {
                for (i, &_cid) in player.discard.iter().enumerate() {
                    receiver
                        .add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                }
                return;
            }
            ChoiceType::SelectSwapSource => {
                for i in 0..player.success_lives.len() {
                    receiver.add_action(
                        (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                    );
                }
                return;
            }
            ChoiceType::SelectStage => {
                for i in 0..3 {
                    if (player.prevent_play_to_slot_mask & (1 << i)) == 0 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
                return;
            }
            ChoiceType::SelectStageEmpty => {
                for i in 0..3 {
                    if player.stage[i] == -1 && (player.prevent_play_to_slot_mask & (1 << i)) == 0 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
                return;
            }
            ChoiceType::SelectLiveSlot => {
                for i in 0..3 {
                    // Usually there's no prevent_play for live slots, but we verify it's open
                    receiver
                        .add_action((crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize);
                }
                return;
            }
            ChoiceType::SelectSwapTarget => {
                for (i, &_cid) in player.hand.iter().enumerate() {
                    receiver.add_action(
                        (crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize,
                    );
                }
                return;
            }
            _ => {}
        }

        match opcode {
            O_TAP_MEMBER => {
                for (i, &cid) in player.stage.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                        );
                    }
                }
                return;
            }
            O_TAP_OPPONENT => {
                // If it's TAP_O, p_idx IS the opponent making the choice for themselves.
                for (i, &cid) in state.players[p_idx].stage.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                        );
                    }
                }
                return;
            }
            O_ORDER_DECK => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
                return;
            }
            O_COLOR_SELECT => {
                for c in 0..6 {
                    receiver
                        .add_action((crate::core::logic::ACTION_BASE_COLOR + c as i32) as usize);
                }
                return;
            }
            O_LOOK_AND_CHOOSE => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_MOVE_TO_DISCARD => {
                let masked_filter = (pi.filter_attr as u32 as u64) & 0xFFFFFFFFFFFF0FFF;
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, masked_filter) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize,
                        );
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(0);
                }
                return;
            }
            O_RECOVER_MEMBER | O_RECOVER_LIVE => {
                let count = player.looked_cards.len();
                for i in 0..count {
                    let cid = player.looked_cards[i];
                    if cid != -1
                        && state.card_matches_filter(db, cid, (pi.filter_attr as u32) as u64)
                    {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_PLAY_MEMBER_FROM_HAND => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, pi.filter_attr) {
                        receiver
                            .add_action((crate::core::logic::ACTION_BASE_HAND + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_PLAY_MEMBER_FROM_DISCARD | O_PLAY_LIVE_FROM_DISCARD => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_SELECT_MEMBER => {
                self.generate_select_member_actions(db, p_idx, state, receiver, pi, pi.filter_attr);
                return;
            }
            O_SELECT_LIVE => {
                for (i, &cid) in player.live_zone.iter().enumerate() {
                    if cid >= 0 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
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
            O_OPPONENT_CHOOSE => {
                self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
                return;
            }
            O_SELECT_CARDS => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_LOOK_REORDER_DISCARD => {
                // This uses SELECT_CARDS_ORDER choice type
                // Similar to O_ORDER_DECK, we present the looked cards for selection/ordering
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
                // Also add a "Done" action (99) to finalize the order if optional or once selections are complete
                receiver.add_action((crate::core::logic::ACTION_BASE_CHOICE + 99) as usize);
                return;
            }
            _ => {
                if choice_type == ChoiceType::SelectMember {
                    self.generate_select_member_actions(
                        db,
                        p_idx,
                        state,
                        receiver,
                        pi,
                        pi.filter_attr,
                    );
                    return;
                }
                if choice_type == ChoiceType::SelectStage {
                    for i in 0..3 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                        );
                    }
                    return;
                }
                if choice_type == ChoiceType::SelectLiveSlot {
                    for i in 0..player.live_zone.len().min(10) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                        );
                    }
                    return;
                }
            }
        }
    }
}

impl ResponseGenerator {
    fn generate_look_and_choose_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        abilities: Option<&Vec<Ability>>,
    ) {
        let player = &state.players[p_idx];
        let mut final_filter_attr = pi.filter_attr;
        if final_filter_attr == 0 {
            if let Some(abs) = abilities {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter()
                        .position(|ab| {
                            (ab.choice_flags
                                & (CHOICE_FLAG_LOOK
                                    | CHOICE_FLAG_MODE
                                    | CHOICE_FLAG_COLOR
                                    | CHOICE_FLAG_ORDER))
                                != 0
                        })
                        .unwrap_or(0)
                } else {
                    pi.ability_index as usize
                };

                if let Some(ab) = abs.get(ab_idx_real) {
                    if let Some(chunk) = ab.bytecode.chunks(5).find(|ch| ch[0] == O_LOOK_AND_CHOOSE)
                    {
                        let a_low = chunk[2] as u32;
                        let a_high = chunk[3] as u32;
                        final_filter_attr = ((a_high as u64) << 32) | (a_low as u64);
                    }
                }
            }
        }

        match pi.choice_type {
            ChoiceType::SelectHandDiscard => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, final_filter_attr) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize,
                        );
                    }
                }
            }
            ChoiceType::SelectDiscardPlay => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if state.card_matches_filter(db, cid, final_filter_attr) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
            }
            ChoiceType::SelectStage => {
                for i in 0..3 {
                    receiver.add_action(
                        (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                    );
                }
            }
            ChoiceType::SelectLiveSlot => {
                for i in 0..player.live_zone.len().min(10) {
                    if player.live_zone[i] >= 0 {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                        );
                    }
                }
            }
            ChoiceType::PayEnergy => {
                for i in 0..player.energy_zone.len().min(10) {
                    if !player.is_energy_tapped(i) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_ENERGY + i as i32) as usize,
                        );
                    }
                }
            }
            _ => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    let filter_only = final_filter_attr & 0xFFFFFFFFFFFF0FFF;
                    if state.card_matches_filter(db, cid, filter_only) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
            }
        }
    }

    fn generate_select_member_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        filter_attr: u64,
    ) {
        if state.debug.debug_mode {
            println!("[DEBUG] generate_select_member_actions: p_idx={}, filter_attr={:X}", p_idx, filter_attr);
        }
        let player = &state.players[p_idx];
        let packed_zone = (filter_attr >> 12) & 0x0F;
        let target_slot = if packed_zone > 0 {
            packed_zone as usize
        } else {
            if pi.effect_opcode == O_SELECT_MEMBER
                || (pi.choice_type == ChoiceType::SelectMember && pi.effect_opcode == 0)
            {
                pi.target_slot as usize
            } else {
                crate::core::logic::interpreter::resolve_target_slot(pi.effect_opcode, &pi.ctx)
            }
        };

        match target_slot {
            6 => {
                // Hand
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_HAND_SELECT + i as i32) as usize,
                        );
                    }
                }
            }
            7 => {
                // Discard
                for (i, &cid) in player.discard.iter().enumerate() {
                    if state.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_CHOICE + i as i32) as usize,
                        );
                    }
                }
            }
            _ => {
                // Stage (0-2) or Default
                for (i, &cid) in player.stage.iter().enumerate() {
                    if cid >= 0 && state.card_matches_filter(db, cid, filter_attr) {
                        receiver.add_action(
                            (crate::core::logic::ACTION_BASE_STAGE_SLOTS + i as i32) as usize,
                        );
                    }
                }
            }
        }
        receiver.add_action(0);
    }

    fn generate_select_mode_actions<R: ActionReceiver + ?Sized>(
        &self,
        _db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        abilities: Option<&Vec<Ability>>,
    ) {
        let count = if pi.v_remaining > 0 {
            pi.v_remaining as i32
        } else {
            4
        };
        for i in 0..count {
            let mut option_valid = true;
            if let Some(abs) = abilities {
                let ab_idx_real = if pi.ability_index == -1 {
                    abs.iter()
                        .position(|ab| (ab.choice_flags & CHOICE_FLAG_MODE) != 0)
                        .unwrap_or(0)
                } else {
                    pi.ability_index as usize
                };

                if ab_idx_real < abs.len() {
                    let ab = &abs[ab_idx_real];
                    let bc = &ab.bytecode;

                    let mut ip = 0;
                    if let Some(pos) = bc.chunks(5).position(|chunk| chunk[0] == O_SELECT_MODE) {
                        ip = pos * 5;
                    } else {
                        // Fallback: If not found in chunks, check if it's the first instruction
                        if bc.get(0) == Some(&(O_SELECT_MODE as i32)) {
                            ip = 0;
                        }
                    }

                    // In 5-word format:
                    // SELECT_MODE v a s
                    // JUMP target1
                    // JUMP target2
                    // ...

                    let jump_instr_ip = ip + 5 + (i as usize * 5);
                    if jump_instr_ip + 1 < bc.len() {
                        let jump_op = bc[jump_instr_ip];
                        if jump_op == O_JUMP {
                            let jump_val = bc[jump_instr_ip + 1];
                            // The JUMP target points to the skip-to-end instruction AFTER the option's effect block.
                            // The actual first effect instruction is 5 bytes BEFORE that target.
                            let jump_target = jump_instr_ip + 5 + (jump_val as usize * 5);
                            let effect_ip = if jump_target >= 5 { jump_target - 5 } else { 0 };

                            if effect_ip + 4 < bc.len() {
                                let target_op = bc[effect_ip];
                                let v = bc[effect_ip + 1];
                                let s = bc[effect_ip + 4];

                                if target_op == O_PAY_ENERGY {
                                    let available = (0..state.players[p_idx].energy_zone.len())
                                        .filter(|&idx| {
                                            !state.players[p_idx].is_energy_tapped(idx)
                                        })
                                        .count()
                                        as i32;
                                    if available < v {
                                        option_valid = false;
                                    }
                                } else if target_op == O_MOVE_TO_DISCARD {
                                    // Source zone can be packed: lower byte = slot/target, upper bytes = source zone
                                    // s=6 means Hand directly, s=0x60001 means source=Hand(6) packed
                                    let source_zone = if s > 255 { (s >> 16) & 0xFF } else { s };
                                    let hand_len = state.players[p_idx].hand.len() as i32;
                                    if (source_zone == 6 || source_zone == 0) && hand_len < v {
                                        option_valid = false;
                                    }
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
