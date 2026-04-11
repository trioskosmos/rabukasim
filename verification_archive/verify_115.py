import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 115...")

ability_115 = data['abilities'][115]
ability_115['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: SELECT_MEMBER missing exclude filter for 'ミア・テイラー以外' (other than Mia Taylor)",
        "Text specifically says to exclude Mia Taylor, but frame doesn't have char_id_1=MIA filter"
    ],
    "text_mapping": {
        "相手のステージにいる「ミア・テイラー」以外のメンバーを1人選ぶ": "Frame 0: SELECT_MEMBER (ISSUE: missing char_id_1=MIA exclude filter)",
        "そのメンバーが持つハートと、このメンバーが持つハートの中に同じ色のハートがある場合、ライブ終了時まで、{{icon_blade.png|ブレード}}を得る": "Frames 1-3: NOP + JUMP_IF_FALSE + ADD_BLADES",
        "それぞれのメンバーのコストが同じ場合、元々の{{icon_blade.png|ブレード}}の数が同じ場合についても同じことを行う": "Frames 4-9: Additional checks for cost and blades"
    },
    "required_frames": [
        "SELECT_MEMBER should have char_id_1=MIA to exclude Mia Taylor"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 115 - marked as unverified due to missing exclude filter")
print("Saved file")
