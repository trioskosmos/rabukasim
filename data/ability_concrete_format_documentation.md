# Concrete Ability Format Documentation

## Purpose

This document describes abilities as manipulations of the game's real state, not as abstract opcodes.

The engine should treat an ability as a structured transformation over:
- zones
- resources
- card state
- timing windows
- filters and choices
- duration and replacement rules

The goal is to preserve what the rules actually care about so runtime code can execute the same mechanics without depending on vague verbs or text-shaped guesses.

## Core Model

An ability is best modeled as:

```text
trigger / timing
  -> optional usage limit
  -> cost
  -> condition
  -> target selection
  -> state mutation
  -> follow-up / duration / replacement
```

The important point is that the ability does not create a special language by itself. It only combines a small number of game primitives in different orders.

## Game State

The engine should represent the game in terms of concrete state objects:

- `GameState`
- `PlayerState`
- `CardState`
- `ZoneState`
- `EffectState`
- `ChoiceState`
- `ContinuousModifierState`
- `ReplacementEffectState`

At minimum, abilities need to read and write:

- card location
- card orientation / tapped state
- controller / owner
- zone contents and order
- score and required heart values
- heart and blade modifiers
- energy count and energy cards
- selected cards and pending choices
- turn and phase context
- continuous restrictions and bonuses

## Zones

The rules define a small set of real zones. These should be first-class runtime concepts.

### Player zones

- `stage_left`
- `stage_center`
- `stage_right`
- `member_area`
- `live_card_area`
- `energy_area`
- `main_deck`
- `energy_deck`
- `hand`
- `discard`
- `success_live_pile`
- `exile`
- `resolution`

### Notes on zones

- `stage_left`, `stage_center`, and `stage_right` are not interchangeable with a generic `stage` label.
- `member_area` and `live_card_area` are distinct areas and should remain distinct in the IR.
- `resolution` is a temporary processing area, not a permanent zone.
- `exile` is a true removal zone, not a discard synonym.

## Resources

The game exposes a small number of real resources.

- `energy`
- `heart`
- `blade`
- `score`
- `required_hearts`
- `tap_state`
- `face_up_state`
- `duration`
- `turn_usage_count`
- `per_turn_usage_count`

These are the mechanical quantities abilities should manipulate.

### Do not flatten these together

- `heart` is not `score`
- `blade` is not `heart`
- `energy` is not a card zone
- `required_hearts` is a cost requirement, not a resource on the same level as energy
- `tap_state` is a card state flag, not a zone or a counter

## Phases And Windows

The rules define the game flow as a sequence of phases and subwindows.

### Main phases

- `active`
- `energy`
- `draw`
- `main`
- `live`

### Live subphases

- `live_set`
- `performance`
- `success_check`

### Timing windows / keyword timings

- `entry_trigger`
- `live_start_trigger`
- `live_success_trigger`
- `center`
- `left_side`
- `right_side`
- `position_change`
- `formation_change`

### Turn-limit keywords

Be careful here:

- `turn1` and `turn2` are not automatically first-turn windows.
- They may be usage limits such as once per turn or twice per turn.
- A true first-turn-only restriction is a different concept and should be represented separately.

Recommended runtime distinction:

- `first_turn_only`: ability can be used only on the first turn of the game or the controller's first turn, if the rules/text explicitly say so.
- `once_per_turn`: usage limit for a single turn.
- `twice_per_turn`: usage limit for two uses in a single turn.

Do not conflate these.

## Ability Grammar

The parsed form should preserve the structure of the printed Japanese text.

```text
[timing keyword]
[usage limit]
[cost]
[condition]
[target filter]
[action]
[follow-up]
[duration]
```

### Examples of slot types

- timing keyword: icon-based entry/start/success markers
- usage limit: once per turn, twice per turn, or first-turn-only restrictions
- cost: tap this card, pay energy, put a card from hand into discard
- condition: if, when, while, if the card is in a zone
- target filter: group, unit, card name, cost, heart, type, zone, position
- action: move, draw, add, set, reveal, play, look, choose, score change
- follow-up: then, if so, each, until, until end of turn / live
- duration: immediate, until end of turn, until end of live, continuous

### Example Decomposition

Original text:

```text
{{toujyou.png|登場}}自分の成功ライブカード置き場にカードが2枚以上ある場合、自分の控え室からライブカードを1枚手札に加える。
{{jyouji.png|常時}}自分の成功ライブカード置き場にあるカード1枚につき、{{icon_blade.png|ブレード}}を得る。
```

Structure:

