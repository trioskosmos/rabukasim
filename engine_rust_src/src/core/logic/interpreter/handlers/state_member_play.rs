use super::*;

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_hand(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
) -> HandlerResult {
    let remaining = if ctx.v_remaining == -1 {
        if v == 1 {
            1
        } else {
            2
        }
    } else {
        ctx.v_remaining
    };

    if remaining == 2 {
        if ctx.choice_index == -1 {
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_PLAY_MEMBER_FROM_HAND,
                0,
                ChoiceType::SelectHandPlay,
                "",
                a as u64,
                remaining,
            ) {
                return HandlerResult::Suspend;
            }
        }
        let h_idx = ctx.choice_index as usize;
        if h_idx < state.players[p_idx].hand.len() {
            ctx.target_slot = h_idx as i16;
            ctx.v_remaining = 1;
            ctx.choice_index = -1;
            return handle_play_member_from_hand(state, db, ctx, instr, instr_ip, p_idx, v, a, s);
        }
    } else if remaining == 1 {
        if ctx.choice_index == -1 {
            let mut next_ctx = ctx.clone();
            next_ctx.player_id = p_idx as u8;
            if suspend_interaction(
                state,
                db,
                &next_ctx,
                instr_ip,
                O_PLAY_MEMBER_FROM_HAND,
                s,
                ChoiceType::SelectStage,
                "",
                a as u64,
                remaining,
            ) {
                return HandlerResult::Suspend;
            }
        }

        let slot_idx = ctx.choice_index as usize;
        if slot_idx < 3 {
            let h_idx = ctx.target_slot as usize;
            if h_idx < state.players[p_idx].hand.len() {
                let Some(cid) = state.players[p_idx].remove_hand_card(h_idx) else {
                    return HandlerResult::Continue;
                };
                if let Some(old) = state.handle_member_leaves_stage(p_idx, slot_idx, db, ctx) {
                    state.players[p_idx].push_discard_card(old);
                }
                state.players[p_idx].stage[slot_idx] = cid;
                state.players[p_idx].set_tapped(slot_idx, false);
                state.players[p_idx].set_moved(slot_idx, true);
                state.register_played_member(p_idx, cid, db);

                let new_ctx = AbilityContext {
                    source_card_id: cid,
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: slot_idx as i16,
                    ..Default::default()
                };
                state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                ctx.choice_index = -1;
                ctx.v_remaining = 0;
                return HandlerResult::Continue;
            }
        }
    }

    HandlerResult::Continue
}

