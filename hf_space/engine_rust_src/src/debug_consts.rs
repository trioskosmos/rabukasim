#[cfg(test)]
mod debug_consts {
    use crate::core::logic::constants::*;
    #[test]
    fn print_consts() {
        println!("FILTER_COLOR_MASK: 0x{:X}", FILTER_COLOR_MASK);
        println!("FILTER_VALUE_ENABLE_FLAG: 0x{:X}", FILTER_VALUE_ENABLE_FLAG);
        println!("FILTER_VALUE_LE_FLAG: 0x{:X}", FILTER_VALUE_LE_FLAG);
        println!("FILTER_VALUE_TYPE_FLAG: 0x{:X}", FILTER_VALUE_TYPE_FLAG);
        println!("FILTER_TYPE_MASK: 0x{:X}", FILTER_TYPE_MASK);
        println!("FILTER_TARGET_SHIFT: {}", FILTER_TARGET_SHIFT);
        println!("FILTER_TYPE_SHIFT_R5: {}", FILTER_TYPE_SHIFT_R5);
        println!("FILTER_GROUP_ENABLE_SHIFT: {}", FILTER_GROUP_ENABLE_SHIFT);
        println!("FILTER_GROUP_ID_SHIFT: {}", FILTER_GROUP_ID_SHIFT);
        println!("FILTER_STATE_SHIFT: {}", FILTER_STATE_SHIFT);
        println!("FILTER_COLOR_SHIFT_R5: {}", FILTER_COLOR_SHIFT_R5);
        println!("FILTER_ZONE_MASK_SHIFT_R5: {}", FILTER_ZONE_MASK_SHIFT_R5);
    }
}
