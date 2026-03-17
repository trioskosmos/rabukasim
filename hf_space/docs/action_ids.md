# Lovecasim Action ID Mapping

This document details the mapping between numeric Action IDs and game engine logical actions.

## 🛠️ Global & Meta Actions

| ID Range | Action | Phase | Notes |
| :--- | :--- | :--- | :--- |
| **0** | **CONFIRM** | Any | Confirm, Pass, Next Turn, or Discard Rest. |
| **5000 - 5001** | **Turn Choice** | TurnChoice | 5000: Go First, 5001: Go Second. |
| **10000 - 10002**| **RPS (Player 1)** | Rps | 0: Rock, 1: Paper, 2: Scissors. |
| **11000 - 11002**| **RPS (Player 2)** | Rps | 0: Rock, 1: Paper, 2: Scissors. |

## 🏗️ Main Phase Actions

| ID Range | Action | Mapping Formula | Constraints |
| :--- | :--- | :--- | :--- |
| **1 - 180** | **Play Member** | `1 + (hand_idx * 3) + slot_idx` | Max 60 cards, 3 slots. |
| **200 - 229** | **Activate Stage** | `200 + (slot_idx * 10) + ab_idx` | 3 slots, 10 abilities/slot. |
| **550 - 849** | **Activated Choice**| `550 + (slot * 100) + (ab * 10) + choice` | Choice-specific activations. |
| **2000 - 2599** | **Activate Discard**| `2000 + (discard_idx * 10) + ab_idx` | 60 discard cards, 10 ab/card. |

## 💎 Response & Choice Actions (Interactive)

| ID Range | Action | Opcode / Usage | Notes |
| :--- | :--- | :--- | :--- |
| **300 - 309** | **Mode Selection** | `O_SELECT_MODE` | Legacy range. |
| **550 - 559** | **Generic List** | `O_SELECT_CARDS`, etc. | Top 10 cards. |
| **560 - 562** | **Slot Selection** | `O_PLAY_MEMBER_FROM...` | Target Stage Slots 0, 1, 2. |
| **580 - 585** | **Color Selection** | `O_COLOR_SELECT` | Pink, Red, Yellow, Green, Blue, Purple. |
| **600 - 602** | **Live Zone Target**| `O_TAP_O`, `LiveResult` | Target Live Slots 0, 1, 2. |

## 📦 Set Phase Actions

| ID Range | Action | Phase | Mapping |
| :--- | :--- | :--- | :--- |
| **300 - 359** | **Mulligan Toggle** | Mulligan | Toggles specific card in hand. |
| **400 - 459** | **Set Live Card** | LiveSet | `400 + hand_idx`. |

---
*Last updated: 2026-02-07*
