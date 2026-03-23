use crate::core::logic::models::AbilityFrame;

use crate::core::logic::interpreter::handlers::HandlerResult;

use crate::core::enums::*;

use crate::core::logic::{AbilityContext, CardDatabase, GameState};



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

    frame: impl Into<AbilityFrame>,

    frame_idx: usize,

) -> HandlerResult {

    let frame: AbilityFrame = frame.into();

    let op = frame.raw_opcode();

    let v = frame.raw_value();

    let a = frame.raw_attr() as i64;

    #[allow(unused_variables)]

    let s = frame.raw_slot();

    let p_idx = ctx.player_id as usize;



    match op {

        O_ENERGY_CHARGE => {

            return state_energy_charge::handle_energy_charge(state, p_idx, frame.dslot(), v);

        }

        O_PAY_ENERGY => {

            return state_energy_charge::handle_pay_energy(state, db, ctx, frame_idx, p_idx, &frame, v);

        }

        O_ACTIVATE_ENERGY => {

            return state_energy_action::handle_activate_energy(state, db, ctx, p_idx, v);

        }

        O_PAY_ENERGY_DYNAMIC => {

            return state_energy_action::handle_pay_energy_dynamic(state, p_idx, v);

        }

        O_PLACE_ENERGY_UNDER_MEMBER => {

            return state_energy_place::handle_place_energy_under_member(

                state, db, ctx, frame_idx, p_idx, &frame, a,

            );

        }

        _ => HandlerResult::Continue,

    }

}





