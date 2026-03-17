**Bytecode Layout**

Current layout: `fixed5x32-v1` uses 5 `i32` words per instruction.

Observed facts from `data/cards_compiled.json`:

- Instructions analyzed: 5,172
- JSON database size: 11,222,487 bytes
- Binary snapshot size: 3,139,615 bytes
- `V` is zero in 36.49% of instructions
- `A_LOW` is zero in 79.39% of instructions
- `A_HIGH` is zero in 79.93% of instructions
- `S` is zero in 45.32% of instructions
- Only 20.07% of instructions need a non-zero high 32 bits of `A`
- Rough zero-bit rate across raw 32-bit words: about 96.75%
- Unique full instructions: 599 out of 5,173, about 11.58%

Instruction shape distribution:

- `op_only`: 1,554 instructions, 30.05%
- `op_v`: 637 instructions, 12.32%
- `op_v_a`: 113 instructions, 2.18%
- `op_v_s`: 1,130 instructions, 21.85%
- `full`: 1,738 instructions, 33.60%

Rough storage estimate:

- Fixed-width words: 25,860
- Compact optional-field words: 13,982
- Potential reduction: 11,878 words, 45.93%

**What This Means**

The fixed-width VM is materially wasteful, but the pain is not just storage. The real coupling is execution math:

- The Rust engine assumes `ip += 5`
- Jumps are encoded in instruction-count units derived from 5-word chunks
- Many helpers use `chunks(5)` directly
- Some higher-level optimizations depend on bytecode offsets lining up with effect indices

So the bytecode is still important, but mostly as a stable execution contract. Its current shape is more of a transport convenience than a semantic necessity.

The zero-bit number is useful, but it overstates the practical gain if read literally. Many instructions are simple and repeated:

- `RETURN` appears everywhere
- common jumps and simple draw/buff effects recur often
- a lot of non-zero fields still only use a handful of bits

So there are really three different optimization levers:

1. Field compaction: stop storing absent `V/A/S` words
2. Narrower payload encoding: stop paying full 32 bits for tiny values
3. Dictionary or template encoding: reuse repeated instructions or repeated short sequences

Field compaction is the safest first step because it preserves the current instruction model.
Template encoding is likely the next-biggest size win because only about 11.6% of full instructions are unique.

**Best Next Step**

Do not jump directly from `fixed5x32-v1` to a fully irregular format.

Safer staged plan:

1. Introduce `BytecodeProgram` and centralize decoding behind an iterator/API.
2. Keep the in-memory interpreter interface stable while abstracting away `chunks(5)`.
3. Add a new layout version that uses a compact header per instruction plus optional payload words.
4. Convert jumps from `ip + 5 + v * 5` math to decoded instruction indices.
5. Keep compiler support for both layouts during migration.

**Recommended Compact Layout**

Use tagged instructions instead of raw 5-word tuples:

- Header word:
  - opcode
  - flags for `has_v`, `has_a`, `has_s`, `wide_a`
- Followed by only the present payload words

Examples:

- `RETURN` -> `[header]`
- `DRAW 1` -> `[header, v]`
- `SET_TAPPED true @slot` -> `[header, v, s]`
- Filtered effect -> `[header, v, a_low]`
- Wide filter effect -> `[header, v, a_low, a_high, s]`

That keeps decoding simple while removing most zero padding.

**Priority Order**

If the goal is maximum practical win with minimum risk:

1. Prune compiled JSON fields
2. Keep using `cards_compiled.bin`
3. Centralize bytecode access behind an abstraction
4. Only then migrate layout

If the goal is readability and debuggability:

1. Push more common patterns into generated Rust
2. Use bytecode as fallback for uncommon/complex patterns
3. Treat compact bytecode as a second-stage optimization
