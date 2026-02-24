use crate::core::gpu_state::GpuGameState;

#[test]
fn test_state_size() {
    println!("GpuGameState size: {}", std::mem::size_of::<GpuGameState>());
    // Size is 1664 bytes: 2 * 672 (GpuPlayerState) + 320 (game state fields + trigger queue)
    assert_eq!(std::mem::size_of::<GpuGameState>(), 1664);
}
