use crate::core::enums::*;
use crate::core::logic::ability_patterns::{
    pending_live_ability, pending_optional_mode_mask, pending_targeted_live_heart_bonus,
};
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::{
    Ability, ActionReceiver, CardDatabase, ChoiceType, GameState, PendingInteraction,
};

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
    fn effect_runtime_attr_for_opcode(ab: &Ability, opcode: i32) -> Option<u64> {
        ab.effects
            .iter()
            .find(|effect| effect.runtime_opcode == opcode)
            .map(|effect| effect.runtime_attr)
    }

    fn effect_filter_attr_for_opcode(ab: &Ability, opcode: i32) -> Option<u64> {
        ab.effects
            .iter()
            .find(|effect| effect.runtime_opcode == opcode)
            .and_then(|effect| {
                effect
                    .params
                    .get("filter")
                    .and_then(|value| value.as_str())
                    .map(crate::core::logic::filter::map_filter_string_to_attr)
            })
    }

    fn is_saintsnow_member(db: &CardDatabase, cid: i32) -> bool {
        db.get_member(cid)
            .map(|card| matches!(card.name.as_str(), "鹿角聖良" | "鹿角理亞"))
            .unwrap_or(false)
    }

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

        let expected_p_idx = ctx.player_id as usize;

        if expected_p_idx != p_idx {
            return;
        }

        let player = &state.players[p_idx];

        // 1. Determine action 0 (fallback/skip)
        // Only allow action 0 if the interaction is marked OPTIONAL
        // or if the choice type is inherently skip-able.
        let mut allow_action_0 = (pi.filter_attr & FILTER_IS_OPTIONAL) != 0;

        if choice_type == ChoiceType::Optional {
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

        if pending_optional_mode_mask(db, pi).is_some() {
            self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
            return;
        }

        let targeted_live_heart_bonus = pending_targeted_live_heart_bonus(db, pi).filter(|_| {
            pi.ctx.trigger_type == TriggerType::OnLiveStart
                && matches!(
                    pi.choice_type,
                    ChoiceType::SelectMember | ChoiceType::SelectHandDiscard
                )
                && (pi.choice_type != ChoiceType::SelectHandDiscard
                    || (state.players[0].hand.is_empty() && state.players[1].hand.is_empty()))
        });

        if let Some((_filter_attr, _heart_color_idx)) = targeted_live_heart_bonus {
            for (i, &cid) in state.players[p_idx].stage.iter().enumerate() {
                if cid >= 0
                    && db
                        .get_member(cid)
                        .map(|card| card.groups.contains(&0))
                        .unwrap_or(false)
                {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
            }
            receiver.add_action(0);
            return;
        }

        match choice_type {
            ChoiceType::Optional => {
                receiver.add_action((ACTION_BASE_CHOICE + 0) as usize); // Yes/Proceed
                receiver.add_action((ACTION_BASE_CHOICE + 1) as usize); // No/Skip
                return;
            }
            ChoiceType::PayEnergy => {
                for i in 0..player.energy_zone.len().min(16) {
                    if pi.effect_opcode == O_PLACE_ENERGY_UNDER_MEMBER
                        || !player.is_energy_tapped(i)
                    {
                        receiver.add_action((ACTION_BASE_ENERGY + i as i32) as usize);
                    }
                }
                if pi.v_remaining == -2 {
                    receiver.add_action((ACTION_BASE_CHOICE + 99) as usize);
                }
                return;
            }
            ChoiceType::RevealHand => {
                for (i, &_cid) in player.hand.iter().enumerate() {
                    receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                return;
            }
            ChoiceType::TapO => {
                let target_p_idx = 1 - (pi.ctx.activator_id as usize);
                for (i, &cid) in state.players[target_p_idx].stage.iter().enumerate() {
                    if cid >= 0 && !state.players[target_p_idx].is_tapped(i) {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectDiscard => {
                for (i, &_cid) in player.discard.iter().enumerate() {
                    receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                }
                return;
            }
            ChoiceType::SelectSwapSource => {
                for i in 0..player.success_lives.len() {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
                return;
            }
            ChoiceType::SelectStage => {
                for i in 0..3 {
                    if (player.prevent_play_to_slot_mask() & (1 << i)) == 0 {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectStageEmpty => {
                // Count empty slots first to check if forced
                let mut empty_slots = Vec::new();
                for i in 0..3 {
                    if player.stage[i] == -1 && (player.prevent_play_to_slot_mask() & (1 << i)) == 0
                    {
                        empty_slots.push(i);
                    }
                }
                // If only one empty slot, auto-select it (forced choice)
                if empty_slots.len() == 1 {
                    receiver.add_action((ACTION_BASE_CHOICE + empty_slots[0] as i32) as usize);
                } else {
                    // Multiple or no choices - present all
                    for i in empty_slots {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectStageEmptyBaton => {
                for i in 0..3 {
                    if player.stage[i] == -1
                        && (player.prevent_play_to_slot_mask() & (1 << i) as u8) == 0
                        && player.baton_source_slots.contains(&i)
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectLiveSlot => {
                for i in 0..3 {
                    // Usually there's no prevent_play for live slots, but we verify it's open
                    receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                }
                return;
            }
            ChoiceType::SelectSwapTarget => {
                for (i, &_cid) in player.hand.iter().enumerate() {
                    receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                }
                return;
            }
            _ => {}
        }

        match opcode {
            O_TAP_MEMBER => {
                for (i, &cid) in player.stage.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
                return;
            }
            O_TAP_OPPONENT => {
                let target_p_idx = 1 - (ctx.activator_id as usize);
                for (i, &cid) in state.players[target_p_idx].stage.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
                return;
            }
            O_ORDER_DECK => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                return;
            }
            O_COLOR_SELECT => {
                let mut choices_to_show = vec![0, 1, 2, 3, 4, 5]; // Default to all 6 colors

                // Try to extract the actual choices from the ability's effect params
                if let Some(abilities_list) = abilities {
                    if (pi.ability_index as usize) < abilities_list.len() {
                        let ability = &abilities_list[pi.ability_index as usize];
                        for effect in &ability.effects {
                            if effect.runtime_opcode == O_COLOR_SELECT {
                                // Extract choices from effect.params["choices"]
                                if let Some(choices_val) = effect.params.get("choices") {
                                    if let Ok(choices_arr) =
                                        serde_json::from_value::<Vec<i32>>(choices_val.clone())
                                    {
                                        choices_to_show = choices_arr
                                            .into_iter()
                                            .filter(|&c| c >= 0 && c < 7)
                                            .collect();
                                    }
                                }
                                break;
                            }
                        }
                    }
                }

                for &c in &choices_to_show {
                    receiver.add_action((ACTION_BASE_COLOR + c) as usize);
                }
                return;
            }
            O_LOOK_AND_CHOOSE => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_MOVE_TO_DISCARD => {
                let masked_filter =
                    pi.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
                let decoded_slot =
                    crate::core::logic::interpreter::instruction::DecodedSlot::decode(
                        pi.target_slot,
                    );
                if decoded_slot.source_zone == crate::core::enums::Zone::Stage {
                    for (i, &cid) in player.stage.iter().enumerate() {
                        if cid >= 0
                            && state.card_matches_filter_with_ctx(db, cid, masked_filter, &pi.ctx)
                        {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                        }
                    }
                } else {
                    for (i, &cid) in player.hand.iter().enumerate() {
                        if state.card_matches_filter_with_ctx(db, cid, masked_filter, &pi.ctx) {
                            receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                        }
                    }
                }
                if (pi.filter_attr & FILTER_IS_OPTIONAL) != 0 {
                    receiver.add_action(0);
                }
                return;
            }
            O_RECOVER_MEMBER | O_RECOVER_LIVE => {
                let count = player.looked_cards.len();
                for i in 0..count {
                    let cid = player.looked_cards[i];
                    if cid != -1
                        && state.card_matches_filter_with_ctx(db, cid, pi.filter_attr, &pi.ctx)
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_PLAY_MEMBER_FROM_HAND => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter(db, cid, pi.filter_attr) {
                        receiver.add_action((ACTION_BASE_HAND + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(0);
                }
                return;
            }
            O_PLAY_MEMBER_FROM_DISCARD | O_PLAY_LIVE_FROM_DISCARD => {
                self.generate_look_and_choose_actions(db, p_idx, state, receiver, pi, abilities);
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
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
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
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
                if (pi.filter_attr & crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL)
                    != 0
                {
                    receiver.add_action(
                        (ACTION_BASE_CHOICE + crate::core::logic::constants::CHOICE_DONE as i32)
                            as usize,
                    );
                }
                return;
            }
            O_LOOK_REORDER_DISCARD => {
                // This uses SELECT_CARDS_ORDER choice type
                // Similar to O_ORDER_DECK, we present the looked cards for selection/ordering
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if cid != -1 {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
                // Also add a "Done" action (99) to finalize the order if optional or once selections are complete
                receiver.add_action(
                    (crate::core::logic::ACTION_BASE_CHOICE
                        + crate::core::logic::constants::CHOICE_DONE as i32)
                        as usize,
                );
                return;
            }
            _ => {
                if choice_type == ChoiceType::SelectMember || choice_type == ChoiceType::TapMSelect
                {
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
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                    return;
                }
                if choice_type == ChoiceType::MoveMemberDest {
                    let composite_filter_attr =
                        crate::core::logic::filter::map_filter_string_to_attr(
                            "HAS_GROUP_AQOURS_OR_SAINT_SNOW",
                        );
                    let filter_attr = abilities
                        .and_then(|abs| {
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

                            abs.get(ab_idx_real)
                        })
                        .and_then(|ab| Self::effect_filter_attr_for_opcode(ab, O_MOVE_MEMBER))
                        .unwrap_or(
                            pi.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK,
                        );
                    for i in 0..3 {
                        let cid = player.stage[i];
                        if i != pi.ctx.area_idx as usize
                            && cid >= 0
                            && (state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx)
                                || (filter_attr == composite_filter_attr
                                    && Self::is_saintsnow_member(db, cid)))
                        {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                        }
                    }
                    return;
                }
                if choice_type == ChoiceType::SelectLiveSlot {
                    for i in 0..player.live_zone.len().min(10) {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
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
                    if (ab.opcodes_mask & (1u128 << (O_LOOK_AND_CHOOSE as u32 % 128))) != 0 {
                        if let Some(attr) =
                            Self::effect_runtime_attr_for_opcode(ab, O_LOOK_AND_CHOOSE)
                        {
                            final_filter_attr = attr;
                        } else if let Some(program) = ab.frame_program.as_ref() {
                            for frame in &program.frames {
                                if frame.opcode() == O_LOOK_AND_CHOOSE {
                                    final_filter_attr = frame.attr();
                                    break;
                                }
                            }
                        }
                    }
                }
            }
        }

        match pi.choice_type {
            ChoiceType::SelectHandDiscard => {
                for (i, &cid) in player.hand.iter().enumerate() {
                    if state.card_matches_filter_with_ctx(db, cid, final_filter_attr, &pi.ctx) {
                        receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
            }
            ChoiceType::SelectDiscardPlay => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if state.card_matches_filter_with_ctx(db, cid, final_filter_attr, &pi.ctx) {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            }
            ChoiceType::SelectStage => {
                for i in 0..3 {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
            }
            ChoiceType::SelectLiveSlot => {
                for i in 0..player.live_zone.len().min(10) {
                    if player.live_zone[i] >= 0 {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
            }
            ChoiceType::PayEnergy => {
                for i in 0..player.energy_zone.len().min(10) {
                    if pi.effect_opcode == O_PLACE_ENERGY_UNDER_MEMBER
                        || !player.is_energy_tapped(i)
                    {
                        receiver.add_action((ACTION_BASE_ENERGY + i as i32) as usize);
                    }
                }
            }
            _ => {
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    let filter_only =
                        final_filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
                    if state.card_matches_filter_with_ctx(db, cid, filter_only, &pi.ctx) {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
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
            println!(
                "[DEBUG] generate_select_member_actions: p_idx={}, filter_attr={:X}",
                p_idx, filter_attr
            );
        }
        let filter_only = filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
        let targeted_live_heart_bonus = pending_targeted_live_heart_bonus(db, pi).filter(|_| {
            pi.ctx.trigger_type == TriggerType::OnLiveStart
                && matches!(
                    pi.choice_type,
                    ChoiceType::SelectMember | ChoiceType::SelectHandDiscard
                )
                && (pi.choice_type != ChoiceType::SelectHandDiscard
                    || (state.players[0].hand.is_empty() && state.players[1].hand.is_empty()))
        });

        if let Some((_follow_up_filter, _heart_color_idx)) = targeted_live_heart_bonus {
            for (i, &cid) in state.players[p_idx].stage.iter().enumerate() {
                if cid >= 0
                    && db
                        .get_member(cid)
                        .map(|card| card.groups.contains(&0))
                        .unwrap_or(false)
                {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
            }
            receiver.add_action(0);
            if state.debug.debug_mode {
                println!("[DEBUG] generate_select_member_actions: targeted_live_heart_bonus shortcut active");
            }
            return;
        }
        let target_player = match (filter_attr & 0x3) as u8 {
            2 => 1 - p_idx,
            3 => p_idx,
            _ => p_idx,
        };
        let player = &state.players[target_player];

        if pi.choice_type == ChoiceType::TapMSelect && filter_only == 0 {
            for (i, &cid) in player.stage.iter().enumerate() {
                if cid >= 0 {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                }
            }
            receiver.add_action(0);
            return;
        }

        let packed_zone = (filter_attr >> 12) & 0x0F;
        let target_slot = if packed_zone > 0 {
            packed_zone as usize
        } else {
            if pi.effect_opcode == O_SELECT_MEMBER
                || pi.choice_type == ChoiceType::TapMSelect
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
                    if filter_only == 0
                        || state.card_matches_filter_with_ctx(db, cid, filter_only, &pi.ctx)
                    {
                        receiver.add_action((ACTION_BASE_HAND_SELECT + i as i32) as usize);
                    }
                }
            }
            7 => {
                // Discard
                for (i, &cid) in player.discard.iter().enumerate() {
                    if filter_only == 0
                        || state.card_matches_filter_with_ctx(db, cid, filter_only, &pi.ctx)
                    {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
                }
            }
            _ => {
                // Stage (0-2) or Default
                let exclude_selected = true;
                for (i, &cid) in player.stage.iter().enumerate() {
                    let matches = cid >= 0
                        && (!exclude_selected || !pi.ctx.selected_cards.contains(&cid))
                        && (filter_only == 0
                            || state.card_matches_filter_with_ctx(db, cid, filter_only, &pi.ctx));
                    if matches {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
            }
        }
        receiver.add_action(0);
    }

    fn generate_select_mode_actions<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        abilities: Option<&Vec<Ability>>,
    ) {
        if let Some(mask) = pending_optional_mode_mask(db, pi) {
            if let Some(ability) = pending_live_ability(db, pi) {
                for effect_idx in 0..ability.effects.len() {
                    let selected_bit = 1i16 << effect_idx;
                    if (mask & selected_bit) != 0 {
                        receiver.add_action((ACTION_BASE_MODE + effect_idx as i32) as usize);
                    }
                }
            } else {
                for effect_idx in 0..mask.count_ones() as i32 {
                    receiver.add_action((ACTION_BASE_MODE + effect_idx) as usize);
                }
            }
            return;
        }

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
                    if let Some(frame_program) = ab.frame_program.as_ref() {
                        let mut select_mode_idx = 0;
                        let mut found = false;
                        for (idx, frame) in frame_program.frames.iter().enumerate() {
                            if frame.opcode() == O_SELECT_MODE {
                                select_mode_idx = idx;
                                found = true;
                                break;
                            }
                        }

                        if found {
                            let jump_frame_idx = select_mode_idx + 1 + i as usize;
                            if let Some(jump_frame) = frame_program.frames.get(jump_frame_idx) {
                                if jump_frame.opcode() == O_JUMP {
                                    let target_idx =
                                        (jump_frame_idx as i32 + 1 + jump_frame.value()) as usize;
                                    if let Some(effect_frame) = frame_program.frames.get(target_idx)
                                    {
                                        let target_op = effect_frame.opcode();
                                        let v = effect_frame.value();

                                        if target_op == O_PAY_ENERGY {
                                            let player = &state.players[p_idx];
                                            let available = player.energy_zone.len() as i32
                                                - player.tapped_energy_count() as i32;
                                            if available < v {
                                                option_valid = false;
                                            }
                                        } else if target_op == O_MOVE_TO_DISCARD {
                                            option_valid = true;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if option_valid {
                receiver.add_action((ACTION_BASE_MODE + i as i32) as usize);
            }
        }
    }
}
