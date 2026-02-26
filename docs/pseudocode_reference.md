# LovecaSim Pseudocode Writing Guide

This guide defines the "Gold Standard" for writing card ability pseudocode. Following these standards ensures that card abilities are parsed correctly by the engine and are readable by humans.

## Table of Contents
1. [Basic Structure](#basic-structure)
2. [Triggers](#triggers)
3. [Costs](#costs)
4. [Conditions](#conditions)
5. [Effects](#effects)
6. [Parameters & Filters](#parameters--filters)
7. [Complex Examples](#complex-examples)

---

## Basic Structure

An ability consists of several sections, usually in this order:
```pseudocode
TRIGGER: [TRIGGER_NAME]
(Once per turn)  <-- Optional
COST: [COST_INSTRUCTION]([VALUE]) {PARAMETERS}
CONDITION: [CONDITION_INSTRUCTION] {PARAMETERS}
EFFECT: [EFFECT_INSTRUCTION]([VALUE]) -> [TARGET] {PARAMETERS}
```

Sections are separated by newlines. Instructions within a section are separated by `;` (semicolon). Multiple costs or conditions are separated by `,` (comma).

---

## Triggers

Triggers define **when** an ability activates.

| Trigger | Description |
| :--- | :--- |
| `ON_PLAY` | Activates when the member is played to the stage. |
| `ON_LIVE_START` | Activates at the start of a Live segment. |
| `ON_LIVE_SUCCESS` | Activates if the Live is successful. |
| `CONSTANT` | Effect is always active (usually for power/score buffs). |
| `ACTIVATED` | A manually triggered ability (usually has a cost). |
| `TURN_START` | Activates at the beginning of your turn. |
| `TURN_END` | Activates at the end of your turn. |
| `ON_LEAVES` | Activates when the card leaves the stage. |
| `ON_REVEAL` | Activates when the card is revealed (from hand or deck). |

---

## Costs

Costs must be paid to activate the ability.

| Instruction | Description | Example |
| :--- | :--- | :--- |
| `PAY_ENERGY` | Pay N energy cards. | `PAY_ENERGY(2)` |
| `DISCARD_HAND` | Discard N cards from hand. | `DISCARD_HAND(1) {FILTER="Red"}` |
| `TAP_PLAYER` | Tap the player (standard cost). | `TAP_PLAYER(0)` |
| `TAP_MEMBER` | Tap a member on stage. | `TAP_MEMBER(1)` |
| `RETURN_DISCARD_TO_DECK` | Return cards from discard to deck. | `RETURN_DISCARD_TO_DECK(6)` |

> [!TIP]
> Use `(Optional)` after a cost to let the user decide whether to pay it.

---

## Conditions

Conditions filter whether an ability can activate or proceed.

| Instruction | Description | Example |
| :--- | :--- | :--- |
| `COUNT_STAGE` | Checks the number of members on stage. | `COUNT_STAGE {MIN=3}` |
| `SCORE_COMPARE` | Compares scores or turn counts. | `SCORE_COMPARE {COMPARISON="GE", MIN=6}` |
| `HAS_LIVE_CARD` | Checks for specific cards in the live zone. | `HAS_LIVE_CARD {HAS_ABILITY=FALSE}` |
| `IS_CENTER` | Checks if the member is in the Center position. | `IS_CENTER` |

---

## Effects

Effects are the actions the ability performs.

| Instruction | Description | Example |
| :--- | :--- | :--- |
| `DRAW` | Draw N cards. | `DRAW(1) -> PLAYER` |
| `BOOST_SCORE` | Add N to the current score. | `BOOST_SCORE(1) -> PLAYER` |
| `ADD_BLADES` | Add N blades to a member or player. | `ADD_BLADES(2) -> SELF` |
| `RECOVER_MEMBER` | Move a member from discard to hand. | `RECOVER_MEMBER(1) -> CARD_HAND {SOURCE="discard"}` |
| `LOOK_AND_CHOOSE` | Look at N cards and pick one. | `LOOK_AND_CHOOSE(5) -> CARD_HAND` |
| `GRANT_ABILITY` | Temporarily add an ability to a target. | `GRANT_ABILITY(1) -> PLAYER {ABILITY="..."}` |

---

## Parameters & Filters

Parameters are enclosed in `{}` and refine how an instruction works.

| Parameter | Values | Description |
| :--- | :--- | :--- |
| `FILTER` | `"Red"`, `"Group=Aqours"`, etc. | Filters targets or sources. |
| `SOURCE` | `"discard"`, `"deck"`, `"hand"` | Specifies where to find cards. |
| `DESTINATION` | `"discard"`, `"deck"`, `"hand"` | Specifies where to move cards. |
| `UNTIL` | `"LIVE_END"`, `"TURN_END"` | Specifies duration for buffs. |
| `PER_CARD` | `"COUNT_VAL"`, `"SUCCESS_LIVE"` | Multiplies effect by a count. |

---

## Complex Examples

### Modal Choices (Options)
```pseudocode
TRIGGER: ACTIVATED
COST: TAP_PLAYER(0)
EFFECT: CHOICE_MODE(1) -> PLAYER
    Options:
      1: DRAW(1) -> PLAYER
      2: ADD_BLADES(1) -> SELF
```

### Sequential Condition (If-Then)
```pseudocode
TRIGGER: ON_PLAY
EFFECT: CONDITION(1) -> PLAYER {FILTER="NOT_SELF"}; DRAW(1) -> PLAYER
```
*Note: This checks a condition during effect resolution. If it fails, the sequence stops.*

### Cross-Zone Movement
```pseudocode
TRIGGER: ON_LIVE_START
COST: RETURN_DISCARD_TO_DECK(1) {FILTER="Umi"}
EFFECT: ACTIVATE_MEMBER(1) -> SELF
```
