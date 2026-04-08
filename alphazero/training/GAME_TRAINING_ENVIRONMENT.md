# Game Training Environment

`alphazero/training/game_training_env.py` is the minimal headless training
wrapper for the Rust engine.

Use this when you want an agent to learn the game without dragging in the
trainer-specific scoring and tracing metadata.

## What It Gives You

- the live Rust engine
- automatic prompt / ability / resolution handling
- compact observations from the engine tensor
- legal action masks
- a simple `reset()` / `step()` API
- turn-10 timeout handling based on `state.turn`

## What `info` Contains

The minimal env keeps `info` small:

- `turn`
- `phase`
- `current_player`
- `winner`
- `legal_action_ids`
- `legal_policy_ids`
- `action_mask`
- `legal_action_mask`

That is enough for a learning agent to act, store transitions, and train
without being tied to the more verbose trainer utilities.

## When To Use It

Use `GameTrainingEnv` if you want:

- a clean learning loop
- smaller `info` payloads
- fewer moving parts

Use `RealGameEnv` only if you specifically need the richer action metadata
and candidate-action features for debugging or analysis.

## Example

```python
from alphazero.training import make_game_training_env

env = make_game_training_env(seed=0, max_turns=10)
obs, info = env.reset()
print(obs.shape)
print(info["legal_action_ids"])

action = int(info["legal_action_ids"][0])
obs, reward, terminated, truncated, info = env.step(action)
```

## Notes

- `step()` accepts either a compact policy id or a raw engine action id.
- The environment still uses the live Rust engine and real rules.
- It does not expose hidden future deck order.

