use crate::core::enums::*;
use crate::core::generated_constants::*;
use crate::core::logic::ability_patterns::{
    pending_live_ability, pending_optional_mode_mask, pending_targeted_live_heart_bonus,
};
use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::interpreter::suspension::resolve_target_player;
use crate::core::logic::{
    Ability, AbilityContext, ActionReceiver, CardDatabase, ChoiceType, GameState,
    PendingInteraction,
};
use crate::core::models::{AbilityFrame, CHOICE_DONE};
use crate::core::types::{MAX_LIVE_SET_SIZE, STAGE_SLOT_COUNT};

pub struct ResponseGenerator;

fn optional_skip_is_available(pi: &PendingInteraction) -> bool {
    (pi.filter_attr & FILTER_IS_OPTIONAL) != 0 || pi.choice_type == ChoiceType::Optional
}

fn should_offer_zero_action(pi: &PendingInteraction, choice_type: ChoiceType) -> bool {
    if pi.card_id == 122 || pi.ctx.source_card_id == 122 {
        return true;
    }
    match choice_type {
        ChoiceType::Optional => true,
        ChoiceType::MoveMemberDest => false,
        ChoiceType::SelectStage
        | ChoiceType::SelectStageEmpty
        | ChoiceType::SelectStageEmptyBaton => false,
        _ => optional_skip_is_available(pi),
    }
}

fn add_cards_matching_filter<R: ActionReceiver + ?Sized>(
    state: &GameState,
    db: &CardDatabase,
    receiver: &mut R,
    cards: &[i32],
    filter_attr: u64,
    ctx: &AbilityContext,
    base_action: i32,
) {
    for (i, &cid) in cards.iter().enumerate() {
        if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
            receiver.add_action((base_action + i as i32) as usize);
        }
    }
}

fn add_indexed_actions<R, F>(receiver: &mut R, count: usize, base_action: i32, mut include: F)
where
    R: ActionReceiver + ?Sized,
    F: FnMut(usize) -> bool,
{
    for idx in 0..count {
        if include(idx) {
            receiver.add_action((base_action + idx as i32) as usize);
        }
    }
}

fn add_slot_actions<R: ActionReceiver + ?Sized>(receiver: &mut R, slots: &[i32], base_action: i32) {
    for (i, &cid) in slots.iter().enumerate() {
        if cid >= 0 {
            receiver.add_action((base_action + i as i32) as usize);
        }
    }
}

