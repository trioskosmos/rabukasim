/// Legacy hook retained for compatibility.
///
/// Card-specific activated energy overrides have been removed. Energy cost must
/// come from authored cost data or decoded frames.
pub fn get_hardcoded_energy_cost(_card_id: i32, _ability_idx: usize) -> Option<i32> {
    None
}
