//! Rules explicitly not present, simplified, or not applicable in the current engine implementation.

// Rule 1.3.2.3 (NOT_PRESENT) - Complex requirement optimization not explicitly implemented.
// Rule 1.3.3 (NOT_PRESENT) - General prohibitive precedence not fully unified (handled case-by-case).
// Rule 2.1.1.3 (NOT_PRESENT) - Wild hearts (Rainbow) are handled as Any-color (Index 6) in satisfies logic.
// Rule 2.1.3 (NOT_PRESENT) - Blade Heart visual representation (overlapping icons) does not affect logic.
// Rule 2.3.2.1 (NOT_PRESENT) - "&" in names (multiple names) is handled as a single string for matching.
// Rule 2.4.2.1 (NOT_PRESENT) - "&" in names (multiple groups) is handled as a single string/ID for matching.
// Rule 2.13 (NOT_PRESENT) - Illustrations are for UI only and do not affect game logic.
// Rule 2.14 (NOT_PRESENT) - Marginalia (Collector Number, Rarity) are metadata only and do not affect logic.
// Rule 3.1.2.1 (NOT_PRESENT) - Master of Always Ability (Implied by card owner).
// Rule 3.1.2.3 (NOT_PRESENT) - Master of Auto Ability (Implied by card owner).
// Rule 3.5.3 (NOT_PRESENT) - Explicit Effect types naming (The engine uses internal EffectType enum).
// Rule 4.1.5 (NOT_PRESENT) - Simultaneous placement order choice (Defaulted to sequential processing).
// Rule 4.1.5.1 (NOT_PRESENT) - Opponent's lack of knowledge of placement order (AI sees all or uses POMDP).
// Rule 4.14 (NOT_PRESENT) - Resolution Area as a physical zone (Handled by interaction stack/trigger queue).
// Rule 5.3 (NOT_PRESENT) - Face-up/Face-down flip action (Handled by `set_revealed` on zones).
// Rule 5.5.1.2 (NOT_PRESENT) - Shuffle 0 or 1 cards (Implicitly a no-op).
// Rule 5.8 (NOT_PRESENT) - Swap action (Implemented as manual moves in bytecode).
// Rule 6.1.2 (NOT_PRESENT) - Construction-time abilities (Deck verification is external).
// Rule 6.2.1.1 (NOT_PRESENT) - Deck presentation (Implied by game start).
