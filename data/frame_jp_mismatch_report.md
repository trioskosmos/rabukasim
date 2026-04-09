# Ability Frame vs JP Text Mismatch Report

Generated manually from `data/ability_frame_source.json`.

## Summary

This report lists confirmed mismatches where the frame/opcode behavior does not fully match the Japanese ability text for the same ability.

## Confirmed issues

1. `T0|686fd7af1ff738fb6c085dcfda4c9c5ce08aec7a`
   - Frames: `META_RULE`, `RETURN`
   - JP text describes optional discard of revealed cards, losing blade-heart, and doing another yell.
   - Issue: the frame is effectively a placeholder and does not implement the described effect.

2. `T1|acd3e7fe410be4be1d86e43e0d2f47e7aa7084e4`
   - Frames: `DRAW 1`, `MOVE_TO_DISCARD 1`
   - JP text includes a separate live-start effect for one card example.
   - Issue: one of the JP descriptions is not represented by this single frame sequence.

3. `T1|6eab94976ce3fea5f3acc7dbeeda0d41ef24be2b`
   - Frames: `DRAW 1`
   - JP text covers multiple different card examples with various effects beyond a simple draw.
   - Issue: this signature is used for multiple divergent JP abilities.

4. `T1|a71ca3f9f06c9e38ed1b86c5afd923e00bd0a6e8`
   - Frames: `SELECT_CARDS` from discard, `MOVE_TO_DECK`
   - JP text requires selecting a live card.
   - Issue: the frame does not encode the live-card restriction or top/bottom deck placement clearly.

5. `T1|ee0c3d44137fdad5c5c274d28c411027f97f6199`
   - Frames: `LOOK_DECK 3`, `ORDER_DECK 3`, `MOVE_TO_DISCARD` from stage.
   - JP text says look at top 3 deck cards and place remaining cards into discard.
   - Issue: frame uses `source_zone=STAGE`, which does not match the described deck discard behavior.

6. `T1|051de2a4e4fc6bb070c96987f624561c0073943e`
   - Frames: `HAS_KEYWORD`, optional `PAY_ENERGY`, `DRAW 2`
   - JP text requires left side stage area condition.
   - Issue: frame lacks the side-area check.

7. `T1|2a6040441970a725ac5cabbde288467fb0154619`
   - Frames: optional `RECOVER_LIVE` from discard.
   - JP text requires a successful live card in the success area.
   - Issue: missing the success-area condition.

8. `T1|545f1e99b3fe77b7b0b0cd2b2afe3e618702a6c3`
   - Frames: `COUNT_STAGE`, `DRAW 1`, `MOVE_TO_DISCARD 1`
   - JP text says "draw 1 for each member on your stage, then discard 1".
   - Issue: frame only draws 1, not one per stage member.

9. `T1|6ab6e639948f832c36996f6388f588a7e36482f4`
   - Frames: `SELECT_MEMBER`, `NEGATE_EFFECT`, `SUM_VALUE`, `NOP`
   - JP text says disable live-start ability and then recover a Liella card.
   - Issue: frame is missing any recovery action.

10. `T1|730f4d02ba45fd8071aa2e3fc3963862ad2de76c`
    - Frames: `RECOVER_LIVE` to hand (self) and `RECOVER_LIVE` to stage2 (opponent).
    - JP text says both players take a live card from discard to hand.
    - Issue: opponent action is to stage, not hand.

11. `T1|bb96639efcd7b877a86e82d52349a8074d5cd70b`
    - Frames: optional `DRAW 3`
    - JP text says discard a live card from hand to draw 3.
    - Issue: discard cost is absent.

12. `T1|e139dc8878e4906085cb5de8c5ec4ce010776b6b`
    - Frames: `NOP`, `SELECT_MEMBER`, `MOVE_MEMBER`
    - JP text requires opponent member with original blade count ≤3.
    - Issue: the original blade-count condition is missing.

13. `T1|f0d320738ca7108d240f57f5a1f1157cb2f0d29c`
    - Frames: optional discard and `LOOK_AND_CHOOSE` 7.
    - JP text says choose up to 3 specific heart-type cards and add one to hand.
    - Issue: frame lacks the heart-filter and selection constraint.

14. `T1|f84203845ee38f6c827180bc72dc7d1369acd576`
    - Frames: `HAS_KEYWORD Lanzhu`, `DRAW_UNTIL 5`
    - JP text says when 3 members entered this turn, draw until 5 cards.
    - Issue: frame lacks the "three members entered this turn" trigger.

15. `T1|012e966cd6c5ecfc07c6b447c40c9da79bbb5047`
    - Frames: optional discard and `LOOK_DECK 5`
    - JP text says choose 1 card from top 5, put the rest into discard.
    - Issue: frame does not encode the choose/remaining-discard behavior.

16. `T1|28ae21261e2450b434deb548bc9657c55b30846e`
    - Frames: optional pay1, optional recover_member, condition, add_blades.
    - JP text says recover a SaintSnow card then gain blades.
    - Issue: frame lacks a `SaintSnow` group filter.

17. `T1|33c8155294426ef65e21f0a8d9c04740d5cf4312`
    - Frames: optional discard 2 with `has_blade_heart=1`, optional recover_live AQOURS.
    - JP text says discard up to 2 members without blade-heart.
    - Issue: blade-heart filter is backwards.

18. `T1|b1885357989fd60b7f7a7c034ebd42ce115b2dcf`
    - Frames: optional discard + `LOOK_AND_CHOOSE` cost 9 member.
    - JP text requires `μ's` group.
    - Issue: missing group restriction.

## Notes

- This report is being written manually without executing any script.
- Additional abilities are still under review if more mismatches are present.
