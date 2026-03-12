"""
Comprehensive heuristic tuning framework with profiling and A/B testing.

Features:
- Systematic weight space exploration
- Alpha-beta pruning effectiveness measurement
- Per-heuristic sensitivity analysis
- Win rate vs eval efficiency trade-off analysis
"""

import json
import time
import subprocess
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import multiprocessing as mp
from itertools import product

# Workspace root discovery
SCRIPT_DIR = Path(__file__).parent
WORKSPACE_ROOT = SCRIPT_DIR.parent
ENGINE_BIN = WORKSPACE_ROOT / "engine_rust_src" / "target" / "release" / "simple_game.exe"

# Default weights ranges (min, max, default)
WEIGHT_RANGES = {
    'board_presence': (1.0, 3.0, 2.0),
    'blades': (0.5, 2.5, 1.75),
    'hearts': (0.5, 2.5, 1.5),
    'saturation_bonus': (2.0, 6.0, 4.0),
    'energy_penalty': (0.0, 1.0, 0.2),
    'live_ev_multiplier': (10.0, 30.0, 18.0),
    'uncertainty_penalty_pow': (0.5, 2.5, 1.2),
    'liveset_placement_bonus': (2.0, 10.0, 6.0),
}

SEARCH_PARAMS = {
    'max_dfs_depth': (8, 12, 10),
    'use_alpha_beta': (True, True, True),  # (min, max, default) - boolean
}


@dataclass
class BenchmarkConfig:
    """Benchmark configuration and results."""
    weights: Dict[str, float]
    search_params: Dict[str, any]
    use_alpha_beta: bool = True
    
    # Results
    win_rate: float = 0.0
    avg_score_p0: float = 0.0
    avg_turns: float = 0.0
    total_evaluations: int = 0
    elapsed_secs: float = 0.0
    sqps: float = 0.0  # "Sequences" per second = evals/s
    
    def efficiency_score(self) -> Tuple[float, float, float]:
        """Return ranking tuple: (win_rate, avg_score, sqps) for sorting."""
        return (self.win_rate, self.avg_score_p0, self.sqps)
    
    def to_dict(self) -> dict:
        return asdict(self)


