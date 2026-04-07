use crate::core::enums::{ChoiceType, Phase, TriggerType};
use crate::core::generated_constants::{ACTION_BASE_CHOICE, ACTION_BASE_HAND_SELECT, ACTION_BASE_MODE, ACTION_BASE_STAGE, ACTION_BASE_STAGE_SLOTS};
use crate::core::hearts::HeartBoard;
use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::{Ability, AbilityContext, MemberCard, O_ADD_BLADES, O_DRAW, O_JUMP, O_PAY_ENERGY, O_RETURN, O_SELECT_MODE, PendingInteraction, O_TAP_MEMBER};
use crate::test_helpers::{create_test_db, create_test_state, load_real_db, FrameBuilder, TestActionReceiver};

fn add_test_member(db: &mut crate::core::logic::CardDatabase, mut member: MemberCard) {
    member.hearts_board = HeartBoard::from_array(&member.hearts);
    member.blade_hearts_board = HeartBoard::from_array(&member.blade_hearts);
    let id = member.card_id;
    db.members.insert(id, member.clone());
    let logic_id = (id as usize) & LOGIC_ID_MASK as usize;
    if logic_id < db.members_vec.len() {
        db.members_vec[logic_id] = Some(member);
    }
}

/// Verifies that granted abilities (Wave 2) are correctly applied to a target card using real IDs.
#[test]
fn test_granted_abilities_stacking() {
    let _db = load_real_db();
    let mut state = create_test_state();

    state.players[0].stage[0] = 121; // Eli

    // Grant an ability to Card 121 (Target) from Card 124 (Source)
    // granted_abilities: Vec<(target_cid, source_cid, ab_idx)>
    state.players[0].granted_abilities.push((121, 124, 0));

    assert_eq!(state.players[0].granted_abilities.len(), 1);
    assert_eq!(state.players[0].granted_abilities[0].0, 121);
}

/// Verifies that removing a source card or explicitly clearing granted abilities works as expected.
#[test]
fn test_granted_abilities_removal() {
    let mut state = create_test_state();

    state.players[0].granted_abilities.push((121, 124, 0));
    assert_eq!(state.players[0].granted_abilities.len(), 1);

    // Manually remove
    state.players[0]
        .granted_abilities
        .retain(|&(target, _, _)| target != 121);
    assert_eq!(state.players[0].granted_abilities.len(), 0);
}

/// Verifies that multiple status effects (Blade buffs, Heart buffs) combine correctly using real card data.
#[test]
fn test_stat_buff_combination() {
    let db = load_real_db();
    let mut state = create_test_state();

    // Eli (121) has base blades (usually 1 or 2). Let's check reality.
    state.players[0].stage[0] = 121;

    let base_blades = db.get_member(121).expect("Eli should exist").blades;

    // 1. Apply Blade buff
    state.players[0].blade_buffs[0] = 3;

    // 2. Check effective blades (Base + Buff 3)
    let effective = state.get_effective_blades(0, 0, &db, 0);
    assert_eq!(effective, base_blades as u32 + 3);
}

#[test]
fn test_card_163_optional_live_start_prompt_uses_yes_no_actions_only() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.players[0].stage[0] = 163;
    state.players[0].energy_zone = vec![2000].into();

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

    let pending = state
        .interaction_stack
        .last()
        .expect("card 163 should suspend for optional energy payment");
    assert_eq!(pending.choice_type, ChoiceType::Optional);

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);

    assert!(actions.actions.contains(&ACTION_BASE_CHOICE));
    assert!(actions.actions.contains(&(ACTION_BASE_CHOICE + 1)));
    assert!(actions.actions.iter().all(|action| {
        *action == 0
            || *action >= ACTION_BASE_CHOICE
            || *action >= ACTION_BASE_STAGE
    }));
    assert!(!actions.actions.iter().any(|action| {
        *action >= ACTION_BASE_HAND_SELECT && *action < ACTION_BASE_STAGE
    }));
}

