use crate::core::gpu_state::GpuGameState;

#[test]
fn test_state_size() {
    println!("GpuGameState size: {}", std::mem::size_of::<GpuGameState>());
    assert_eq!(std::mem::size_of::<GpuGameState>(), 1280);
}