class HeuristicTuner:
    """Framework for tuning heuristic weights through systematic exploration."""
    
    def __init__(self, games_per_config: int = 2, timeout_sec: int = 180):
        self.games_per_config = games_per_config
        self.timeout_sec = timeout_sec
        self.results: List[BenchmarkConfig] = []
    
    def run_benchmark(self, config: BenchmarkConfig) -> Optional[BenchmarkConfig]:
        """Execute a single benchmark configuration."""
        try:
            # Build command
            weight_args = []
            for k, v in config.weights.items():
                weight_args.append(f"--weight")
                weight_args.append(f"{k}={v:.4f}")
            
            search_args = []
            if isinstance(config.search_params.get('max_dfs_depth'), int):
                search_args.append("--weight")
                search_args.append(f"max_dfs_depth={config.search_params['max_dfs_depth']}")
            
            # Add flags for search options
            if not config.use_alpha_beta:
                search_args.append("--no-alpha-beta")
            
            if not config.search_params.get('use_memoization', True):
                search_args.append("--no-memo")
            
            if config.search_params.get('beam_search', False):
                search_args.append("--beam-search")
            
            cmd = [
                str(ENGINE_BIN),
                "--games", str(self.games_per_config),
                "--json",
            ] + weight_args + search_args
            
            # Run with environment setup
            env = os.environ.copy()
            cpu_count = mp.cpu_count()
            env['RAYON_NUM_THREADS'] = str(max(1, cpu_count // 2))
            
            start = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout_sec,
                cwd=str(WORKSPACE_ROOT),
                env=env,
            )
            elapsed = time.time() - start
            
            if result.returncode != 0:
                print(f"  ✗ Error: {result.stderr[:200]}")
                return None
            
            # Parse JSON output
            try:
                output = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"  ✗ JSON parse error: {e}")
                print(f"    stdout: {result.stdout[:200]}")
                return None
            
            # Extract metrics
            config.win_rate = output.get('p0_win_rate', 0.0)
            config.avg_score_p0 = output.get('avg_score_p0', 0.0)
            config.avg_turns = output.get('avg_turns', 0.0)
            config.total_evaluations = output.get('total_evaluations', 0)
            config.elapsed_secs = elapsed
            config.sqps = config.total_evaluations / elapsed if elapsed > 0 else 0
            
            return config
        
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout after {self.timeout_sec}s")
            return None
        except Exception as e:
            print(f"  ✗ Exception: {e}")
            return None
    
    def test_single_weight_sensitivity(
        self,
        weight_name: str,
        values: List[float],
        base_config: Optional[Dict[str, float]] = None,
        search_params: Optional[Dict] = None,
        use_alpha_beta: bool = True,
    ) -> List[BenchmarkConfig]:
        """Test sensitivity of a single weight across multiple values."""
        if base_config is None:
            base_config = {k: r[2] for k, r in WEIGHT_RANGES.items()}
        if search_params is None:
            search_params = {k: r[2] for k, r in SEARCH_PARAMS.items()}
        
        results = []
        print(f"\n{'='*60}")
        print(f"Testing sensitivity of '{weight_name}'")
        print(f"{'='*60}")
        
        for val in values:
            weights = base_config.copy()
            weights[weight_name] = val
            config = BenchmarkConfig(weights=weights, search_params=search_params, use_alpha_beta=use_alpha_beta)
            
            print(f"\n  Testing {weight_name}={val:.3f}...", end=' ', flush=True)
            result = self.run_benchmark(config)
            
            if result:
                results.append(result)
                print(f"✓ {result.sqps:.0f} eval/s | {result.win_rate:.1%} WR | {result.avg_score_p0:.2f} avg")
            else:
                print(f"✗ Failed")
        
        return results
    
    def test_alpha_beta_effectiveness(
        self,
        base_config: Optional[Dict[str, float]] = None,
        search_params: Optional[Dict] = None,
        trials: int = 2,
    ) -> Tuple[BenchmarkConfig, BenchmarkConfig]:
        """A/B test alpha-beta pruning vs pure negamax."""
        if base_config is None:
            base_config = {k: r[2] for k, r in WEIGHT_RANGES.items()}
        if search_params is None:
            search_params = {k: r[2] for k, r in SEARCH_PARAMS.items()}
        
        print(f"\n{'='*60}")
        print(f"A/B Testing: Alpha-Beta vs Negamax (pure DFS)")
        print(f"{'='*60}")
        
        # Alpha-beta
        print(f"\n  Testing WITH alpha-beta pruning ({trials} games)...", end=' ', flush=True)
        config_ab = BenchmarkConfig(
            weights=base_config.copy(),
            search_params=search_params.copy(),
            use_alpha_beta=True,
        )
        result_ab = self.run_benchmark(config_ab)
        if result_ab:
            print(f"✓ {result_ab.sqps:.0f} eval/s | {result_ab.win_rate:.1%} WR")
        else:
            print("✗ Failed")
            result_ab = config_ab
        
        # Pure negamax
        print(f"\n  Testing WITHOUT alpha-beta (pure DFS) ({trials} games)...", end=' ', flush=True)
        config_nm = BenchmarkConfig(
            weights=base_config.copy(),
            search_params=search_params.copy(),
            use_alpha_beta=False,
        )
        result_nm = self.run_benchmark(config_nm)
        if result_nm:
            print(f"✓ {result_nm.sqps:.0f} eval/s | {result_nm.win_rate:.1%} WR")
        else:
            print("✗ Failed")
            result_nm = config_nm
        
        # Compare
        if result_ab and result_nm:
            speedup = result_ab.sqps / result_nm.sqps if result_nm.sqps > 0 else 1.0
            node_reduction = (1.0 - result_ab.total_evaluations / result_nm.total_evaluations) * 100 if result_nm.total_evaluations > 0 else 0
            print(f"\n  {'─'*50}")
            print(f"  Speedup: {speedup:.2f}x")
            print(f"  Node reduction: {node_reduction:.1f}%")
            print(f"  {'─'*50}")
        
        return result_ab, result_nm
    
    def grid_search(
        self,
        weight_names: List[str],
        value_sets: List[List[float]],
        base_config: Optional[Dict[str, float]] = None,
        search_params: Optional[Dict] = None,
    ) -> List[BenchmarkConfig]:
        """Grid search over multiple weights."""
        if base_config is None:
            base_config = {k: r[2] for k, r in WEIGHT_RANGES.items()}
        if search_params is None:
            search_params = {k: r[2] for k, r in SEARCH_PARAMS.items()}
        
        results = []
        print(f"\n{'='*60}")
        print(f"Grid Search: {weight_names}")
        print(f"{'='*60}")
        
        total_combos = 1
        for vs in value_sets:
            total_combos *= len(vs)
        
        combo_idx = 0
        for values in product(*value_sets):
            weights = base_config.copy()
            for wname, val in zip(weight_names, values):
                weights[wname] = val
            
            combo_idx += 1
            config = BenchmarkConfig(weights=weights, search_params=search_params, use_alpha_beta=True)
            
            weight_str = " | ".join(f"{wname}={val:.2f}" for wname, val in zip(weight_names, values))
            print(f"\n  [{combo_idx}/{total_combos}] {weight_str}", end=' ', flush=True)
            
            result = self.run_benchmark(config)
            if result:
                results.append(result)
                print(f"✓ {result.sqps:.0f} eval/s | {result.win_rate:.1%} WR")
                self.results.append(result)
            else:
                print("✗ Failed")
        
        # Sort and display top results
        if results:
            results.sort(key=lambda c: c.efficiency_score(), reverse=True)
            print(f"\n{'─'*60}")
            print(f"Top 3 configurations:\n")
            for i, cfg in enumerate(results[:3], 1):
                print(f"  {i}. {cfg.sqps:.0f} eval/s | {cfg.win_rate:.1%} WR | {cfg.avg_score_p0:.2f} avg")
                for k, v in cfg.weights.items():
                    print(f"     {k}: {v:.3f}")
        
        return results
    
    def save_results(self, filename: str = "tuning_results.json"):
        """Save all results to JSON."""
        output_path = WORKSPACE_ROOT / filename
        data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_configs_tested': len(self.results),
            'best_config': self.results[0].to_dict() if self.results else None,
            'top_10': [cfg.to_dict() for cfg in sorted(
                self.results,
                key=lambda c: c.efficiency_score(),
                reverse=True
            )[:10]],
            'all_results': [cfg.to_dict() for cfg in self.results],
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nResults saved to {output_path}")


