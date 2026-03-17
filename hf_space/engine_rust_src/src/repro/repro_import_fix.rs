use crate::core::enums::*;
use crate::core::logic::*;

#[test]
fn test_import_constants() {
    let _a = crate::core::generated_constants::O_DRAW;
    let _b = crate::core::generated_constants::O_SELECT_CARDS;
    let _c = crate::core::generated_constants::O_PLAY_MEMBER_FROM_HAND;
    println!("Imports work!");
}
