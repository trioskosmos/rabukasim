# Manual Ability Audit Notes

Date: 2026-04-11

Status: manual review scan complete; remediation work still pending.

I manually reviewed the ability text and frame pairings in `data/ability_frame_source.json` and checked the current frame shapes against the repo's recognized opcodes.

Full source scan complete: `612` ability entries were inspected in chunks.

## Audited so far

- `0` ON_REVEAL yell-pile cleanup: needs real engine support for yell-pile tracking, discard-if-no-live logic, and re-yell execution. Current frames are all `META_RULE` placeholders.
- `1` ON_PLAY draw/discard: matches the text.
- `2` LIVE_START conditional heart gain: missing implementation entirely. Needs a live-card heart-count check and an `ADD_HEARTS` effect that lasts until end of live.
- `3` ON_PLAY optional discard then look-and-choose: matches the text.
- `4` ON_PLAY discard up to 3 then draw same count: looks aligned with the text.
- `5` ON_PLAY draw 1: matches the text.
- `6` LIVE_START top-3 discard plus all-members check: needs engine support for `CHECK_ALL_MEMBERS` or equivalent lowering.
- `7` ACTIVATED pay energy, discard hand, recover Nijigasaki live card: frame shape looks right; group-filter details need to stay explicit in source if they are not already attached in the attrs.
- `8` ON_PLAY draw then bottom-deck one card: needs a real `BOTTOM_DECK` opcode or a normalized lowering to deck placement.
- `9` ON_PLAY mill 10 from deck: likely fine if the source zone defaults to deck top as intended.
- `10` to `13` ON_PLAY named-member play effects: look structurally fine, assuming the member-name and cost filters are preserved in the frame attrs.
- `14` ON_PLAY top-3 look, reorder, discard remainder: looks aligned, but I want to keep an eye on whether the reorder op is represented cleanly enough for all variants.
- `15` ON_PLAY recover live card from discard to deck bottom: looks aligned if the select/move pair keeps the live-card restriction.
- `16` ON_PLAY recover card from discard to deck top: looks aligned.
- `17` LIVE_START / ON_PLAY optional self-tap into opponent tap: looks structurally plausible, but I want to verify the tap cost and the target selection details on the full entry.
- `18` ON_PLAY draw 2, discard 1: matches the text.
- `19` ON_PLAY optional discard to energy charge: looks aligned if the energy-deck placement is preserved in attrs.
- `20` LIVE_START optional self-tap into top-2 look/reorder/discard: needs a real opcode if `LOOK_REORDER_DISCARD` is not already recognized.
- `21` ON_PLAY draw 2, discard 2: matches the text.
- `22` ON_PLAY optional discard then look-and-choose: matches the text.
- `23` ON_PLAY optional discard then look-and-choose plus live-start energy/blade rider: composite shape looks right, but I want to inspect the attachment between the two clauses and make sure nothing is implicit-only.
- `24` ON_PLAY turn-counter draw-until-5: likely needs a real counter/check opcode rather than a generic `HAS_KEYWORD` style placeholder.
- `25` ON_PLAY / move-trigger tap effect: the condition is probably encoded too loosely; I want to verify that the trigger is really tied to both play and area movement, not just a generic no-op branch.
- `26` ON_PLAY / LIVE_START choose-one effect: structurally plausible, but I want to verify the branch wiring against the printed options.
- `27` ON_PLAY baton-touch draw plus discard-play: looks structurally fine.
- `28` ON_PLAY left-side draw effect: likely fine if the left-side check is really encoded in the selection predicate.
- `29` and `30` baton-touch draw/discard effects: look aligned.
- `31` LIVE_START baton-touch plus energy placement: missing implementation entirely.
- `32` ON_PLAY right-side energy activation: likely fine.
- `33` ON_PLAY left-side draw/discard: likely fine.
- `34` ON_PLAY baton-touch from a lower-cost member plus live recovery: the shape looks right, but the trigger/condition plumbing is very opaque and needs another look.
- `35` ON_PLAY energy activation: matches the text.
- `36` ON_PLAY baton-touch recovery: looks aligned.
- `37` ON_PLAY optional discard live card for draw 3: missing the discard side of the cost.
- `38` ON_PLAY discard then recover a MIRAKRA PARK card if another member is present: the current condition chain looks too implicit and probably needs a clearer "other member exists" check.
- `39` LIVE_START optional discard then top-7 selection by heart thresholds: missing implementation entirely.
- `40` LIVE_START optional discard then recover Nijigasaki live card: missing implementation entirely.
- `41` ON_PLAY baton-touch from ability-less member draw 1: looks aligned.
- `42` ON_PLAY both players recover a live card: looks plausible, but I want to verify the player targeting semantics.
- `43` ON_PLAY if energy >= 11 recover a live card: looks plausible if the energy count comparison is already encoded correctly.
- `44` ON_PLAY negate Liella live-start abilities and then recover a live card if negated: likely needs a cleaner duration/negation implementation path.
- `45` ON_PLAY draw for each member on stage then discard 1: looks aligned if the stage count is the intended draw amount.
- `46` ON_PLAY if a cost-13+ member is on stage draw 1: likely needs the cost filter to stay explicit in the frame attrs.
- `47` ON_PLAY mill 4 then gain blades if a live card was among them: likely needs a proper "discarded cards contain live card" check if `DISCARDED_CARDS` is not already a real value source.
- `48` ON_PLAY swap a Nijigasaki live card between success pile and discard: looks aligned.
- `49` and `50` ON_PLAY recover member from discard: look aligned, assuming the cost filter is preserved.
- `51` LIVE_START / ON_PLAY tap-this-member then tap opponent member on exact blade count 4: likely needs the full compare condition retained; the current frame summary is too short to fully trust.
- `52` ON_PLAY passive blade gain on play/move: matches the text.
- `53` ON_PLAY pay energy then look-and-choose: matches the text.
- `54` ON_PLAY pay energy then recover SaintSnow card and gain blades: looks aligned if the optional recover branch really gates the blade gain.
- `55` ON_PLAY baton-touch draw/discard for both players: looks structurally fine.
- `56` and `57` ON_PLAY optional tap-self plus look-and-choose for Aqours/Liella: look aligned in shape, but I want to keep the filter/cost details explicit.
- `58` LIVE_START optional tap-self plus look-and-choose for μ's: missing implementation entirely.
- `59` and `60` ON_PLAY optional tap-self plus look-and-choose for Love Live groups: look aligned in shape, but I want to verify the group filters and the top-5 / reveal / choose plumbing.
- `61` ON_PLAY simple blade gain: matches the text.
- `62` ON_PLAY choose-one between draw/discard and tap all low-cost opponent members: likely needs a real all-target selection path if the `SELECT_MEMBER` branch only handles one target today.
- `63` ON_PLAY choose-one between Aqours blade buff and Saint Snow tap: looks structurally fine.
- `64` ON_PLAY choose-one based on discard-pile composition: looks like it needs a clearer count-on-distinct-property implementation.
- `65` ON_PLAY discard up to 2 hand members to recover matching Aqours live cards: likely needs the discard count / same-count recovery path made explicit.
- `66` ON_PLAY optional discard to tap up to 2 opponent members: looks aligned if multi-target tap is actually supported.
- `67` through `69` ON_PLAY optional discard then top-4 selection by heart thresholds: look like they need a clearer predicate path for the card-type/heart requirement combination.
- `70` ON_PLAY optional discard then top-5 selection by group uniqueness: likely needs a distinct-group counting / filtering path.
- `71` ON_PLAY optional discard then recover EdelNote live card: looks aligned.
- `72` ON_PLAY position-change swap between self and opponent centers: looks aligned.
- `73` ON_PLAY energy >= 7 draw 1: matches the text.
- `74` ON_PLAY success-pile score total >= 6 then charge energy: needs the score-total comparison opcode/path to be clearly supported.
- `75` ON_PLAY auto on another cost-11 member entering: looks plausible, but I want to verify the stage-count filter really excludes this member.
- `76` ON_PLAY auto on cost-10 member entering draw 1: likely needs the cost filter to stay explicit and not collapse into a generic group filter.
- `77` ON_PLAY center BiBi member may force opponent active member wait: looks structurally fine.
- `78` ON_PLAY only-BiBi-stage condition then tap opponent member: looks structurally fine, but I want the condition predicate to stay explicit.
- `79` ON_PLAY center plus success-pile score check then grant ability twice: this one needs a closer look because the branch shape is unusual and may be overloading the grant path.
- `80` ON_PLAY pay 4 energy recover member from discard: matches the text.
- `81` ON_PLAY pay 2 energy then look 7 and choose Liella card: looks aligned.
- `82` ON_PLAY pay 2 energy then play a Nijigasaki member from hand: the play/move sequence looks incomplete and probably needs clearer engine support for the played card's destination.
- `83` ON_PLAY pay 1 energy baton-touch heart gain rider: looks aligned if the heart-gain duration is preserved in attrs.
- `84` and `85` baton-touch draw/discard by named member: look aligned.
- `86` ON_PLAY may wait self and discard one Liella member to re-play that card to the same area: likely needs a clearer "play back to previous area" move path.
- `87` ON_PLAY left/right side draw/discard: looks aligned.
- `88` ON_PLAY baton-touch from lower-cost DOLLCHESTRA member gain blades: looks aligned.
- `89` ON_PLAY may wait self and discard one card to look top3 choose1: looks aligned.
- `90` ON_PLAY may wait self draw then unless Printemps baton-touch discard 1: the "unless" branch is a little opaque and may need a clearer negative-condition path.
- `91` ON_PLAY may wait self to tap opponent member cost <= 9: looks aligned.
- `92` LIVE_START may wait self then activate energy per Printemps member: missing implementation entirely.
- `93` ON_PLAY may wait self then select a Liella live card from top4: likely needs a closer review of the heart-threshold filter and reveal semantics.
- `94` ON_PLAY may wait self recover μ's member from discard: looks aligned if the group filter is preserved.
- `95` ON_PLAY draw then swap area: matches the text.

