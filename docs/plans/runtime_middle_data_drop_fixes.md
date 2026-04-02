# Runtime Middle-Layer Data Drop Fixes

This note documents the engine-side fixes for the current failure cluster where authored data exists in the source files and expected behavior exists in the generated outputs, but important execution semantics were still lost or flattened inside the Rust runtime.

## Problem 1: `Not Self` filters were decoded but not enforced uniformly

Symptoms:
- Cost reducers that should count "other cards" were counting the source card.
- "This member other than itself" stage conditions treated the source card as a legal match.
- Same-card stage duplicates could fail rulings that depend on object identity rather than card-name identity.

Root cause:
- The runtime filter matcher decoded `special_id == 3` (`NOT_SELF`) but never applied it in the main `CardFilter::matches` path.
- Count-based reducers then had to rely on ad hoc decrements, and those decrements only fired for a narrow zero-attr legacy shape.

Fix:
- Enforce `NOT_SELF` directly in the filter matcher.
- Use slot identity when the source is on stage, so identical cards in different stage slots still count each other.
- Keep the explicit count-path decrement for hand/stage/discard/success counts when the source card is included in a dynamic reduce-cost calculation.

Why this is general:
- The fix restores a core filter semantic instead of patching individual cards.
- All future abilities using the same special filter now benefit automatically.

## Problem 2: Frame data was attached, but semantic effects stayed under-hydrated

Symptoms:
- Response generation and selection logic could see attached `frame_program`s, but later code still read zeroed `runtime_opcode`, `runtime_attr`, `runtime_slot`, or empty `params` from `effects`.
- Prompt type, filter source, and selection restrictions could diverge from the authored frame behavior.

Root cause:
- `attach_sparse_ability_index()` only copied frame-derived runtime fields into effects when `effects` was completely empty.
- Real compiled cards usually already had semantic effect rows, so the hydration step was skipped even though those rows still lacked runtime execution fields.

Fix:
- Always merge missing runtime fields and params from attached frames into existing semantic effects.
- Preserve authored semantic effects, but fill runtime gaps instead of treating their presence as complete execution data.

Why this is general:
- It aligns the two runtime representations instead of forcing downstream systems to guess which one is authoritative.
- This improves selection prompts, cost filters, recovery filters, and any other subsystem that still consults `effects` for metadata.

## Problem 3: `LOOK_AND_CHOOSE` choose-count data was being dropped during frame parsing

Symptoms:
- Cards that should choose multiple cards after looking at a set were collapsing to a default choose count of 1.
- Multi-pick resume flows reopened with the wrong remaining count.

Root cause:
- Consolidated frame JSON often carries look-and-choose semantics in human-readable `decoded` / `summary` text rather than an explicit numeric `choose_count` field.
- The Rust parser extracted `look` counts from those fields, but not `choose` counts.

Fix:
- Extend `AbilityFrame::from_json_value()` to parse `choose_count` from explicit JSON when present and fall back to `decoded` / `summary` text when it is not.

Why this is general:
- This repairs the semantic frame import path for every authored `LOOK_AND_CHOOSE` frame that uses the same compact representation.

## Problem 4: Reduce-cost modifier fallback read the wrong effect row

Symptoms:
- Dynamic cost reductions could miss `per_card` or similar parameters even when the semantic effect row had them.

Root cause:
- `apply_reduce_cost_modifiers()` incremented the frame index before using it as an effect index fallback, producing an off-by-one lookup.

Fix:
- Use the current frame's aligned effect row (`frame_idx - 1`) when frame params are absent.

Why this is general:
- This fixes the frame-to-effect alignment for every reducer that relies on semantic params instead of packed frame params.

## Problem 5: Granted abilities targeted the source slot instead of the selected member context

Symptoms:
- Activated abilities that select a member and then grant a temporary ability could fail to register that granted ability at all.
- Until-live-end grants could be missing immediately after the activation resolved.

Root cause:
- `GRANT_ABILITY` used the raw resolved slot derived from `target_slot == Context Card`, which often still pointed at the source card's area rather than the selected target member.
- When no concrete stage slot was recovered, the grant silently no-op'd.

Fix:
- Resolve the grant target from `ctx.selected_cards.last()` first, then fall back to explicit slot data.

Why this is general:
- This restores the expected selection-to-follow-up-target pipeline for any grant effect that operates on a previously selected member.

## Net Effect

These changes address the failure family at the runtime seam where authored frame semantics were partially decoded, then later ignored, guessed, or reinterpreted through incomplete effect metadata. The fixes do not modify generated card data or tests. They make the runtime preserve and use the existing authored intent more faithfully.