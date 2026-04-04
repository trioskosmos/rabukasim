# Consolidated Handler System

This directory contains the ability handler system with a unified dispatch architecture.

## Architecture

### Core Dispatch
- **`mod.rs`** - Centralized opcode dispatch into domain handlers

### Working Implementation Modules
The actual working implementations are organized by domain:

#### Score/Hearts Operations
- **`state_score_hearts.rs`** - Main dispatch for score/hearts opcodes
- **`state_score_bonus.rs`** - Score boosting, cost reduction, set score
- **`state_score_stats.rs`** - Blades, hearts, color transforms
- **`state_score_requirements.rs`** - Heart requirements and costs
- **`state_score_slots.rs`** - Slot targeting utilities
- **`state_score_transforms.rs`** - Heart/blade transformation logic

#### Member Operations
- **`state_member.rs`** - Main dispatch for member opcodes
- **`state_member_tap.rs`** - Tapping, activation
- **`state_member_position.rs`** - Movement, formation changes
- **`state_member_play.rs`** - Playing members from hand/discard
- **`state_member_play_*.rs`** - Play resolution and selection

#### Energy Operations
- **`state_energy.rs`** - Main dispatch for energy opcodes
- **`state_energy_charge.rs`** - Energy charging logic
- **`state_energy_action.rs`** - Energy activation
- **`state_energy_place.rs`** - Placing energy under members
- **`state_energy_place_select.rs`** - Selection for energy placement

#### Zone/Movement Operations
- **`movement_draw.rs`** - Drawing cards
- **`movement_deck.rs`** - Deck operations (search, order, look)
- **`movement_discard.rs`** - Discard pile operations
- **`movement_swap_zone.rs`** - Zone swapping

#### Flow/Control Operations
- **`flow_state_mod.rs`** - State-modifying flow opcodes
- **`flow_select.rs`** - Selection handling
- **`flow_select_resolve.rs`** - Selection result resolution
- **`flow_swap.rs`** - Swap-area and related control flow
- **`flow_meta_rule.rs`** - Meta rule processing
- **`flow_effects.rs`** - Effect resolution
- **`flow_context.rs`** - Context management
- **`flow_helpers.rs`** - Flow utilities

#### Interaction Operations
- **`interaction.rs`** - Main dispatch for interaction opcodes
- **`interaction_select_cards.rs`** - Card selection
- **`interaction_look_choose.rs`** - Look and choose operations
- **`interaction_recovery.rs`** - Recovery operations
- **`interaction_play_live.rs`** - Playing lives from discard
- **`interaction_zone.rs`** - Zone interactions

### Supporting Files
- **`state_helpers.rs`** - Shared utilities for state operations
- **`choice_prompt.rs`** - Choice prompting and NOP handling
- **`select_mode.rs`** - Select mode handling
- **`state_ops.rs`** - Re-exports of working implementations (consolidated entry point)

## Key Design Principles

### 1. Clear Dispatch Chain
- Single dispatch point in `mod.rs`
- Each opcode maps to a domain handler (state, movement, flow, interaction)
- Domain handlers dispatch to specific implementations

### 2. Domain Organization
- Score/Hearts: `handle_score_hearts` → `state_score_*.rs`
- Members: `handle_member_state` → `state_member_*.rs`
- Energy: `handle_energy` → `state_energy_*.rs`
- Zones: `handle_deck_zones` → `movement_*.rs`
- Flow: `handle_meta_control` → `flow_*.rs`

### 3. Working Code Only
All files contain actual working implementations - no stub code or placeholders.
