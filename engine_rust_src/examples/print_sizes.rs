use engine_rust::core::logic::GameState;
use engine_rust::core::logic::PlayerState;
use engine_rust::core::gpu_state::GpuGameState;

fn main() {
    println!("Size of GameState: {} bytes", std::mem::size_of::<GameState>());
    println!("Size of PlayerState: {} bytes", std::mem::size_of::<PlayerState>());
    println!("Size of GpuGameState: {} bytes", std::mem::size_of::<GpuGameState>());
}