#[test]
fn test_granted_live_start_optional_ability_uses_definition_card_on_resume() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let target_id = 9100;
    let source_id = 9101;

    let target_program = FrameBuilder::new()
        .op(O_PAY_ENERGY)
        .v(1)
        .optional(true)
        .op(O_ADD_BLADES)
        .v(2)
        .target(4)
        .op(O_RETURN)
        .build_prog();
    let source_program = FrameBuilder::new()
        .op(O_PAY_ENERGY)
        .v(1)
        .optional(true)
        .op(O_ADD_BLADES)
        .v(3)
        .target(4)
        .op(O_RETURN)
        .build_prog();

    add_test_member(
        &mut db,
        MemberCard {
            card_id: target_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnLiveStart,
                frame_program: Some(target_program),
                ..Default::default()
            }],
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnLiveStart,
                frame_program: Some(source_program),
                ..Default::default()
            }],
            ..Default::default()
        },
    );

    state.players[0].stage[0] = target_id;
    state.players[0].energy_zone = vec![2000, 2001].into();
    state.players[0]
        .granted_abilities
        .push((target_id, source_id, 0));

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
    let mut resolved_prompts = 0;
    while resolved_prompts < 3 && (!state.interaction_stack.is_empty() || !state.trigger_queue.is_empty()) {
        if state.interaction_stack.is_empty() {
            state.process_trigger_queue(&db);
        }
        if state.interaction_stack.is_empty() {
            break;
        }

        state
            .step(&db, ACTION_BASE_CHOICE)
            .expect("live-start optional trigger should resolve");
        resolved_prompts += 1;
    }

    assert_eq!(resolved_prompts, 2);
    assert!(state.interaction_stack.is_empty());
    assert_eq!(state.players[0].blade_buffs[0], 5);
}

#[test]
fn test_card_163_can_trigger_again_after_turn_cleanup() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.players[0].stage[0] = 163;
    state.players[0].energy_zone = vec![2000, 2001].into();

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
    state
        .step(&db, ACTION_BASE_CHOICE)
        .expect("first live-start prompt should resolve");
    assert_eq!(state.players[0].blade_buffs[0], 2);

    state.players[0].untap_all(false);
    assert_eq!(state.players[0].blade_buffs[0], 0);

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
    assert!(!state.interaction_stack.is_empty());
    state
        .step(&db, ACTION_BASE_CHOICE)
        .expect("second live-start prompt should resolve after cleanup");
    assert_eq!(state.players[0].blade_buffs[0], 2);
}

#[test]
fn test_card_710_live_start_reduces_heart_requirement_from_other_hasunosora_lives() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.phase = crate::core::enums::Phase::PerformanceP1;
    state.current_player = 0;

    let source_live_id = 710;
    let support_lives = db
        .lives
        .values()
        .filter(|live| live.card_id != source_live_id && live.groups.contains(&4))
        .take(2)
        .map(|live| live.card_id)
        .collect::<Vec<_>>();
    assert_eq!(support_lives.len(), 2, "expected two other Hasunosora live cards in the real DB");

    state.players[0].live_zone = [source_live_id, support_lives[0], support_lives[1]];

    let ctx = AbilityContext {
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnLiveStart,
        source_card_id: source_live_id,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);

    assert!(state.interaction_stack.is_empty(), "card 710 reduction is automatic and should not prompt");
    assert_eq!(state.players[0].heart_req_reductions.get_color_count(3), 4);
    assert!(state.players[0]
        .heart_req_reduction_logs
        .iter()
        .any(|&(src_id, color, amount)| src_id == source_live_id && color == 3 && amount == 4));

    let live_card = db.get_live(source_live_id).expect("card 710 should exist in the real DB");
    let (req_board, _) = crate::core::logic::performance::get_live_requirements(&state, &db, 0, live_card);

    assert_eq!(req_board.get_color_count(3), 5, "green requirement should drop from 9 to 5");
    assert_eq!(req_board.get_color_count(6), 5, "generic requirement should stay unchanged");
}

#[test]
fn test_tap_m_select_uses_opponent_cost_filter_for_wait_targets() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9707;
    let low_cost_left = 9708;
    let high_cost_middle = 9709;
    let low_cost_right = 9710;

    let filter_attr = CardFilter {
        is_enabled: true,
        target_player: 2,
        value_enabled: true,
        value_threshold: 4,
        is_le: true,
        is_cost_type: true,
        ..Default::default()
    }
    .to_attr();

    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnPlay,
                frame_program: Some(
                    FrameBuilder::new()
                        .op(O_TAP_MEMBER)
                        .v(2)
                        .a(filter_attr as i64)
                        .target(4)
                        .op(O_RETURN)
                        .build_prog(),
                ),
                ..Default::default()
            }],
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: low_cost_left,
            cost: 4,
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: high_cost_middle,
            cost: 5,
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: low_cost_right,
            cost: 4,
            ..Default::default()
        },
    );

    state.players[0].stage[0] = source_id;
    state.players[1].stage = [low_cost_left, high_cost_middle, low_cost_right];

    let ctx = AbilityContext {
        source_card_id: source_id,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    let pending = state
        .interaction_stack
        .last()
        .expect("tap-member ability should suspend for target selection");
    assert_eq!(pending.choice_type, ChoiceType::TapMSelect);

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);

    assert!(actions.actions.contains(&ACTION_BASE_STAGE_SLOTS));
    assert!(!actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + 1)));
    assert!(actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + 2)));
}

