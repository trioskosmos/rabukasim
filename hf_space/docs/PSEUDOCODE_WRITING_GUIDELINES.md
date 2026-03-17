# Pseudocode Writing Guidelines

## Overview
This document provides guidelines for writing pseudocodes for Love Live! School Idol Collection card abilities. The pseudocode format is designed to be human-readable while maintaining strict compatibility with the game engine's Ability model and bytecode compiler.

## Structure

An ability is represented as blocks of text with the following sections:

```
TRIGGER: [TriggerType]
(Once per turn)  <-- Optional flag
COST: [CostType]([Value]) {PARAMS...} (Optional)
CONDITION: [NOT] [ConditionType] {PARAMS...}
EFFECT: [EffectType]([Value]) -> [TargetType] {PARAMS...} (Optional)
```

## Trigger Types (Japanese → English)

| Japanese | Pseudocode | Notes |
|----------|------------|-------|
| 登場 | ON_PLAY | When member enters stage |
| ライブ開始時 | ON_LIVE_START | At live start |
| ライブ成功時 | ON_LIVE_SUCCESS | After winning live |
| ターン開始時 | TURN_START | Start of turn |
| ターン終了時 | TURN_END | End of turn |
| 常時 | CONSTANT | Always active |
| 起動 | ACTIVATED | Activated ability |
| 自動 | ON_LEAVES | When member leaves stage |
| 公開 | ON_REVEAL | When revealed via cheer |

## Effect Types

### Core Effects
- `DRAW(n)` - Draw n cards
- `ADD_BLADES(n)` - Gain n blades
- `ADD_HEARTS(n)` - Gain n hearts (use `{HEART_TYPE=x}` for color)
- `BOOST_SCORE(n)` - Add n to live score
- `RECOVER_MEMBER(n)` - Recover n member cards from discard
- `RECOVER_LIVE(n)` - Recover n live cards from discard

### Manipulation Effects
- `LOOK_AND_CHOOSE(n)` - Look at top n cards, choose some
- `MOVE_TO_DECK(n)` - Return n cards to deck
- `MOVE_TO_DISCARD(n)` - Move n cards to discard
- `TAP_OPPONENT(n)` - Put n opponent members in wait state
- `TAP_MEMBER(n)` - Tap n members
- `ACTIVATE_MEMBER(n)` - Activate n members/energy

### Special Effects
- `SELECT_MODE(n)` - Choose from n options (use with indented OPTION blocks)
- `ACTIVATE_ENERGY(n)` - Activate n energy
- `PAY_ENERGY(n)` - Pay n energy as cost
- `PLAY_MEMBER_FROM_DISCARD(n)` - Play member from discard
- `PLAY_MEMBER_FROM_HAND(n)` - Play member from hand

## Condition Types

- `COUNT_STAGE {MIN=n}` - Count members on stage
- `COUNT_SUCCESS_LIVE {MIN=n}` - Count successful lives
- `COUNT_ENERGY {MIN=n}` - Count active energy
- `COUNT_DISCARD {MIN=n}` - Count cards in discard
- `IS_CENTER` - Check if in center position
- `SCORE_COMPARE {comparison=GE/LE/GT/LT}` - Compare scores
- `SCORE_LEAD` - Player has score lead
- `COST_LEAD` - Player has cost lead
- `OPPONENT_HAS_WAIT` - Opponent has wait members
- `HAS_LIVE_CARD` - Has live card in specific zone

## Cost Types

- `DISCARD_HAND(n)` - Discard n cards from hand
- `PAY_ENERGY(n)` - Pay n energy
- `TAP_MEMBER` / `TAP_SELF` - Tap member (put in wait)
- `MOVE_TO_DISCARD` - Move self to discard (sacrifice)
- `REVEAL_HAND(n)` - Reveal n cards from hand

## Target Types

- `SELF` - The card itself
- `PLAYER` - The player
- `OPPONENT` - The opponent
- `ALL_PLAYERS` - Both players
- `MEMBER_SELF` - This member
- `MEMBER_OTHER` - Another member
- `CARD_HAND` - Card in hand
- `CARD_DISCARD` - Card in discard pile

## Filter Parameters