#[allow(clippy::too_many_arguments)]
pub fn handle_play_member_from_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    p_idx: usize,
    v: i32,
    a: i64,
    s: i32,
    target_slot: i32,
    resolved_slot: i32,
) -> HandlerResult {
    // Distinguish legacy vs modern:
    // Nico (Legacy): a=1 or 2, s=filter_attr
    // Modern: a=filter_attr, s=flags
    let (filter_attr_base, target_p_idx) = if a >= 1 && a <= 2 && (s as u32) > 1000 {
        (
            0, // Legacy player-targeted variant often lacks explicit filter in bytecode, s contains flags.
            if a == 2 {
                1 - (ctx.activator_id as usize)
            } else {
                ctx.activator_id as usize
            },
        )
    } else {
        let filter_target = (a as u64) & 0x03;
        let is_opp = filter_target == 2 || instr.slot().is_opponent;
        let t_idx = if is_opp {
            1 - (ctx.activator_id as usize)
        } else {
            ctx.activator_id as usize
        };
        (a as u64, t_idx)
    };

    let empty_slot_only = ((s as u64) & FLAG_EMPTY_SLOT_ONLY) != 0;
    let baton_slot_only = ((s as u64) & FLAG_BATON_SLOT_ONLY) != 0;

    // Total Cost detection:
    // Support modern bit 60 (compare_accumulated)
    // Support legacy bit 50 (FILTER_TOTAL_COST)
    // Support bit 31 (FILTER_COST_TYPE_FLAG) + bit 30 (FILTER_COST_LE) for legacy compiled cards
    let is_total_cost = (filter_attr_base & (1u64 << 60)) != 0
        || (filter_attr_base & (1u64 << 50)) != 0
        || ((filter_attr_base & FILTER_COST_TYPE_FLAG) != 0 && (filter_attr_base & 1073741824) != 0);

    let mut remaining = if ctx.v_remaining == -1 {
        if is_total_cost {
            ctx.v_accumulated =
                ((filter_attr_base >> crate::core::logic::constants::FILTER_VALUE_THRESHOLD_SHIFT)
                    & 0x1F) as i16;
        }
        v as i16 * 2
    } else {
        ctx.v_remaining
    };

    if remaining <= 0 {
        return HandlerResult::Continue;
    }

    if remaining % 2 == 0 {
        // Card Selection Step (4, 2, ...)
        if empty_slot_only && state.players[target_p_idx].stage.iter().all(|&c| c >= 0) {
            return HandlerResult::Continue;
        }

        // IMPORTANT: Always clear looked_cards if we are STARTING a new pick.
        if ctx.choice_index == -1 {
            state.players[target_p_idx].looked_cards.clear();
        }

        if state.players[target_p_idx].looked_cards.is_empty() {
            let mut filter_attr = filter_attr_base;
            if is_total_cost {
                // Ensure bit 60 is set so CardFilter::matches uses ctx.v_accumulated
                filter_attr |= 1u64 << 60;
            }
            let matched_ids: Vec<i32> = state.players[target_p_idx]
                .discard
                .iter()
                .filter(|&&cid| {
                    db.get_member(cid).is_some()
                        && (filter_attr == 0 || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx))
                })
                .cloned()
                .collect();
            state.players[target_p_idx].looked_cards.extend(matched_ids);
            if state.players[target_p_idx].looked_cards.is_empty() {
                return HandlerResult::Continue;
            }

            let mut target_ctx = ctx.clone();
            target_ctx.player_id = target_p_idx as u8;
            target_ctx.v_remaining = remaining;
            target_ctx.v_accumulated = ctx.v_accumulated;
            target_ctx.choice_index = -1; // Standard reset for suspension

            let choice_text = get_choice_text(db, &target_ctx);
            if suspend_interaction(
                state,
                db,
                &target_ctx,
                instr_ip,
                O_PLAY_MEMBER_FROM_DISCARD,
                s,
                ChoiceType::SelectDiscardPlay,
                &choice_text,
                filter_attr,
                remaining,
            ) {
                return HandlerResult::Suspend;
            }
        }
        let idx = ctx.choice_index as usize;
        let cards_len = state.players[target_p_idx].looked_cards.len();

        if idx < cards_len {
            let cid = state.players[target_p_idx].looked_cards[idx];
            state.players[target_p_idx].looked_cards.clear();
            state.players[target_p_idx].looked_cards.push(cid);

            remaining -= 1;
            let mut target_ctx = ctx.clone();
            target_ctx.player_id = target_p_idx as u8;
            target_ctx.v_remaining = remaining;
            target_ctx.v_accumulated = ctx.v_accumulated;
            target_ctx.choice_index = -1; // CRITICAL FIX: Reset choice_index so SelectStage doesn't reuse the card index

            let choice_type = if baton_slot_only {
                ChoiceType::SelectStageEmptyBaton
            } else if empty_slot_only {
                ChoiceType::SelectStageEmpty
            } else {
                ChoiceType::SelectStage
            };
            if suspend_interaction(
                state,
                db,
                &target_ctx,
                instr_ip,
                O_PLAY_MEMBER_FROM_DISCARD,
                s,
                choice_type,
                "",
                filter_attr_base,
                remaining,
            ) {
                return HandlerResult::Suspend;
            }
        }
    } else {
        // Card Placement Step (3, 1, ...)
        if state.players[target_p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }
        let card_id = state.players[target_p_idx].looked_cards.remove(0);

        if ctx.choice_index == 99 {
            return HandlerResult::Continue;
        }

        let resolved_slot = if ctx.choice_index >= 600 && ctx.choice_index < 603 {
            ctx.choice_index - 600
        } else if ctx.choice_index >= 10 && ctx.choice_index < 13 {
            ctx.choice_index - 10
        } else {
            ctx.choice_index
        };

        if let Some(pos) = state.players[target_p_idx]
            .discard
            .iter()
            .position(|&cid| cid == card_id)
        {
            let slot_idx = if ctx.choice_index >= 0 && ctx.choice_index < 3 {
                ctx.choice_index as usize
            } else {
                resolved_slot as usize
            };

            if slot_idx < 3 {
                if (state.players[target_p_idx].prevent_play_to_slot_mask & (1 << slot_idx)) != 0
                    || (empty_slot_only && state.players[target_p_idx].stage[slot_idx] != -1)
                {
                    return HandlerResult::Continue;
                }

                if is_total_cost {
                    if let Some(m) = db.get_member(card_id) {
                        ctx.v_accumulated = (ctx.v_accumulated - m.cost as i16).max(0);
                    }
                }

                let pos = pos as usize;
                state.players[target_p_idx].remove_discard_card(pos);
                if let Some(old) = state.handle_member_leaves_stage(target_p_idx, slot_idx, db, ctx)
                {
                    state.players[target_p_idx].push_discard_card(old);
                }
                state.players[target_p_idx].stage[slot_idx] = card_id;
                state.players[target_p_idx].set_tapped(slot_idx, true);
                state.players[target_p_idx].set_moved(slot_idx, true);
                state.register_played_member(target_p_idx, card_id, db);
                state.players[target_p_idx].prevent_play_to_slot_mask |= 1 << slot_idx;

                // Cards placed in WAIT state from discard should not trigger OnPlay abilities
                // since they were not actually "played" - they were summoned in a tapped state.
                // The Rule 8.8.1 states: "Members summoned in WAIT state do not trigger abilities."
            }
        }

        remaining -= 1;
        ctx.v_remaining = remaining;
        if remaining > 0 {
            ctx.choice_index = -1; // Reset for the NEXT pick step (crucial for budget re-evaluation)
            return HandlerResult::Branch(instr_ip);
        }
    }

    HandlerResult::Continue
}
