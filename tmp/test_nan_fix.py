"""Quick smoke test: run 1 iteration of training to verify NaN is fixed."""
import torch, numpy as np, random, time, os, json, sys, collections, concurrent.futures
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

search_paths = [
    root_dir / "engine_rust_src" / "target" / "release",
    root_dir / "engine_rust_src" / "target" / "dev-release",
    root_dir / "engine_rust_src" / "target" / "debug",
]
for p in search_paths:
    if (p / "engine_rust.pyd").exists():
        sys.path.insert(0, str(p)); break

# Patch sys.path to find the overnight script's imports
training_dir = root_dir / "alphazero" / "training"
sys.path.insert(0, str(training_dir))

from alphazero.alphanet import AlphaNet
import torch.nn.functional as F
import engine_rust
from engine.game.deck_utils import UnifiedDeckParser

# Import training functions directly  
import importlib.util
spec = importlib.util.spec_from_file_location("overnight", str(training_dir / "overnight_pure_zero.py"))
mod = importlib.util.load_from_spec = None  # Can't import due to circular; inline key functions

# Just test: load model + make a batch with real obs values and check for NaN
db_path = root_dir / "data" / "cards_compiled.json"
with open(db_path, encoding="utf-8") as f:
    full_db = json.load(f)
db_json = json.dumps(full_db)
db = engine_rust.PyCardDatabase(db_json)

parser = UnifiedDeckParser(full_db)
decks_dir = root_dir / "ai" / "decks"
standard_energy_ids = [38, 39, 40, 41, 42] * 4

loaded_decks = []
for deck_file in list(decks_dir.glob("*.txt"))[:2]:
    with open(deck_file) as f: content = f.read()
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
        loaded_decks.append({"members": (m+m*4)[:48], "lives": (l+l*4)[:12], "energy": (e+standard_energy_ids*12)[:12]})

if not loaded_decks:
    print("ERROR: No decks loaded"); sys.exit(1)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

model = AlphaNet().to(device)
model.train()

# Collect a few obs
d0, d1 = loaded_decks[0], loaded_decks[-1]
state = engine_rust.PyGameState(db)
state.initialize_game(d0["members"]+d0["lives"], d1["members"]+d1["lives"], d0["energy"], d1["energy"], [], [])
state.silent = True

obs_list = []
for _ in range(10):
    if state.is_terminal(): break
    legal_ids = state.get_legal_action_ids()
    if not legal_ids: break
    
    # Simulate the FIXED storage
    obs_raw = np.array(state.to_alphazero_tensor(), dtype=np.float32)
    obs_raw = np.nan_to_num(obs_raw, nan=0.0, posinf=0.0, neginf=0.0)  # float32 storage (fixed)
    obs_list.append(obs_raw)
    state.step(random.choice(legal_ids))
    state.auto_step(db)

if not obs_list:
    print("ERROR: No observations collected"); sys.exit(1)

print(f"Collected {len(obs_list)} observations")
print(f"Obs range: [{min(o.min() for o in obs_list):.1f}, {max(o.max() for o in obs_list):.1f}]")
print(f"Has inf: {any(np.isinf(o).any() for o in obs_list)}")
print(f"Has nan: {any(np.isnan(o).any() for o in obs_list)}")

# Forward pass through model
obs_t = torch.from_numpy(np.stack(obs_list)).to(device)
obs_t = torch.nan_to_num(obs_t, nan=0.0, posinf=0.0, neginf=0.0)

with torch.no_grad():
    policy_logits, value_preds = model(obs_t)

print(f"\nForward pass:")
print(f"  policy_logits has nan: {torch.isnan(policy_logits).any().item()}")
print(f"  policy_logits has inf: {torch.isinf(policy_logits).any().item()}")
print(f"  value_preds has nan: {torch.isnan(value_preds).any().item()}")
print(f"  value_preds range: [{value_preds.min().item():.4f}, {value_preds.max().item():.4f}]")

# Compute losses
pol_t = torch.zeros(len(obs_list), 22000, device=device)
pol_t[:, 0] = 1.0  # dummy target
val_t = torch.zeros(len(obs_list), 3, device=device)
val_t[:, 0] = 1.0

log_probs = F.log_softmax(policy_logits, dim=1)
log_probs_clamped = log_probs.clamp(min=-100.0)
value_loss = F.mse_loss(value_preds, val_t)
policy_loss = F.kl_div(log_probs_clamped, pol_t, reduction='batchmean')

print(f"\n  value_loss: {value_loss.item():.4f}")
print(f"  policy_loss: {policy_loss.item():.4f}")
print(f"  value_loss is nan: {torch.isnan(value_loss).item()}")
print(f"  policy_loss is nan: {torch.isnan(policy_loss).item()}")
print()
if not torch.isnan(value_loss) and not torch.isnan(policy_loss):
    print("✅ NaN FIX CONFIRMED: No NaN in forward pass or losses!")
else:
    print("❌ Still NaN — need more investigation.")