## What is mostly fixable in data

- Missing `is_optional` flags on "may" / optional choices.
- Missing `group_id` / group scope on cards that explicitly mention `μ's`, `Aqours`, `Liella!`, and similar group names.
- Missing source/destination zone details for discard, deck, and hand operations.
- Missing duration fields for "until end of live" style effects.
- Missing count/comparison frames for "at least / exactly / if X or more" conditions.
- Placeholder-only frame programs, especially `META_RULE` entries that should be executable opcodes.

## What needs engine/opcode support

- `CHECK_ALL_MEMBERS` should either be implemented or mapped to an existing count/check opcode.
- `BOTTOM_DECK` should be supported as a real opcode or normalized to a `MOVE_TO_DECK` bottom-zone form.
- `COUNT_SUCCESS_LIVE` appears in the source and should be handled explicitly instead of relying on a generic success counter.
- Any frame that currently relies on placeholder `META_RULE` entries needs a real opcode or a clearer lowering path.

## Opcode coverage gap

The source currently uses a wider opcode vocabulary than the current metadata list exposes. The most important gaps I saw during the scan are:

- `BATON`
- `BOTTOM_DECK`
- `CHECK_ALL_MEMBERS`
- `COUNT_SUCCESS_LIVE`
- `COUNT_BLADE_HEART_TYPES`
- `COUNT_ENERGY_EXACT`
- `DECK_REFRESHED`
- `HAS_EXCESS_HEART`
- `HAS_KEYWORD`
- `HAS_MEMBER`
- `HEART_LEAD`
- `IN_SUCCESS_PILE`
- `IS_CENTER`
- `IS_SELF_MOVE`
- `MAIN_PHASE`
- `NOT_HAS_EXCESS_HEART`
- `OPPONENT_ENERGY_DIFF`
- `SCORE_COMPARE`
- `SCORE_TOTAL_CHECK`
- `SUCCESS_PILE_COUNT`
- `SUM_VALUE`
- `SYNC_COST`
- `TARGET_MEMBER_HAS_NO_HEARTS`
- `TOTAL_BLADES`
- `TYPE_CHECK`

That does not mean every one of those is missing from the engine, only that the current source format depends on them more heavily than the current metadata registry makes obvious.

## Only-return abilities

These entries still have no executable frame logic beyond `RETURN` and need direct source fixes:

- `2`
- `31`
- `39`
- `40`
- `58`
- `92`
- `179`
- `361`
- `470`
- `471`
- `472`
- `521`
- `522`
- `524`

## Manual conclusion

Most abilities are simple enough that the right fix is to write the missing frame details directly into the existing source rather than introduce another abstraction layer.

The remaining work is a mix of:

- straightforward data edits
- a small set of engine/opcode additions
- a few genuinely special-case abilities that need individual treatment
