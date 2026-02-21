# Love Live TCG - Action Space Mapping

This document defines the 2,000-dimensional action space used by the game engine. Each ID corresponds to a specific atomic action in the game.

## Main Map (Sorted by ID)

| ID Range | Category | Description | Parameters |
| :--- | :--- | :--- | :--- |
| **0** | **System** | Pass / Confirm / Skip / Cancel | N/A |
| **1 - 180** | **Play Member** | Play a member card from hand to stage | `(Hand Index 0-59) * 3 + (Slot Index 0-2)` |
| **200 - 202** | **Ability** | Activate a member's 【起動】 ability | `(Slot Index 0-2)` |
| **300 - 359** | **Mulligan** | Toggle selection of a card in hand for mulligan | `(Hand Index 0-59)` |
| **400 - 459** | **Live Set** | Set a card from hand face-down in the live zone | `(Hand Index 0-59)` |
| **500 - 559** | **Select Hand** | Select a card in hand for an effect (e.g. discard) | `(Hand Index 0-59)` |
| **560 - 562** | **Select Stage** | Select a member or slot on your side of the stage | `(Slot Index 0-2)` |
| **570 - 579** | **Modal** | Select option N from a modal choice effect | `(Option Index 0-9)` |
| **580 - 585** | **Color Select** | Select a member color (Pk, Rd, Bl, Gn, Yl, Pr) | `0=Pk, 1=Rd, 2=Bl, 3=Gn, 4=Yl, 5=Pr` |
| **590 - 599** | **Triggers** | Choose which pending trigger to resolve next | `(Trigger Index 0-9)` |
| **600 - 659** | **Generic List** | Select from a dynamic list (Look Deck, Deck) | `(List Index 0-59)` |
| **660 - 719** | **Discard List** | Select a card from the discard pile (Recovery) | `(List Index 0-59)` |
| **720 - 759** | **Formation** | Formation/Order items | `(Index 0-39)` |
| **760 - 819** | **Success Lives**| Select from the Success Live (Score) pile | `(List Index 0-59)` |
| **820 - 822** | **Live Zone** | Select a specific slot in the Live Zone | `(Slot Index 0-2)` |
| **830 - 849** | **Energy Zone** | Select a specific card in the Energy Zone | `(Index 0-19)` |
| **850 - 909** | **Removed/Opp** | Select from Removed cards or Opponent's Hand | `(Index 0-59)` |
| **910 - 912** | **Perform** | Select which Live card to attempt performance | `(Live Zone Index 0-2)` |
| **1000 - 1999**| **Reserved** | Reserved for future expansion | N/A |

## Choice Type Mapping

The engine uses `pending_choices` to contextually interpret these IDs.

| Choice Type | ID Range Used | Interpretation |
| :--- | :--- | :--- |
| `TARGET_HAND` | 500 - 559 | Hand Index |
| `TARGET_MEMBER` | 560 - 562 | Stage Slot Index |
| `DISCARD_SELECT` | 500 - 559 | Hand Index |
| `SELECT_FROM_LIST` | 600 - 659 | Index in provided `cards` list |
| `SELECT_FROM_DISCARD`| 660 - 719 | Index in discard selection list |
| `TARGET_OPPONENT_MEMBER`| 600 - 602 | Opponent's Slot Index |
| `COLOR_SELECT` | 580 - 585 | Color index |
| `MODAL` | 570 - 579 | Option index |

## Design Philosophy

1.  **Sparsity**: ranges are separated to allow the UI to easily map IDs to visual components without overlap.
2.  **Compatibility**: The fixed size (2,000) is designed for MCTS and RL models to have a consistent output head.
3.  **Extensibility**: Over 50% of the space is reserved for new card types or mechanics.
