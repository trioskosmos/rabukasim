#[inline]
pub fn apply_to_target_slots(target_slot: i32, resolved_slot: i32, mut apply: impl FnMut(usize)) {
    // target_slot: 1 = explicit all slots, 0/4 are resolved through context or area_idx first.
    if target_slot == 1 {
        for slot_idx in 0..3 {
            apply(slot_idx);
        }
    } else if (0..3).contains(&resolved_slot) {
        apply(resolved_slot as usize);
    }
}
