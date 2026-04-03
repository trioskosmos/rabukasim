use crate::core::logic::constants::TARGET_SLOT_STAGE;

pub fn apply_to_target_slots(target_slot: i32, resolved_slot: i32, mut apply: impl FnMut(usize)) {
    // target_slot: 0 = default/all slots (SELF context), 1 = explicit all slots, 4 = area-based
    if target_slot == 1 || target_slot == 0 || target_slot == TARGET_SLOT_STAGE as i32 {
        for slot_idx in 0..3 {
            apply(slot_idx);
        }
    } else if (0..3).contains(&resolved_slot) {
        apply(resolved_slot as usize);
    }
}
