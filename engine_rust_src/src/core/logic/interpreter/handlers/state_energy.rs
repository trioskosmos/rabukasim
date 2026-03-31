use crate::core::enums::*;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

/// Energy handler - delegates to unified implementation
pub fn handle_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    match frame_data.opcode {
        O_ENERGY_CHARGE => super::super::unified::handle_energy_charge(state, db, ctx, frame_data),
        O_PAY_ENERGY => super::super::unified::handle_pay_energy(state, db, ctx, frame_data, frame_idx),
        O_ACTIVATE_ENERGY => super::super::unified::handle_activate_energy(state, db, ctx, frame_data),
        O_PAY_ENERGY_DYNAMIC => super::super::unified::handle_pay_energy_dynamic(state, db, ctx, frame_data),
        O_PLACE_ENERGY_UNDER_MEMBER => super::super::unified::handle_place_energy_under_member(state, db, ctx, frame_data, frame_idx),
        _ => HandlerResult::Continue,
    }
}
