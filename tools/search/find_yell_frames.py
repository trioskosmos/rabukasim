import json


def find_yells(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    states = data.get("states", [])
    prev_scores = [0, 0]
    yell_frames = []

    for i, state in enumerate(states):
        current_scores = [len(p.get("success_lives", [])) for p in state.get("players", [])]

        # Check if score increased for either player
        if current_scores[0] > prev_scores[0]:
            yell_frames.append({"frame": i, "player": 0, "new_score": current_scores[0], "turn": state.get("turn")})
        if current_scores[1] > prev_scores[1]:
            yell_frames.append({"frame": i, "player": 1, "new_score": current_scores[1], "turn": state.get("turn")})

        prev_scores = current_scores

    return yell_frames


if __name__ == "__main__":
    yells = find_yells("replays/game_14.json")
    print("Yell Events in Game #14:")
    for y in yells:
        print(f"Frame {y['frame']}: Player {y['player']} Yell! (Score {y['new_score']}, Turn {y['turn']})")
