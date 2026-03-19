# Findings: Why The Hybrid Ability Stack Stalled

## What We Learned

The canonical/runtime-plan experiment did prove one useful thing: the old bytecode-era behavior could be described with named instructions, and the engine could still reach the same handler family in many cases.

But the experiment also added extra layers instead of removing them.

## The Core Problem

We ended up with too many overlapping representations:

- legacy packed bytecode
- semantic IR
- runtime plan
- effective choice metadata
- compatibility helpers in Rust and Python
- launcher-side normalization

That made the system harder to debug than the original bytecode-only model.

## Where It Broke Down

- Choice metadata still had to be derived and synchronized in multiple places.
- Some cards compiled with the right semantic instruction but stale exported selection fields.
- Pending interaction bugs looked like engine bugs, but were often export or metadata bugs.
- The runtime plan still carried numeric transport fields, so the new layer was not actually simpler than bytecode in practice.
- The UI and Rust paths still needed compatibility glue, so we never reached a single source of truth.

## Important Observation

The Rust engine already knew how to suspend on real choice opcodes like `SELECT_MEMBER`.

That means the biggest failure mode was not missing opcode support.
It was the fact that the new stack made interaction metadata depend on too many intermediate conversions.

## Conclusion

The semantic stack was useful as a diagnostic bridge, but it was not a good final architecture.
If the goal is simplification, the clean move is to go back to a bytecode baseline and rebuild one smaller, explicit instruction model instead of keeping two parallel ones.
