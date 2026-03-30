#[cfg(test)]
mod tests {
    use crate::core::enums::Zone;
    use crate::core::generated_constants::O_PLACE_ENERGY_UNDER_MEMBER;
    use crate::core::logic::*;
    use crate::test_helpers::{create_test_db, create_test_state, FrameBuilder};

    fn opcode_97_frames(target_slot: u8) -> Vec<AbilityFrame> {
        FrameBuilder::new()
            .op(O_PLACE_ENERGY_UNDER_MEMBER)
            .v(1)
            .a(0)
            .source(Zone::Energy)
            .s(target_slot as i32)
            .op(O_RETURN)
            .build()
    }

    fn run_opcode_97(
        state: &mut GameState,
        db: &CardDatabase,
        ctx: &AbilityContext,
        target_slot: u8,
    ) {
        let frames = opcode_97_frames(target_slot);
        state.resolve_semantic_frames(db, &frames, ctx);
    }

    fn setup_state(stage_slot: usize, source_card_id: i32) -> GameState {
        let mut state = create_test_state();
        state.players[0].player_id = 0;
        state.players[0].stage = [-1; 3];
        for slot in 0..3 {
            state.players[0].stage_energy[slot].clear();
        }
        state.players[0].energy_zone.clear();
        state.players[0].stage[stage_slot] = source_card_id;
        state.players[0].energy_zone.push(9001);
        state
    }

    #[test]
    fn test_opcode_97_self_and_member_self_use_area_idx() {
        let db = create_test_db();

        for target_slot in [0u8, 4u8] {
            let mut state = setup_state(1, 5001);
            let ctx = AbilityContext {
                player_id: 0,
                source_card_id: 5001,
                activator_id: 0,
                area_idx: 1,
                target_slot: -1,
                ..Default::default()
            };

            run_opcode_97(&mut state, &db, &ctx, target_slot);

            assert_eq!(
                state.players[0].stage_energy[1].len(),
                1,
                "opcode 97 with target_slot={} should place energy under the triggering member",
                target_slot
            );
            assert_eq!(state.players[0].stage_energy[0].len(), 0);
            assert_eq!(state.players[0].stage_energy[2].len(), 0);
            assert_eq!(state.players[0].energy_zone.len(), 0);
        }
    }

    #[test]
    fn test_opcode_97_explicit_stage_slot_ignores_area_idx() {
        let db = create_test_db();
        let mut state = setup_state(0, 5002);
        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 5002,
            activator_id: 0,
            area_idx: 0,
            target_slot: -1,
            ..Default::default()
        };

        run_opcode_97(&mut state, &db, &ctx, 1);

        assert_eq!(state.players[0].stage_energy[0].len(), 0);
        assert_eq!(state.players[0].stage_energy[1].len(), 1);
        assert_eq!(state.players[0].stage_energy[2].len(), 0);
        assert_eq!(state.players[0].energy_zone.len(), 0);
    }

    #[test]
    fn test_opcode_97_member_select_uses_ctx_target_slot() {
        let db = create_test_db();
        let mut state = setup_state(0, 5003);
        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 5003,
            activator_id: 0,
            area_idx: 0,
            target_slot: 2,
            ..Default::default()
        };

        run_opcode_97(&mut state, &db, &ctx, 10);

        assert_eq!(state.players[0].stage_energy[0].len(), 0);
        assert_eq!(state.players[0].stage_energy[1].len(), 0);
        assert_eq!(state.players[0].stage_energy[2].len(), 1);
        assert_eq!(state.players[0].energy_zone.len(), 0);
    }

    #[test]
    fn test_opcode_97_out_of_range_slot_noops() {
        let db = create_test_db();
        let mut state = setup_state(1, 5004);
        let initial_energy_len = state.players[0].energy_zone.len();
        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 5004,
            activator_id: 0,
            area_idx: 1,
            target_slot: -1,
            ..Default::default()
        };

        run_opcode_97(&mut state, &db, &ctx, 7);

        assert_eq!(state.players[0].energy_zone.len(), initial_energy_len);
        assert_eq!(state.players[0].stage_energy[0].len(), 0);
        assert_eq!(state.players[0].stage_energy[1].len(), 0);
        assert_eq!(state.players[0].stage_energy[2].len(), 0);
    }
}
