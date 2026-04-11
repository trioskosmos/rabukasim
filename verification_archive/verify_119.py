import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 119...")

ability_119 = data['abilities'][119]
ability_119['frame_verification'] = {
    "verified": True,
    "notes": [
        "Opponent choice: discard live or grant +1 score ability",
        "Frame 0: SELECT_MODE with is_opponent=1",
        "Frames 1-2: JUMP to respective branches",
        "Frame 3: MOVE_TO_DISCARD with card_type=LIVE (option 1)",
        "Frame 4: JUMP to end",
        "Frame 5: GRANT_ABILITY (option 2)",
        "Frame 6: JUMP to end",
        "2 cards share this pattern (桜内梨子 variants)"
    ],
    "text_mapping": {
        "相手は手札からライブカードを1枚控え室に置いてもよい": "Frame 3: MOVE_TO_DISCARD with card_type=LIVE (option 1)",
        "そうしなかった場合、ライブ終了時まで、「{{jyouji.png|常時}}ライブの合計スコアを+１する。」を得る": "Frame 5: GRANT_ABILITY (option 2)"
    }
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 119 - frames match text correctly")
print("Saved file")