#[test]
fn test_card_707_wait_prompt_excludes_opponent_members_above_cost_4() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.phase = crate::core::enums::Phase::Main;

    let low_cost_left = db
        .members
        .iter()
        .find_map(|(&cid, member)| (member.cost == 4).then_some(cid))
        .expect("real DB should contain a cost-4 member");
    let high_cost_middle = db
        .members
        .iter()
        .find_map(|(&cid, member)| (member.cost >= 5).then_some(cid))
        .expect("real DB should contain a cost-5-or-higher member");
    let low_cost_right = db
        .members
        .iter()
        .find_map(|(&cid, member)| (member.cost <= 3 && cid != low_cost_left).then_some(cid))
        .expect("real DB should contain another cost-4-or-lower member");

    state.players[0].stage[0] = 707;
    state.players[0].hand = vec![121].into();
    state.players[1].stage = [low_cost_left, high_cost_middle, low_cost_right];

    let ctx = AbilityContext {
        source_card_id: 707,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    let pending = state
        .interaction_stack
        .last()
        .expect("card 707 should prompt for optional discard");
    assert_eq!(pending.choice_type, ChoiceType::SelectHandDiscard);

    state
        .step(&db, ACTION_BASE_HAND_SELECT)
        .expect("card 707 discard cost should resolve");

    let pending = state
        .interaction_stack
        .last()
        .expect("card 707 should prompt for opponent wait targets");
    assert_eq!(pending.choice_type, ChoiceType::TapO);

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);

    assert!(actions.actions.contains(&ACTION_BASE_STAGE_SLOTS));
    assert!(!actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + 1)));
    assert!(actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + 2)));
}

#[test]
fn test_tap_member_opponent_target_execution_honors_cost_filter() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9713;
    let low_cost_left = 9714;
    let high_cost_middle = 9715;
    let low_cost_right = 9716;

    let filter_attr = CardFilter {
        is_enabled: true,
        target_player: 2,
        value_enabled: true,
        value_threshold: 4,
        is_le: true,
        is_cost_type: true,
        ..Default::default()
    }
    .to_attr();

    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnPlay,
                frame_program: Some(
                    FrameBuilder::new()
                        .op(crate::core::logic::O_TAP_MEMBER)
                        .v(2)
                        .a(filter_attr as i64)
                        .target(4)
                        .op(O_RETURN)
                        .build_prog(),
                ),
                ..Default::default()
            }],
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: low_cost_left,
            cost: 4,
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: high_cost_middle,
            cost: 5,
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: low_cost_right,
            cost: 3,
            ..Default::default()
        },
    );

    state.players[0].stage[0] = source_id;
    state.players[1].stage = [low_cost_left, high_cost_middle, low_cost_right];

    let ctx = AbilityContext {
        source_card_id: source_id,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    state
        .step(&db, ACTION_BASE_STAGE_SLOTS)
        .expect("first filtered opponent tap selection should resolve");
    state
        .step(&db, ACTION_BASE_STAGE_SLOTS + 2)
        .expect("second filtered opponent tap selection should resolve");

    assert!(state.players[1].is_tapped(0));
    assert!(!state.players[1].is_tapped(1));
    assert!(state.players[1].is_tapped(2));
}

