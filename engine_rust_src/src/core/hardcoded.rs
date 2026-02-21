// GENERATED CODE - DO NOT EDIT
use crate::core::logic::{GameState, CardDatabase, AbilityContext};

pub fn execute_hardcoded_ability(state: &mut GameState, _db: &CardDatabase, card_id: i32, ab_idx: usize, ctx: &AbilityContext) -> bool {
    let p_idx = ctx.player_id as usize;
    match (card_id, ab_idx) {
        (10, 0) => {
            state.core.players[p_idx].cost_reduction += 1;
            true
        },
        (11, 1) => {
            state.pay_energy(p_idx, 6);
            state.core.players[p_idx].blade_buffs[1 as usize] += 3;
            true
        },
        (13, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (14, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (19, 0) => {
            true
        },
        (21, 0) => {
            true
        },
        (23, 1) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (4119, 1) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (24, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (4120, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (26, 0) => {
            state.draw_cards(p_idx, 203 as u32);
            true
        },
        (4122, 0) => {
            state.draw_cards(p_idx, 203 as u32);
            true
        },
        (8218, 0) => {
            state.draw_cards(p_idx, 203 as u32);
            true
        },
        (12314, 0) => {
            state.draw_cards(p_idx, 203 as u32);
            true
        },
        (27, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (4123, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (4151, 0) => {
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 2 as i32);
            true
        },
        (8247, 0) => {
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 2 as i32);
            true
        },
        (12343, 0) => {
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 2 as i32);
            true
        },
        (58, 1) => {
            state.core.players[p_idx].live_score_bonus += 1;
            true
        },
        (64, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (65, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (87, 0) => {
            true
        },
        (87, 2) => {
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 1 as i32);
            true
        },
        (4183, 0) => {
            true
        },
        (4183, 2) => {
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 1 as i32);
            true
        },
        (88, 1) => {
            state.activate_energy(p_idx, 1);
            true
        },
        (4184, 1) => {
            state.activate_energy(p_idx, 1);
            true
        },
        (97, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (4193, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (120, 1) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (143, 1) => {
            state.pay_energy(p_idx, 2);
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (144, 1) => {
            state.pay_energy(p_idx, 2);
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (147, 1) => {
            state.pay_energy(p_idx, 2);
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (159, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (164, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (166, 0) => {
            state.activate_energy(p_idx, 2);
            true
        },
        (4262, 0) => {
            state.activate_energy(p_idx, 2);
            true
        },
        (4264, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            state.core.players[p_idx].live_score_bonus += 1;
            true
        },
        (8360, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            state.core.players[p_idx].live_score_bonus += 1;
            true
        },
        (12456, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            state.core.players[p_idx].live_score_bonus += 1;
            true
        },
        (169, 1) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (4265, 1) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (8361, 1) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (12457, 1) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (172, 0) => {
            state.pay_energy(p_idx, 2);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (4268, 0) => {
            state.pay_energy(p_idx, 2);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (193, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (4289, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (234, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (4330, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (239, 1) => {
            state.pay_energy(p_idx, 2);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (4335, 1) => {
            state.pay_energy(p_idx, 2);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (8431, 1) => {
            state.pay_energy(p_idx, 2);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (12527, 1) => {
            state.pay_energy(p_idx, 2);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (269, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            state.core.players[p_idx].blade_buffs[0 as usize] += 2;
            true
        },
        (4365, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            state.core.players[p_idx].blade_buffs[0 as usize] += 2;
            true
        },
        (8461, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            state.core.players[p_idx].blade_buffs[0 as usize] += 2;
            true
        },
        (12557, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            state.core.players[p_idx].blade_buffs[0 as usize] += 2;
            true
        },
        (281, 0) => {
            state.draw_cards(p_idx, 2 as u32);
            true
        },
        (284, 0) => {
            true
        },
        (287, 0) => {
            true
        },
        (303, 2) => {
            state.activate_energy(p_idx, 1);
            state.activate_energy(p_idx, 1);
            true
        },
        (4399, 2) => {
            state.activate_energy(p_idx, 1);
            state.activate_energy(p_idx, 1);
            true
        },
        (8495, 2) => {
            state.activate_energy(p_idx, 1);
            state.activate_energy(p_idx, 1);
            true
        },
        (12591, 2) => {
            state.activate_energy(p_idx, 1);
            state.activate_energy(p_idx, 1);
            true
        },
        (309, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (331, 0) => {
            true
        },
        (4427, 0) => {
            true
        },
        (340, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (4436, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (376, 0) => {
            state.activate_energy(p_idx, 2);
            true
        },
        (378, 1) => {
            state.pay_energy(p_idx, 2);
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 1 as i32);
            true
        },
        (398, 1) => {
            state.pay_energy(p_idx, 2);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (399, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (400, 1) => {
            state.pay_energy(p_idx, 2);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (401, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (402, 0) => {
            state.core.players[p_idx].blade_buffs[0 as usize] += 1;
            true
        },
        (439, 1) => {
            true
        },
        (4535, 1) => {
            true
        },
        (8631, 1) => {
            true
        },
        (12727, 1) => {
            true
        },
        (443, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (4539, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (448, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (449, 0) => {
            state.set_member_tapped(p_idx, 1 as usize, false);
            true
        },
        (451, 0) => {
            state.core.players[p_idx].cost_reduction += -1;
            true
        },
        (452, 0) => {
            true
        },
        (472, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (473, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (474, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (498, 1) => {
            true
        },
        (4594, 1) => {
            true
        },
        (8690, 1) => {
            true
        },
        (12786, 1) => {
            true
        },
        (501, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (4597, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (529, 0) => {
            state.draw_energy_cards(p_idx, 1);
            true
        },
        (4625, 0) => {
            state.draw_energy_cards(p_idx, 1);
            true
        },
        (535, 0) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (4631, 0) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (8727, 0) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (12823, 0) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (542, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (545, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (567, 0) => {
            true
        },
        (4663, 0) => {
            true
        },
        (8759, 0) => {
            true
        },
        (12855, 0) => {
            true
        },
        (568, 0) => {
            state.pay_energy(p_idx, 1);
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 1 as i32);
            true
        },
        (571, 0) => {
            state.core.players[p_idx].heart_buffs[0 as usize].add_to_color(0 as usize, 1 as i32);
            true
        },
        (577, 0) => {
            state.pay_energy(p_idx, 0);
            state.core.players[p_idx].blade_buffs[1 as usize] += 1;
            true
        },
        (588, 1) => {
            state.pay_energy(p_idx, 6);
            state.core.players[p_idx].live_score_bonus += 1;
            true
        },
        (4684, 1) => {
            state.pay_energy(p_idx, 6);
            state.core.players[p_idx].live_score_bonus += 1;
            true
        },
        (591, 0) => {
            state.pay_energy(p_idx, 2);
            state.draw_energy_cards(p_idx, 1);
            true
        },
        (591, 1) => {
            state.pay_energy(p_idx, 3);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (4687, 0) => {
            state.pay_energy(p_idx, 2);
            state.draw_energy_cards(p_idx, 1);
            true
        },
        (4687, 1) => {
            state.pay_energy(p_idx, 3);
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (592, 0) => {
            state.draw_energy_cards(p_idx, 1);
            true
        },
        (4688, 0) => {
            state.draw_energy_cards(p_idx, 1);
            true
        },
        (593, 0) => {
            true
        },
        (593, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (4689, 0) => {
            true
        },
        (4689, 1) => {
            state.core.players[p_idx].blade_buffs[1 as usize] += 2;
            true
        },
        (594, 0) => {
            state.activate_energy(p_idx, 2);
            true
        },
        (4690, 0) => {
            state.activate_energy(p_idx, 2);
            true
        },
        (603, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (617, 0) => {
            state.draw_cards(p_idx, 1 as u32);
            true
        },
        (626, 0) => {
            state.pay_energy(p_idx, 2);
            state.draw_energy_cards(p_idx, 1);
            true
        },
        _ => false,
    }
}
