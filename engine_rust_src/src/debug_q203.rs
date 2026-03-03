use crate::core::logic::*;
use crate::test_helpers::*;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn debug_q203_trace() {
        let mut state = GameState::default();
        let db = load_real_db();

        let live_id = 358;
        let niji_member_id = 4430;

        state.debug.debug_mode = true;

        // 1. Verify card data
        let member = db.get_member(niji_member_id);
        println!("=== MEMBER LOOKUP ===");
        println!(
            "get_member({}) = {:?}",
            niji_member_id,
            member.map(|m| (&m.name, &m.groups, m.card_id))
        );

        let live = db.get_live(live_id);
        println!("=== LIVE LOOKUP ===");
        println!(
            "get_live({}) = {:?}",
            live_id,
            live.map(|l| (&l.name, l.card_id))
        );
        if let Some(l) = live {
            println!("Live abilities count: {}", l.abilities.len());
            if !l.abilities.is_empty() {
                println!("Ability 0 trigger: {:?}", l.abilities[0].trigger);
                println!("Ability 0 bytecode: {:?}", l.abilities[0].bytecode);
                println!(
                    "Ability 0 conditions count: {}",
                    l.abilities[0].conditions.len()
                );
            }
        }

        // 2. Setup state
        state.core.players[0].live_zone[0] = live_id;
        state.core.players[0].stage[0] = niji_member_id;
        for _ in 0..5 {
            state.core.players[0].energy_zone.push(3001);
        }
        state.core.players[0].set_energy_tapped(0, true);

        // 3. Call handle_energy
        println!("\n=== HANDLE_ENERGY ===");
        let mut ctx = AbilityContext {
            source_card_id: niji_member_id,
            player_id: 0,
            activator_id: 0,
            ..Default::default()
        };
        crate::core::logic::interpreter::handlers::handle_energy(
            &mut state, &db, &mut ctx, 81, 1, 0, 0, 0,
        );
        println!(
            "activated_energy_group_mask = {} (binary: {:b})",
            state.core.players[0].activated_energy_group_mask,
            state.core.players[0].activated_energy_group_mask
        );
        println!("Expected: bit 2 set = 4 (binary: 100)");
        assert!(
            (state.core.players[0].activated_energy_group_mask & (1 << 2)) != 0,
            "FAIL: Energy mask does NOT have bit 2 set! Actual: {}",
            state.core.players[0].activated_energy_group_mask
        );

        // 4. Trigger OnLiveStart
        println!("\n=== TRIGGER ON_LIVE_START ===");
        state.trigger_abilities(&db, TriggerType::OnLiveStart, &ctx);
        state.process_trigger_queue(&db);

        println!("\n=== RESULT ===");
        println!(
            "live_score_bonus = {} (expected: 1)",
            state.core.players[0].live_score_bonus
        );
        assert_eq!(
            state.core.players[0].live_score_bonus, 1,
            "live_score_bonus should be 1"
        );
    }
}