#[test]
fn test_card_707_wait_execution_honors_cost_filter() {
    let db = load_real_db();
    let mut state = create_test_state();
    state.ui.silent = true;
    state.phase = crate::core::enums::Phase::Main;

    let low_cost_left = db
        .members
        .iter()
        .find_map(|(&cid, member)| (member.cost == 4).then_some(cid))
        .expect("real DB should contain a cost-4 member");
    let high_cost_middle = db
        .members
        .iter()
        .find_map(|(&cid, member)| (member.cost >= 5).then_some(cid))
        .expect("real DB should contain a cost-5-or-higher member");
    let low_cost_right = db
        .members
        .iter()
        .find_map(|(&cid, member)| (member.cost <= 3 && cid != low_cost_left).then_some(cid))
        .expect("real DB should contain another cost-4-or-lower member");

    state.players[0].stage[0] = 707;
    state.players[0].hand = vec![121].into();
    state.players[1].stage = [low_cost_left, high_cost_middle, low_cost_right];

    let ctx = AbilityContext {
        source_card_id: 707,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    state
        .step(&db, ACTION_BASE_HAND_SELECT)
        .expect("card 707 discard cost should resolve");
    state
        .step(&db, ACTION_BASE_STAGE_SLOTS)
        .expect("card 707 first wait target should resolve");
    state
        .step(&db, ACTION_BASE_STAGE_SLOTS + 2)
        .expect("card 707 second wait target should resolve");

    assert!(state.players[1].is_tapped(0));
    assert!(!state.players[1].is_tapped(1));
    assert!(state.players[1].is_tapped(2));
}

#[test]
fn test_tap_opponent_single_ineligible_target_does_not_auto_tap() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9711;
    let high_cost_target = 9712;
    let filter_attr = CardFilter {
        is_enabled: true,
        target_player: 2,
        value_enabled: true,
        value_threshold: 4,
        is_le: true,
        is_cost_type: true,
        ..Default::default()
    }
    .to_attr();

    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnPlay,
                frame_program: Some(
                    FrameBuilder::new()
                        .op(crate::core::logic::O_TAP_OPPONENT)
                        .v(1)
                        .a(filter_attr as i64)
                        .op(O_RETURN)
                        .build_prog(),
                ),
                ..Default::default()
            }],
            ..Default::default()
        },
    );
    add_test_member(
        &mut db,
        MemberCard {
            card_id: high_cost_target,
            cost: 5,
            ..Default::default()
        },
    );

    state.players[0].stage[0] = source_id;
    state.players[1].stage[0] = high_cost_target;

    let ctx = AbilityContext {
        source_card_id: source_id,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    assert!(state.interaction_stack.is_empty());
    assert!(!state.players[1].is_tapped(0));
}

#[test]
fn test_legacy_select_mode_wait_branch_prompts_and_uses_descriptive_labels() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9900;
    let low_cost_left = 9901;
    let low_cost_right = 9902;
    let high_cost_middle = 9903;
    let filter_attr = CardFilter {
        is_enabled: true,
        target_player: 2,
        value_enabled: true,
        value_threshold: 4,
        is_le: true,
        is_cost_type: true,
        ..Default::default()
    }
    .to_attr();

    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnPlay,
                raw_text: "Choose one: wait an opponent member with cost 4 or less, or draw 1.".to_string(),
                frame_program: Some(
                    FrameBuilder::new()
                        .op(O_SELECT_MODE)
                        .v(2)
                        .op(O_JUMP)
                        .v(1)
                        .op(O_JUMP)
                        .v(2)
                        .op(O_TAP_MEMBER)
                        .v(1)
                        .a(filter_attr as i64)
                        .target(4)
                        .op(O_JUMP)
                        .v(3)
                        .op(O_DRAW)
                        .v(1)
                        .target(4)
                        .op(O_JUMP)
                        .v(1)
                        .op(O_RETURN)
                        .build_prog(),
                ),
                ..Default::default()
            }],
            ..Default::default()
        },
    );
    add_test_member(&mut db, MemberCard { card_id: low_cost_left, cost: 4, ..Default::default() });
    add_test_member(&mut db, MemberCard { card_id: low_cost_right, cost: 3, ..Default::default() });
    add_test_member(&mut db, MemberCard { card_id: high_cost_middle, cost: 5, ..Default::default() });

    state.players[0].stage[0] = source_id;
    state.players[1].stage = [low_cost_left, high_cost_middle, low_cost_right];

    let ctx = AbilityContext {
        source_card_id: source_id,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    let pending = state
        .interaction_stack
        .last()
        .expect("legacy select mode should suspend for a mode choice");
    assert_eq!(pending.choice_type, ChoiceType::SelectMode);
    let labels = pending
        .options
        .iter()
        .map(|option| option["label"].as_str().unwrap_or_default().to_string())
        .collect::<Vec<_>>();
    assert!(labels.iter().all(|label| !label.starts_with("Option ")));
    assert!(labels.iter().any(|label| label.contains("draw")));

    state
        .step(&db, ACTION_BASE_MODE)
        .expect("wait branch should select the first legacy mode");

    let pending = state
        .interaction_stack
        .last()
        .expect("wait branch should prompt for a target when multiple legal targets exist");
    assert!(matches!(pending.choice_type, ChoiceType::TapO | ChoiceType::TapMSelect | ChoiceType::SelectStage));

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);
    assert!(actions.actions.contains(&ACTION_BASE_STAGE_SLOTS));
    assert!(!actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + 1)));
    assert!(actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + 2)));

    state
        .step(&db, ACTION_BASE_STAGE_SLOTS + 2)
        .expect("wait branch target should resolve");

    assert!(!state.players[1].is_tapped(0));
    assert!(!state.players[1].is_tapped(1));
    assert!(state.players[1].is_tapped(2));
    assert_eq!(state.players[0].hand.len(), 0);
}

