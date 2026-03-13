---
name: board_layout_rules
description: Unified reference for card orientations, zone requirements, and rotation logic.
---

# Board Layout & Card Orientation Rules

This skill defines the definitive rules for how cards should be displayed and rotated across different zones on the game board.

## 1. Card Type Classifications

| Card Type | Native Image Orientation | Default Mode |
| :--- | :--- | :--- |
| **Member Card** | Portrait (Vertical) | Active Member |
| **Live Card** | Landscape (Horizontal) | Goal/Requirement |

## 2. Zone Orientation Standards

| Zone | Primary Orientation | Justification |
| :--- | :--- | :--- |
| **Hand** | **Vertical (Portrait)** | Maximize horizontal density and readability. |
| **Stage** | **Vertical (Portrait)** | Standard member placement. |
| **Live Zone** | **Horizontal (Landscape)** | Standard live card/set-piece orientation. |
| **Success Zone** | **Horizontal (Landscape)** | Matches Live card orientation. |
| **Energy Row** | **HUD/Pips** | Minimized strip to maximize board space. |

## 3. Rotation Logic Matrix

To achieve the Target Orientation, cards must be rotated based on their Native Orientation.

| Zone | Member Card (Native: Port) | Live Card (Native: Land) |
| :--- | :--- | :--- |
| **Hand** | **0°** (Vertical) | **90°** (Stand up to Vertical) |
| **Stage** | **0°** (Vertical) | N/A (Live cards not in Stage) |
| **Live Zone** | **90°** (Lay down to Landscape) | **0°** (Horizontal) |
| **Success Zone** | **90°** (Lay down to Landscape) | (MEMBER CARDS DO NOT GO HERE) |

### Key Rule: The "Vertical Hand" Policy
All cards in the player's hand MUST be vertical. Even though Live cards are natively horizontal, they must be rotated 90 degrees to stand upright while in the hand.

### Key Rule: The "Horizontal Live-Set" Policy
The Live Set/Live Zone is a horizontal space. Any card entering this space, including Members (typically performed to the zone), must be laid down horizontally.

## 4. Layout Priority (The "Board Math")

To ensure the Stage and Live zones are always the focus, the following flex ratios are enforced:

- **Field Row (Stage/Live)**: `flex: 20`
- **Hand Row**: `flex: 2.5`
- **Energy Row**: `flex: 0.1` (or fixed `30px-40px`)

## 5. Sidebar Responsibility

- **Left Sidebar**: Deck counts, Energy Deck counts, Discard visual + button.
- **Right Sidebar**: Success Zone (stacked Landscape cards), Rule Log, Actions.
- **Side Column Width**: Standardized to `140px` to comfortably fit landscape-rotated cards in the Success Zone.