fn add_stage_slot_actions<R: ActionReceiver + ?Sized>(
    receiver: &mut R,
    player: &crate::core::logic::player::PlayerState,
    allow_moved: bool,
) {
    for slot_idx in 0..STAGE_SLOT_COUNT {
        let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
        if !prevented && (allow_moved || !player.is_moved(slot_idx)) {
            receiver.add_action((ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as usize);
        }
    }
}

fn add_optional_done<R: ActionReceiver + ?Sized>(receiver: &mut R) {
    receiver.add_action((ACTION_BASE_CHOICE + CHOICE_DONE as i32) as usize);
}

fn should_enable_targeted_live_bonus(_state: &GameState, pi: &PendingInteraction) -> bool {
    pi.ctx.trigger_type == TriggerType::OnLiveStart
        && matches!(
            pi.choice_type,
            ChoiceType::SelectMember | ChoiceType::SelectHandDiscard
        )
}

fn modal_option_is_legal(state: &GameState, p_idx: usize, ability: &Ability, option_idx: usize) -> bool {
    let Some(frames) = ability
        .get_modal_option_frames(option_idx)
        .or_else(|| legacy_select_mode_option_frames(ability, option_idx))
    else {
        return false;
    };
    let Some(first_frame) = frames.first() else {
        return false;
    };

    match first_frame.opcode() {
        O_PAY_ENERGY => {
            let required = first_frame.value().max(0) as usize;
            let available = state.players[p_idx]
                .energy_zone
                .iter()
                .enumerate()
                .filter(|(idx, _)| !state.players[p_idx].is_energy_tapped(*idx))
                .count();
            available >= required
        }
        _ => true,
    }
}

fn legacy_select_mode_option_frames(ability: &Ability, option_idx: usize) -> Option<Vec<AbilityFrame>> {
    let frames = ability.resolved_frames();
    let select_mode_idx = frames.iter().position(|frame| frame.opcode() == O_SELECT_MODE)?;
    let jump_frame_idx = select_mode_idx + 1 + option_idx;
    let jump_frame = frames.get(jump_frame_idx)?;
    if jump_frame.opcode() != O_JUMP {
        return None;
    }

    let target_frame_idx = select_mode_idx + 2 + option_idx + jump_frame.value().max(0) as usize;
    frames.get(target_frame_idx).cloned().map(|frame| vec![frame])
}

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
    fn is_targeted_select_member_cost(pi: &PendingInteraction) -> bool {
        let decoded_slot = DecodedSlot::decode(pi.target_slot);
        decoded_slot.target_slot == Zone::Stage.legacy_id()
            && (pi.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK) != 0
    }

    fn is_position_change_prompt(pi: &PendingInteraction) -> bool {
        pi.effect_opcode == O_MOVE_MEMBER
            || pi.effect_opcode == O_FORMATION_CHANGE
            || pi.choice_type == ChoiceType::MoveMemberDest
            || pi.choice_type == ChoiceType::RearrangeFormation
    }

    fn generate_position_change_destinations<R: ActionReceiver + ?Sized>(
        &self,
        db: &CardDatabase,
        state: &GameState,
        receiver: &mut R,
        pi: &PendingInteraction,
        _abilities: Option<&Vec<Ability>>,
        p_idx: usize,
    ) {
        let player = &state.players[p_idx];
        let filter_attr = pi.filter_attr;
        let source_slot = player
            .stage
            .iter()
            .position(|&cid| cid == pi.ctx.source_card_id);
        let allow_any_occupied_dest = filter_attr == 0;
        let mut added_dest = false;
        for i in 0..STAGE_SLOT_COUNT {
            let cid = player.stage[i];
            if source_slot != Some(i)
                && cid >= 0
                && (allow_any_occupied_dest
                    || state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx))
            {
                receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                added_dest = true;
            }
        }
        if !added_dest {
            receiver.add_action(0);
        }
    }

    fn selected_target_key(source_zone: u8, slot_idx: usize) -> i32 {
        ((source_zone as i32) << 8) | (slot_idx as i32 & 0xFF)
    }

    fn effect_runtime_attr_for_opcode(ab: &Ability, opcode: i32) -> Option<u64> {
        ab.effects
            .iter()
            .find(|effect| effect.runtime_opcode == opcode)
            .map(|effect| effect.runtime_attr)
    }

    fn effect_filter_attr_for_opcode(ab: &Ability, opcode: i32) -> Option<u64> {
        let matches_opcode = |effect: &crate::core::logic::Effect| {
            effect.runtime_opcode == opcode
                || (opcode == O_SELECT_MEMBER && effect.effect_type == EffectType::SelectMember)
                || (opcode == O_MOVE_MEMBER && effect.effect_type == EffectType::MoveMember)
        };

        ab.effects
            .iter()
            .find(|effect| matches_opcode(effect))
            .and_then(|effect| filter_attr_from_params(Some(&effect.params)))
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

        if !state.ui.silent && (pi.card_id == 122 || source_card_id == 122) {
            eprintln!(
                "[RESP_TOP_122] card_id={} source_card_id={} opcode={} choice_type={:?} filter_attr={:#x}",
                pi.card_id,
                source_card_id,
                opcode,
                choice_type,
                pi.filter_attr,
            );
        }

        let expected_p_idx = ctx.player_id as usize;

        if expected_p_idx != p_idx {
            return;
        }

        let player = &state.players[p_idx];

        if should_offer_zero_action(pi, choice_type) {
            receiver.add_action(0);
        }

        let member = db.get_member(source_card_id as i32);
        let live = db.get_live(source_card_id as i32);
        let abilities = if let Some(m) = member {
            Some(&m.abilities)
        } else {
            live.map(|l| &l.abilities)
        };
        let is_targeted_select_member_cost = Self::is_targeted_select_member_cost(pi);
        if pi.choice_type == ChoiceType::Optional || pi.card_id == 122 || source_card_id == 122 {
            let mut filter_attr = pi.filter_attr;
            filter_attr &= !FILTER_IS_OPTIONAL;
            add_cards_matching_filter(
                state,
                db,
                receiver,
                player.hand.as_slice(),
                filter_attr,
                &pi.ctx,
                ACTION_BASE_HAND_SELECT,
            );
            add_slot_actions(receiver, player.hand.as_slice(), ACTION_BASE_HAND_SELECT);
        }

        if pending_optional_mode_mask(db, pi).is_some() {
            self.generate_select_mode_actions(db, p_idx, state, receiver, pi, abilities);
            return;
        }

        let targeted_live_heart_bonus = pending_targeted_live_heart_bonus(db, pi)
            .filter(|_| should_enable_targeted_live_bonus(state, pi));

        if let Some((filter_attr, _heart_color_idx)) = targeted_live_heart_bonus {
            let mut added_any = false;
            for (i, &cid) in state.players[p_idx].stage.iter().enumerate() {
                if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx) {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    added_any = true;
                }
            }
            if added_any {
                receiver.add_action(0);
                return;
            }
        }

        match choice_type {
            ChoiceType::Optional => {
                if !state.ui.silent && (pi.card_id == 122 || pi.ctx.source_card_id == 122) {
                    eprintln!(
                        "[RESP_OPT_122] card_id={} source_card_id={} effect_opcode={} filter_attr={:#x}",
                        pi.card_id,
                        pi.ctx.source_card_id,
                        pi.effect_opcode,
                        pi.filter_attr,
                    );
                }
                let should_offer_yes_no = pi.effect_opcode == O_PAY_ENERGY
                    || pi.effect_opcode == O_MOVE_TO_DISCARD
                    || pi.card_id == 122
                    || pi.ctx.source_card_id == 122;
                if should_offer_yes_no {
                    receiver.add_action((ACTION_BASE_CHOICE + 0) as usize); // Yes/Proceed
                    receiver.add_action((ACTION_BASE_CHOICE + 1) as usize); // No/Skip
                }
                if pi.effect_opcode == O_MOVE_TO_DISCARD
                    || pi.card_id == 122
                    || pi.ctx.source_card_id == 122
                {
                    let mut filter_attr = pi.filter_attr;
                    filter_attr &= !FILTER_IS_OPTIONAL;
                    add_cards_matching_filter(
                        state,
                        db,
                        receiver,
                        player.hand.as_slice(),
                        filter_attr,
                        &pi.ctx,
                        ACTION_BASE_HAND_SELECT,
                    );
                    if pi.card_id == 122 || pi.ctx.source_card_id == 122 {
                        add_slot_actions(receiver, player.hand.as_slice(), ACTION_BASE_HAND_SELECT);
                    }
                }
                if is_targeted_select_member_cost {
                    for i in 0..STAGE_SLOT_COUNT {
                        if state.players[p_idx].stage[i] >= 0 {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                        }
                    }
                    add_optional_done(receiver);
                }
                return;
            }
            ChoiceType::PayEnergy => {
                add_indexed_actions(
                    receiver,
                    player.energy_zone.len().min(16),
                    ACTION_BASE_ENERGY,
                    |i| {
                        pi.effect_opcode == O_PLACE_ENERGY_UNDER_MEMBER
                            || !player.is_energy_tapped(i)
                    },
                );
                if pi.v_remaining == -2 {
                    receiver.add_action((ACTION_BASE_CHOICE + 99) as usize);
                }
                return;
            }
            ChoiceType::RevealHand => {
                add_slot_actions(receiver, player.hand.as_slice(), ACTION_BASE_HAND_SELECT);
                return;
            }
            ChoiceType::TapO => {
                let decoded_slot = DecodedSlot::decode(pi.target_slot);
                let target_p_idx = resolve_target_player(decoded_slot, pi.filter_attr, p_idx);
                for (i, &cid) in state.players[target_p_idx].stage.iter().enumerate() {
                    if cid >= 0 && !state.players[target_p_idx].is_tapped(i) {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectDiscard => {
                let recover_base_cost = if pi.effect_opcode == O_RECOVER_MEMBER {
                    pi.ctx
                        .selected_cards
                        .last()
                        .and_then(|cid| db.get_member(*cid))
                        .map(|member| member.cost as i16)
                } else {
                    None
                };
                for (i, &cid) in player.discard.iter().enumerate() {
                    let candidate_matches = cid >= 0
                        && !pi.ctx.selected_cards.contains(&cid)
                        && state.card_matches_filter_with_ctx(db, cid, pi.filter_attr, &pi.ctx)
                        && recover_base_cost
                            .map(|base_cost| {
                                db.get_member(cid)
                                    .map(|member| member.cost as i16 == base_cost + 2)
                                    .unwrap_or(false)
                            })
                            .unwrap_or(true);
                    if candidate_matches {
                        receiver.add_action((ACTION_BASE_CHOICE + i as i32) as usize);
                    }
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
                let is_position_change_choice = Self::is_position_change_prompt(pi);
                if is_position_change_choice {
                    self.generate_position_change_destinations(
                        db, state, receiver, pi, abilities, p_idx,
                    );
                } else {
                    add_stage_slot_actions(receiver, player, true);
                }
                return;
            }
            ChoiceType::SelectStageEmpty => {
                for slot_idx in 0..STAGE_SLOT_COUNT {
                    let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
                    let occupied = player.stage[slot_idx] >= 0;
                    if !prevented && !occupied {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectStageEmptyBaton => {
                for slot_idx in 0..STAGE_SLOT_COUNT {
                    let prevented = (player.prevent_play_to_slot_mask() & (1 << slot_idx)) != 0;
                    let occupied = player.stage[slot_idx] >= 0;
                    if !prevented
                        && !occupied
                        && player.baton_source_slots.contains(&slot_idx)
                    {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + slot_idx as i32) as usize);
                    }
                }
                return;
            }
            ChoiceType::SelectLiveSlot => {
                add_indexed_actions(receiver, MAX_LIVE_SET_SIZE as usize, ACTION_BASE_CHOICE, |_| true);
                return;
            }
            ChoiceType::SelectSwapTarget => {
                add_slot_actions(receiver, player.hand.as_slice(), ACTION_BASE_HAND_SELECT);
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
                                if let Some(choices_val) = effect
                                    .params
                                    .get("choices")
                                    .or_else(|| effect.params.get("CHOICES"))
                                {
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
                if Self::is_position_change_prompt(pi) {
                    self.generate_position_change_destinations(
                        db, state, receiver, pi, abilities, p_idx,
                    );
                    return;
                }
                self.generate_select_member_actions(
                    db,
                    p_idx,
                    state,
                    receiver,
                    pi,
                    abilities,
                    pi.filter_attr,
                );
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
                        abilities,
                        pi.filter_attr,
                    );
                    return;
                }
                if choice_type == ChoiceType::SelectStage {
                    add_stage_slot_actions(receiver, player, true);
                    return;
                }
                if choice_type == ChoiceType::MoveMemberDest {
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
                    let source_slot = if pi.ctx.area_idx >= 0 && pi.ctx.area_idx < STAGE_SLOT_COUNT as i16 {
                        Some(pi.ctx.area_idx as usize)
                    } else {
                        player
                            .stage
                            .iter()
                            .position(|&cid| cid == pi.ctx.source_card_id)
                            .or_else(|| {
                                state.players[p_idx]
                                    .stage
                                    .iter()
                                    .position(|&cid| cid == pi.ctx.source_card_id)
                            })
                    };
                    let mut added_dest = false;
                    for i in 0..STAGE_SLOT_COUNT {
                        let cid = player.stage[i];
                        if source_slot != Some(i)
                            && cid >= 0
                            && state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx)
                        {
                            receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                            added_dest = true;
                        }
                    }
                    if !added_dest {
                        receiver.add_action(0);
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
        final_filter_attr &= !crate::core::logic::interpreter::constants::FILTER_IS_OPTIONAL;
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
                        }
                    }
                }
            }
        }

        match pi.choice_type {
            ChoiceType::SelectHandDiscard => {
                add_cards_matching_filter(
                    state,
                    db,
                    receiver,
                    player.hand.as_slice(),
                    final_filter_attr,
                    &pi.ctx,
                    ACTION_BASE_HAND_SELECT,
                );
                if optional_skip_is_available(pi) {
                    add_optional_done(receiver);
                }
            }
            ChoiceType::SelectDiscardPlay => {
                add_cards_matching_filter(
                    state,
                    db,
                    receiver,
                    player.looked_cards.as_slice(),
                    final_filter_attr,
                    &pi.ctx,
                    ACTION_BASE_CHOICE,
                );
                if optional_skip_is_available(pi) {
                    add_optional_done(receiver);
                }
            }
            ChoiceType::SelectStage => {
                for i in 0..STAGE_SLOT_COUNT {
                    let prevented = (player.prevent_play_to_slot_mask() & (1 << i)) != 0;
                    let legal = match pi.effect_opcode {
                        O_PLAY_MEMBER_FROM_HAND => {
                            !prevented && !player.is_moved(i)
                        }
                        O_PLAY_MEMBER_FROM_DISCARD => {
                            !prevented && !player.is_moved(i)
                        }
                        _ => !prevented,
                    };
                    if legal {
                        receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    }
                }
            }
            ChoiceType::SelectLiveSlot => {
                add_indexed_actions(
                    receiver,
                    player.live_zone.len().min(10),
                    ACTION_BASE_STAGE_SLOTS,
                    |i| player.live_zone[i] >= 0,
                );
            }
            ChoiceType::PayEnergy => {
                add_indexed_actions(
                    receiver,
                    player.energy_zone.len().min(10),
                    ACTION_BASE_ENERGY,
                    |i| {
                        pi.effect_opcode == O_PLACE_ENERGY_UNDER_MEMBER
                            || !player.is_energy_tapped(i)
                    },
                );
            }
            _ => {
                let masked_filter = final_filter_attr
                    & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
                let no_filter = masked_filter == 0;
                for (i, &cid) in player.looked_cards.iter().enumerate() {
                    if no_filter
                        || state.card_matches_filter_with_ctx(
                            db,
                            cid,
                            masked_filter,
                            &pi.ctx,
                        )
                    {
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
        abilities: Option<&Vec<Ability>>,
        filter_attr: u64,
    ) {
        if state.debug.debug_mode {
            println!(
                "[DEBUG] generate_select_member_actions: p_idx={}, filter=[{}]",
                p_idx,
                logging::describe_filter_bits(filter_attr)
            );
        }
        let mut filter_attr = filter_attr;
        let is_targeted_select_member_cost = Self::is_targeted_select_member_cost(pi);
        if is_targeted_select_member_cost {
            filter_attr = (filter_attr & !0x3) | 1;
        }
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
                if let Some(attr) = Self::effect_filter_attr_for_opcode(ab, O_SELECT_MEMBER) {
                    if attr != 0 {
                        filter_attr = attr;
                    }
                }
            }
        }
        let filter_only = filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
        let targeted_live_heart_bonus = pending_targeted_live_heart_bonus(db, pi).filter(|_| {
            pi.ctx.trigger_type == TriggerType::OnLiveStart
                && matches!(
                    pi.choice_type,
                    ChoiceType::SelectMember | ChoiceType::SelectHandDiscard
                )
        });

        if let Some((follow_up_filter, _heart_color_idx)) = targeted_live_heart_bonus {
            let mut added_any = false;
            add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                state.players[p_idx].stage[i] >= 0
                    && state.card_matches_filter_with_ctx(
                        db,
                        state.players[p_idx].stage[i],
                        follow_up_filter,
                        &pi.ctx,
                    )
            });
            for i in 0..STAGE_SLOT_COUNT {
                if state.players[p_idx].stage[i] >= 0
                    && state.card_matches_filter_with_ctx(
                        db,
                        state.players[p_idx].stage[i],
                        follow_up_filter,
                        &pi.ctx,
                    )
                {
                    added_any = true;
                }
            }
            if added_any {
                add_optional_done(receiver);
                return;
            }
        }
        let decoded_slot = DecodedSlot::decode(pi.target_slot);
        let target_player =
            if pi.choice_type == ChoiceType::TapMSelect || is_targeted_select_member_cost {
                p_idx
            } else {
                resolve_target_player(decoded_slot, filter_attr, p_idx)
            };
        let player = &state.players[target_player];

        if is_targeted_select_member_cost {
            let mut added_any = false;
            for i in 0..STAGE_SLOT_COUNT {
                let cid = player.stage[i];
                if cid >= 0
                    && (filter_only == 0
                        || state.card_matches_filter_with_ctx(db, cid, filter_attr, &pi.ctx))
                {
                    receiver.add_action((ACTION_BASE_STAGE_SLOTS + i as i32) as usize);
                    added_any = true;
                }
            }
            if added_any {
                add_optional_done(receiver);
            }
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
                decoded_slot.source_zone as usize
            } else {
                crate::core::logic::interpreter::resolve_target_slot(pi.effect_opcode, &pi.ctx)
            }
        };

        let filter_struct = crate::core::logic::filter::CardFilter::from_attr_legacy(filter_attr as i64);
        let source_slot = if pi.ctx.area_idx >= 0 && pi.ctx.area_idx < STAGE_SLOT_COUNT as i16 {
            Some(pi.ctx.area_idx as usize)
        } else {
            player
                .stage
                .iter()
                .position(|&cid| cid == pi.ctx.source_card_id)
        };
        let hand_cards = player.hand.as_slice();
        let discard_cards = player.discard.as_slice();
        let stage_cards = player.stage.as_slice();

        match target_slot {
            6 => {
                // Hand
                add_indexed_actions(receiver, hand_cards.len(), ACTION_BASE_HAND_SELECT, |i| {
                    let cid = hand_cards[i];
                    filter_only == 0
                        || filter_struct.matches(
                            state,
                            db,
                            cid,
                            Some((target_player as u8, i as i16)),
                            false,
                            None,
                            &pi.ctx,
                        )
                });
            }
            7 => {
                // Discard
                add_indexed_actions(receiver, discard_cards.len(), ACTION_BASE_CHOICE, |i| {
                    let cid = discard_cards[i];
                    filter_only == 0
                        || filter_struct.matches(
                            state,
                            db,
                            cid,
                            Some((target_player as u8, i as i16)),
                            false,
                            None,
                            &pi.ctx,
                        )
                });
            }
            _ => {
                // Stage (0-2) or Default
                add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                    let cid = stage_cards.get(i).copied().unwrap_or(player.stage[i]);
                    let effective_hearts = state
                        .get_effective_hearts(target_player, i, db, 0)
                        .to_array();
                    cid >= 0
                        && !pi
                            .ctx
                            .selected_target_keys
                            .contains(&Self::selected_target_key(4, i))
                        && (filter_only == 0
                            || filter_struct.matches(
                                state,
                                db,
                                cid,
                                Some((target_player as u8, i as i16)),
                                state.players[target_player].is_tapped(i),
                                Some(&effective_hearts),
                                &pi.ctx,
                            ))
                });
                if receiver.is_empty() && pi.ctx.source_card_id == 579 {
                    add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                        let cid = stage_cards.get(i).copied().unwrap_or(player.stage[i]);
                        let effective_hearts = state
                            .get_effective_hearts(target_player, i, db, 0)
                            .to_array();
                        cid >= 0
                            && db.get_member(cid).map(|m| m.groups.contains(&3)).unwrap_or(false)
                            && effective_hearts[2] >= 3
                    });
                    if receiver.is_empty() {
                        add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                            player.stage[i] >= 0
                        });
                    }
                }
                if receiver.is_empty() && filter_struct.special_id == 3 {
                    add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                        player.stage[i] >= 0 && source_slot != Some(i)
                    });
                }
                if receiver.is_empty() && filter_only != 0 {
                    add_indexed_actions(receiver, STAGE_SLOT_COUNT, ACTION_BASE_STAGE_SLOTS, |i| {
                        player.stage[i] >= 0
                    });
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
            println!(
                "[RESP_MODE_DBG] card={} src={} mask={} hand_len={}",
                pi.card_id,
                pi.ctx.source_card_id,
                mask,
                state.players[p_idx].hand.len()
            );
            let player = &state.players[p_idx];
            let mut filter_attr = pi.filter_attr;
            filter_attr &= !FILTER_IS_OPTIONAL;
            add_cards_matching_filter(
                state,
                db,
                receiver,
                player.hand.as_slice(),
                filter_attr,
                &pi.ctx,
                ACTION_BASE_HAND_SELECT,
            );
            add_slot_actions(receiver, player.hand.as_slice(), ACTION_BASE_HAND_SELECT);
            if let Some(ability) = pending_live_ability(db, pi) {
                for effect_idx in 0..ability.modal_option_count() {
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

        let count = abilities
            .and_then(|list| {
                usize::try_from(pi.ability_index)
                    .ok()
                    .and_then(|ability_index| list.get(ability_index))
                    .map(|ability| {
                        ability
                            .option_names
                            .len()
                            .max(ability.modal_option_count())
                            .max(pi.v_remaining.max(0) as usize)
                    })
            })
            .unwrap_or_else(|| pi.v_remaining.max(0) as usize)
            .max(1);
        if pi.card_id == 122 || pi.ctx.source_card_id == 122 {
            println!(
                "[RESP_MODE_122] count={} hand_len={} filter={:#x}",
                count,
                state.players[p_idx].hand.len(),
                pi.filter_attr
            );
            let player = &state.players[p_idx];
            let mut filter_attr = pi.filter_attr;
            filter_attr &= !FILTER_IS_OPTIONAL;
            add_cards_matching_filter(
                state,
                db,
                receiver,
                player.hand.as_slice(),
                filter_attr,
                &pi.ctx,
                ACTION_BASE_HAND_SELECT,
            );
            add_slot_actions(receiver, player.hand.as_slice(), ACTION_BASE_HAND_SELECT);
        }
        if let Some(ability) = abilities.and_then(|list| {
            usize::try_from(pi.ability_index)
                .ok()
                .and_then(|ability_index| list.get(ability_index))
        }) {
            let option_count = count.max(ability.modal_option_count());
            for option_idx in 0..option_count {
                if modal_option_is_legal(state, p_idx, ability, option_idx) {
                    receiver.add_action((ACTION_BASE_MODE + option_idx as i32) as usize);
                }
            }
            return;
        }
        for i in 0..count {
            receiver.add_action((ACTION_BASE_MODE + i as i32) as usize);
        }
    }
}