```json
{
  "logic": [
    {
      "trigger": "entry_trigger",
      "condition": {
        "kind": "zone_count_at_least",
        "subject": "self",
        "zone": "success_live_pile",
        "count": 2
      },
      "effect": {
        "kind": "move_card",
        "subject": "self",
        "from_zone": "discard",
        "to_zone": "hand",
        "card_type": "live",
        "count": 1
      }
    },
    {
      "trigger": "continuous",
      "condition": {
        "kind": "per_card",
        "subject": "self",
        "zone": "success_live_pile"
      },
      "effect": {
        "kind": "gain_resource",
        "resource": "blade",
        "amount": 1
      }
    }
  ]
}
```

## What Is Exchangeable

These are the slots that vary between abilities and should be normalized, not hardcoded:

- card names
- character names
- group names
- unit names
- stage position names
- zones
- counts
- comparison values
- heart types
- blade counts
- score values
- source / target references
- optionality markers
- duration markers
- choice sets

The printed text may use icons, quoted names, or plain Japanese to express these. The parser should keep them as structured fields, not flatten them into prose.

## What Is Not Exchangeable

These are actual game mechanics and should remain distinct types:

- `draw`
- `move`
- `play`
- `look`
- `choose`
- `reveal`
- `shuffle`

## Single Placeholder Compression

For discovery and clustering, the extractor should also support a very compact
view where every replaceable mechanics span is collapsed into one generic
placeholder token.

That means a clause such as:

```text
自分の控え室からライブカードを1枚手札に加える。
```

can be reduced to something like:

```text
⟦M⟧の⟦M⟧から⟦M⟧を⟦M⟧に加える。
```

The exact placeholder token is not important. What matters is that the same
token is used for every replaceable mechanic slot so the remaining text shows
the reusable skeleton of the ability.

Keep the removed pieces available in structured side data when possible so the
engine can still recover zones, counts, references, timing markers, and other
mechanical slots later.
- `tap`
- `untap`
- `pay`
- `add_hearts`
- `add_blades`
- `modify_score`
- `modify_cost`
- `apply_restriction`
- `apply_continuous_modifier`
- `replacement_effect`
- `triggered_effect`

## State Manipulation Families

Treat each ability as one or more of these families.

### Zone movement

- move from deck to hand
- move from hand to discard
- move from discard to hand
- move from stage to discard
- move from energy deck to energy area
- move from stage to another stage slot
- place under a member

### Resource mutation

- draw cards
- add or remove energy
- add or remove hearts
- add or remove blades
- set or modify score
- set or modify required hearts

### Selection and search

- look at top N
- choose from revealed cards
- search for a card matching filters
- select a card or player
- select one of multiple effect branches

### State flags and restrictions

- tap / untap
- face-up / face-down
- cannot play
- cannot activate
- cannot move
- treat as another card type
- count as another name / group / unit

### Continuous effects

- until end of turn
- until end of live
- while a condition holds
- per matching card
- modify rules or counts

### Replacement effects

- instead of X, do Y
- if X would happen, do Y
- when X happens, replace resolution

## Mechanics-First Interpretation

The engine should read the JP text as a set of instructions over abilityless mechanics.

That means:

- identify the timing marker first
- identify any explicit cost
- identify the affected zone or card
- identify filters and counts
- identify the action primitive
- identify any duration or replacement rule
- only then produce runtime logic

This avoids the common failure mode of guessing a flat English-like meaning and losing the actual mechanical structure.

## Comparison And Conditions

The rules use comparisons and conditions as structured mechanics, not just words.

Examples:

- `cost <= 4`
- `count >= 2`
- `heart >= required`
- `if this card is on stage`
- `if the revealed cards include...`
- `if this player has...`

Keep comparisons explicit in the IR. Do not bury them inside a text blob.

## Canonical Runtime Shape

A good concrete runtime record should look roughly like this:

```json
{
  "jp": "original Japanese ability text",
  "logic": [
    {
      "trigger": "live_start_trigger",
      "usage_limit": "once_per_turn",
      "cost": [
        {"kind": "pay_energy", "amount": 1}
      ],
      "condition": [
        {"kind": "zone_contains", "zone": "stage", "subject": "self"}
      ],
      "action": [
        {"kind": "add_blades", "target": "self", "amount": 2}
      ],
      "duration": "until_end_of_live"
    }
  ],
  "card_examples": [
    "PL!... | Example Card (ab#0)"
  ],
  "ability_index": 0
}
```

The precise field names can change, but the structure should not:

- source text
- structured logic
- card references
- ability index

## Practical Rule For Parsing

When a phrase is mechanical, preserve it as a typed slot.

When a phrase is decorative, reminder text, or rules explanation, keep it out of the executable logic but do not destroy it if it matters for traceability.

The extractor should therefore prefer:

- structured nodes for mechanics
- traceable metadata for card text
- no conflation of resources, zones, and timing windows

## Summary

The best model for this game is not "opcode-like abilities" but "state transformations over a small set of real mechanics."

If the parser stays faithful to that model, the engine can reason about:

- what the ability touches
- when it can happen
- what it costs
- what it changes
- how long it lasts
- whether it replaces or grants a rule
