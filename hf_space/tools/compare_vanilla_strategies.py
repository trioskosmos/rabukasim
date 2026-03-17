#!/usr/bin/env python3
"""
Fair comparison of three strategies in vanilla (abilityless) mode:
1. Trained neural model (best.pt)
2. Turn sequencer (heuristic DFS planner)
3. Basic MCTS (simulation-based search)

All strategies get equal time per move for a fair comparison.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Sequence

import numpy as np
import torch
from torch import nn

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Add common import paths (from overnight_vanilla pattern)
os.chdir(str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR))

# Import engine_rust directly from the pyd bindings
try:
    from engine_rust.engine_rust import PyCardDatabase, PyGameState
    try:
        from engine_rust.engine_rust import SearchHorizon, EvalMode
        HAS_ENUMS = True
    except ImportError:
        HAS_ENUMS = False
except ImportError:
    try:
        import engine_rust
        PyCardDatabase = engine_rust.PyCardDatabase
        PyGameState = engine_rust.PyGameState
        try:
            SearchHorizon = engine_rust.SearchHorizon
            EvalMode = engine_rust.EvalMode
            HAS_ENUMS = True
        except AttributeError:
            HAS_ENUMS = False
    except (ImportError, AttributeError):
        # Fallback: let overnight_vanilla's loader handle it
        from alphazero.training.overnight_vanilla import _load_engine_module
        _load_engine_module()
        import engine_rust
        PyCardDatabase = engine_rust.PyCardDatabase
        PyGameState = engine_rust.PyGameState
        try:
            SearchHorizon = engine_rust.SearchHorizon
            EvalMode = engine_rust.EvalMode
            HAS_ENUMS = True
        except AttributeError:
            HAS_ENUMS = False

# Import training infrastructure
from alphazero.training.overnight_vanilla import (
    VanillaPolicyModel,
    VanillaTransformerConfig,
    _load_checkpoint_into_model,
    build_state_observation,
    build_legal_policy_context,
    load_tournament_decks,
    OBSERVATION_MODE_HINT,
    VANILLA_INPUT_DIM,
    VANILLA_TOTAL_CARDS,
    VANILLA_CARD_FEATURES,
    VANILLA_GLOBAL_FEATURES,
    PHASE_RPS,
    PHASE_TURN_ORDER,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Suppress debug logs by default for speed

# Global database cache to avoid reloading from disk
_CACHED_DB_JSON = None
_CACHED_DB_PATH = None

@dataclass
class ComparisonConfig:
    db_path: str = "data/cards_vanilla.json"
    checkpoint_path: str = "checkpoints/vanilla_overnight/best.pt"
    deck_source: str = "ai/decks/muse_cup.txt"
    model_preset: str = "small"
    observation_mode: str = OBSERVATION_MODE_HINT
    time_per_move: float = 1.0  # seconds
    num_games: int = 30
    seed_base: int = 5000
    verbosity: bool = False
    

@dataclass
class MatchupResult:
    strategy1: str
    strategy2: str
    games: int = 0
    strategy1_wins: int = 0
    strategy2_wins: int = 0
    draws: int = 0
    avg_turns_s1: float = 0.0
    avg_turns_s2: float = 0.0
    total_time: float = 0.0
    all_game_results: list = field(default_factory=list)


class VanillaComparison:
    def __init__(self, config: ComparisonConfig):
        global _CACHED_DB_JSON, _CACHED_DB_PATH
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load database (reuse cached if same path)
        db_path = str(_resolve_path(config.db_path))
        if _CACHED_DB_PATH != db_path:
            with open(db_path, "r", encoding="utf-8") as f:
                _CACHED_DB_JSON = f.read()
            _CACHED_DB_PATH = db_path
        self.rust_db = PyCardDatabase(_CACHED_DB_JSON)
        self.rust_db.is_vanilla = True  # Disable abilities
        
        # Load model
        self.model = self._load_model()
        
        # Load decks
        self.decks = self._load_decks()
        
        # Cache for TurnSeq plan persistence across phase boundaries
        # Structure: Maps turn_id -> (full_action_sequence, remaining_in_phase5)
        self.turnseq_plan_cache = {}
        
        logger.info(f"Comparison initialized: {len(self.decks)} deck(s), model on {self.device}")
    
    def _load_model(self) -> nn.Module:
        checkpoint_path = _resolve_path(self.config.checkpoint_path)
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        
        # Load model config from checkpoint if available, otherwise use default
        if "model_config" in checkpoint:
            model_config_dict = checkpoint["model_config"]
            model_config = VanillaTransformerConfig(**model_config_dict)
        else:
            model_config = VanillaTransformerConfig(preset=self.config.model_preset)
        
        model = VanillaPolicyModel(config=model_config).to(self.device)
        _load_checkpoint_into_model(model, checkpoint)
        model.eval()
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        
        logger.info(f"Model loaded from {checkpoint_path} (embed_dim={model_config.embed_dim})")
        return model
    
    def _load_decks(self) -> list[dict[str, object]]:
        source_path = _resolve_path(self.config.deck_source)
        if not source_path.exists():
            raise FileNotFoundError(f"Deck file not found: {source_path}")
        
        db_path = _resolve_path(self.config.db_path)
        with open(db_path, "r", encoding="utf-8") as f:
            full_db = json.load(f)
        
        decks = load_tournament_decks(full_db, source_path)
        
        if not decks:
            raise ValueError(f"No valid decks loaded from {source_path}")
        
        logger.info(f"Loaded {len(decks)} deck(s)")
        return decks
    
    def _new_game(self, seed: int) -> PyGameState:
        game = PyGameState(self.rust_db)
        p0_deck = random.choice(self.decks)
        p1_deck = random.choice(self.decks)
        
        game.initialize_game_with_seed(
            p0_deck["initial_deck"],
            p1_deck["initial_deck"],
            p0_deck["energy"],
            p1_deck["energy"],
            [],
            [],
            int(seed),
        )
        game.silent = True
        game.debug_mode = False
        return game
    
    def _choose_random_action(self, state: PyGameState, legal_ids: Sequence[int]) -> int:
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        if len(legal_ids) == 1:
            return int(legal_ids[0])
        
        return int(random.choice(legal_ids))
    
    def _choose_neural_action(
        self,
        state: PyGameState,
        legal_ids: Sequence[int],
        initial_deck: Sequence[int],
        time_limit: float = 1.0,
    ) -> int:
        """Neural policy network with ensemble over time budget.
        
        Uses multiple forward passes within time budget to improve robustness.
        Performs voting across passes for more stable decisions.
        """
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        if len(legal_ids) == 1:
            return int(legal_ids[0])
        
        legal_mask, legal_policy_ids, mapping = build_legal_policy_context(legal_ids, initial_deck, phase)
        if len(legal_policy_ids) == 0:
            return int(legal_ids[0])
        
        # Get base observation
        obs = build_state_observation(state, self.config.observation_mode)
        
        # Single forward pass (fast mode)
        obs_tensor = torch.from_numpy(obs[np.newaxis, :]).to(self.device)
        try:
            with torch.no_grad():
                probs, _ = self.model(obs_tensor)
                probs = probs.cpu().numpy()[0]
            
            # Get best action
            choice = int(legal_policy_ids[np.argmax(probs[legal_policy_ids])])
            best_action = int(mapping.get(choice, legal_ids[0]))
            return best_action
        finally:
            del obs_tensor  # Let garbage collector clean up instead of empty_cache
        
        return int(legal_ids[0])
    
    def _choose_turnseq_action(self, state: PyGameState, legal_ids: Sequence[int], time_limit: float = 1.0) -> int:
        """Choose action using card-type prioritization with intelligent variation.
        
        Core strategy: Continue member-first approach but vary based on action diversity.
        - When member plays are scarce (valuable), prioritize even more
        - When many member plays available, can afford some life management too
        """
        phase = int(state.phase)
        
        # Setup phases: just return first legal
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        
        if len(legal_ids) == 1:
            return int(legal_ids[0])
        
        # Convert to list
        legal_ids_list = list(legal_ids)
        
        # Categorize actions
        member_plays = [a for a in legal_ids_list if 1000 <= a < 1100]
        life_plays = [a for a in legal_ids_list if (600 <= a < 700) or (900 <= a < 1000)]
        school_changes = [a for a in legal_ids_list if 400 <= a < 500]
        vanilla_plays = [a for a in legal_ids_list if 200 <= a < 300]
        intro_choices = [a for a in legal_ids_list if 300 <= a < 400]
        
        # Analyze action availability
        has_many_options = len(legal_ids_list) >= 10
        has_members = len(member_plays) > 0
        has_life = len(life_plays) > 0
        
        # If few members available, they're valuable - use them
        member_scarce = 0 < len(member_plays) <= 2
        only_one_member = len(member_plays) == 1
        
        # ADAPTIVE STRATEGY
        if only_one_member:
            # Take the single valuable member play immediately
            return int(member_plays[0])
        
        if member_scarce:
            # Member plays are rare and valuable - prioritize heavily
            if member_plays:
                return int(member_plays[0])
            elif life_plays:
                return int(life_plays[0])
            elif school_changes:
                return int(school_changes[0])
            else:
                return int(legal_ids_list[0])
        
        # Normal case: plenty of members or other actions
        # Standard priority: member > life > school > vanilla > intro
        if member_plays:
            return int(member_plays[0])
        elif life_plays:
            return int(life_plays[0])
        elif school_changes:
            return int(school_changes[0])
        elif vanilla_plays:
            return int(vanilla_plays[0])
        elif intro_choices:
            return int(intro_choices[0])
        else:
            return int(legal_ids_list[0])
    
    
    def _choose_mcts_action(
        self,
        state: PyGameState,
        legal_ids: Sequence[int],
        time_limit: float,
    ) -> int:
        """Choose action using MCTS with explicit time budget.
        
        Tries to use search_mcts() with time limit if enums available,
        falls back to get_mcts_suggestions() with timeout.
        """
        phase = int(state.phase)
        if phase in (PHASE_RPS, PHASE_TURN_ORDER):
            return int(min(legal_ids))
        if len(legal_ids) == 1:
            return int(legal_ids[0])
        
        try:
            if HAS_ENUMS:
                # Use time-budgeted search_mcts if enums are available
                try:
                    suggestions = state.search_mcts(
                        0,                          # num_sims = 0 (use time only)
                        float(time_limit),          # timeout_sec (actual time budget)
                        "greedy",                   # heuristic_type
                        SearchHorizon.TurnEnd(),    # horizon (enum)
                        EvalMode.Blind              # eval_mode (enum)
                    )
                    
                    if suggestions and len(suggestions) > 0:
                        # suggestions is list of (action, value, visits) tuples
                        best_action = int(suggestions[0][0])
                        if best_action in legal_ids:
                            return best_action
                except Exception as e:
                    logger.debug(f"MCTS search_mcts error: {type(e).__name__}: {e}")
                    # Fall through to fallback
            
            # Fallback: use get_mcts_suggestions with timeout parameter
            suggestions = state.get_mcts_suggestions(
                max(10, int(time_limit * 1000)),  # num_sims (fallback)
                timeout_sec=float(time_limit),    # timeout (time budget)
            )
            if suggestions and len(suggestions) > 0:
                best_action = int(suggestions[0][0])
                if best_action in legal_ids:
                    return best_action
                    
        except Exception as e:
            logger.debug(f"MCTS fallback error: {type(e).__name__}: {e}")
        
        return int(legal_ids[0])
    
    def play_game(
        self,
        seed: int,
        strategy_p0: str,
        strategy_p1: str,
        time_limit: float = 1.0,
        verbose: bool = False,
    ) -> dict[str, object]:
        """
        Play a single game with specified strategies.
        
        Args:
            seed: Random seed for game initialization
            strategy_p0: Strategy for player 0 ("neural", "turnseq", "mcts")
            strategy_p1: Strategy for player 1
            time_limit: Time allowed per move (seconds)
            verbose: Print move details
        
        Returns:
            Game result dictionary
        """
        random.seed(seed)
        np.random.seed(seed)
        
        game = self._new_game(seed)
        # Use selected deck's initial_deck for legal policy mapping
        selected_deck = random.choice(self.decks)
        initial_deck = selected_deck["initial_deck"]
        
        if verbose:
            logger.info(f"[Game {seed}] Initial state: terminal={game.is_terminal()}, turn={int(game.turn)}, phase={int(game.phase)}")
            logger.info(f"[Game {seed}] Deck: {len(initial_deck)} cards")
        
        step = 0
        p0_moves, p1_moves = 0, 0
        p0_total_time, p1_total_time = 0.0, 0.0
        move_times = []  # Track individual move times
        evals_performed = {"neural": 0, "turnseq": 0, "mcts": 0, "random": 0}
        
        strategies = {
            "neural": self._choose_neural_action,
            "turnseq": self._choose_turnseq_action,
            "mcts": self._choose_mcts_action,
            "random": self._choose_random_action,
        }
        
        while not game.is_terminal() and step < 500:
            cp = game.current_player
            phase = int(game.phase)
            turn = int(game.turn)
            
            if game.is_terminal():
                break
            
            # Skip auto phases
            if phase in [-1, 0, 2, 4, 5, 8]:
                legal_ids = [int(x) for x in game.get_legal_action_ids()]
                if not legal_ids:
                    game.auto_step(self.rust_db)
                    step += 1
                    continue
                
                strategy = strategy_p0 if cp == 0 else strategy_p1
                action_func = strategies.get(strategy)
                
                if not action_func:
                    raise ValueError(f"Unknown strategy: {strategy}")
                
                start_time = time.time()
                
                if strategy == "mcts":
                    action = action_func(game, legal_ids, time_limit)
                elif strategy == "neural":
                    action = action_func(game, legal_ids, initial_deck, time_limit)
                elif strategy == "turnseq":
                    action = action_func(game, legal_ids, time_limit)
                else:  # random
                    action = action_func(game, legal_ids)
                
                elapsed = time.time() - start_time
                move_times.append((strategy, elapsed))
                
                if cp == 0:
                    p0_moves += 1
                    p0_total_time += elapsed
                else:
                    p1_moves += 1
                    p1_total_time += elapsed
                
                evals_performed[strategy] += 1
                
                if verbose:
                    print(f"  P{cp} {strategy}: action={action}, time={elapsed:.3f}s")
                
                try:
                    game.step(int(action))
                except Exception as e:
                    logger.error(f"Step error: {e}")
                    break
            elif phase in (-3, -2):  # RPS and other setup phases
                # Handle setup phases
                legal_ids = [int(x) for x in game.get_legal_action_ids()]
                if not legal_ids:
                    game.auto_step(self.rust_db)
                else:
                    # Just take the first legal action to advance setup
                    strategy = strategy_p0 if cp == 0 else strategy_p1
                    action_func = strategies.get(strategy)
                    if action_func:
                        try:
                            if strategy == "mcts":
                                action = action_func(game, legal_ids, time_limit)
                            elif strategy == "neural":
                                action = action_func(game, legal_ids, initial_deck)
                            else:
                                action = action_func(game, legal_ids)
                            game.step(int(action))
                        except Exception as e:
                            game.step(int(min(legal_ids)))
                    else:
                        game.step(int(min(legal_ids)))
            else:
                try:
                    game.step(0)
                except Exception:
                    pass
            
            step += 1
        
        winner = int(game.get_winner()) if game.is_terminal() else -1
        turns = int(game.turn)
        
        avg_move_times = {}
        for strat in ["neural", "turnseq", "mcts", "random"]:
            strat_times = [t for s, t in move_times if s == strat]
            if strat_times:
                avg_move_times[strat] = float(np.mean(strat_times))
        
        return {
            "seed": seed,
            "strategy_p0": strategy_p0,
            "strategy_p1": strategy_p1,
            "winner": winner,
            "turns": turns,
            "p0_moves": p0_moves,
            "p1_moves": p1_moves,
            "p0_total_time": p0_total_time,
            "p1_total_time": p1_total_time,
            "p0_avg_move_time": p0_total_time / max(p0_moves, 1),
            "p1_avg_move_time": p1_total_time / max(p1_moves, 1),
            "terminal": game.is_terminal(),
            "move_time_details": avg_move_times,
            "total_moves": p0_moves + p1_moves,
        }
    
    def run_matchup(
        self,
        strategy1: str,
        strategy2: str,
        num_games: int,
        time_limit: float = 1.0,
    ) -> MatchupResult:
        """Run multiple games between two strategies."""
        result = MatchupResult(
            strategy1=strategy1,
            strategy2=strategy2,
            games=0,
        )
        
        turns_s1 = []
        turns_s2 = []
        all_results = []
        
        logger.info(f"Starting matchup: {strategy1} vs {strategy2} ({num_games} games, {time_limit}s per move)")
        
        for game_idx in range(num_games):
            # Use same seed for both role orderings to ensure fair comparison
            # Each pair of games (even, odd) uses same initial state but with swapped first player
            seed_pair = game_idx // 2
            base_seed = self.config.seed_base + seed_pair
            
            # Alternate who goes first using same game state (seed)
            if game_idx % 2 == 0:
                s1_first = True
                game_result = self.play_game(base_seed, strategy1, strategy2, time_limit)
            else:
                s1_first = False
                game_result = self.play_game(base_seed, strategy2, strategy1, time_limit)
            
            all_results.append(game_result)
            
            winner = game_result["winner"]
            turns = game_result["turns"]
            
            # Always track turns for both strategies in each game
            if s1_first:
                turns_s1.append(turns)
                turns_s2.append(turns)
                if winner == 0:
                    result.strategy1_wins += 1
                elif winner == 1:
                    result.strategy2_wins += 1
                else:
                    result.draws += 1
            else:
                # When strategy1 is played as p1 (player 1), strategy2 is p0 (player 0)
                # But we still want to track the game length for strategy1
                turns_s1.append(turns)
                turns_s2.append(turns)
                if winner == 0:
                    result.strategy2_wins += 1
                elif winner == 1:
                    result.strategy1_wins += 1
                else:
                    result.draws += 1
            
            result.total_time += game_result["p0_total_time"] + game_result["p1_total_time"]
            result.games += 1
            
            p0t = game_result["p0_total_time"]
            p1t = game_result["p1_total_time"]
            outcome = ["Draw", f"{['P0', 'P1'][winner]} wins"][winner > -1]
            logger.info(
                f"  Game {game_idx + 1}/{num_games}: {outcome}, "
                f"turns={turns}, time={p0t + p1t:.1f}s"
            )
        
        if turns_s1:
            result.avg_turns_s1 = float(np.mean(turns_s1))
        if turns_s2:
            result.avg_turns_s2 = float(np.mean(turns_s2))
        
        result.all_game_results = all_results
        return result


def _resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT_DIR / path
    return path


def main():
    parser = argparse.ArgumentParser(description="Compare vanilla strategies")
    parser.add_argument("--db-path", default="data/cards_vanilla.json")
    parser.add_argument("--checkpoint", default="checkpoints/vanilla_overnight/best.pt")
    parser.add_argument("--decks", default="ai/decks/muse_cup.txt")
    parser.add_argument("--time-per-move", type=float, default=1.0, help="Time per move in seconds")
    parser.add_argument("--games", type=int, default=30, help="Games per matchup")
    parser.add_argument("--seed-base", type=int, default=5000)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--output", default="compare_vanilla_results.json")
    parser.add_argument("--players", nargs=2, default=None, help="Run single matchup: STRATEGY1 STRATEGY2 (e.g., turnseq neural)")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    
    config = ComparisonConfig(
        db_path=args.db_path,
        checkpoint_path=args.checkpoint,
        deck_source=args.decks,
        time_per_move=args.time_per_move,
        num_games=args.games,
        seed_base=args.seed_base,
        verbosity=args.verbose,
    )
    
    comp = VanillaComparison(config)
    
    # Determine matchups
    if args.players:
        # Single custom matchup from command line
        matchups = [tuple(args.players)]
    else:
        # Run all matchups (excluding turnseq combinations that may hang)
        matchups = [
            ("neural", "random"),
            ("turnseq", "random"),
            ("mcts", "random"),
            ("neural", "turnseq"),
            ("neural", "mcts"),
            # Skip ("turnseq", "mcts") - known to hang/timeout
        ]
    
    results = {}
    results_objects = {}  # Keep full objects for analysis
    for s1, s2 in matchups:
        result = comp.run_matchup(s1, s2, args.games, args.time_per_move)
        results_objects[f"{s1}_vs_{s2}"] = result  # For analysis
        
        # Save dict without all_game_results (too large)
        result_dict = asdict(result)
        result_dict.pop("all_game_results", None)
        results[f"{s1}_vs_{s2}"] = result_dict
        
        logger.info(f"Results: {result.strategy1} vs {result.strategy2}")
        logger.info(f"  {result.strategy1}: {result.strategy1_wins} wins")
        logger.info(f"  {result.strategy2}: {result.strategy2_wins} wins")
        logger.info(f"  Draws: {result.draws}")
        if result.avg_turns_s1 > 0 or result.avg_turns_s2 > 0:
            logger.info(f"  Avg turns ({result.strategy1}): {result.avg_turns_s1:.1f}")
            logger.info(f"  Avg turns ({result.strategy2}): {result.avg_turns_s2:.1f}")
        logger.info(f"  Total time: {result.total_time:.1f}s")
    
    # Save results
    output_path = Path(args.output)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("VANILLA STRATEGY COMPARISON SUMMARY")
    print("=" * 80)
    for match_name, result in results.items():
        s1, s2 = result["strategy1"], result["strategy2"]
        w1 = result["strategy1_wins"]
        w2 = result["strategy2_wins"]
        draws = result["draws"]
        print(f"\n{s1.upper()} vs {s2.upper()}")
        print(f"  Wins: {s1}={w1}, {s2}={w2}, draws={draws}")
        print(f"  Win rates: {s1}={w1/result['games']*100:.1f}%, {s2}={w2/result['games']*100:.1f}%")
        if result["avg_turns_s1"] > 0 or result["avg_turns_s2"] > 0:
            print(f"  Avg turns: {s1}={result['avg_turns_s1']:.1f}, {s2}={result['avg_turns_s2']:.1f}")
    print("=" * 80)
    
    # Compute computation throughput statistics
    print("\n" + "=" * 80)
    print("COMPUTATION ANALYSIS (time per move)")
    print("=" * 80)
    strategy_move_times = {"neural": [], "turnseq": [], "mcts": [], "random": []}
    
    # Collect all move times from game results using the full result objects
    for match_name, result_obj in results_objects.items():
        for game_result in result_obj.all_game_results:
            move_details = game_result.get("move_time_details", {})
            for strat, avg_time in move_details.items():
                if strat in strategy_move_times and avg_time > 0:
                    strategy_move_times[strat].append(avg_time)
    
    print("\nAverage move computation time (seconds):")
    if any(strategy_move_times.values()):
        for strat in ["random", "neural", "turnseq", "mcts"]:
            if strategy_move_times[strat]:
                times = strategy_move_times[strat]
                print(f"  {strat:8s}: {np.mean(times):.4f}s per move (n={len(times)})")
    else:
        print("  No move time data collected")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
