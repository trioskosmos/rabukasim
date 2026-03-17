import json

REPLAY_FILE = "replays/game_14.json"


def main():
    try:
        with open(REPLAY_FILE, "r", encoding="utf-8") as f:
            replay = json.load(f)
    except Exception as e:
        print(f"Failed: {e}")
        return

    print("=== P0 Stage History ===")

    replay_states = replay.get("states", [])
    print(f"Loaded {len(replay_states)} states.\n")

    prev_stage = [None, None, None]

    for i, state in enumerate(replay_states):
        p0 = state.get("players", [{}, {}])[0]
        stage = p0.get("stage", [])

        # Current stage as list of card names
        stage_names = []
        stage_ids = []
        for slot in stage:
            if slot:
                stage_names.append(slot.get("name", "???"))
                stage_ids.append(slot.get("id", "?"))
            else:
                stage_names.append("Empty")
                stage_ids.append(None)

        # Metadata
        phase = state.get("phase", "???")
        turn = state.get("turn", "?")
        act = state.get("action_taken", -1)
        player = state.get("current_player", -1)

        # Detect changes
        stage_changed = stage_ids != prev_stage

        # Interpret action
        action_desc = ""
        if 1 <= act <= 180:
            hand_idx = (act - 1) // 3
            area_idx = (act - 1) % 3
            action_desc = f"PLAY Hand[{hand_idx}] → Area[{area_idx}]"
        elif 200 <= act <= 202:
            area_idx = act - 200
            action_desc = f"ABILITY Area[{area_idx}]"
        elif act == 0:
            action_desc = "CONFIRM/NEXT"
        elif act == 300:
            action_desc = "CHARGE ENERGY"
        elif 400 <= act <= 459:
            action_desc = f"SET LIVE [{act}]"
        else:
            action_desc = f"Action {act}"

        if player == 0 and stage_changed:
            print(f"\nFrame {i}: T{turn} [{phase}] P{player}")
            print(f"  Action: {action_desc}")
            print(f"  Stage Before: {prev_stage}")
            print(f"  Stage After:  {stage_ids}")
            print(f"  Cards: {stage_names}")

        prev_stage = stage_ids.copy()


if __name__ == "__main__":
    main()
