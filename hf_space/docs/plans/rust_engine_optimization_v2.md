
Rooの発言

Real Bottleneck Analysis
I've examined the benchmark code flow and found the actual performance bottlenecks:

The Hot Path in Benchmark
benchmark_unified.rs line 74: sim.step(db, chosen_action)
    └── handle_main()
        └── play_member_with_choice()     ← MOST EXPENSIVE
            └── get_member_cost()          ← CALLED 2-4x PER ACTION!
            └── execute_play_member_state()
                └── resolve_bytecode()      ← OnPlay triggers
        └── auto_step()                    ← Runs multiple phases
#1 Bottleneck: get_member_cost() - Called Multiple Times
File: rules.rs:217-280

This function is called:

Once in action generation (to validate if action is legal)
Again in play_member_with_choice (to calculate actual cost)
// rules.rs:217 - This is called TWICE for every play action!
pub fn get_member_cost(...) -> i32 {
    let m = db.get_member(base_id);           // Hash lookup #1
    if let Some(old_m) = db.get_member(old_cid)  // Hash lookup #2
    // ... then iterates abilities and calls check_condition()!
}
#2 Bottleneck: Condition Checking in Hot Path
The check_condition() function is called from:

get_member_cost() - for cost modifiers
Action generation - to validate each action
Interpreter - for trigger conditions
Each call may iterate through card abilities and do more lookups.

What Changes Would Actually Help
Cache cost calculations: Don't recalculate cost in both action generation AND play
Skip condition checks in benchmark: The benchmark uses random actions - many will fail legality checks, wasting time
Fast-path for legal actions: Pre-compute legal actions and cache validity
Quick Question
What is your current benchmark output? (games/sec and steps/sec)

This will help me understand if we'