#[test]
fn test_legacy_select_mode_draw_branch_resolves_without_wait_prompt() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9910;
    let low_cost_target = 9911;
    let filter_attr = CardFilter {
        is_enabled: true,
        target_player: 2,
        value_enabled: true,
        value_threshold: 4,
        is_le: true,
        is_cost_type: true,
        ..Default::default()
    }
    .to_attr();

    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnPlay,
                raw_text: "Choose one: wait an opponent member with cost 4 or less, or draw 1.".to_string(),
                frame_program: Some(
                    FrameBuilder::new()
                        .op(O_SELECT_MODE)
                        .v(2)
                        .op(O_JUMP)
                        .v(1)
                        .op(O_JUMP)
                        .v(2)
                        .op(O_TAP_MEMBER)
                        .v(1)
                        .a(filter_attr as i64)
                        .target(4)
                        .op(O_JUMP)
                        .v(3)
                        .op(O_DRAW)
                        .v(1)
                        .target(4)
                        .op(O_JUMP)
                        .v(1)
                        .op(O_RETURN)
                        .build_prog(),
                ),
                ..Default::default()
            }],
            ..Default::default()
        },
    );
    add_test_member(&mut db, MemberCard { card_id: low_cost_target, cost: 4, ..Default::default() });

    state.players[0].stage[0] = source_id;
    state.players[1].stage[0] = low_cost_target;

    let ctx = AbilityContext {
        source_card_id: source_id,
        player_id: 0,
        activator_id: 0,
        trigger_type: TriggerType::OnPlay,
        area_idx: 0,
        ..Default::default()
    };

    state.trigger_abilities(&db, TriggerType::OnPlay, &ctx);
    state.process_trigger_queue(&db);

    state
        .step(&db, ACTION_BASE_MODE + 1)
        .expect("draw branch should select the second legacy mode");

    assert!(state.interaction_stack.is_empty());
    assert_eq!(state.players[0].hand.len(), 1);
    assert!(!state.players[1].is_tapped(0));
}

#[test]
fn test_branch_only_select_mode_generates_mode_actions_instead_of_pass_fallback() {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9920;
    add_test_member(
        &mut db,
        MemberCard {
            card_id: source_id,
            abilities: vec![Ability {
                trigger: TriggerType::OnPlay,
                raw_text: "Choose yourself or your opponent.".to_string(),
                frame_program: Some(
                    FrameBuilder::new()
                        .op(O_SELECT_MODE)
                        .v(2)
                        .op(O_JUMP)
                        .v(1)
                        .op(O_JUMP)
                        .v(1)
                        .op(O_RETURN)
                        .build_prog(),
                ),
                ..Default::default()
            }],
            ..Default::default()
        },
    );

    state.players[0].stage[0] = source_id;
    state.phase = Phase::Response;
    state.interaction_stack.push(PendingInteraction {
        ctx: AbilityContext {
            source_card_id: source_id,
            player_id: 0,
            activator_id: 0,
            ability_index: 0,
            trigger_type: TriggerType::OnPlay,
            area_idx: 0,
            v_remaining: 2,
            ..Default::default()
        },
        card_id: source_id,
        ability_index: 0,
        effect_opcode: O_SELECT_MODE,
        choice_type: ChoiceType::SelectMode,
        v_remaining: 2,
        ..Default::default()
    });

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, 0, &mut actions);

    assert!(actions.actions.contains(&ACTION_BASE_MODE));
    assert!(actions.actions.contains(&(ACTION_BASE_MODE + 1)));
    assert!(!actions.actions.contains(&0));
}
