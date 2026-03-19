use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::instruction::BytecodeInstruction;

#[path = "state_energy_charge.rs"]
mod state_energy_charge;
#[path = "state_energy_action.rs"]
mod state_energy_action;
#[path = "state_energy_place.rs"]
mod state_energy_place;
pub fn handle_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let op = instr.op;
    let v = instr.v;
    let a = instr.a;
    #[allow(unused_variables)]
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;

    match op {
        O_ENERGY_CHARGE => {
            return state_energy_charge::handle_energy_charge(state, p_idx, instr.slot(), v);
        }
        O_PAY_ENERGY => {
            return state_energy_charge::handle_pay_energy(state, db, ctx, instr_ip, p_idx, instr, v);
        }
        O_ACTIVATE_ENERGY => {
            return state_energy_action::handle_activate_energy(state, db, ctx, p_idx, v);
        }
        O_PAY_ENERGY_DYNAMIC => {
            return state_energy_action::handle_pay_energy_dynamic(state, p_idx, v);
        }
        O_PLACE_ENERGY_UNDER_MEMBER => {
            return state_energy_place::handle_place_energy_under_member(
                state, db, ctx, instr_ip, p_idx, instr, a,
            );
        }
        _ => HandlerResult::Continue,
    }
}


