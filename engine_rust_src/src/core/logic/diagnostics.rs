use crate::core::logic::player::PlayerState;
use crate::core::logic::CardDatabase;
use crate::core::logic::GameState;

impl GameState {
    pub fn dump_diagnostics(&self, db: &CardDatabase) {
        println!(
            "\n================================================================================"
        );
        println!(
            "DIAGNOSTIC DUMP - Turn: {}, Phase: {:?}, Current Player: {}",
            self.turn, self.phase, self.current_player
        );
        println!(
            "================================================================================"
        );

        for i in 0..2 {
            println!("--- PLAYER {} ---", i);
            let p = &self.core.players[i];

            // Flags
            let tapped = [p.is_tapped(0), p.is_tapped(1), p.is_tapped(2)];
            let moved = [p.is_moved(0), p.is_moved(1), p.is_moved(2)];
            let refreshed = p.get_flag(PlayerState::FLAG_DECK_REFRESHED);

            println!(
                "  [FLAGS] Tapped: {:?}, Moved: {:?}, Refreshed: {}",
                tapped, moved, refreshed
            );
            println!(
                "  [SCORE] Score: {}, Bonus: {}, Volume: {}",
                p.score, p.live_score_bonus, p.current_turn_notes
            );

            // Zones
            print!("  [HAND]  ");
            if p.hand.is_empty() {
                print!("(Empty)");
            }
            for &cid in &p.hand {
                print!("{} ", cid);
            }
            println!();

            println!("  [STAGE]");
            for slot in 0..3 {
                let cid = p.stage[slot];
                if cid >= 0 {
                    let card_no = db
                        .get_member(cid)
                        .map(|m| m.card_no.as_str())
                        .unwrap_or("???");
                    print!("    Slot {}: ID={} No={} ", slot, cid, card_no);
                    if tapped[slot] {
                        print!("[TAPPED] ");
                    }
                    if moved[slot] {
                        print!("[MOVED] ");
                    }

                    let energy = &p.stage_energy[slot];
                    if !energy.is_empty() {
                        print!("(Under: ");
                        for &ecid in energy {
                            print!("{} ", ecid);
                        }
                        print!(")");
                    }
                    println!();
                } else {
                    println!("    Slot {}: (Empty)", slot);
                }
            }

            print!("  [ENERGY] ");
            if p.energy_zone.is_empty() {
                print!("(Empty)");
            }
            for (idx, &cid) in p.energy_zone.iter().enumerate() {
                let is_tapped = p.is_energy_tapped(idx);
                print!(
                    "{}{}{} ",
                    if is_tapped { "[" } else { "" },
                    cid,
                    if is_tapped { "]" } else { "" }
                );
            }
            println!();

            print!("  [DISCARD] ");
            if p.discard.is_empty() {
                print!("(Empty)");
            }
            for &cid in &p.discard {
                print!("{} ", cid);
            }
            println!();

            println!();
        }

        if !self.interaction_stack.is_empty() {
            println!(
                "--- INTERACTION STACK ({}) ---",
                self.interaction_stack.len()
            );
            for (idx, pending) in self.interaction_stack.iter().enumerate() {
                println!(
                    "  [{}] Op: {}, Type: {}, Card: {}, Choices: {}",
                    idx,
                    pending.effect_opcode,
                    pending.choice_type,
                    pending.card_id,
                    pending.choice_text
                );
            }
            println!();
        }

        println!(
            "================================================================================\n"
        );
    }
}