def main():
    """Example: comprehensive tuning suite."""
    tuner = HeuristicTuner(games_per_config=2, timeout_sec=180)
    
    # 1. A/B test alpha-beta effectiveness
    print("\n" + "="*70)
    print("PHASE 1: Measuring Alpha-Beta Pruning Effectiveness")
    print("="*70)
    ab_result, nm_result = tuner.test_alpha_beta_effectiveness()
    tuner.results.append(ab_result)
    tuner.results.append(nm_result)
    
    # 2. Single-weight sensitivity analysis
    print("\n" + "="*70)
    print("PHASE 2: Single-Weight Sensitivity Analysis")
    print("="*70)
    
    base_weights = {k: r[2] for k, r in WEIGHT_RANGES.items()}
    search_params = {k: r[2] for k, r in SEARCH_PARAMS.items()}
    
    # Test a few critical weights
    sensitivity_results = []
    for weight_name in ['board_presence', 'live_ev_multiplier', 'saturation_bonus']:
        min_val, max_val, default_val = WEIGHT_RANGES[weight_name]
        test_values = [
            min_val,
            min_val + (max_val - min_val) * 0.33,
            default_val,
            min_val + (max_val - min_val) * 0.67,
            max_val,
        ]
        results = tuner.test_single_weight_sensitivity(
            weight_name,
            test_values,
            base_config=base_weights,
            search_params=search_params,
        )
        sensitivity_results.extend(results)
        tuner.results.extend(results)
    
    # 3. Depth sensitivity (how does eval/s scale with depth?)
    print("\n" + "="*70)
    print("PHASE 3: Search Depth Sensitivity")
    print("="*70)
    print("\nTesting how eval/s scales with max_dfs_depth:")
    
    for depth in [8, 9, 10, 11]:
        search_p = search_params.copy()
        search_p['max_dfs_depth'] = depth
        cfg = BenchmarkConfig(weights=base_weights.copy(), search_params=search_p, use_alpha_beta=True)
        print(f"  Depth {depth}...", end=' ', flush=True)
        result = tuner.run_benchmark(cfg)
        if result:
            print(f"✓ {result.sqps:.0f} eval/s | {result.total_evaluations} nodes")
            tuner.results.append(result)
        else:
            print("✗ Failed")
    
    # 4. Grid search over top 2 weights
    print("\n" + "="*70)
    print("PHASE 4: Grid Search - Board Presence × Live EV Multiplier")
    print("="*70)
    
    bp_min, bp_max, bp_def = WEIGHT_RANGES['board_presence']
    lev_min, lev_max, lev_def = WEIGHT_RANGES['live_ev_multiplier']
    
    grid_results = tuner.grid_search(
        weight_names=['board_presence', 'live_ev_multiplier'],
        value_sets=[
            [bp_def - 0.5, bp_def, bp_def + 0.5],
            [lev_def - 5, lev_def, lev_def + 5],
        ],
        base_config=base_weights,
        search_params=search_params,
    )
    tuner.results.extend(grid_results)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    if tuner.results:
        sorted_results = sorted(tuner.results, key=lambda c: c.efficiency_score(), reverse=True)
        print(f"\nTested {len(tuner.results)} configurations")
        print(f"\nTop 5 configurations by efficiency (win rate → avg score → eval/s):\n")
        
        for i, cfg in enumerate(sorted_results[:5], 1):
            print(f"  {i}. Win Rate: {cfg.win_rate:>6.1%} | Avg Score: {cfg.avg_score_p0:>6.2f} | Speed: {cfg.sqps:>7.0f} eval/s")
            print(f"     Weights: " + ", ".join(f"{k}={v:.2f}" for k, v in cfg.weights.items()))
    
    tuner.save_results()


if __name__ == '__main__':
    main()
