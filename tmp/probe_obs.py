"""Quick probe: check actual obs tensor values from the Rust engine."""
import sys, json, random
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))

search = [
    root / "engine_rust_src" / "target" / "release",
    root / "engine_rust_src" / "target" / "dev-release",
    root / "engine_rust_src" / "target" / "debug",
]
for p in search:
    if (p / "engine_rust.pyd").exists():
        sys.path.insert(0, str(p)); break

import engine_rust
import numpy as np
from engine.game.deck_utils import UnifiedDeckParser

db_path = root / "data" / "cards_compiled.json"
with open(db_path, "r", encoding="utf-8") as f:
    full_db = json.load(f)

db_json = json.dumps(full_db)
db = engine_rust.PyCardDatabase(db_json)

parser = UnifiedDeckParser(full_db)
decks_dir = root / "ai" / "decks"
standard_energy_ids = [38, 39, 40, 41, 42] * 4

loaded_decks = []
for deck_file in list(decks_dir.glob("*.txt"))[:3]:
    with open(deck_file, "r", encoding="utf-8") as f:
        content = f.read()
    results = parser.extract_from_content(content)
    if not results: continue
    d = results[0]
    m, l, e = [], [], []
    for code in d['main']:
        cdata = parser.resolve_card(code)
        if not cdata: continue
        if cdata.get("type") == "Member": m.append(cdata["card_id"])
        elif cdata.get("type") == "Live": l.append(cdata["card_id"])
    for code in d['energy']:
        cdata = parser.resolve_card(code)
        if cdata: e.append(cdata["card_id"])
    if len(m) >= 30:
        loaded_decks.append({
            "members": (m + m*4)[:48],
            "lives": (l + l*4)[:12],
            "energy": (e + standard_energy_ids*12)[:12]
        })

if not loaded_decks:
    print("No decks found!"); sys.exit(1)

d0, d1 = loaded_decks[0], loaded_decks[min(1, len(loaded_decks)-1)]
state = engine_rust.PyGameState(db)
state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
state.silent = True
state.debug_mode = False

all_obs = []
steps = 0
while not state.is_terminal() and state.turn < 10:
    legal_ids = state.get_legal_action_ids()
    if not legal_ids: break
    obs = np.array(state.to_alphazero_tensor(), dtype=np.float32)
    all_obs.append(obs)
    state.step(random.choice(legal_ids))
    state.auto_step(db)
    steps += 1

if not all_obs:
    print("Game ended instantly."); sys.exit(1)

obs_stack = np.stack(all_obs)
print(f"Collected {len(all_obs)} observations over {steps} steps")
print(f"Obs shape: {obs_stack.shape}")
print(f"Value range: min={obs_stack.min():.4f}  max={obs_stack.max():.4f}")
print(f"  mean={obs_stack.mean():.4f}  std={obs_stack.std():.4f}")
print(f"  has_inf: {np.isinf(obs_stack).any()}")
print(f"  has_nan: {np.isnan(obs_stack).any()}")

# Show problematic buckets
bins = [-1e9, -1000, -100, -10, -1, 0, 1, 10, 100, 1000, 1e9]
hist, edges = np.histogram(obs_stack.flatten(), bins=bins)
print("\nValue distribution:")
for i, count in enumerate(hist):
    if count > 0:
        print(f"  [{edges[i]:.0f}, {edges[i+1]:.0f}): {count:,}")

# Check float16 safety
f16_safe = obs_stack[(obs_stack > -65000) & (obs_stack < 65000)]
overflow_count = obs_stack.size - f16_safe.size
print(f"\nFloat16 overflow count: {overflow_count} / {obs_stack.size}")
if overflow_count > 0:
    overflow_vals = obs_stack[(obs_stack <= -65000) | (obs_stack >= 65000)]
    print(f"  Overflow values: {overflow_vals[:20]}")
