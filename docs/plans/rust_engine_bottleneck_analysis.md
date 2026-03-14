# Rust Engine - Real Bottleneck Analysis

## Benchmark Hot Path

```
benchmark_unified.rs:74: sim.step(db, chosen_action)
  └── game.rs:922: step()
      └── handlers.rs:114: handle_main()
          └── play_member_with_choice()      ← MOST EXPENSIVE
              └── rules.rs:217: get_member_cost()     ← CALLED 2-4x PER ACTION
              └── execute_play_member_state()
                  └── resolve_bytecode()    ← OnPlay triggers
          └── game.rs:577: auto_step()     ← Runs multiple phases
```

## #1 REAL Bottleneck: get_member_cost() Called