Use `{FILTER="..."}` for card selection filters:
- `GROUP_ID=n` - Filter by group (0=μ's, 1=Aqours, 2=Nijigasaki, 3=Liella!, 4=Hasunosora)
- `UNIT=name` - Filter by unit (Printemps, BiBi, lilywhite, etc.)
- `TYPE_LIVE` / `TYPE_MEMBER` - Filter by card type
- `COST_LE=n` / `COST_GE=n` - Filter by cost
- `COLOR_x` - Filter by heart color

## Heart Types

Based on `heart_0x.png` files in [`launcher/static_content/img/texticon/`](launcher/static_content/img/texticon/):

| Icon File | Pseudocode | Notes |
|-----------|------------|-------|
| heart_00.png | HEART_00 | Pink heart |
| heart_01.png | HEART_01 | Red heart |
| heart_02.png | HEART_02 | Yellow heart |
| heart_03.png | HEART_03 | Green heart |
| heart_04.png | HEART_04 | Blue heart |
| heart_05.png | HEART_05 | Purple heart |
| heart_06.png | HEART_06 | Star/All heart |

**Important**: In Japanese ability texts, hearts are referenced as `{{heart_0x.png|heart0x}}`. Use the exact `HEART_0x` format in pseudocode to avoid color name ambiguity.

## Common Patterns

### Optional Cost/Effect
Add `(Optional)` after the cost or effect:
```
COST: DISCARD_HAND(1) (Optional)
```

### Once Per Turn
Add flag after trigger:
```
TRIGGER: ACTIVATED (Once per turn)
```

### Modal Selection
Use SELECT_MODE with indented options:
```
EFFECT: SELECT_MODE(1)
  OPTION: ドロー | EFFECT: DRAW(1); DISCARD_HAND(1)
  OPTION: ウェイト | EFFECT: TAP_OPPONENT(99) {FILTER="COST_LE_2"}
```

### Per-Card Scaling
Use `{PER_CARD="..."}` for effects that scale:
```
EFFECT: ADD_BLADES(1) {PER_CARD="SUCCESS_LIVE"}
```

### Conditional Effects
Use CONDITION before EFFECT:
```
CONDITION: COUNT_SUCCESS_LIVE {MIN=2}
EFFECT: BOOST_SCORE(1) -> SELF
```

## Japanese Keyword Translations

| Japanese | English |
|----------|---------|
| ～てもよい | (Optional) |
| ターン1回 | (Once per turn) |
| 控え室 | Discard pile |
| デッキ | Deck |
| 手札 | Hand |
| ステージ | Stage |
| ウェイト | Wait state |
| アクティブ | Active |
| ブレード | Blade |
| ハート | Heart |
| ライブ | Live |
| エール | Cheer |
| エネルギー | Energy |

## Writing Process

1. **Identify the trigger** - When does the ability activate?
2. **Check for costs** - Is there a cost to pay? Is it optional?
3. **Check for conditions** - Are there prerequisites?
4. **Write the effects** - What happens when the ability resolves?
5. **Add filters and parameters** - Specify targets and constraints
6. **Mark optional elements** - Add (Optional) where appropriate

## Example Translations

### Example 1: Simple On Play
Japanese: `登場カードを1枚引き、手札を1枚控え室に置く。`
Pseudocode:
```
TRIGGER: ON_PLAY
EFFECT: DRAW(1) -> PLAYER; DISCARD_HAND(1) -> PLAYER
```

### Example 2: Optional Cost with Condition
Japanese: `登場手札を1枚控え室に置いてもよい：自分のデッキの上からカードを3枚見る。その中から1枚を手札に加え、残りを控え室に置く。`
Pseudocode:
```
TRIGGER: ON_PLAY
COST: DISCARD_HAND(1) (Optional)
EFFECT: LOOK_AND_CHOOSE(3) -> CARD_HAND, DISCARD_REMAINDER
```

### Example 3: Live Start with Energy Cost
Japanese: `ライブ開始時E支払ってもよい：ライブ終了時まで、ブレードブレードを得る。`
Pseudocode:
```
TRIGGER: ON_LIVE_START
COST: PAY_ENERGY(1) (Optional)
EFFECT: ADD_BLADES(2) -> SELF
```

### Example 4: Activated Once Per Turn
Japanese: `起動ターン1回手札を2枚控え室に置く：自分の控え室から必要ハートにheart03を3以上含むライブカードを1枚手札に加える。`
Pseudocode:
```
TRIGGER: ACTIVATED (Once per turn)
COST: DISCARD_HAND(2)
EFFECT: RECOVER_LIVE(1) {FILTER="HEARTS_GE_3, COLOR_YELLOW"} -> CARD_HAND
```
