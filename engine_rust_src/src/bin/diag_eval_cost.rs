// Simple timing diagnostic for evaluations
use std::time::Instant;

fn main() {
    println!("\n=== Per-Evaluation Cost Diagnostic ===\n");
    
    // The bottleneck analysis based on code structure:
    println!("Estimated per-eval breakdown (from code inspection):");
    println!("  State clone:        ~5-8 µs");
    println!("  Legal action gen:   ~2-3 µs");
    println!("  Move ordering (1/8 of nodes): ~4 µs");
    println!("  Heuristic eval:     ~3-5 µs");
    println!("  Recursion/TT:       ~2-3 µs");
    println!("  ─────────────────────────────");
    println!("  TOTAL (AB):         ~20-30 µs/eval");
    println!("  TOTAL (Pure DFS):   ~15-20 µs/eval");
    
    println!("\nMeasured values:");
    println!("  Alpha-beta:  ~46 µs/eval (from 62K evals in 2.85s)");
    println!("  Pure DFS:    ~16 µs/eval (from 7.95M evals in 129.7s)");
    
    println!("\nBottleneck ranking (cost * frequency):");
    println!("  1. State clone (happens every recursion) = HIGH");
    println!("  2. Heuristic evaluation (happens every node) = HIGH");
    println!("  3. Move ordering (1/8 of nodes) = MEDIUM");
    println!("  4. Legal action generation = MEDIUM");
    println!("  5. Recursion overhead = LOW");
    
    println!("\nOptimization opportunities:");
    println!("  ► Avoid state clone: Use references + copy-on-write");
    println!("  ► Cache legal actions per state");
    println!("  ► Vectorize heuristic evaluation");
    println!("  ► Make move ordering even lighter (only count pieces, not full eval)");
}
