// use crate::test_helpers::{Action, TestUtils, create_test_db, create_test_state, p_state};

#[test]
fn test_state_size() {
    println!("GpuGameState size: {}", std::mem::size_of::<GpuGameState>());
    assert_eq!(std::mem::size_of::<GpuGameState>(), 1132);
}
