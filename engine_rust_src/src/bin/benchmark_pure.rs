use std::env;
use std::fs;
use std::time::Instant;
use engine_rust::core::logic::{CardDatabase, GameState};

fn main() {
    let args: Vec<String> = env::args().collect();
    let json_path = if args.len() > 1 { &args[1] } else { "../data/cards_compiled.json" };

    println!("Loading cards from {}...", json_path);
    let json_str = fs::read_to_string(json_path).expect("Failed to read cards JSON");
    let db = CardDatabase::from_json(&json_str).expect("Failed to parse JSON");
    println!("Database loaded. Members: {}", db.members.len());

    let all_members: Vec<i32> = db.members.keys().map(|&k| k as i32).collect();
    let all_lives: Vec<i32> = db.lives.keys().map(|&k| k as i32).collect();

    // Create a realistic populated state
    let mut p0_main: Vec<i32> = all_members.iter().take(50).cloned().collect();
    p0_main.extend(all_lives.iter().take(20).cloned());
    let mut p1_main: Vec<i32> = all_members.iter().skip(50).take(50).cloned().collect();
    p1_main.extend(all_lives.iter().skip(20).take(20).cloned());

    let mut game = GameState::default();
    game.initialize_game(
        p0_main, p1_main,
        vec![], vec![],
        Vec::new(), Vec::new(),
    );
    game.ui.silent = true;

    // Warmup
    for _ in 0..1000 {
        let _ = game.clone();
    }

    let iterations = 1_000_000;
    println!("Benchmarking GameState::clone() for {} iterations...", iterations);

    let start = Instant::now();
    for _ in 0..iterations {
        let _ = std::hint::black_box(game.clone());
    }
    let duration = start.elapsed();

    println!("Total time: {:.4} s", duration.as_secs_f64());
    println!("Latency per copy: {:.4} us", duration.as_secs_f64() * 1_000_000.0 / iterations as f64);
    println!("Ops/sec: {:.0}", iterations as f64 / duration.as_secs_f64());
}
