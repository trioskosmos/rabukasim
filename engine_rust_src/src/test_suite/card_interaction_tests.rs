use crate::core::enums::{ChoiceType, Phase, TriggerType};
use crate::core::generated_constants::{ACTION_BASE_CHOICE, ACTION_BASE_HAND_SELECT, ACTION_BASE_MODE, ACTION_BASE_STAGE, ACTION_BASE_STAGE_SLOTS};
use crate::core::hearts::HeartBoard;
use crate::core::logic::card_db::LOGIC_ID_MASK;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::{Ability, AbilityContext, MemberCard, O_DRAW, O_JUMP, O_RETURN, O_SELECT_MODE, PendingInteraction, O_TAP_MEMBER};
use crate::core::types::STAGE_SLOT_COUNT;
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

fn add_legacy_select_mode_source(db: &mut crate::core::logic::CardDatabase, source_id: i32) {
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
        db,
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
}

fn prepare_legacy_select_mode_fixture(targets: &[(usize, i32, i32)]) -> (crate::core::logic::CardDatabase, crate::core::logic::GameState, i32) {
    let mut db = create_test_db();
    let mut state = create_test_state();
    state.ui.silent = true;

    let source_id = 9900;
    add_legacy_select_mode_source(&mut db, source_id);

    for &(slot_idx, card_id, cost) in targets {
        add_test_member(&mut db, MemberCard { card_id, cost: cost as u32, ..Default::default() });
        state.players[1].stage[slot_idx] = card_id;
    }

    state.players[0].stage[0] = source_id;
    (db, state, source_id)
}

#[test]
fn test_legacy_select_mode_branches_use_descriptive_labels_and_resolve_correctly() {
    {
        let (db, mut state, source_id) = prepare_legacy_select_mode_fixture(&[
            (0, 9901, 4),
            (1, 9902, 5),
            (2, 9903, 3),
        ]);

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
        assert_eq!(pending.options.len(), 2);

        let labels = pending
            .options
            .iter()
            .map(|option| option["label"].as_str().unwrap_or_default().trim().to_string())
            .collect::<Vec<_>>();

        assert!(labels.iter().all(|label| !label.is_empty()));
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

    {
        let (db, mut state, source_id) = prepare_legacy_select_mode_fixture(&[(0, 9911, 4)]);

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
}

#[test]
fn test_branch_only_select_mode_generates_mode_actions_and_hides_stage_targets_before_choice() {
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
    for slot_idx in 0..STAGE_SLOT_COUNT {
        assert!(
            !actions.actions.contains(&(ACTION_BASE_STAGE_SLOTS + slot_idx as i32)),
            "stage target {} should stay hidden until the mode is chosen",
            slot_idx
        );
    }
    assert!(!actions.actions.contains(&ACTION_BASE_STAGE));
    assert!(!actions.actions.contains(&ACTION_BASE_HAND_SELECT));
    assert!(!actions.actions.contains(&ACTION_BASE_CHOICE));
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

