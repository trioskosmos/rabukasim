import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read the file
with open('data/ability_frame_source.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Manually verifying ability 126...")

ability_126 = data['abilities'][126]
ability_126['frame_verification'] = {
    "verified": False,
    "issues": [
        "Frame 0: COUNT_STAGE uses group_id=LIELLA but text says '5yncri5e!'",
        "5yncri5e! is group_id=12, not LIELLA - wrong group filter"
    ],
    "text_mapping": {
        "自分のステージにいるメンバーが『5yncri5e!』のみの場合": "Frame 0: COUNT_STAGE (ISSUE: uses group_id=LIELLA, should be group_id=12 for 5yncri5e!)",
        "自分と対戦相手は、センターエリアのメンバーを左サイドエリアに、左サイドエリアのメンバーを右サイドエリアに、右サイドエリアのメンバーをセンターエリアに、それぞれ移動させる": "Frame 2: SWAP_AREA"
    },
    "required_frames": [
        "COUNT_STAGE should have group_id=12 for 5yncri5e! instead of LIELLA"
    ]
}

# Write back to file
with open('data/ability_frame_source.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Verified ability 126 - marked as unverified due to wrong group filter")
print("Saved file")
