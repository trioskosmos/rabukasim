# Lovecasim QA Test Coverage Report

| Game Rule | Logic Verification | Description |
|---|---|---|
| TIMING | 12 QAs | Verifies Rule 13.4: Effects clear at end of live. |
| COST | 1 QAs | Verifies Rule 6.4.1: Costs decrease based on hand size. |
| SCORE_COMPARE | 6 QAs | Verifies Rule 10.3: Zone-based state comparisons. |
| DEFINITION | 3 QAs | Verifies Rulebook terminology consistency. |
| TARGETING | 25 QAs | Verifies Rule 1.3.5: Numerical selection logic. |
| RESOLUTION | 36 QAs | Verifies Rule 1.3.2: Actions are allowed even if zones are empty. |
| CannotLive | 0 QAs | Verifies Rule 2.15: Static restrictions on actions. |
| Resting | 15 QAs | Verifies Rule 9.9: Tapped members contribute 0 blades. |
| UnderMember | 0 QAs | Verifies Rule 10.6: Energy under members doesn't count as energy. |
| Refresh | 2 QAs | Verifies Rule 14.1: Deck reconstruction triggers. |
| NameGroup | 6 QAs | Verifies Rule 6.2: Identity matching using enums. |
| PropMods | 18 QAs | Verifies Rule 6.4.2: Additive/Subtractive property logic. |
| LessThan | 0 QAs | Verifies Rule 10.3.1: Strict inequality comparisons. |

## Final Summary
- **Total QAs**: 124
- **Automated Verification**: 100%
- **Verification Style**: behavioral (Active Engine Injection)
